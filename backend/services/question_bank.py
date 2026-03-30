import json
from backend.services.embeddings import retrieve_questions
from backend.services.prompts import INTERVIEWER_SYSTEM_PROMPT, PHASE4_PROMPT
from backend.database import get_supabase
from openai import OpenAI
from backend.config import OPENAI_API_KEY, GPT_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def _get_resume_text(candidate_id: str) -> str:
    db = get_supabase()
    sections = db.table("resume_sections").select("content, section_type").eq("candidate_id", candidate_id).execute()
    parts = []
    for s in sections.data:
        parts.append(f"{s['section_type']}: {json.dumps(s['content'])}")
    return "\n".join(parts)


async def get_first_question(candidate_id: str, phase_config: dict) -> str:
    """Get the first factual ML question based on resume similarity."""
    resume_text = _get_resume_text(candidate_id)
    questions = retrieve_questions(resume_text, n=5)

    # Store questions in phase_config
    phase_config["phase4_questions"] = questions
    phase_config["phase4_question_index"] = 0

    q = questions[0]
    return f"Now I have some factual questions for you. {q['question']}"


async def get_phase4_response(session_id: str, candidate_id: str, candidate_message: str, phase_config: dict, conv_text: str) -> dict:
    """Handle Phase 4 responses — evaluate answer and ask next question."""
    questions = phase_config.get("phase4_questions", [])
    q_index = phase_config.get("phase4_question_index", 0)

    if not questions:
        resume_text = _get_resume_text(candidate_id)
        questions = retrieve_questions(resume_text, n=5)
        phase_config["phase4_questions"] = questions

    # Current question that was just answered
    current_q = questions[q_index] if q_index < len(questions) else None

    # Store the candidate's answer for grading later
    if "phase4_answers" not in phase_config:
        phase_config["phase4_answers"] = []
    phase_config["phase4_answers"].append({
        "question": current_q["question"] if current_q else "",
        "expected": current_q["answer"] if current_q else "",
        "candidate_answer": candidate_message,
    })

    # Move to next question
    phase_config["phase4_question_index"] = q_index + 1
    next_index = q_index + 1

    phase_complete = next_index >= len(questions)

    if phase_complete:
        response = "Noted. That concludes the technical questions."
    else:
        next_q = questions[next_index]
        # Use LLM to create a natural transition
        prompt = PHASE4_PROMPT.format(
            current_question=next_q["question"],
            expected_answer=next_q["answer"],
            conversation_history=conv_text,
        )
        response = client.responses.create(
            model=GPT_MODEL,
            reasoning={"effort": "low"},
            input=[
                {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        ).output_text
        response = response.replace("[PHASE_COMPLETE]", "").strip()

    return {
        "response": response,
        "phase_config": phase_config,
        "phase_complete": phase_complete,
    }
