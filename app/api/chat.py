from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.services.groq_service import GroqService
from app.core.limiter import limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
groq_service = GroqService()

@router.post("/chat")
@limiter.limit("20/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    """
    Streaming chat endpoint that processes user messages and returns an AI response via Groq.
    """
    if not chat_request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")
        
    return StreamingResponse(
        groq_service.generate_chat_stream(chat_request.messages),
        media_type="text/event-stream"
    )
