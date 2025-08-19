"""
End-to-end integration test for the /chat endpoint using real services and DB.

This test intentionally avoids mocks to exercise the full stack and persist rows
so you can inspect them in PGAdmin and debug step-by-step.

Prerequisites (env vars):
  - ENVIRONMENT=test
  - TEST_DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/DB
  - GROQ_API_KEY=<your key>
  - GROQ_MODEL=llama3-70b-8192 (or other supported)
"""

import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app.models.message import Message
from app.models.conversation import Conversation
from app.config import settings


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def test_chat_e2e_math_flow_persists_rows():
    # Ensure required configuration is present (reads from .env via decouple)
    assert settings.ENVIRONMENT.lower() == "test", "ENVIRONMENT must be 'test'"
    assert settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must be set to your Postgres URL"
    assert settings.GROQ_API_KEY, "GROQ_API_KEY must be set for AIService initialization"

    # Use a unique conversation id so rows are easy to find in PGAdmin
    conversation_id = f"e2e-{uuid.uuid4()}"

    request_data = {
        "message": "What is 5 + 3?",  # Should route to MathAgent via rule-based routing
        "user_id": "e2e_user",
        "conversation_id": conversation_id,
    }

    with TestClient(app) as client:
        resp = client.post("/chat/", json=request_data)

    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] == conversation_id
    assert "response" in data and isinstance(data["response"], str)
    assert "agent_workflow" in data and isinstance(data["agent_workflow"], list)
    assert any(step.get("agent") == "RouterAgent" for step in data["agent_workflow"])  # basic shape

    # Verify rows were persisted (no rollback since we used real dependency in app)
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        assert conv is not None, "Conversation row should exist"

        msgs = db.query(Message).filter(Message.conversation_id == conversation_id).all()
        assert len(msgs) >= 1, "At least one message row should exist"
    finally:
        db.close()



def test_chat_e2e_knowledge_flow_persists_rows():
    # Ensure required configuration is present (reads from .env via decouple)
    assert settings.ENVIRONMENT.lower() == "test", "ENVIRONMENT must be 'test'"
    assert settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must be set to your Postgres URL"
    assert settings.GROQ_API_KEY, "GROQ_API_KEY must be set for AIService initialization"

    # Unique conversation id
    conversation_id = f"e2e-{uuid.uuid4()}"

    request_data = {
        "message": "What are the fees for card machines at InfinitePay?",  # Should route to KnowledgeAgent via rules
        "user_id": "e2e_user",
        "conversation_id": conversation_id,
    }

    with TestClient(app) as client:
        resp = client.post("/chat/", json=request_data)

    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] == conversation_id
    assert any(step.get("agent") == "RouterAgent" for step in data["agent_workflow"])  # basic shape
    # Verify selected agent is KnowledgeAgent
    assert any(step.get("agent") == "KnowledgeAgent" for step in data["agent_workflow"])

    # Verify rows persisted
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        assert conv is not None, "Conversation row should exist"
        msgs = db.query(Message).filter(Message.conversation_id == conversation_id).all()
        assert len(msgs) >= 1, "At least one message row should exist"
    finally:
        db.close()


def test_chat_e2e_mixed_message_prefers_math_rules():
    # Ensure required configuration is present
    assert settings.ENVIRONMENT.lower() == "test", "ENVIRONMENT must be 'test'"
    assert settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must be set to your Postgres URL"
    assert settings.GROQ_API_KEY, "GROQ_API_KEY must be set for AIService initialization"

    conversation_id = f"e2e-{uuid.uuid4()}"

    # Contains both knowledge keywords and a math expression; rules check math first
    request_data = {
        "message": "What are the card machine fees and what is 5 + 3?",
        "user_id": "e2e_user",
        "conversation_id": conversation_id,
    }

    with TestClient(app) as client:
        resp = client.post("/chat/", json=request_data)

    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation_id"] == conversation_id
    # Router step present
    assert any(step.get("agent") == "RouterAgent" for step in data["agent_workflow"])
    # Should route to MathAgent due to rule priority
    assert any(step.get("agent") == "MathAgent" for step in data["agent_workflow"])

    # Verify rows persisted
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        assert conv is not None, "Conversation row should exist"
        msgs = db.query(Message).filter(Message.conversation_id == conversation_id).all()
        assert len(msgs) >= 1, "At least one message row should exist"
    finally:
        db.close()


def test_chat_e2e_multi_turn_routes_both_agents_and_persists():
    # Ensure required configuration is present
    assert settings.ENVIRONMENT.lower() == "test", "ENVIRONMENT must be 'test'"
    assert settings.TEST_DATABASE_URL, "TEST_DATABASE_URL must be set to your Postgres URL"
    assert settings.GROQ_API_KEY, "GROQ_API_KEY must be set for AIService initialization"

    conversation_id = f"e2e-{uuid.uuid4()}"

    first_request = {
        "message": "I need help understanding the payment options and fees.",  # Knowledge
        "user_id": "e2e_user",
        "conversation_id": conversation_id,
    }
    second_request = {
        "message": "Now calculate 12 * 4 for me, based on the previous discussion.",  # Math
        "user_id": "e2e_user",
        "conversation_id": conversation_id,
    }

    with TestClient(app) as client:
        resp1 = client.post("/chat/", json=first_request)
        resp2 = client.post("/chat/", json=second_request)

    assert resp1.status_code == 200 and resp2.status_code == 200
    data1 = resp1.json()
    data2 = resp2.json()

    assert data1["conversation_id"] == conversation_id
    assert data2["conversation_id"] == conversation_id

    # First should have KnowledgeAgent step
    assert any(step.get("agent") == "KnowledgeAgent" for step in data1["agent_workflow"])
    # Second should have MathAgent step
    assert any(step.get("agent") == "MathAgent" for step in data2["agent_workflow"])

    # Verify rows persisted (at least two messages)
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.conversation_id == conversation_id).first()
        assert conv is not None, "Conversation row should exist"
        msgs = db.query(Message).filter(Message.conversation_id == conversation_id).all()
        assert len(msgs) >= 2, "At least two message rows should exist for multi-turn conversation"
    finally:
        db.close()