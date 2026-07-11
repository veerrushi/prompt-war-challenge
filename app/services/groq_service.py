import asyncio
import logging
from typing import AsyncGenerator, List
from groq import AsyncGroq
from app.core.config import get_settings
from app.models.schemas import Message

logger = logging.getLogger(__name__)

# System prompt defining the persona and constraints
SYSTEM_PROMPT = """You are a highly capable and empathetic Monsoon Preparedness & Citizen Assistance AI.
Your primary goal is to help individuals, families, and communities prepare for the monsoon season and assist them before, during, and after severe weather events.

Core Responsibilities:
1. Provide personalized preparedness plans based on user context (location, family size, specific needs).
2. Offer emergency checklists, travel advisories, and safety recommendations.
3. If the user hasn't provided enough context (e.g., location, specific concern), politely ask clarifying questions to provide better, tailored advice.
4. Keep your responses concise, actionable, and formatted beautifully using Markdown (bullet points, bold text for emphasis).
5. If asked about topics completely unrelated to monsoon preparedness, severe weather, or emergencies, politely decline and steer the conversation back to your core purpose.

Always prioritize safety. Emphasize that for immediate, life-threatening emergencies, they should contact local emergency services.
"""

class GroqService:
    def __init__(self):
        settings = get_settings()
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        
    async def generate_chat_stream(self, messages: List[Message]) -> AsyncGenerator[str, None]:
        # Prepend system prompt
        groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in messages:
            groq_messages.append({"role": msg.role, "content": msg.content})
            
        try:
            stream = await self.client.chat.completions.create(
                messages=groq_messages,
                model=self.model,
                stream=True,
                temperature=0.5,
                max_tokens=2048,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    # Small sleep to yield to event loop (optional, but good practice in async generators)
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Error communicating with Groq API: {e}")
            yield f"Error: Unable to generate response at this time. Please try again later. ({str(e)})"
