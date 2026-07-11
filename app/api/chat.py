"""
Chat API router.

Exposes the ``POST /api/chat`` streaming endpoint that proxies user messages
to the Groq LLM service and returns server-sent events (SSE).
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.limiter import limiter
from app.models.schemas import ChatRequest
from app.services.groq_service import GroqService

logger = logging.getLogger(__name__)

router = APIRouter()
_groq_service = GroqService()


@router.post(
    "/chat",
    summary="Stream a chat response",
    response_description="Server-sent event stream of text tokens",
)
@limiter.limit("20/minute")
async def chat_endpoint(
    request: Request, chat_request: ChatRequest
) -> StreamingResponse:
    """Accept a conversation history and return a streaming AI response.

    The endpoint validates the incoming payload via Pydantic, then delegates
    to :class:`~app.services.groq_service.GroqService` which streams tokens
    from the Groq LLM as they are generated.

    Args:
        request: The raw FastAPI request (required by SlowAPI for rate-limiting).
        chat_request: Validated chat payload containing the conversation history.

    Returns:
        A :class:`~fastapi.responses.StreamingResponse` with ``text/event-stream`` media type.

    Raises:
        HTTPException: 400 if the messages list is empty.
    """
    if not chat_request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")

    logger.info(
        "Chat request received – %d message(s), last role: %s",
        len(chat_request.messages),
        chat_request.messages[-1].role,
    )

    return StreamingResponse(
        _groq_service.generate_chat_stream(chat_request.messages),
        media_type="text/event-stream",
    )
