import json
from openai import OpenAI
from backend.config import OPENAI_API_KEY, GPT_MODEL
from backend.database import get_supabase
from backend.services.prompts import (
    INTERVIEWER_SYSTEM_PROMPT,
    PHASE1_PROMPT,
    PHASE2_PROMPT,
    PHASE3_PROMPT,
    PHASE4_PROMPT,
    PHASE5_PROMPT,
)

client = OpenAI(api_key=OPENAI_API_KEY)


def _get_resume_data(candidate_id: str) -> dict:
    db = get_supabase()
    sections = db.table("resume_sections").select("*").eq("candidate_id", candidate_id).execute()
    resume = {}
    for s in sections.data:
        resume[s["section_type"]] = s["content"]
    return resume


def _get_conversation_history(session_id: str, phase: int | None = None) -> list[dict]:
    db = get_supabase()
    query = db.table("conversation_history").select("*").eq("session_id", session_id).order("created_at")
    if phase is not None:
        query = query.eq("phase", phase)
    result = query.execute()
    return result.data


def _format_conversation(history: list[dict]) -> str:
    if not history:
        return "No conversation yet. This is the start of the interview."
    lines = []
    for msg in history:
        role = "Interviewer" if msg["role"] == "interviewer" else "Candidate"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def _select_project(resume_data: dict, project_index: int) -> dict:
    """Select a project for deep-dive. project_index 0 = primary, 1 = secondary."""
    # Combine experience and projects, prioritize by relevance
    all_projects = []
    for exp in resume_data.get("experience", []):
        all_projects.append(exp)
    for proj in resume_data.get("projects", []):
        all_projects.append(proj)

    if project_index < len(all_projects):
        return all_projects[project_index]
    return all_projects[0] if all_projects else {"name": "Unknown", "bullets": []}


def _save_message(session_id: str, role: str, content: str, phase: int, depth_level: int = 0, is_hint: bool = False, speech_rate: float | None = None):
    db = get_supabase()
    record = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "phase": phase,
        "depth_level": depth_level,
        "is_hint": is_hint,
    }
    if speech_rate is not None:
        record["speech_rate"] = speech_rate
    db.table("conversation_history").insert(record).execute()


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.responses.create(
        model=GPT_MODEL,
        reasoning={"effort": "medium"},
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.output_text


async def start_interview(candidate_id: str) -> dict:
    """Start a new interview session and return the first question."""
    db = get_supabase()

    # Create session
    session = db.table("interview_sessions").insert({
        "candidate_id": candidate_id,
        "current_phase": 1,
        "status": "active",
        "phase_config": {
            "phase2_depth": 0,
            "phase3_depth": 0,
            "phase2_hints": 0,
            "phase3_hints": 0,
            "phase2_hint_recoveries": 0,
            "phase3_hint_recoveries": 0,
            "phase4_question_index": 0,
            "phase4_scores": [],
            "phase5_question_index": 0,
            "phase1_exchanges": 0,
        },
    }).execute()

    session_id = session.data[0]["id"]
    resume_data = _get_resume_data(candidate_id)

    # Generate first question
    prompt = PHASE1_PROMPT.format(
        resume_data=json.dumps(resume_data, indent=2),
        conversation_history="No conversation yet. Start the interview.",
    )
    response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)

    _save_message(session_id, "interviewer", response, phase=1)

    return {
        "session_id": session_id,
        "phase": 1,
        "interviewer_message": response,
    }


