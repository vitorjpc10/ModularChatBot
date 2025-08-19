"""
AI service using LangChain with Groq API integration.
"""

import time
import logging
from typing import Optional, Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI service for LLM interactions using Groq API."""
    
    def __init__(self):
        """Initialize the AI service with Groq client."""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for AIService")
        
        self.client = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.1,
            max_tokens=2048
        )
        logger.info(f"AI Service initialized with model: {settings.GROQ_MODEL}")
    
    async def generate_response(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.1
    ) -> str:
        """
        Generate a response using the Groq LLM.
        
        Args:
            prompt: The user prompt
            system_message: Optional system message to set context
            temperature: Controls randomness (0.0 = deterministic, 1.0 = very random)
            
        Returns:
            Generated response text
        """
        start_time = time.time()
        
        try:
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=prompt))
            
            # Update temperature for this request
            self.client.temperature = temperature
            
            response = await self.client.agenerate([messages])
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"AI response generated in {execution_time}ms")
            
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"AI response generation failed after {execution_time}ms: {e}")
            raise
    
    async def generate_structured_response(
        self, 
        prompt: str, 
        output_schema: BaseModel,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured response using Pydantic output parsing.
        
        Args:
            prompt: The user prompt
            output_schema: Pydantic model defining the expected output structure
            system_message: Optional system message to set context
            
        Returns:
            Structured response as dictionary
        """
        start_time = time.time()
        
        try:
            parser = PydanticOutputParser(pydantic_object=output_schema)
            
            # Add format instructions to the prompt
            format_instructions = parser.get_format_instructions()
            full_prompt = f"{prompt}\n\n{format_instructions}"
            
            messages = []
            
            if system_message:
                messages.append(SystemMessage(content=system_message))
            
            messages.append(HumanMessage(content=full_prompt))
            
            response = await self.client.agenerate([messages])
            response_text = response.generations[0][0].text.strip()
            
            # Parse the structured response
            parsed_response = parser.parse(response_text)
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Structured AI response generated in {execution_time}ms")
            
            return parsed_response.dict()
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Structured AI response generation failed after {execution_time}ms: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if the AI service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            return bool(settings.GROQ_API_KEY and self.client)
        except Exception as e:
            logger.error(f"AI service health check failed: {e}")
            return False
