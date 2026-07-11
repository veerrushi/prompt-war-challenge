from pydantic import BaseModel, Field
from typing import List

class Message(BaseModel):
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of messages representing the conversation history")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {"role": "user", "content": "What should I pack for a monsoon emergency kit?"}
                ]
            }
        }
    }
