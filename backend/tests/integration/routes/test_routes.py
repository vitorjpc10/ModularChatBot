"""
Integration tests for API routes with TestClient and patched dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


pytestmark = pytest.mark.integration


class TestChatRoutes:
    """Test cases for chat routes."""

    def test_chat_endpoint_success(self, client: TestClient):
        """Test successful chat request."""
        request_data = {
            "message": "What are the card machine fees?",
            "user_id": "test_user_123",
            "conversation_id": "test_conv_456"
        }

        with patch('app.routes.chat.router_service.route_message') as mock_route, \
             patch('app.routes.chat.knowledge_service.get_response') as mock_knowledge:
            
            mock_route.return_value = {
                "agent": "KnowledgeAgent",
                "confidence": 0.9,
                "reasoning": "Knowledge question detected",
                "execution_time": 150,
                "method": "rule_based"
            }
            
            mock_knowledge.return_value = {
                "response": "Card machine fees are 2.5% per transaction",
                "source_content": "Fee information",
                "execution_time": 1200,
                "sources": ["https://example.com"]
            }

            response = client.post("/chat/", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "agent_workflow" in data
            assert "execution_time" in data
            assert data["conversation_id"] == request_data["conversation_id"]

    def test_chat_endpoint_math_request(self, client: TestClient):
        """Test math request routing."""
        request_data = {
            "message": "What is 5 + 3?",
            "user_id": "test_user_123",
            "conversation_id": "test_conv_456"
        }

        with patch('app.routes.chat.router_service.route_message') as mock_route, \
             patch('app.routes.chat.math_service.calculate') as mock_math:
            
            mock_route.return_value = {
                "agent": "MathAgent",
                "confidence": 0.9,
                "reasoning": "Mathematical expression detected",
                "execution_time": 100,
                "method": "rule_based"
            }
            
            mock_math.return_value = {
                "response": "5 plus 3 equals 8",
                "expression": "5+3",
                "result": "8",
                "execution_time": 800
            }

            response = client.post("/chat/", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "5 plus 3 equals 8" in data["response"]

    def test_chat_endpoint_invalid_request(self, client: TestClient):
        """Test chat endpoint with invalid request data."""
        invalid_requests = [
            {},  # Empty request
            {"message": "", "user_id": "test", "conversation_id": "test"},  # Empty message
            {"message": "test", "conversation_id": "test"},  # Missing user_id
            {"message": "test", "user_id": "test"},  # Missing conversation_id
        ]

        for request_data in invalid_requests:
            response = client.post("/chat/", json=request_data)
            assert response.status_code == 422  # Validation error

    def test_chat_endpoint_message_sanitization(self, client: TestClient):
        """Test message sanitization in chat endpoint."""
        malicious_request = {
            "message": "<script>alert('xss')</script>What are the fees?",
            "user_id": "test_user_123",
            "conversation_id": "test_conv_456"
        }

        with patch('app.routes.chat.router_service.route_message') as mock_route, \
             patch('app.routes.chat.knowledge_service.get_response') as mock_knowledge:
            
            mock_route.return_value = {
                "agent": "KnowledgeAgent",
                "confidence": 0.9,
                "reasoning": "Knowledge question detected",
                "execution_time": 150,
                "method": "rule_based"
            }
            
            mock_knowledge.return_value = {
                "response": "Here is information about fees",
                "source_content": "Fee information",
                "execution_time": 1200,
                "sources": ["https://example.com"]
            }

            response = client.post("/chat/", json=malicious_request)
            
            assert response.status_code == 200
            # The script tag should be removed from the message
            assert "<script>" not in mock_route.call_args[1]["message"]


class TestConversationRoutes:
    """Test cases for conversation routes."""

    def test_create_conversation_success(self, client: TestClient):
        """Test successful conversation creation."""
        conversation_data = {
            "conversation_id": "test_conv_789",
            "user_id": "test_user_123",
            "title": "Test Conversation"
        }

        response = client.post("/conversations/", json=conversation_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == conversation_data["conversation_id"]
        assert data["user_id"] == conversation_data["user_id"]
        assert data["title"] == conversation_data["title"]

    def test_get_conversation_success(self, client: TestClient):
        """Test successful conversation retrieval."""
        conversation_id = "test_conv_789"
        
        response = client.get(f"/conversations/{conversation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id

    def test_get_conversation_not_found(self, client: TestClient):
        """Test conversation retrieval when conversation doesn't exist."""
        conversation_id = "nonexistent_conv"
        
        response = client.get(f"/conversations/{conversation_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_user_conversations_success(self, client: TestClient):
        """Test successful user conversations retrieval."""
        user_id = "test_user_123"
        
        response = client.get(f"/conversations/user/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_conversation_title_success(self, client: TestClient):
        """Test successful conversation title update."""
        conversation_id = "test_conv_789"
        new_title = "Updated Title"
        
        response = client.put(f"/conversations/{conversation_id}/title?title={new_title}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == new_title

    def test_delete_conversation_success(self, client: TestClient):
        """Test successful conversation deletion."""
        conversation_id = "test_conv_789"
        
        response = client.delete(f"/conversations/{conversation_id}")
        
        assert response.status_code == 204

    def test_get_conversation_stats_success(self, client: TestClient):
        """Test successful conversation statistics retrieval."""
        conversation_id = "test_conv_789"
        
        response = client.get(f"/conversations/{conversation_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "agent_breakdown" in data


class TestMessageRoutes:
    """Test cases for message routes."""

    def test_create_message_success(self, client: TestClient):
        """Test successful message creation."""
        message_data = {
            "conversation_id": "test_conv_789",
            "content": "Test message content",
            "response": "Test response content",
            "source_agent": "KnowledgeAgent",
            "source_agent_response": "Test agent response",
            "agent_workflow": [
                {"agent": "RouterAgent", "decision": "KnowledgeAgent", "execution_time": 150},
                {"agent": "KnowledgeAgent", "execution_time": 1200}
            ],
            "execution_time": 1350
        }

        response = client.post("/messages/", json=message_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == message_data["conversation_id"]
        assert data["content"] == message_data["content"]

    def test_get_message_success(self, client: TestClient):
        """Test successful message retrieval."""
        message_id = 1
        
        response = client.get(f"/messages/{message_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id

    def test_get_message_not_found(self, client: TestClient):
        """Test message retrieval when message doesn't exist."""
        message_id = 999
        
        response = client.get(f"/messages/{message_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_conversation_messages_success(self, client: TestClient):
        """Test successful conversation messages retrieval."""
        conversation_id = "test_conv_789"
        
        response = client.get(f"/messages/conversation/{conversation_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_messages_success(self, client: TestClient):
        """Test successful user messages retrieval."""
        user_id = "test_user_123"
        
        response = client.get(f"/messages/user/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_update_message_success(self, client: TestClient):
        """Test successful message update."""
        message_id = 1
        update_data = {
            "response": "Updated response",
            "execution_time": 1500
        }

        response = client.put(f"/messages/{message_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == update_data["response"]

    def test_delete_message_success(self, client: TestClient):
        """Test successful message deletion."""
        message_id = 1
        
        response = client.delete(f"/messages/{message_id}")
        
        assert response.status_code == 204

    def test_get_message_stats_success(self, client: TestClient):
        """Test successful message statistics retrieval."""
        response = client.get("/messages/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_messages" in data
        assert "agent_breakdown" in data


class TestHealthRoutes:
    """Test cases for health check routes."""

    def test_health_check_basic(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_check_detailed(self, client: TestClient):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "ai_service" in data
        assert "overall_status" in data

    def test_health_check_ready(self, client: TestClient):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    
class TestErrorHandling:
    """Test cases for error handling."""

    def test_global_exception_handler(self, client: TestClient):
        """Test global exception handler."""
        response = client.get("/nonexistent_endpoint")
        
        # Should return a proper error response
        assert response.status_code in [404, 500]
        data = response.json()
        assert "detail" in data

    def test_validation_error_handling(self, client: TestClient):
        """Test validation error handling."""
        invalid_data = {
            "message": "",  # Empty message should fail validation
            "user_id": "test",
            "conversation_id": "test"
        }

        response = client.post("/chat/", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)


