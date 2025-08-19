"""
Unit tests for the RouterService.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.router_service import RouterService, RouterDecision
from app.services.ai_service import AIService


pytestmark = pytest.mark.unit


class TestRouterService:
    """Test cases for RouterService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        mock_service = AsyncMock(spec=AIService)
        mock_service.generate_structured_response = AsyncMock()
        return mock_service

    @pytest.fixture
    def router_service(self, mock_ai_service):
        """Create a RouterService instance with mocked dependencies."""
        return RouterService(mock_ai_service)

    @pytest.mark.asyncio
    async def test_rule_based_routing_math_expressions(self, router_service):
        """Test rule-based routing for mathematical expressions."""
        # Test various math patterns
        math_messages = [
            "What is 5 + 3?",
            "Calculate 10 * 2",
            "How much is 15 / 3",
            "What is 2^3?",
            "Calculate 5 x 4",
            "What is (2 + 3) * 4?",
            "How much is 100 - 25?"
        ]

        for message in math_messages:
            result = router_service._rule_based_routing(message)
            assert result is not None
            assert result["agent"] == "MathAgent"
            assert result["confidence"] == 0.9
            assert "Mathematical expression detected" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_rule_based_routing_knowledge_questions(self, router_service):
        """Test rule-based routing for knowledge questions."""
        # Test various knowledge patterns
        knowledge_messages = [
            "What are the fees for card machines?",
            "How do I use the payment system?",
            "Can I use this card machine?",
            "What card machine options do you have?",
            "How does the payment process work?",
            "I need help with my account",
            "Support for technical issues"
        ]

        for message in knowledge_messages:
            result = router_service._rule_based_routing(message)
            assert result is not None
            assert result["agent"] == "KnowledgeAgent"
            assert result["confidence"] == 0.8
            assert "Knowledge question detected" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_rule_based_routing_ambiguous_messages(self, router_service):
        """Test rule-based routing for ambiguous messages."""
        ambiguous_messages = [
            "Hello",
            "Thank you",
            "Good morning",
            "I have a question",
            "Can you help me?"
        ]

        for message in ambiguous_messages:
            result = router_service._rule_based_routing(message)
            assert result is None

    @pytest.mark.asyncio
    async def test_ai_based_routing_success(self, router_service, mock_ai_service):
        """Test AI-based routing with successful response."""
        mock_ai_service.generate_structured_response.return_value = {
            "agent": "KnowledgeAgent",
            "confidence": 0.85,
            "reasoning": "This is a question about services"
        }

        result = await router_service._ai_based_routing("What are your services?")

        assert result["agent"] == "KnowledgeAgent"
        assert result["confidence"] == 0.85
        assert result["reasoning"] == "This is a question about services"
        mock_ai_service.generate_structured_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_ai_based_routing_failure(self, router_service, mock_ai_service):
        """Test AI-based routing with failure."""
        mock_ai_service.generate_structured_response.side_effect = Exception("API Error")

        result = await router_service._ai_based_routing("What are your services?")

        assert result["agent"] == "KnowledgeAgent"
        assert result["confidence"] == 0.6
        assert "AI routing failed" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_route_message_rule_based_priority(self, router_service, mock_ai_service):
        """Test that rule-based routing takes priority over AI-based routing."""
        # This should trigger rule-based routing
        message = "What is 5 + 3?"
        
        result = await router_service.route_message(message, "test_conv", "test_user")

        assert result["agent"] == "MathAgent"
        assert result["method"] == "rule_based"
        assert result["confidence"] == 0.9
        # AI service should not be called for rule-based decisions
        mock_ai_service.generate_structured_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_route_message_ai_based_fallback(self, router_service, mock_ai_service):
        """Test AI-based routing when rule-based routing fails."""
        # This should not trigger rule-based routing
        message = "Tell me about your company"
        
        mock_ai_service.generate_structured_response.return_value = {
            "agent": "KnowledgeAgent",
            "confidence": 0.8,
            "reasoning": "Company information request"
        }

        result = await router_service.route_message(message, "test_conv", "test_user")

        assert result["agent"] == "KnowledgeAgent"
        assert result["method"] == "ai_based"
        assert result["confidence"] == 0.8
        mock_ai_service.generate_structured_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_message_error_handling(self, router_service, mock_ai_service):
        """Test error handling in route_message."""
        # Mock both rule-based and AI-based routing to fail
        with patch.object(router_service, '_rule_based_routing', return_value=None):
            mock_ai_service.generate_structured_response.side_effect = Exception("Test error")

            result = await router_service.route_message("Test message", "test_conv", "test_user")

            assert result["agent"] == "KnowledgeAgent"
            assert result["confidence"] == 0.5
            assert result["method"] == "fallback"
            assert "Fallback decision due to error" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_route_message_execution_time(self, router_service, mock_ai_service):
        """Test that execution time is properly calculated."""
        mock_ai_service.generate_structured_response.return_value = {
            "agent": "KnowledgeAgent",
            "confidence": 0.8,
            "reasoning": "Test reasoning"
        }

        result = await router_service.route_message("Test message", "test_conv", "test_user")

        assert "execution_time" in result
        assert isinstance(result["execution_time"], int)
        assert result["execution_time"] >= 0
        
    def test_router_decision_schema(self):
        """Test RouterDecision Pydantic schema validation."""
        # Valid data
        valid_data = {
            "agent": "KnowledgeAgent",
            "confidence": 0.9,
            "reasoning": "Test reasoning"
        }
        decision = RouterDecision(**valid_data)
        assert decision.agent == "KnowledgeAgent"
        assert decision.confidence == 0.9
        assert decision.reasoning == "Test reasoning"
        
        # Test confidence bounds
        with pytest.raises(ValueError):
            RouterDecision(agent="KnowledgeAgent", confidence=1.5, reasoning="Test")
        
        with pytest.raises(ValueError):
            RouterDecision(agent="KnowledgeAgent", confidence=-0.1, reasoning="Test")


