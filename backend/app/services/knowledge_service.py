"""
Knowledge service for RAG-based responses using InfinitePay help content.
"""

import time
import logging
import requests
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
import re

from .ai_service import AIService
from ..config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for knowledge-based responses using RAG."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the knowledge service."""
        self.ai_service = ai_service
        self.knowledge_base = {}
        self.last_update = None
        logger.info("Knowledge Service initialized")
    
    async def get_response(
        self, 
        message: str, 
        conversation_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get a knowledge-based response using RAG.
        
        Args:
            message: User message
            conversation_id: Conversation identifier
            user_id: User identifier
            
        Returns:
            Dictionary containing response and metadata
        """
        start_time = time.time()
        
        try:
            # Update knowledge base if needed
            await self._update_knowledge_base()
            
            # Search for relevant content
            relevant_content = self._search_knowledge_base(message)
            
            # Generate response using AI with context
            response = await self._generate_response_with_context(message, relevant_content)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Knowledge response generated for conversation {conversation_id} "
                f"in {execution_time}ms"
            )
            
            return {
                "response": response,
                "source_content": relevant_content,
                "execution_time": execution_time,
                "sources": self._extract_sources(relevant_content)
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Knowledge response generation failed after {execution_time}ms: {e}")
            
            # Fallback response
            return {
                "response": "I apologize, but I'm having trouble accessing the knowledge base right now. Please try again later or contact support for immediate assistance.",
                "source_content": "",
                "execution_time": execution_time,
                "sources": [],
                "error": str(e)
            }
    
    async def _update_knowledge_base(self) -> None:
        """Update the knowledge base from InfinitePay help content."""
        # For now, we'll use a simple approach
        # In a production system, you might want to implement proper caching
        # and periodic updates
        
        if self.knowledge_base and self.last_update:
            # Check if we need to update (e.g., every hour)
            import datetime
            if (datetime.datetime.now() - self.last_update).seconds < 3600:
                return
        
        try:
            # Fetch content from InfinitePay help
            content = await self._fetch_infinitepay_content()
            
            # Process and store content
            self.knowledge_base = self._process_content(content)
            self.last_update = datetime.datetime.now()
            
            logger.info("Knowledge base updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}")
            # Use fallback content if available
            if not self.knowledge_base:
                self.knowledge_base = self._get_fallback_content()
    
    async def _fetch_infinitepay_content(self) -> str:
        """Fetch content from InfinitePay help website."""
        try:
            response = requests.get(settings.INFINITEPAY_HELP_URL, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract relevant content (adjust selectors based on actual website structure)
            content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            
            content = []
            for element in content_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short text
                    content.append(text)
            
            return "\n".join(content)
            
        except Exception as e:
            logger.error(f"Failed to fetch InfinitePay content: {e}")
            raise
    
    def _process_content(self, content: str) -> Dict[str, str]:
        """Process raw content into searchable knowledge base."""
        # Simple processing - split into chunks
        # In a production system, you might use more sophisticated chunking
        
        chunks = content.split('\n\n')
        knowledge_base = {}
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                # Create a simple key for the chunk
                key = f"chunk_{i}"
                knowledge_base[key] = chunk.strip()
        
        return knowledge_base
    
    def _search_knowledge_base(self, query: str) -> str:
        """Search the knowledge base for relevant content."""
        query_lower = query.lower()
        relevant_chunks = []
        
        for key, content in self.knowledge_base.items():
            # Simple keyword matching
            # In a production system, you might use vector embeddings or more sophisticated search
            
            content_lower = content.lower()
            score = 0
            
            # Check for keyword matches
            keywords = query_lower.split()
            for keyword in keywords:
                if keyword in content_lower:
                    score += 1
            
            if score > 0:
                relevant_chunks.append((score, content))
        
        # Sort by relevance score
        relevant_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 3 most relevant chunks
        top_chunks = relevant_chunks[:3]
        return "\n\n".join([chunk[1] for chunk in top_chunks])
    
    async def _generate_response_with_context(self, message: str, context: str) -> str:
        """Generate response using AI with context from knowledge base."""
        system_message = """
        You are a helpful assistant for InfinitePay, a payment processing company.
        Use the provided context to answer user questions accurately and helpfully.
        If the context doesn't contain enough information, be honest about it and suggest contacting support.
        Always be friendly and professional in your responses.
        """
        
        prompt = f"""
        Context from knowledge base:
        {context}
        
        User question: {message}
        
        Please provide a helpful and accurate response based on the context above.
        If the context doesn't fully answer the question, acknowledge this and suggest contacting support for more specific information.
        """
        
        return await self.ai_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            temperature=0.3
        )
    
    def _extract_sources(self, content: str) -> List[str]:
        """Extract source information from content."""
        # For now, return a simple source
        # In a production system, you might extract actual URLs or references
        return [settings.INFINITEPAY_HELP_URL]
    
    def _get_fallback_content(self) -> Dict[str, str]:
        """Get fallback content when external source is unavailable."""
        return {
            "general_info": """
            InfinitePay is a payment processing company that provides card machine services.
            We offer various payment solutions for businesses of all sizes.
            For specific information about fees, rates, or technical support, please contact our support team.
            """,
            "contact_info": """
            For immediate assistance, please contact our support team.
            You can reach us through our website or by calling our support line.
            Our team is available to help with any questions about our services.
            """
        }
