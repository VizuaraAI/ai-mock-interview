from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.resume import router as resume_router
from backend.routers.interview import router as interview_router
from backend.routers.voice import router as voice_router

app = FastAPI(title="AI Mock Interview Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router)
app.include_router(interview_router)
app.include_router(voice_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
