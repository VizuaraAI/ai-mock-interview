import io
from openai import OpenAI
from backend.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> dict:
    """Transcribe audio using OpenAI Whisper. Returns text + word-level timestamps."""
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    # Get detailed transcription with word timestamps
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        timestamp_granularities=["word"],
    )

    words = response.words if hasattr(response, "words") and response.words else []
    duration = response.duration if hasattr(response, "duration") else 0

    # Calculate speech rate (words per minute)
    word_count = len(words)
    speech_rate = (word_count / duration * 60) if duration > 0 else 0

    # Detect stuttering: repeated consecutive words
    stutter_count = 0
    for i in range(1, len(words)):
        if words[i].word.lower().strip() == words[i - 1].word.lower().strip():
            stutter_count += 1

    # Detect long pauses (gaps > 2 seconds between words)
    long_pauses = 0
    for i in range(1, len(words)):
        gap = words[i].start - words[i - 1].end
        if gap > 2.0:
            long_pauses += 1

    return {
        "text": response.text,
        "duration": duration,
        "word_count": word_count,
        "speech_rate_wpm": round(speech_rate, 1),
        "stutter_count": stutter_count,
        "long_pauses": long_pauses,
    }
