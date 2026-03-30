import io
import json
from openai import OpenAI
from backend.config import OPENAI_API_KEY, GPT_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

PARSE_PROMPT = """Parse this resume PDF and extract ALL information into a structured JSON format.
Return ONLY valid JSON with these exact keys:

{
  "name": "Full name",
  "email": "Email address",
  "phone": "Phone number",
  "linkedin": "LinkedIn URL",
  "github": "GitHub URL",
  "education": [
    {
      "institution": "Name",
      "degree": "Degree and field",
      "duration": "Start - End",
      "gpa": "GPA if mentioned"
    }
  ],
  "experience": [
    {
      "company": "Company name",
      "role": "Job title",
      "duration": "Start - End",
      "location": "Location",
      "bullets": ["bullet point 1", "bullet point 2"]
    }
  ],
  "projects": [
    {
      "name": "Project name",
      "tech_stack": "Technologies used",
      "duration": "Start - End",
      "bullets": ["bullet point 1", "bullet point 2"]
    }
  ],
  "publications": [
    {
      "title": "Publication title",
      "venue": "Conference/Journal"
    }
  ],
  "skills": {
    "languages": [],
    "frameworks": [],
    "tools": [],
    "other": []
  }
}

Be thorough — extract every single detail from the resume. If a field is not present, use null or empty array."""


async def parse_resume_pdf(pdf_bytes: bytes) -> dict:
    """Parse a resume PDF using OpenAI's file upload + responses API."""
    # Step 1: Upload file via Files API
    pdf_file = io.BytesIO(pdf_bytes)
    pdf_file.name = "resume.pdf"

    uploaded = client.files.create(file=pdf_file, purpose="assistants")

    # Step 2: Use responses API with file reference
    response = client.responses.create(
        model=GPT_MODEL,
        reasoning={"effort": "medium"},
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": uploaded.id,
                    },
                    {
                        "type": "input_text",
                        "text": PARSE_PROMPT,
                    },
                ],
            }
        ],
    )

    raw_text = response.output_text
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")]

    return json.loads(raw_text.strip())
