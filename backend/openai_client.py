# backend/openai_client.py
from openai import AsyncOpenAI
import os, logging
from typing import AsyncGenerator, Optional, Union, List, Dict

logger = logging.getLogger(__name__)


class OpenAIClient:


    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY env-var missing")
        self.client = AsyncOpenAI(api_key=api_key)

        # let env override, otherwise use the speedy/cheap model
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")

    # ------------------------------------------------------------------ #
    async def _chat(self, messages: List[Dict[str, str]], *, stream: bool):
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=150,
            stream=stream,
        )

    # ------------------------------------------------------------------ #
    async def generate_response(
        self,
        state: str,
        base_prompt: str,
        user_name: Optional[str] = None,
        stream: bool = False,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        If stream==False  → returns a str  
        If stream==True   → returns an async generator that yields incremental text
        """

        system_prompt = (
            "You are a friendly insurance-onboarding assistant. "
            "Keep replies warm, ≤3 short sentences, and ask ONLY for the field in the current step."
        )
        user_prompt = (
            f"Current state: {state}\n"
            f"Base message: {base_prompt}\n"
            f"User name: {user_name or 'Not provided'}\n\n"
            "Rewrite the base message conversationally. "
            "Use the user's name sparingly (≈ once every few turns)."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        # ---- non-stream ----
        if not stream:
            try:
                resp = await self._chat(messages, stream=False)
                return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error("OpenAI error (non-stream): %s", e)
                return base_prompt

        # ---- streaming branch ----
        async def _gen() -> AsyncGenerator[str, None]:
            try:
                async for chunk in (await self._chat(messages, stream=True)):
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
            except Exception as e:
                logger.error("OpenAI error (stream): %s", e)
                yield "\n*(sorry, I hit an error)*"

        return _gen()

    # ------------------------------------------------------------------ #
    async def generate_error_response(
        self, state: str, user_input: str, error_message: str
    ) -> str:
        """simple non-stream helper"""
        sys_prompt = (
            "You are a helpful insurance assistant. "
            "When users make input errors, gently guide them without sounding condescending."
        )
        user_prompt = (
            f"The user provided invalid input for {state}.\n"
            f'User input: "{user_input}"\n'
            f"Error: {error_message}\n"
            "Create a friendly 1-2 sentence clarification."
        )
        try:
            resp = await self._chat(
                [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                stream=False,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error("OpenAI error (error-resp): %s", e)
            return f"I didn't understand that—{error_message}"
