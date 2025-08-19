"""
Unit tests for the AIService.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ai_service import AIService
from app.config import settings


pytestmark = pytest.mark.unit


class TestAIService:
    """Test cases for AIService."""

    @pytest.fixture
    def mock_groq_client(self):
        """Create a mock Groq client."""
        mock_client = AsyncMock()
        mock_client.agenerate = AsyncMock()
        return mock_client

    @pytest.fixture
    def ai_service(self, mock_groq_client):
        """Create an AIService instance with mocked dependencies."""
        with patch('app.services.ai_service.ChatGroq', return_value=mock_groq_client):
            with patch('app.config.settings.GROQ_API_KEY', 'test-api-key'):
                with patch('app.config.settings.GROQ_MODEL', 'test-model'):
                    return AIService()

    def test_initialization_success(self, mock_groq_client):
        """Test successful AIService initialization."""
        with patch('app.services.ai_service.ChatGroq', return_value=mock_groq_client):
            with patch('app.config.settings.GROQ_API_KEY', 'test-api-key'):
                with patch('app.config.settings.GROQ_MODEL', 'test-model'):
                    service = AIService()
                    assert service.client == mock_groq_client

    def test_initialization_missing_api_key(self):
        """Test AIService initialization with missing API key."""
        with patch('app.config.settings.GROQ_API_KEY', ''):
            with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
                AIService()

    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service, mock_groq_client):
        """Test successful response generation."""
        # Mock the response structure
        mock_generation = MagicMock()
        mock_generation.text = "This is a test response"
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        result = await ai_service.generate_response("Test prompt")

        assert result == "This is a test response"
        mock_groq_client.agenerate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_response_with_system_message(self, ai_service, mock_groq_client):
        """Test response generation with system message."""
        mock_generation = MagicMock()
        mock_generation.text = "System-guided response"
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        system_message = "You are a helpful assistant"
        result = await ai_service.generate_response("Test prompt", system_message=system_message)

        assert result == "System-guided response"
        # Verify that both system and human messages were added
        call_args = mock_groq_client.agenerate.call_args[0][0][0]
        assert len(call_args) == 2
        assert call_args[0].content == system_message
        assert call_args[1].content == "Test prompt"

    @pytest.mark.asyncio
    async def test_generate_response_with_temperature(self, ai_service, mock_groq_client):
        """Test response generation with custom temperature."""
        mock_generation = MagicMock()
        mock_generation.text = "Temperature-adjusted response"
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        result = await ai_service.generate_response("Test prompt", temperature=0.8)

        assert result == "Temperature-adjusted response"
        assert ai_service.client.temperature == 0.8

    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, ai_service, mock_groq_client):
        """Test error handling in response generation."""
        mock_groq_client.agenerate.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await ai_service.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_structured_response_success(self, ai_service, mock_groq_client):
        """Test successful structured response generation."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            result: str = Field(description="Test result")
            explanation: str = Field(description="Test explanation")

        # Mock the response structure
        mock_generation = MagicMock()
        mock_generation.text = '{"result": "success", "explanation": "Test explanation"}'
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        result = await ai_service.generate_structured_response(
            "Test prompt", 
            TestSchema
        )

        assert isinstance(result, dict)
        assert result["result"] == "success"
        assert result["explanation"] == "Test explanation"

    @pytest.mark.asyncio
    async def test_generate_structured_response_with_system_message(self, ai_service, mock_groq_client):
        """Test structured response generation with system message."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            result: str = Field(description="Test result")

        mock_generation = MagicMock()
        mock_generation.text = '{"result": "success"}'
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        system_message = "You are a structured response generator"
        result = await ai_service.generate_structured_response(
            "Test prompt", 
            TestSchema,
            system_message=system_message
        )

        assert result["result"] == "success"
        # Verify system message was included
        call_args = mock_groq_client.agenerate.call_args[0][0][0]
        assert len(call_args) == 2
        assert call_args[0].content == system_message

    @pytest.mark.asyncio
    async def test_generate_structured_response_parsing_error(self, ai_service, mock_groq_client):
        """Test structured response generation with parsing error."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            result: str = Field(description="Test result")

        # Mock invalid JSON response
        mock_generation = MagicMock()
        mock_generation.text = "Invalid JSON response"
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        with pytest.raises(Exception):
            await ai_service.generate_structured_response("Test prompt", TestSchema)

    @pytest.mark.asyncio
    async def test_generate_structured_response_api_error(self, ai_service, mock_groq_client):
        """Test structured response generation with API error."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            result: str = Field(description="Test result")

        mock_groq_client.agenerate.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await ai_service.generate_structured_response("Test prompt", TestSchema)

    def test_health_check_success(self, ai_service):
        """Test successful health check."""
        with patch('app.config.settings.GROQ_API_KEY', 'test-key'):
            result = ai_service.health_check()
            assert result is True

    def test_health_check_failure_no_api_key(self, ai_service):
        """Test health check failure with no API key."""
        with patch('app.config.settings.GROQ_API_KEY', ''):
            result = ai_service.health_check()
            assert result is False

    def test_health_check_failure_no_client(self, ai_service):
        """Test health check failure with no client."""
        ai_service.client = None
        result = ai_service.health_check()
        assert result is False

    def test_health_check_exception_handling(self, ai_service):
        """Test health check exception handling."""
        ai_service.client = None
        with patch('app.config.settings.GROQ_API_KEY', side_effect=Exception("Config error")):
            result = ai_service.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_response_execution_time(self, ai_service, mock_groq_client):
        """Test that execution time is properly calculated."""
        import time

        mock_generation = MagicMock()
        mock_generation.text = "Test response"
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        start_time = time.time()
        result = await ai_service.generate_response("Test prompt")
        end_time = time.time()

        assert result == "Test response"
        # Execution time should be reasonable (less than 1 second for mock)
        assert (end_time - start_time) < 1

    @pytest.mark.asyncio
    async def test_generate_structured_response_execution_time(self, ai_service, mock_groq_client):
        """Test that execution time is properly calculated for structured responses."""
        from pydantic import BaseModel, Field

        class TestSchema(BaseModel):
            result: str = Field(description="Test result")

        mock_generation = MagicMock()
        mock_generation.text = '{"result": "success"}'
        mock_generations = [[mock_generation]]
        mock_response = MagicMock()
        mock_response.generations = mock_generations
        mock_groq_client.agenerate.return_value = mock_response

        import time
        start_time = time.time()
        result = await ai_service.generate_structured_response("Test prompt", TestSchema)
        end_time = time.time()

        assert result["result"] == "success"
        # Execution time should be reasonable (less than 1 second for mock)
        assert (end_time - start_time) < 1