async def process_response(session_id: str, candidate_message: str, speech_rate: float | None = None) -> dict:
    """Process a candidate's response and generate the next interviewer message."""
    db = get_supabase()

    # Get session
    session = db.table("interview_sessions").select("*").eq("id", session_id).single().execute()
    session_data = session.data
    current_phase = session_data["current_phase"]
    candidate_id = session_data["candidate_id"]
    phase_config = session_data["phase_config"]

    if session_data["status"] != "active":
        return {"session_id": session_id, "phase": current_phase, "interviewer_message": "This interview has ended.", "status": "completed"}

    # Save candidate message
    depth = phase_config.get(f"phase{current_phase}_depth", 0) if current_phase in [2, 3] else 0
    _save_message(session_id, "candidate", candidate_message, phase=current_phase, depth_level=depth, speech_rate=speech_rate)

    # Get resume and conversation
    resume_data = _get_resume_data(candidate_id)
    conversation = _get_conversation_history(session_id)
    conv_text = _format_conversation(conversation)

    # Generate response based on current phase
    phase_complete = False

    if current_phase == 1:
        phase_config["phase1_exchanges"] = phase_config.get("phase1_exchanges", 0) + 1
        prompt = PHASE1_PROMPT.format(resume_data=json.dumps(resume_data, indent=2), conversation_history=conv_text)
        response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)

        if "[PHASE_COMPLETE]" in response or phase_config["phase1_exchanges"] >= 3:
            response = response.replace("[PHASE_COMPLETE]", "").strip()
            phase_complete = True

    elif current_phase == 2:
        project = _select_project(resume_data, 0)
        phase_config["phase2_depth"] = phase_config.get("phase2_depth", 0) + 1
        prompt = PHASE2_PROMPT.format(
            project_data=json.dumps(project, indent=2),
            resume_data=json.dumps(resume_data, indent=2),
            conversation_history=conv_text,
            depth_level=phase_config["phase2_depth"],
        )
        response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)

        if "[HINT]" in response:
            response = response.replace("[HINT]", "").strip()
            phase_config["phase2_hints"] = phase_config.get("phase2_hints", 0) + 1
            _save_message(session_id, "interviewer", response, phase=2, depth_level=phase_config["phase2_depth"], is_hint=True)

        if "[PHASE_COMPLETE]" in response or phase_config["phase2_depth"] >= 8:
            response = response.replace("[PHASE_COMPLETE]", "").strip()
            phase_complete = True

    elif current_phase == 3:
        project = _select_project(resume_data, 1)
        phase_config["phase3_depth"] = phase_config.get("phase3_depth", 0) + 1
        prompt = PHASE3_PROMPT.format(
            project_data=json.dumps(project, indent=2),
            resume_data=json.dumps(resume_data, indent=2),
            conversation_history=conv_text,
            depth_level=phase_config["phase3_depth"],
        )
        response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)

        if "[HINT]" in response:
            response = response.replace("[HINT]", "").strip()
            phase_config["phase3_hints"] = phase_config.get("phase3_hints", 0) + 1
            _save_message(session_id, "interviewer", response, phase=3, depth_level=phase_config["phase3_depth"], is_hint=True)

        if "[PHASE_COMPLETE]" in response or phase_config["phase3_depth"] >= 8:
            response = response.replace("[PHASE_COMPLETE]", "").strip()
            phase_complete = True

    elif current_phase == 4:
        # Phase 4 is handled differently — see question_bank integration
        # This will be filled in by Task 5
        from backend.services.question_bank import get_phase4_response
        result = await get_phase4_response(session_id, candidate_id, candidate_message, phase_config, conv_text)
        response = result["response"]
        phase_config = result["phase_config"]
        phase_complete = result["phase_complete"]

    elif current_phase == 5:
        phase_config["phase5_question_index"] = phase_config.get("phase5_question_index", 0) + 1
        prompt = PHASE5_PROMPT.format(
            conversation_history=conv_text,
            question_index=phase_config["phase5_question_index"],
        )
        response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)

        if "[PHASE_COMPLETE]" in response or phase_config["phase5_question_index"] >= 4:
            response = response.replace("[PHASE_COMPLETE]", "").strip()
            phase_complete = True

    # Save interviewer message (if not already saved as hint)
    if not (current_phase in [2, 3] and "[HINT]" not in response and phase_config.get(f"phase{current_phase}_hints", 0) > 0):
        is_hint = "[HINT]" in response if current_phase in [2, 3] else False
        if not is_hint:  # hints are saved above
            _save_message(session_id, "interviewer", response, phase=current_phase, depth_level=depth)

    # Handle phase transition
    status = "active"
    if phase_complete:
        if current_phase < 5:
            current_phase += 1
            # Generate the first question of the new phase
            new_phase_response = await _generate_phase_opener(session_id, candidate_id, current_phase, resume_data, phase_config)
            response = response + "\n\n" + new_phase_response if response.strip() else new_phase_response
        else:
            status = "completed"
            db.table("interview_sessions").update({"ended_at": "now()"}).eq("id", session_id).execute()

    # Update session
    db.table("interview_sessions").update({
        "current_phase": current_phase,
        "phase_config": phase_config,
        "status": status,
    }).eq("id", session_id).execute()

    result = {
        "session_id": session_id,
        "phase": current_phase,
        "interviewer_message": response,
        "status": status,
    }

    if current_phase in [2, 3]:
        result["depth_level"] = phase_config.get(f"phase{current_phase}_depth", 0)

    return result


async def _generate_phase_opener(session_id: str, candidate_id: str, phase: int, resume_data: dict, phase_config: dict) -> str:
    """Generate the opening question for a new phase."""
    conv_text = _format_conversation(_get_conversation_history(session_id))

    if phase == 2:
        project = _select_project(resume_data, 0)
        prompt = PHASE2_PROMPT.format(
            project_data=json.dumps(project, indent=2),
            resume_data=json.dumps(resume_data, indent=2),
            conversation_history=conv_text,
            depth_level=0,
        )
    elif phase == 3:
        project = _select_project(resume_data, 1)
        prompt = PHASE3_PROMPT.format(
            project_data=json.dumps(project, indent=2),
            resume_data=json.dumps(resume_data, indent=2),
            conversation_history=conv_text,
            depth_level=0,
        )
    elif phase == 4:
        from backend.services.question_bank import get_first_question
        question_text = await get_first_question(candidate_id, phase_config)
        _save_message(session_id, "interviewer", question_text, phase=4)
        return question_text
    elif phase == 5:
        prompt = PHASE5_PROMPT.format(
            conversation_history=conv_text,
            question_index=0,
        )
    else:
        return ""

    response = _call_llm(INTERVIEWER_SYSTEM_PROMPT, prompt)
    response = response.replace("[PHASE_COMPLETE]", "").replace("[HINT]", "").strip()
    _save_message(session_id, "interviewer", response, phase=phase)
    return response
