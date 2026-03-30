from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from backend.services.speech_to_text import transcribe_audio
from backend.services.text_to_speech import synthesize_speech
from backend.services.anxiety_detector import detect_anxiety

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """Transcribe audio to text using Whisper + anxiety detection."""
    try:
        audio_bytes = await file.read()
        result = transcribe_audio(audio_bytes, filename=file.filename or "audio.webm")

        # Handle coroutine if async
        if hasattr(result, "__await__"):
            result = await result

        # Run anxiety detection
        anxiety = detect_anxiety(result)

        return {
            "text": result["text"],
            "speech_rate_wpm": result["speech_rate_wpm"],
            "duration": result["duration"],
            "anxiety": anxiety,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SynthesizeRequest(BaseModel):
    text: str


@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    """Convert text to speech using ElevenLabs (Dr. Raj Dandekar voice)."""
    try:
        audio_bytes = await synthesize_speech(req.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
