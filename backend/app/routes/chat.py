"""
Chat routes for the main chatbot functionality.
"""

import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.chat import ChatRequest, ChatResponse, AgentWorkflowStep
from ..services import (
    AIService, RouterService, KnowledgeService, MathService,
    ConversationService, MessageService
)
from ..models import Conversation, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize services (in production, these would be dependency injected)
ai_service = AIService()
router_service = RouterService(ai_service)
knowledge_service = KnowledgeService(ai_service)
math_service = MathService(ai_service)
conversation_service = ConversationService()
message_service = MessageService()


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> ChatResponse:
    """
    Main chat endpoint that routes messages to appropriate agents.
    
    This endpoint:
    1. Creates or retrieves the conversation
    2. Routes the message to the appropriate agent
    3. Generates a response using the selected agent
    4. Stores the message and response in the database
    5. Returns the response with workflow information
    """
    start_time = time.time()
    
    try:
        # Step 1: Ensure conversation exists
        conversation = await conversation_service.get_conversation(db, request.conversation_id)
        if not conversation:
            from ..schemas.conversation import ConversationCreate
            conversation_data = ConversationCreate(
                conversation_id=request.conversation_id,
                user_id=request.user_id,
                title=f"Chat with {request.user_id}"
            )
            conversation = await conversation_service.create_conversation(db, conversation_data)
        
        # Step 2: Route message to appropriate agent
        router_start = time.time()
        routing_decision = await router_service.route_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_id=request.user_id
        )
        router_time = int((time.time() - router_start) * 1000)
        
        # Step 3: Generate response using selected agent
        agent_start = time.time()
        selected_agent = routing_decision["agent"]
        
        if selected_agent == "KnowledgeAgent":
            agent_response = await knowledge_service.get_response(
                message=request.message,
                conversation_id=request.conversation_id,
                user_id=request.user_id
            )
            source_agent_response = agent_response["response"]
            agent_time = agent_response["execution_time"]
            
        elif selected_agent == "MathAgent":
            agent_response = await math_service.calculate(
                message=request.message,
                conversation_id=request.conversation_id,
                user_id=request.user_id
            )
            source_agent_response = agent_response["response"]
            agent_time = agent_response["execution_time"]
            
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown agent: {selected_agent}"
            )
        
        # Step 4: Build agent workflow
        agent_workflow = [
            AgentWorkflowStep(
                agent="RouterAgent",
                decision=selected_agent,
                execution_time=router_time
            ),
            AgentWorkflowStep(
                agent=selected_agent,
                execution_time=agent_time
            )
        ]
        
        # Step 5: Store message in database
        from ..schemas.message import MessageCreate
        message_data = MessageCreate(
            conversation_id=request.conversation_id,
            content=request.message,
            response=source_agent_response,
            source_agent=selected_agent,
            source_agent_response=source_agent_response,
            agent_workflow=[step.dict() for step in agent_workflow],
            execution_time=router_time + agent_time
        )
        
        await message_service.create_message(db, message_data)
        
        # Step 6: Calculate total execution time
        total_execution_time = int((time.time() - start_time) * 1000)
        
        # Step 7: Log the interaction
        logger.info(
            f"Chat request processed - User: {request.user_id}, "
            f"Conversation: {request.conversation_id}, "
            f"Agent: {selected_agent}, "
            f"Total time: {total_execution_time}ms"
        )
        
        # Step 8: Return response
        return ChatResponse(
            response=source_agent_response,
            source_agent_response=source_agent_response,
            agent_workflow=agent_workflow,
            conversation_id=request.conversation_id,
            execution_time=total_execution_time
        )
        
    except Exception as e:
        total_execution_time = int((time.time() - start_time) * 1000)
        logger.error(
            f"Chat request failed after {total_execution_time}ms - "
            f"User: {request.user_id}, Conversation: {request.conversation_id}, Error: {e}"
        )
        
        # Return error response
        error_workflow = [
            AgentWorkflowStep(
                agent="ErrorHandler",
                decision="Error occurred during processing",
                execution_time=total_execution_time
            )
        ]
        
        return ChatResponse(
            response="I apologize, but I'm experiencing technical difficulties right now. Please try again later or contact support for immediate assistance.",
            source_agent_response="Error occurred during message processing",
            agent_workflow=error_workflow,
            conversation_id=request.conversation_id,
            execution_time=total_execution_time
        )
