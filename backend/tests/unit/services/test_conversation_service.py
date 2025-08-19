"""
Unit tests for the ConversationService.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.services.conversation_service import ConversationService
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationResponse


pytestmark = pytest.mark.unit


class TestConversationService:
    """Test cases for ConversationService."""

    @pytest.fixture
    def conversation_service(self):
        """Create a ConversationService instance."""
        return ConversationService()

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock(spec=Session)

    @pytest.fixture
    def sample_conversation_data(self):
        """Sample conversation data for testing."""
        return {
            "conversation_id": "test_conv_123",
            "user_id": "test_user_456",
            "title": "Test Conversation"
        }

    @pytest.fixture
    def mock_conversation(self, sample_conversation_data):
        """Create a mock conversation object."""
        conversation = MagicMock(spec=Conversation)
        conversation.conversation_id = sample_conversation_data["conversation_id"]
        conversation.user_id = sample_conversation_data["user_id"]
        conversation.title = sample_conversation_data["title"]
        conversation.created_at = "2024-01-01T00:00:00"
        conversation.updated_at = "2024-01-01T00:00:00"
        conversation.messages = []
        return conversation

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, conversation_service, mock_db_session, sample_conversation_data):
        """Test successful conversation creation."""
        # Mock that conversation doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        conversation_data = ConversationCreate(**sample_conversation_data)
        
        result = await conversation_service.create_conversation(mock_db_session, conversation_data)
        
        assert isinstance(result, ConversationResponse)
        assert result.conversation_id == sample_conversation_data["conversation_id"]
        assert result.user_id == sample_conversation_data["user_id"]
        assert result.title == sample_conversation_data["title"]
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_conversation_already_exists(self, conversation_service, mock_db_session, sample_conversation_data, mock_conversation):
        """Test conversation creation when conversation already exists."""
        # Mock that conversation exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        conversation_data = ConversationCreate(**sample_conversation_data)
        
        result = await conversation_service.create_conversation(mock_db_session, conversation_data)
        
        assert isinstance(result, ConversationResponse)
        assert result.conversation_id == sample_conversation_data["conversation_id"]
        # Should not add new conversation
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_conversation_database_error(self, conversation_service, mock_db_session, sample_conversation_data):
        """Test conversation creation with database error."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add.side_effect = Exception("Database error")
        
        conversation_data = ConversationCreate(**sample_conversation_data)
        
        with pytest.raises(Exception, match="Database error"):
            await conversation_service.create_conversation(mock_db_session, conversation_data)
        
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_conversation_success(self, conversation_service, mock_db_session, mock_conversation):
        """Test successful conversation retrieval."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        result = await conversation_service.get_conversation(mock_db_session, "test_conv_123")
        
        assert isinstance(result, ConversationResponse)
        assert result.conversation_id == "test_conv_123"
        assert result.message_count == 0

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, conversation_service, mock_db_session):
        """Test conversation retrieval when conversation doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await conversation_service.get_conversation(mock_db_session, "nonexistent_conv")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_conversations_success(self, conversation_service, mock_db_session, mock_conversation):
        """Test successful user conversations retrieval."""
        mock_conversations = [mock_conversation]
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        
        result = await conversation_service.get_user_conversations(mock_db_session, "test_user_456", limit=10, offset=0)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ConversationResponse)
        assert result[0].user_id == "test_user_456"

    @pytest.mark.asyncio
    async def test_get_user_conversations_empty(self, conversation_service, mock_db_session):
        """Test user conversations retrieval when user has no conversations."""
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        result = await conversation_service.get_user_conversations(mock_db_session, "test_user_456")
        
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_update_conversation_title_success(self, conversation_service, mock_db_session, mock_conversation):
        """Test successful conversation title update."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        result = await conversation_service.update_conversation_title(mock_db_session, "test_conv_123", "Updated Title")
        
        assert isinstance(result, ConversationResponse)
        assert result.title == "Updated Title"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_conversation_title_not_found(self, conversation_service, mock_db_session):
        """Test conversation title update when conversation doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await conversation_service.update_conversation_title(mock_db_session, "nonexistent_conv", "New Title")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_conversation_success(self, conversation_service, mock_db_session, mock_conversation):
        """Test successful conversation deletion."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        result = await conversation_service.delete_conversation(mock_db_session, "test_conv_123")
        
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_conversation)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, conversation_service, mock_db_session):
        """Test conversation deletion when conversation doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await conversation_service.delete_conversation(mock_db_session, "nonexistent_conv")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_get_conversation_stats_success(self, conversation_service, mock_db_session, mock_conversation):
        """Test successful conversation statistics retrieval."""
        # Mock messages
        mock_message1 = MagicMock()
        mock_message1.response = "Response 1"
        mock_message1.source_agent = "KnowledgeAgent"
        mock_message1.execution_time = 100
        
        mock_message2 = MagicMock()
        mock_message2.response = "Response 2"
        mock_message2.source_agent = "MathAgent"
        mock_message2.execution_time = 200
        
        mock_conversation.messages = [mock_message1, mock_message2]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        result = await conversation_service.get_conversation_stats(mock_db_session, "test_conv_123")
        
        assert isinstance(result, dict)
        assert result["conversation_id"] == "test_conv_123"
        assert result["total_messages"] == 2
        assert result["user_messages"] == 2
        assert result["agent_responses"] == 2
        assert result["agent_breakdown"]["KnowledgeAgent"] == 1
        assert result["agent_breakdown"]["MathAgent"] == 1
        assert result["average_execution_time"] == 150

    @pytest.mark.asyncio
    async def test_get_conversation_stats_not_found(self, conversation_service, mock_db_session):
        """Test conversation statistics retrieval when conversation doesn't exist."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = await conversation_service.get_conversation_stats(mock_db_session, "nonexistent_conv")
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_conversation_stats_no_messages(self, conversation_service, mock_db_session, mock_conversation):
        """Test conversation statistics retrieval with no messages."""
        mock_conversation.messages = []
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        result = await conversation_service.get_conversation_stats(mock_db_session, "test_conv_123")
        
        assert result["total_messages"] == 0
        assert result["user_messages"] == 0
        assert result["agent_responses"] == 0
        assert result["average_execution_time"] == 0


