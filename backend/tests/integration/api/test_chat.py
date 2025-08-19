"""
Integration tests for the chat endpoint using TestClient and real app dependencies,
but without real external services (DB is test DB via fixture).
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


pytestmark = pytest.mark.integration


def test_chat_endpoint_basic(client: TestClient, sample_chat_request):
    response = client.post("/chat/", json=sample_chat_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "agent_workflow" in data
    assert "conversation_id" in data
    assert data["conversation_id"] == sample_chat_request["conversation_id"]


def test_chat_endpoint_invalid_request(client: TestClient):
    invalid_request = {
        "message": "Test message"
    }
    response = client.post("/chat/", json=invalid_request)
    assert response.status_code == 422


def test_chat_endpoint_math_request(client: TestClient, sample_math_request):
    response = client.post("/chat/", json=sample_math_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "agent_workflow" in data
    assert data["response"] is not None
    assert len(data["response"]) > 0


def test_chat_endpoint_empty_message(client: TestClient):
    request = {
        "message": "",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    response = client.post("/chat/", json=request)
    assert response.status_code == 422


def test_chat_endpoint_long_message(client: TestClient):
    long_message = "A" * 3000
    request = {
        "message": long_message,
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    response = client.post("/chat/", json=request)
    assert response.status_code == 422


def test_chat_endpoint_sanitization(client: TestClient):
    malicious_request = {
        "message": "<script>alert('xss')</script>What are the fees?",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    response = client.post("/chat/", json=malicious_request)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data


def test_chat_endpoint_conversation_creation(client: TestClient, sample_chat_request):
    response1 = client.post("/chat/", json=sample_chat_request)
    assert response1.status_code == 200
    response2 = client.post("/chat/", json=sample_chat_request)
    assert response2.status_code == 200
    data1 = response1.json()
    data2 = response2.json()
    assert data1["conversation_id"] == data2["conversation_id"]


def test_chat_endpoint_error_handling(client: TestClient):
    sample_request = {
        "message": "Test message",
        "user_id": "test_user",
        "conversation_id": "test_conv"
    }
    response = client.post("/chat/", json=sample_request)
    assert response.status_code in [200, 500]


def test_chat_endpoint_response_structure(client: TestClient, sample_chat_request):
    response = client.post("/chat/", json=sample_chat_request)
    assert response.status_code == 200
    data = response.json()
    required_fields = [
        "response", "source_agent_response", "agent_workflow",
        "conversation_id", "execution_time", "timestamp"
    ]
    for field in required_fields:
        assert field in data
    workflow = data["agent_workflow"]
    assert isinstance(workflow, list)
    for step in workflow:
        assert "agent" in step
        assert "execution_time" in step
        assert isinstance(step["agent"], str)
        assert isinstance(step["execution_time"], int)
        assert step["execution_time"] >= 0


def test_chat_endpoint_performance(client: TestClient, sample_chat_request):
    import time
    start_time = time.time()
    response = client.post("/chat/", json=sample_chat_request)
    end_time = time.time()
    assert response.status_code == 200
    response_time = end_time - start_time
    assert response_time < 30
    data = response.json()
    assert data["execution_time"] > 0
    assert data["execution_time"] < 30000


