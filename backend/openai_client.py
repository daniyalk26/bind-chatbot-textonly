# backend/openai_client.py
from openai import OpenAI
import os
from typing import AsyncGenerator, Optional, Union
import logging
import asyncio

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        # Use synchronous client
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"
    
    async def generate_response(
        self, 
        state: str, 
        base_prompt: str, 
        user_name: Optional[str] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[str, None]]:
        
        system_prompt = """You are a friendly insurance onboarding assistant. Keep responses:
        1. Conversational and warm
        2. Clear and concise (max 2-3 sentences)
        3. Focused on collecting the required information
        
        Never ask for information that's not in the current step."""
        
        user_prompt = f"""Current state: {state}
Base message: {base_prompt}
User name: {user_name if user_name else 'Not provided yet'}

Deliver the base message conversationally. Use the user's name sparingly if known."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            if stream:
                return self._stream_response(messages)
            else:
                # Run synchronous call in executor
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=150
                    )
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return base_prompt
    
    async def _stream_response(self, messages) -> AsyncGenerator[str, None]:
        try:
            # For streaming, we'll use the sync client
            loop = asyncio.get_event_loop()
            
            def get_stream():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=150,
                    stream=True
                )
            
            stream = await loop.run_in_executor(None, get_stream)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            yield "I apologize, but I'm having trouble generating a response."
    
    async def generate_error_response(
        self, 
        state: str, 
        user_input: str, 
        error_message: str
    ) -> str:
        
        system_prompt = """You are a helpful insurance assistant. When users make input errors, 
        gently guide them to the correct format without being condescending."""
        
        user_prompt = f"""The user provided invalid input for {state}.
User input: "{user_input}"
Error: {error_message}

Create a friendly 1-2 sentence response that guides them to the correct format."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"I didn't understand that. {error_message}"