import os, logging, asyncio, base64
from deepgram import Deepgram
from typing import AsyncGenerator, Optional

log = logging.getLogger(__name__)

class DeepgramClient:
    """Thin async helper around the Deepgram Realtime Voice-Agent websocket."""

    def __init__(self) -> None:
        key = os.getenv("DEEPGRAM_API_KEY")
        if not key:
            raise RuntimeError("DEEPGRAM_API_KEY missing")
        self._dg     = Deepgram(key)
        self._socket = None          # will hold the DG realtime socket
        self._queue  = asyncio.Queue()   # assistant → audio we push back

    # ----------------------------------------------------------- CONNECT
    async def open(self) -> None:
        if self._socket:             # already open
            return
        self._socket = await self._dg.transcription.prerecorded.live(
            {
                "model":     "nova-2",
                "encoding":  "linear16",
                "sample_rate": 16000,
                "punctuate": True,
                "endpointing": 300,
            },
            self._handle_event,
        )

    # ------------------------------------------------- AUDIO → DEEPGRAM
    async def send_audio(self, pcm16: bytes) -> None:
        await self.open()
        await self._socket.send(pcm16)

    # ------------------------------------------- pull assistant speech
    async def assistant_audio(self) -> bytes:
        """await-able that yields next audio frame produced by DG TTS"""
        return await self._queue.get()

    # ------------------------------------------------ internal handler
    async def _handle_event(self, data: dict) -> None:
        """
        Deepgram fires many event types.
        We're interested in:
            • "channel.alternatives"   → partial / final transcript
            • "audio.playback"        → TTS audio chunks (base64)
        """
        if data.get("type") == "audio.playback":
            # put decoded MP3/PCM into queue so main loop can forward
            b64 = data["audio"]["data"]
            await self._queue.put(base64.b64decode(b64))

    # ---------------------------------------- helper to close politely
    async def close(self) -> None:
        if self._socket:
            await self._socket.finish()
            self._socket = None
