"""
Router service that decides which agent should handle a user message.
"""

import time
import logging
import re
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from .ai_service import AIService

logger = logging.getLogger(__name__)


class RouterDecision(BaseModel):
    """Schema for router decision output."""
    
    agent: str = Field(..., description="Selected agent: KnowledgeAgent or MathAgent")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the decision")
    reasoning: str = Field(..., description="Reasoning for the decision")


class RouterService:
    """Service for routing messages to appropriate agents."""
    
    def __init__(self, ai_service: AIService):
        """Initialize the router service."""
        self.ai_service = ai_service
        logger.info("Router Service initialized")
    
    async def route_message(
        self, 
        message: str, 
        conversation_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Route a message to the appropriate agent.
        
        Args:
            message: User message to route
            conversation_id: Conversation identifier
            user_id: User identifier
            
        Returns:
            Dictionary containing routing decision and metadata
        """
        start_time = time.time()
        
        try:
            # First, try rule-based routing for efficiency
            rule_based_decision = self._rule_based_routing(message)
            
            if rule_based_decision:
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Router decision made via rules: {rule_based_decision['agent']} "
                    f"for conversation {conversation_id} in {execution_time}ms"
                )
                return {
                    **rule_based_decision,
                    "execution_time": execution_time,
                    "method": "rule_based"
                }
            
            # If rule-based routing fails, use AI-based routing
            ai_decision = await self._ai_based_routing(message)
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Router decision made via AI: {ai_decision['agent']} "
                f"for conversation {conversation_id} in {execution_time}ms"
            )
            
            return {
                **ai_decision,
                "execution_time": execution_time,
                "method": "ai_based"
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Router decision failed after {execution_time}ms: {e}")
            
            # Fallback to KnowledgeAgent as default
            return {
                "agent": "KnowledgeAgent",
                "confidence": 0.5,
                "reasoning": f"Fallback decision due to error: {str(e)}",
                "execution_time": execution_time,
                "method": "fallback"
            }
    
    def _rule_based_routing(self, message: str) -> Dict[str, Any]:
        """
        Rule-based routing using pattern matching.
        
        Args:
            message: User message to analyze
            
        Returns:
            Routing decision or None if no clear pattern
        """
        message_lower = message.lower().strip()
        
        # Math patterns
        math_patterns = [
            r'\b\d+\s*[\+\-\*\/\^]\s*\d+',  # Basic operations
            r'\bhow much is\b',  # "How much is X"
            r'\bcalculate\b',    # "Calculate X"
            r'\bwhat is\s+\d+',  # "What is 123"
            r'[\+\-\*\/\^\(\)]',  # Any math operators
            r'\b\d+\s*x\s*\d+',  # Multiplication with 'x'
            r'\b\d+\s*\*\s*\d+', # Multiplication with '*'
        ]
        
        for pattern in math_patterns:
            if re.search(pattern, message_lower):
                return {
                    "agent": "MathAgent",
                    "confidence": 0.9,
                    "reasoning": f"Mathematical expression detected: {pattern}"
                }
        
        # Knowledge patterns (questions about services, products, etc.)
        knowledge_patterns = [
            r'\bwhat\b.*\bfees?\b',      # Questions about fees
            r'\bhow\b.*\buse\b',         # How to use questions
            r'\bcan\b.*\buse\b',         # Can I use questions
            r'\bcard\b.*\bmachine\b',    # Card machine questions
            r'\bpayment\b',              # Payment questions
            r'\bhelp\b',                 # Help questions
            r'\bsupport\b',              # Support questions
        ]
        
        for pattern in knowledge_patterns:
            if re.search(pattern, message_lower):
                return {
                    "agent": "KnowledgeAgent",
                    "confidence": 0.8,
                    "reasoning": f"Knowledge question detected: {pattern}"
                }
        
        return None
    
    async def _ai_based_routing(self, message: str) -> Dict[str, Any]:
        """
        AI-based routing using LLM for complex decisions.
        
        Args:
            message: User message to analyze
            
        Returns:
            Routing decision from AI
        """
        system_message = """
        You are a router agent that decides which specialized agent should handle a user message.
        
        You have two agents available:
        1. KnowledgeAgent - Handles questions about products, services, fees, how-to guides, support, etc.
        2. MathAgent - Handles mathematical calculations, arithmetic operations, numerical questions
        
        Analyze the user message and determine which agent is most appropriate.
        Respond with high confidence (0.8-1.0) for clear cases and lower confidence (0.6-0.8) for ambiguous cases.
        """
        
        prompt = f"""
        User message: "{message}"
        
        Determine which agent should handle this message:
        - KnowledgeAgent: For questions about products, services, fees, how-to guides, support, etc.
        - MathAgent: For mathematical calculations, arithmetic operations, numerical questions
        
        Provide your decision with confidence and reasoning.
        """
        
        try:
            decision = await self.ai_service.generate_structured_response(
                prompt=prompt,
                output_schema=RouterDecision,
                system_message=system_message
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"AI-based routing failed: {e}")
            # Fallback to KnowledgeAgent
            return {
                "agent": "KnowledgeAgent",
                "confidence": 0.6,
                "reasoning": f"AI routing failed, defaulting to KnowledgeAgent: {str(e)}"
            }
