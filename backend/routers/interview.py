from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.interview_engine import start_interview, process_response
from backend.services.report_generator import generate_report

router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartInterviewRequest(BaseModel):
    candidate_id: str


class RespondRequest(BaseModel):
    session_id: str
    message: str
    speech_rate: float | None = None


@router.post("/start")
async def start(req: StartInterviewRequest):
    try:
        result = await start_interview(req.candidate_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/respond")
async def respond(req: RespondRequest):
    try:
        result = await process_response(req.session_id, req.message, req.speech_rate)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/report")
async def get_report(session_id: str):
    try:
        result = await generate_report(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
