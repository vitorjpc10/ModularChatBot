"""
Unit tests for the MessageService.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.message_service import MessageService
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


pytestmark = pytest.mark.unit


class TestMessageService:
    """Test cases for MessageService."""

    @pytest.fixture
    def message_service(self):
        """Create a MessageService instance."""
        return MessageService()

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def sample_message_data(self):
        """Sample message data for testing."""
        return {
            "conversation_id": "test_conv_123",
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
    def mock_message(self, sample_message_data):
        """Create a mock message object."""
        message = MagicMock(spec=Message)
        message.id = 1
        message.conversation_id = sample_message_data["conversation_id"]
        message.content = sample_message_data["content"]
        message.response = sample_message_data["response"]
        message.source_agent = sample_message_data["source_agent"]
        message.source_agent_response = sample_message_data["source_agent_response"]
        message.agent_workflow = sample_message_data["agent_workflow"]
        message.created_at = "2024-01-01T00:00:00"
        message.execution_time = sample_message_data["execution_time"]
        return message

    @pytest.mark.asyncio
    async def test_create_message_success(self, message_service, mock_db_session, sample_message_data):
        """Test successful message creation."""
        message_data = MessageCreate(**sample_message_data)
        
        result = await message_service.create_message(mock_db_session, message_data)
        
        assert isinstance(result, MessageResponse)
        assert result.conversation_id == sample_message_data["conversation_id"]
        assert result.content == sample_message_data["content"]
        assert result.response == sample_message_data["response"]
        assert result.source_agent == sample_message_data["source_agent"]
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_message_database_error(self, message_service, mock_db_session, sample_message_data):
        """Test message creation with database error."""
        mock_db_session.add.side_effect = Exception("Database error")
        
        message_data = MessageCreate(**sample_message_data)
        
        with pytest.raises(Exception, match="Database error"):
            await message_service.create_message(mock_db_session, message_data)
        
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_success(self, message_service, mock_db_session, mock_message):
        """Test successful message retrieval."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        result = await message_service.get_message(mock_db_session, 1)
        
        assert isinstance(result, MessageResponse)
        assert result.id == 1
        assert result.conversation_id == "test_conv_123"

    @pytest.mark.asyncio
    async def test_get_message_not_found(self, message_service, mock_db_session):
        """Test message retrieval when message doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await message_service.get_message(mock_db_session, 999)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_conversation_messages_success(self, message_service, mock_db_session, mock_message):
        """Test successful conversation messages retrieval."""
        mock_messages = [mock_message]
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        result = await message_service.get_conversation_messages(mock_db_session, "test_conv_123", limit=10, offset=0)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MessageResponse)
        assert result[0].conversation_id == "test_conv_123"

    @pytest.mark.asyncio
    async def test_get_conversation_messages_empty(self, message_service, mock_db_session):
        """Test conversation messages retrieval when conversation has no messages."""
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        result = await message_service.get_conversation_messages(mock_db_session, "test_conv_123")
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_user_messages_success(self, message_service, mock_db_session, mock_message):
        """Test successful user messages retrieval."""
        mock_messages = [mock_message]
        mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_messages
        
        result = await message_service.get_user_messages(mock_db_session, "test_user_456", limit=10, offset=0)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], MessageResponse)

    @pytest.mark.asyncio
    async def test_get_user_messages_empty(self, message_service, mock_db_session):
        """Test user messages retrieval when user has no messages."""
        mock_db_session.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        result = await message_service.get_user_messages(mock_db_session, "test_user_456")
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_message_success(self, message_service, mock_db_session, mock_message):
        """Test successful message update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        update_data = {
            "response": "Updated response",
            "execution_time": 1500
        }
        
        result = await message_service.update_message(mock_db_session, 1, update_data)
        
        assert isinstance(result, MessageResponse)
        assert result.response == "Updated response"
        assert result.execution_time == 1500
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_message_not_found(self, message_service, mock_db_session):
        """Test message update when message doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = {"response": "Updated response"}
        
        result = await message_service.update_message(mock_db_session, 999, update_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_message_invalid_field(self, message_service, mock_db_session, mock_message):
        """Test message update with invalid field."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        update_data = {
            "invalid_field": "This should be ignored",
            "response": "Valid update"
        }
        
        result = await message_service.update_message(mock_db_session, 1, update_data)
        
        assert isinstance(result, MessageResponse)
        assert result.response == "Valid update"
        # Invalid field should be ignored

    @pytest.mark.asyncio
    async def test_delete_message_success(self, message_service, mock_db_session, mock_message):
        """Test successful message deletion."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_message
        
        result = await message_service.delete_message(mock_db_session, 1)
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_message)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_message_not_found(self, message_service, mock_db_session):
        """Test message deletion when message doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await message_service.delete_message(mock_db_session, 999)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_message_stats_by_conversation(self, message_service, mock_db_session, mock_message):
        """Test message statistics retrieval by conversation."""
        # Create multiple mock messages
        mock_message1 = MagicMock()
        mock_message1.response = "Response 1"
        mock_message1.source_agent = "KnowledgeAgent"
        mock_message1.execution_time = 100
        
        mock_message2 = MagicMock()
        mock_message2.response = "Response 2"
        mock_message2.source_agent = "MathAgent"
        mock_message2.execution_time = 200
        
        mock_message3 = MagicMock()
        mock_message3.response = None  # No response
        mock_message3.source_agent = None
        mock_message3.execution_time = None
        
        mock_messages = [mock_message1, mock_message2, mock_message3]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_messages
        
        result = await message_service.get_message_stats(mock_db_session, conversation_id="test_conv_123")
        
        assert isinstance(result, dict)
        assert result["total_messages"] == 3
        assert result["messages_with_responses"] == 2
        assert result["messages_with_agents"] == 2
        assert result["agent_breakdown"]["KnowledgeAgent"] == 1
        assert result["agent_breakdown"]["MathAgent"] == 1
        assert result["execution_time_stats"]["average"] == 150
        assert result["execution_time_stats"]["minimum"] == 100
        assert result["execution_time_stats"]["maximum"] == 200
        assert result["execution_time_stats"]["total_measured"] == 2
        assert result["conversation_id"] == "test_conv_123"
        
    @pytest.mark.asyncio
    async def test_get_message_stats_by_user(self, message_service, mock_db_session):
        """Test message statistics retrieval by user."""
        mock_messages = []
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = mock_messages
        
        result = await message_service.get_message_stats(mock_db_session, user_id="test_user_456")
        
        assert isinstance(result, dict)
        assert result["total_messages"] == 0
        assert result["user_id"] == "test_user_456"
        
    @pytest.mark.asyncio
    async def test_get_message_stats_no_execution_times(self, message_service, mock_db_session):
        """Test message statistics retrieval with no execution times."""
        mock_message = MagicMock()
        mock_message.response = "Response"
        mock_message.source_agent = "KnowledgeAgent"
        mock_message.execution_time = None
        
        mock_messages = [mock_message]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_messages
        
        result = await message_service.get_message_stats(mock_db_session, conversation_id="test_conv_123")
        
        assert result["execution_time_stats"]["average"] == 0
        assert result["execution_time_stats"]["minimum"] == 0
        assert result["execution_time_stats"]["maximum"] == 0
        assert result["execution_time_stats"]["total_measured"] == 0
        
    @pytest.mark.asyncio
    async def test_get_message_stats_no_filters(self, message_service, mock_db_session):
        """Test message statistics retrieval with no filters."""
        mock_messages = []
        mock_db_session.query.return_value.all.return_value = mock_messages
        
        result = await message_service.get_message_stats(mock_db_session)
        
        assert isinstance(result, dict)
        assert result["total_messages"] == 0
        assert "conversation_id" not in result
        assert "user_id" not in result


