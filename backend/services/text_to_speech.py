import httpx
from backend.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"


async def synthesize_speech(text: str) -> bytes:
    """Convert text to speech using ElevenLabs API with Dr. Raj Dandekar's voice clone."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            ELEVENLABS_URL,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.85,
                    "style": 0.2,
                    "use_speaker_boost": True,
                },
            },
        )
        response.raise_for_status()
        return response.content
