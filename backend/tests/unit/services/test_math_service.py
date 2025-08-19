"""
Unit tests for the MathService.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.math_service import MathService, MathCalculation
from app.services.ai_service import AIService


pytestmark = pytest.mark.unit


class TestMathService:
    """Test cases for MathService."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create a mock AI service."""
        mock_service = AsyncMock(spec=AIService)
        mock_service.generate_structured_response = AsyncMock()
        return mock_service

    @pytest.fixture
    def math_service(self, mock_ai_service):
        """Create a MathService instance with mocked dependencies."""
        return MathService(mock_ai_service)

    def test_extract_expression_simple_math(self, math_service):
        """Test expression extraction for simple mathematical operations."""
        test_cases = [
            ("What is 5 + 3?", "5+3"),
            ("Calculate 10 * 2", "10*2"),
            ("How much is 15 / 3", "15/3"),
            ("What is 2^3?", "2^3"),
            ("Calculate 5 x 4", "5*4"),
            ("What is 100 - 25?", "100-25"),
            ("How much is 7.5 * 2.5?", "7.5*2.5")
        ]

        for message, expected in test_cases:
            result = math_service._extract_expression(message)
            assert result == expected

    def test_extract_expression_complex_math(self, math_service):
        """Test expression extraction for complex mathematical expressions."""
        test_cases = [
            ("What is (2 + 3) * 4?", "(2+3)*4"),
            ("Calculate 10 + 5 * 2", "10+5*2"),
            ("How much is (15 - 3) / 4?", "(15-3)/4"),
            ("What is 2^3 + 1?", "2^3+1")
        ]

        for message, expected in test_cases:
            result = math_service._extract_expression(message)
            assert result == expected

    def test_extract_expression_no_math(self, math_service):
        """Test expression extraction when no mathematical expression is found."""
        messages_without_math = [
            "Hello, how are you?",
            "What are your services?",
            "Can you help me?",
            "Thank you for your assistance",
            "I need information about fees"
        ]

        for message in messages_without_math:
            result = math_service._extract_expression(message)
            assert result is None

    def test_validate_expression_safe(self, math_service):
        """Test expression validation for safe mathematical expressions."""
        safe_expressions = [
            "5+3",
            "10*2",
            "15/3",
            "2^3",
            "(2+3)*4",
            "7.5*2.5",
            "100-25"
        ]

        for expression in safe_expressions:
            assert math_service._validate_expression(expression) is True

    def test_validate_expression_dangerous(self, math_service):
        """Test expression validation for dangerous expressions."""
        dangerous_expressions = [
            "import os",
            "exec('print(1)')",
            "eval('1+1')",
            "__import__('os')",
            "open('file.txt')",
            "print('hello')"
        ]

        for expression in dangerous_expressions:
            assert math_service._validate_expression(expression) is False

    @pytest.mark.asyncio
    async def test_calculate_with_expression_success(self, math_service, mock_ai_service):
        """Test calculation with extracted expression."""
        mock_ai_service.generate_structured_response.return_value = {
            "expression": "5+3",
            "result": "8",
            "explanation": "5 plus 3 equals 8"
        }

        result = await math_service._calculate_with_ai("5+3", "What is 5 + 3?")

        assert result["expression"] == "5+3"
        assert result["result"] == "8"
        assert result["explanation"] == "5 plus 3 equals 8"
        mock_ai_service.generate_structured_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_without_expression_success(self, math_service, mock_ai_service):
        """Test calculation when no expression is extracted."""
        mock_ai_service.generate_structured_response.return_value = {
            "expression": "10*2",
            "result": "20",
            "explanation": "10 multiplied by 2 equals 20"
        }

        result = await math_service._calculate_with_ai("", "What is 10 times 2?")

        assert result["expression"] == "10*2"
        assert result["result"] == "20"
        assert result["explanation"] == "10 multiplied by 2 equals 20"

    @pytest.mark.asyncio
    async def test_calculate_with_ai_failure(self, math_service, mock_ai_service):
        """Test calculation when AI service fails."""
        mock_ai_service.generate_structured_response.side_effect = Exception("AI Error")

        result = await math_service._calculate_with_ai("5+3", "What is 5 + 3?")

        assert result["expression"] == "5+3"
        assert result["result"] == "Unable to calculate"
        assert "couldn't calculate it" in result["explanation"]

    @pytest.mark.asyncio
    async def test_calculate_without_expression_failure(self, math_service, mock_ai_service):
        """Test calculation failure when no expression is found."""
        mock_ai_service.generate_structured_response.side_effect = Exception("AI Error")

        result = await math_service._calculate_with_ai("", "Hello, how are you?")

        assert result["expression"] == ""
        assert result["result"] == "No expression found"
        assert "couldn't identify a clear mathematical expression" in result["explanation"]

    @pytest.mark.asyncio
    async def test_calculate_success(self, math_service, mock_ai_service):
        """Test successful calculation workflow."""
        mock_ai_service.generate_structured_response.return_value = {
            "expression": "10*5",
            "result": "50",
            "explanation": "10 multiplied by 5 equals 50"
        }

        result = await math_service.calculate("What is 10 * 5?", "test_conv", "test_user")

        assert result["response"] == "10 multiplied by 5 equals 50"
        assert result["expression"] == "10*5"
        assert result["result"] == "50"
        assert "execution_time" in result
        assert isinstance(result["execution_time"], int)

    @pytest.mark.asyncio
    async def test_calculate_no_expression(self, math_service, mock_ai_service):
        """Test calculation when no expression is found in message."""
        mock_ai_service.generate_structured_response.return_value = {
            "expression": "15+3",
            "result": "18",
            "explanation": "15 plus 3 equals 18"
        }

        result = await math_service.calculate("I need to add 15 and 3", "test_conv", "test_user")

        assert result["response"] == "15 plus 3 equals 18"
        assert result["expression"] == "15+3"
        assert result["result"] == "18"

    @pytest.mark.asyncio
    async def test_calculate_error_handling(self, math_service, mock_ai_service):
        """Test error handling in calculate method."""
        mock_ai_service.generate_structured_response.side_effect = Exception("Calculation error")

        result = await math_service.calculate("What is 5 + 3?", "test_conv", "test_user")

        assert "I apologize, but I'm having trouble" in result["response"]
        assert result["expression"] == ""
        assert result["result"] == ""
        assert "error" in result
        assert result["error"] == "Calculation error"

    @pytest.mark.asyncio
    async def test_calculate_execution_time(self, math_service, mock_ai_service):
        """Test that execution time is properly calculated."""
        mock_ai_service.generate_structured_response.return_value = {
            "expression": "2+2",
            "result": "4",
            "explanation": "2 plus 2 equals 4"
        }

        result = await math_service.calculate("What is 2 + 2?", "test_conv", "test_user")

        assert "execution_time" in result
        assert isinstance(result["execution_time"], int)
        assert result["execution_time"] >= 0

    def test_math_calculation_schema(self):
        """Test MathCalculation Pydantic schema validation."""
        # Valid data
        valid_data = {
            "expression": "5+3",
            "result": "8",
            "explanation": "5 plus 3 equals 8"
        }
        calculation = MathCalculation(**valid_data)
        assert calculation.expression == "5+3"
        assert calculation.result == "8"
        assert calculation.explanation == "5 plus 3 equals 8"

        # Test required fields
        with pytest.raises(ValueError):
            MathCalculation(expression="5+3", result="8")  # Missing explanation

        with pytest.raises(ValueError):
            MathCalculation(expression="5+3", explanation="Test")  # Missing result


