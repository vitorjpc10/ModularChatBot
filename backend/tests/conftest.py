"""
Test configuration and fixtures for the Modular Chatbot application.
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings


# Test database configuration
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db() -> Generator:
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create test database and tables."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    # Clean up
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """Create a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session) -> Generator:
    """Create a test client with overridden database dependency."""
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_chat_request():
    """Sample chat request data for testing."""
    return {
        "message": "What are the card machine fees?",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456"
    }


@pytest.fixture
def sample_math_request():
    """Sample math request data for testing."""
    return {
        "message": "How much is 65 x 3.11?",
        "user_id": "test_user_123",
        "conversation_id": "test_conv_456"
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "conversation_id": "test_conv_789",
        "user_id": "test_user_123",
        "title": "Test Conversation"
    }


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
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


@pytest.fixture
def mock_ai_service(monkeypatch):
    """Mock AI service for testing."""
    class MockAIService:
        def __init__(self):
            self.health_check_called = False
        
        def health_check(self):
            self.health_check_called = True
            return True
        
        async def generate_response(self, prompt, system_message=None, temperature=0.1):
            return "Mock AI response"
        
        async def generate_structured_response(self, prompt, output_schema, system_message=None):
            return {
                "agent": "KnowledgeAgent",
                "confidence": 0.9,
                "reasoning": "Mock reasoning"
            }
    
    return MockAIService()


@pytest.fixture
def mock_router_service(mock_ai_service):
    """Mock router service for testing."""
    class MockRouterService:
        def __init__(self, ai_service):
            self.ai_service = ai_service
            self.route_message_called = False
        
        async def route_message(self, message, conversation_id, user_id):
            self.route_message_called = True
            return {
                "agent": "KnowledgeAgent",
                "confidence": 0.9,
                "reasoning": "Mock routing decision",
                "execution_time": 150,
                "method": "mock"
            }
    
    return MockRouterService(mock_ai_service)


@pytest.fixture
def mock_knowledge_service(mock_ai_service):
    """Mock knowledge service for testing."""
    class MockKnowledgeService:
        def __init__(self, ai_service):
            self.ai_service = ai_service
            self.get_response_called = False
        
        async def get_response(self, message, conversation_id, user_id):
            self.get_response_called = True
            return {
                "response": "Mock knowledge response",
                "source_content": "Mock source content",
                "execution_time": 1200,
                "sources": ["https://example.com"]
            }
    
    return MockKnowledgeService(mock_ai_service)


@pytest.fixture
def mock_math_service(mock_ai_service):
    """Mock math service for testing."""
    class MockMathService:
        def __init__(self, ai_service):
            self.ai_service = ai_service
            self.calculate_called = False
        
        async def calculate(self, message, conversation_id, user_id):
            self.calculate_called = True
            return {
                "response": "Mock math response",
                "expression": "65 * 3.11",
                "result": "202.15",
                "execution_time": 800
            }
    
    return MockMathService(mock_ai_service)
