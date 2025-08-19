"""
Unit tests for the KnowledgeService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.knowledge_service import KnowledgeService
from app.services.ai_service import AIService


pytestmark = pytest.mark.unit


class TestKnowledgeService:
    """Test cases for KnowledgeService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        mock_service = AsyncMock(spec=AIService)
        mock_service.generate_response = AsyncMock()
        return mock_service

    @pytest.fixture
    def knowledge_service(self, mock_ai_service):
        """Create a KnowledgeService instance with mocked dependencies."""
        return KnowledgeService(mock_ai_service)

    @pytest.mark.asyncio
    async def test_fetch_infinitepay_content_success(self, knowledge_service):
        """Test successful content fetching from InfinitePay help URL."""
        mock_response = MagicMock()
        mock_response.content = b"""
        <html>
            <body>
                <h1>InfinitePay Help</h1>
                <p>This is a test paragraph about card machine fees.</p>
                <p>Another paragraph about payment processing.</p>
                <li>List item about support</li>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None

        with patch('app.services.knowledge_service.requests.get', return_value=mock_response):
            content = await knowledge_service._fetch_infinitepay_content()

        assert "InfinitePay Help" in content
        assert "card machine fees" in content
        assert "payment processing" in content
        assert "support" in content

    @pytest.mark.asyncio
    async def test_fetch_infinitepay_content_failure(self, knowledge_service):
        """Test content fetching failure."""
        with patch('app.services.knowledge_service.requests.get', side_effect=Exception("Network error")):
            with pytest.raises(Exception, match="Network error"):
                await knowledge_service._fetch_infinitepay_content()

    def test_process_content(self, knowledge_service):
        """Test content processing into knowledge base."""
        raw_content = """
        Card Machine Fees: Our card machines have competitive fees.
        Payment Processing: We offer fast and secure payment processing.
        Support: Our support team is available 24/7.
        Technical Issues: Contact us for technical assistance.
        """

        knowledge_base = knowledge_service._process_content(raw_content)

        assert isinstance(knowledge_base, dict)
        assert len(knowledge_base) > 0
        # Check that content is properly chunked
        for key, content in knowledge_base.items():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_search_knowledge_base(self, knowledge_service):
        """Test knowledge base search functionality."""
        # Set up a mock knowledge base
        knowledge_service.knowledge_base = {
            "fees": "Card machine fees are 2.5% per transaction",
            "support": "Contact support at support@infinitepay.com",
            "processing": "Payment processing takes 1-2 business days"
        }

        # Test search for fees
        result = knowledge_service._search_knowledge_base("What are the fees?")
        assert "2.5%" in result
        assert "Card machine fees" in result

        # Test search for support
        result = knowledge_service._search_knowledge_base("I need help")
        assert "support@infinitepay.com" in result

        # Test search with no matches
        result = knowledge_service._search_knowledge_base("unrelated query")
        assert result == ""

    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, knowledge_service, mock_ai_service):
        """Test response generation with context."""
        mock_ai_service.generate_response.return_value = "Based on our knowledge base, card machine fees are 2.5% per transaction."

        context = "Card machine fees are 2.5% per transaction"
        message = "What are the fees?"

        result = await knowledge_service._generate_response_with_context(message, context)

        assert "2.5%" in result
        mock_ai_service.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_knowledge_base_success(self, knowledge_service):
        """Test successful knowledge base update."""
        mock_content = "Test content for knowledge base"
        
        with patch.object(knowledge_service, '_fetch_infinitepay_content', return_value=mock_content):
            await knowledge_service._update_knowledge_base()

        assert knowledge_service.knowledge_base is not None
        assert knowledge_service.last_update is not None

    @pytest.mark.asyncio
    async def test_update_knowledge_base_failure(self, knowledge_service):
        """Test knowledge base update failure."""
        with patch.object(knowledge_service, '_fetch_infinitepay_content', side_effect=Exception("Fetch error")):
            await knowledge_service._update_knowledge_base()

        # Should fall back to default content
        assert knowledge_service.knowledge_base is not None
        assert "InfinitePay" in str(knowledge_service.knowledge_base.values())

    @pytest.mark.asyncio
    async def test_get_response_success(self, knowledge_service, mock_ai_service):
        """Test successful response generation."""
        # Mock the knowledge base update
        knowledge_service.knowledge_base = {
            "fees": "Card machine fees are 2.5% per transaction"
        }
        knowledge_service.last_update = None

        mock_ai_service.generate_response.return_value = "Card machine fees are 2.5% per transaction."

        result = await knowledge_service.get_response("What are the fees?", "test_conv", "test_user")

        assert "2.5%" in result["response"]
        assert "execution_time" in result
        assert "sources" in result
        assert isinstance(result["execution_time"], int)

    @pytest.mark.asyncio
    async def test_get_response_failure(self, knowledge_service, mock_ai_service):
        """Test response generation failure."""
        mock_ai_service.generate_response.side_effect = Exception("AI Error")

        result = await knowledge_service.get_response("What are the fees?", "test_conv", "test_user")

        assert "I apologize, but I'm having trouble" in result["response"]
        assert "error" in result
        assert result["error"] == "AI Error"

    def test_extract_sources(self, knowledge_service):
        """Test source extraction."""
        content = "Some content from our knowledge base"
        sources = knowledge_service._extract_sources(content)

        assert isinstance(sources, list)
        assert len(sources) == 1
        assert "infinitepay.io" in sources[0]

    def test_get_fallback_content(self, knowledge_service):
        """Test fallback content generation."""
        fallback_content = knowledge_service._get_fallback_content()

        assert isinstance(fallback_content, dict)
        assert "general_info" in fallback_content
        assert "contact_info" in fallback_content
        assert "InfinitePay" in fallback_content["general_info"]
        assert "support" in fallback_content["contact_info"]

    @pytest.mark.asyncio
    async def test_get_response_with_empty_knowledge_base(self, knowledge_service, mock_ai_service):
        """Test response generation with empty knowledge base."""
        knowledge_service.knowledge_base = {}
        mock_ai_service.generate_response.return_value = "I don't have specific information about that."

        result = await knowledge_service.get_response("What are the fees?", "test_conv", "test_user")

        assert "I don't have specific information" in result["response"]
        assert result["source_content"] == ""

    @pytest.mark.asyncio
    async def test_get_response_caching(self, knowledge_service, mock_ai_service):
        """Test that knowledge base is not updated too frequently."""
        # Set up initial knowledge base
        knowledge_service.knowledge_base = {"test": "content"}
        knowledge_service.last_update = None

        mock_ai_service.generate_response.return_value = "Test response"

        # First call should update knowledge base
        await knowledge_service.get_response("Test question", "test_conv", "test_user")
        first_update = knowledge_service.last_update

        # Second call should not update (within 1 hour)
        await knowledge_service.get_response("Another question", "test_conv", "test_user")
        second_update = knowledge_service.last_update

        assert first_update == second_update

    @pytest.mark.asyncio
    async def test_get_response_execution_time(self, knowledge_service, mock_ai_service):
        """Test that execution time is properly calculated."""
        knowledge_service.knowledge_base = {"test": "content"}
        mock_ai_service.generate_response.return_value = "Test response"

        result = await knowledge_service.get_response("Test question", "test_conv", "test_user")

        assert "execution_time" in result
        assert isinstance(result["execution_time"], int)
        assert result["execution_time"] >= 0


