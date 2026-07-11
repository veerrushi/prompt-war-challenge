"""
Pydantic request/response schemas for the chat API.

Keeping schemas in a dedicated module decouples the data contract from
routing and business logic, making each layer easier to test and evolve.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single turn in the conversation.

    Attributes:
        role: The speaker role – must be one of ``user``, ``assistant``, or ``system``.
        content: The text content of the message.
    """

    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Role of the message sender (user, assistant, or system).",
    )
    content: str = Field(..., description="Text content of the message.", min_length=1)


class ChatRequest(BaseModel):
    """Payload accepted by the ``POST /api/chat`` endpoint.

    Attributes:
        messages: Ordered list of messages representing the full conversation history.
    """

    messages: list[Message] = Field(
        ...,
        description="Ordered conversation history sent to the LLM.",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "What should I pack for a monsoon emergency kit?",
                    }
                ]
            }
        }
    }
