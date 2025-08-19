"""
Math service for handling mathematical calculations using LLM interpretation.
"""

import time
import logging
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from .ai_service import AIService

logger = logging.getLogger(__name__)


class MathCalculation(BaseModel):
    """Schema for math calculation output."""
    
    expression: str = Field(..., description="The mathematical expression")
    result: str = Field(..., description="The calculated result")
    explanation: str = Field(..., description="Explanation of the calculation")


class MathService:
    """Service for mathematical calculations using LLM interpretation."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the math service."""
        self.ai_service = ai_service
        logger.info("Math Service initialized")
    
    async def calculate(
        self, 
        message: str, 
        conversation_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Calculate mathematical expressions from user message.
        
        Args:
            message: User message containing mathematical expression
            conversation_id: Conversation identifier
            user_id: User identifier
            
        Returns:
            Dictionary containing calculation result and metadata
        """
        start_time = time.time()
        
        try:
            # First, try to extract expression using rules
            expression = self._extract_expression(message)
            
            if expression:
                # Use AI to calculate and explain
                result = await self._calculate_with_ai(expression, message)
            else:
                # Let AI handle the entire message
                result = await self._calculate_with_ai("", message)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Math calculation completed for conversation {conversation_id} "
                f"in {execution_time}ms"
            )
            
            return {
                "response": result["explanation"],
                "expression": result["expression"],
                "result": result["result"],
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Math calculation failed after {execution_time}ms: {e}")
            
            # Fallback response
            return {
                "response": "I apologize, but I'm having trouble with that calculation right now. Please try rephrasing your question or contact support if you need immediate assistance.",
                "expression": "",
                "result": "",
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def _extract_expression(self, message: str) -> Optional[str]:
        """
        Extract mathematical expression from message using regex patterns.
        
        Args:
            message: User message
            
        Returns:
            Extracted expression or None
        """
        message_lower = message.lower()
        
        # Common patterns for mathematical expressions
        patterns = [
            # "How much is X" pattern
            r'how much is\s+([\d\s\+\-\*\/\^\(\)\.]+)',
            # "Calculate X" pattern
            r'calculate\s+([\d\s\+\-\*\/\^\(\)\.]+)',
            # "What is X" pattern
            r'what is\s+([\d\s\+\-\*\/\^\(\)\.]+)',
            # Direct expression patterns
            r'(\d+\s*[\+\-\*\/\^]\s*\d+)',
            r'(\d+\s*x\s*\d+)',  # Multiplication with 'x'
            r'(\d+\s*\*\s*\d+)', # Multiplication with '*'
            # Parenthesized expressions
            r'\(([\d\s\+\-\*\/\^\(\)\.]+)\)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                expression = match.group(1) if len(match.groups()) > 0 else match.group(0)
                # Clean up the expression
                expression = re.sub(r'\s+', '', expression)  # Remove spaces
                expression = re.sub(r'x', '*', expression)   # Replace 'x' with '*'
                return expression
        
        return None
    
    async def _calculate_with_ai(self, expression: str, original_message: str) -> Dict[str, str]:
        """
        Use AI to calculate and explain mathematical expressions.
        
        Args:
            expression: Extracted mathematical expression
            original_message: Original user message
            
        Returns:
            Dictionary with calculation result and explanation
        """
        system_message = """
        You are a mathematical assistant that helps users with calculations.
        When given a mathematical expression, calculate it accurately and provide a clear explanation.
        Always show your work and explain the steps taken.
        If the expression is unclear, ask for clarification.
        Be friendly and helpful in your explanations.
        """
        
        if expression:
            prompt = f"""
            Please calculate the following mathematical expression: {expression}
            
            Original user message: "{original_message}"
            
            Provide the calculation, result, and a clear explanation of the steps.
            """
        else:
            prompt = f"""
            The user is asking for a mathematical calculation: "{original_message}"
            
            Please identify the mathematical expression in their message, calculate it, and provide a clear explanation.
            If you can't identify a clear mathematical expression, ask for clarification.
            """
        
        try:
            result = await self.ai_service.generate_structured_response(
                prompt=prompt,
                output_schema=MathCalculation,
                system_message=system_message
            )
            
            return result
            
        except Exception as e:
            logger.error(f"AI calculation failed: {e}")
            
            # Fallback to simple response
            if expression:
                return {
                    "expression": expression,
                    "result": "Unable to calculate",
                    "explanation": f"I found the expression '{expression}' but couldn't calculate it. Please try rephrasing or contact support."
                }
            else:
                return {
                    "expression": "",
                    "result": "No expression found",
                    "explanation": "I couldn't identify a clear mathematical expression in your message. Please try rephrasing your question."
                }
    
    def _validate_expression(self, expression: str) -> bool:
        """
        Validate mathematical expression for safety.
        
        Args:
            expression: Mathematical expression to validate
            
        Returns:
            True if expression is safe, False otherwise
        """
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'import\s+',           # Import statements
            r'exec\s*\(',           # Exec function
            r'eval\s*\(',           # Eval function
            r'__\w+__',             # Dunder methods
            r'[a-zA-Z_]\w*\s*\(',   # Function calls
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return False
        
        # Only allow safe mathematical characters
        safe_pattern = r'^[\d\s\+\-\*\/\^\(\)\.]+$'
        return bool(re.match(safe_pattern, expression))
