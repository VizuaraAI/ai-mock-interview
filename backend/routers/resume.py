import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.resume_parser import parse_resume_pdf
from backend.database import get_supabase

router = APIRouter(prefix="/api", tags=["resume"])


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    parsed = await parse_resume_pdf(pdf_bytes)

    db = get_supabase()

    # Insert candidate
    candidate = db.table("candidates").insert({
        "name": parsed.get("name", "Unknown"),
        "email": parsed.get("email"),
        "resume_raw": str(parsed),
    }).execute()

    candidate_id = candidate.data[0]["id"]

    # Insert resume sections
    section_mapping = {
        "education": parsed.get("education", []),
        "experience": parsed.get("experience", []),
        "projects": parsed.get("projects", []),
        "publications": parsed.get("publications", []),
        "skills": parsed.get("skills", {}),
        "contact": {
            "name": parsed.get("name"),
            "email": parsed.get("email"),
            "phone": parsed.get("phone"),
            "linkedin": parsed.get("linkedin"),
            "github": parsed.get("github"),
        },
    }

    for section_type, content in section_mapping.items():
        db.table("resume_sections").insert({
            "candidate_id": candidate_id,
            "section_type": section_type,
            "content": content,
        }).execute()

    return {
        "candidate_id": candidate_id,
        "parsed_resume": parsed,
    }
