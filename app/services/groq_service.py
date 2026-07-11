"""
Groq LLM service for streaming chat completions.

Wraps the AsyncGroq client and injects the domain-specific system prompt
so that every conversation is grounded in monsoon preparedness guidance.
"""

import asyncio
import logging
from typing import AsyncGenerator, List

from groq import APIError, AsyncGroq

from app.core.config import get_settings
from app.models.schemas import Message

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: LLM model to use for all completions.
MODEL_ID = "llama-3.3-70b-versatile"

#: Controls creativity: lower values produce more focused, factual answers.
TEMPERATURE = 0.5

#: Maximum tokens the model may generate per response.
MAX_TOKENS = 2048

#: Rate at which the async generator yields control back to the event loop.
STREAM_YIELD_INTERVAL = 0  # seconds (0 = next iteration, no sleep)

SYSTEM_PROMPT = """You are a highly capable and empathetic Monsoon Preparedness & Citizen Assistance AI.
Your primary goal is to help individuals, families, and communities prepare for the monsoon season
and assist them before, during, and after severe weather events.

Core Responsibilities:
1. Provide personalised preparedness plans based on user context (location, family size, specific needs).
2. Offer emergency checklists, travel advisories, and safety recommendations.
3. If the user hasn't provided enough context (e.g., location, specific concern), politely ask
   clarifying questions to provide better, tailored advice.
4. Keep responses concise, actionable, and formatted in Markdown (bullet points, bold text for emphasis).
5. If asked about topics completely unrelated to monsoon preparedness, severe weather, or emergencies,
   politely decline and steer the conversation back to your core purpose.

Always prioritise safety. Emphasise that for immediate, life-threatening emergencies, users should
contact local emergency services immediately.
"""


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class GroqService:
    """Async wrapper around the Groq chat-completions API.

    Handles client initialisation, message formatting, and streaming token
    delivery via an :class:`~typing.AsyncGenerator`.
    """

    def __init__(self) -> None:
        """Initialise the Groq client from application settings."""
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = MODEL_ID

    def _build_messages(self, messages: List[Message]) -> List[dict]:
        """Prepend the system prompt to the user conversation history.

        Args:
            messages: The ordered list of user/assistant turns.

        Returns:
            A list of message dicts ready for the Groq API.
        """
        return [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

    async def generate_chat_stream(
        self, messages: List[Message]
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens for the given conversation.

        Yields each text chunk as it arrives from the Groq API.  On API or
        unexpected errors, yields a human-readable error message instead of
        raising, so the SSE stream closes gracefully.

        Args:
            messages: Ordered conversation history (user + assistant turns).

        Yields:
            Successive text chunks from the LLM response.
        """
        groq_messages = self._build_messages(messages)

        try:
            stream = await self.client.chat.completions.create(
                messages=groq_messages,
                model=self.model,
                stream=True,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
            )

            async for chunk in stream:
                token = chunk.choices[0].delta.content if chunk.choices else None
                if token:
                    yield token
                    await asyncio.sleep(STREAM_YIELD_INTERVAL)

        except APIError as exc:
            logger.error("Groq API error (status=%s): %s", exc.status_code, exc.message)
            yield "⚠️ The AI service is temporarily unavailable. Please try again in a moment."

        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error during Groq streaming: %s", exc)
            yield "⚠️ An unexpected error occurred. Please try again later."
