import json
from openai import OpenAI
from backend.config import OPENAI_API_KEY, GPT_MODEL
from backend.database import get_supabase

client = OpenAI(api_key=OPENAI_API_KEY)


def _call_llm(prompt: str) -> str:
    response = client.responses.create(
        model=GPT_MODEL,
        reasoning={"effort": "medium"},
        input=[{"role": "user", "content": prompt}],
    )
    return response.output_text


async def evaluate_interview(session_id: str) -> dict:
    """Run full evaluation across all phases and store results."""
    db = get_supabase()

    session = db.table("interview_sessions").select("*").eq("id", session_id).single().execute()
    phase_config = session.data["phase_config"]

    conversation = db.table("conversation_history").select("*").eq("session_id", session_id).order("created_at").execute()
    messages = conversation.data

    scores = {}

    # Phase 2: Socrates Depth Score + Hint Utilization
    scores["phase2"] = _evaluate_drill_phase(messages, phase_config, phase_num=2)
    _store_eval(db, session_id, 2, "socrates_depth", scores["phase2"]["depth_score"], 1.0,
                {"depth_reached": scores["phase2"]["depth_reached"], "max_depth": scores["phase2"]["max_depth"]})
    _store_eval(db, session_id, 2, "hint_utilization", scores["phase2"]["hint_utilization"], 1.0,
                {"hints_given": scores["phase2"]["hints_given"], "recoveries": scores["phase2"]["recoveries"]})

    # Phase 3: Same metrics
    scores["phase3"] = _evaluate_drill_phase(messages, phase_config, phase_num=3)
    _store_eval(db, session_id, 3, "socrates_depth", scores["phase3"]["depth_score"], 1.0,
                {"depth_reached": scores["phase3"]["depth_reached"], "max_depth": scores["phase3"]["max_depth"]})
    _store_eval(db, session_id, 3, "hint_utilization", scores["phase3"]["hint_utilization"], 1.0,
                {"hints_given": scores["phase3"]["hints_given"], "recoveries": scores["phase3"]["recoveries"]})

    # Phase 4: Factual accuracy
    scores["phase4"] = await _evaluate_factual(phase_config)
    _store_eval(db, session_id, 4, "factual_accuracy", scores["phase4"]["accuracy"], 1.0,
                {"correct": scores["phase4"]["correct"], "total": scores["phase4"]["total"],
                 "details": scores["phase4"]["question_results"]})

    # Phase 5: Behavioral
    phase5_msgs = [m for m in messages if m["phase"] == 5]
    scores["phase5"] = await _evaluate_behavioral(phase5_msgs)
    for metric, value in scores["phase5"].items():
        _store_eval(db, session_id, 5, metric, value, 5.0, {})

    # Compute overall composite score
    p2_score = scores["phase2"]["depth_score"]
    p3_score = scores["phase3"]["depth_score"]
    p4_score = scores["phase4"]["accuracy"]
    p5_avg = sum(scores["phase5"].values()) / (len(scores["phase5"]) * 5) if scores["phase5"] else 0

    overall = (p2_score * 0.30) + (p3_score * 0.25) + (p4_score * 0.25) + (p5_avg * 0.20)

    return {
        "overall_score": round(overall * 100, 1),
        "phase_scores": {
            "phase2_socrates_depth": round(p2_score * 100, 1),
            "phase2_hint_utilization": round(scores["phase2"]["hint_utilization"] * 100, 1),
            "phase3_socrates_depth": round(p3_score * 100, 1),
            "phase3_hint_utilization": round(scores["phase3"]["hint_utilization"] * 100, 1),
            "phase4_factual_accuracy": round(p4_score * 100, 1),
            "phase5_visionary": scores["phase5"].get("visionary", 0),
            "phase5_groundedness": scores["phase5"].get("groundedness", 0),
            "phase5_team_player": scores["phase5"].get("team_player", 0),
        },
        "details": scores,
    }


def _evaluate_drill_phase(messages: list, phase_config: dict, phase_num: int) -> dict:
    """Evaluate Socratic depth for Phase 2 or 3."""
    phase_msgs = [m for m in messages if m["phase"] == phase_num]
    candidate_msgs = [m for m in phase_msgs if m["role"] == "candidate"]

    max_depth = phase_config.get(f"phase{phase_num}_depth", 0)
    hints_given = phase_config.get(f"phase{phase_num}_hints", 0)
    recoveries = phase_config.get(f"phase{phase_num}_hint_recoveries", 0)

    # Depth score: how deep did they go relative to max (8)
    depth_reached = max_depth
    depth_score = min(depth_reached / 8.0, 1.0) if depth_reached > 0 else 0.0

    # Hint utilization: did they recover after hints?
    hint_utilization = (recoveries / hints_given) if hints_given > 0 else 1.0

    return {
        "depth_score": depth_score,
        "depth_reached": depth_reached,
        "max_depth": 8,
        "hints_given": hints_given,
        "recoveries": recoveries,
        "hint_utilization": hint_utilization,
        "num_exchanges": len(candidate_msgs),
    }


async def _evaluate_factual(phase_config: dict) -> dict:
    """Evaluate Phase 4 factual answers using LLM grading."""
    answers = phase_config.get("phase4_answers", [])
    if not answers:
        return {"accuracy": 0.0, "correct": 0, "total": 0, "question_results": []}

    correct = 0
    results = []

    for qa in answers:
        grade_prompt = f"""Grade whether the candidate's answer is correct.

Question: {qa['question']}
Expected Answer: {qa['expected']}
Candidate's Answer: {qa['candidate_answer']}

Respond with ONLY a JSON object:
{{"correct": true/false, "explanation": "brief reason"}}"""

        raw = _call_llm(grade_prompt)
        # Strip code fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:raw.rfind("```")]
        try:
            grade = json.loads(raw.strip())
        except json.JSONDecodeError:
            grade = {"correct": False, "explanation": "Could not parse grading response"}

        if grade.get("correct"):
            correct += 1

        results.append({
            "question": qa["question"],
            "candidate_answer": qa["candidate_answer"],
            "correct": grade.get("correct", False),
            "explanation": grade.get("explanation", ""),
        })

    return {
        "accuracy": correct / len(answers) if answers else 0.0,
        "correct": correct,
        "total": len(answers),
        "question_results": results,
    }


async def _evaluate_behavioral(phase5_msgs: list) -> dict:
    """Evaluate Phase 5 behavioral responses using LLM."""
    if not phase5_msgs:
        return {"visionary": 0, "groundedness": 0, "team_player": 0}

    conversation = "\n".join(
        f"{'Interviewer' if m['role'] == 'interviewer' else 'Candidate'}: {m['content']}"
        for m in phase5_msgs
    )

    grade_prompt = f"""Evaluate this candidate's behavioral interview responses.

CONVERSATION:
{conversation}

Score each dimension from 1-5:
- visionary: Does the candidate have a clear long-term vision and ambition? (1=no direction, 5=clear compelling vision)
- groundedness: Are their goals realistic and well-reasoned? (1=unrealistic, 5=very grounded)
- team_player: Do they demonstrate collaboration, empathy, and conflict resolution? (1=poor teamwork, 5=excellent collaborator)

Respond with ONLY a JSON object:
{{"visionary": N, "groundedness": N, "team_player": N}}"""

    raw = _call_llm(grade_prompt)
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:raw.rfind("```")]
    try:
        scores = json.loads(raw.strip())
    except json.JSONDecodeError:
        scores = {"visionary": 3, "groundedness": 3, "team_player": 3}

    return scores


def _store_eval(db, session_id: str, phase: int, metric: str, score: float, max_score: float, details: dict):
    db.table("evaluations").insert({
        "session_id": session_id,
        "phase": phase,
        "metric_name": metric,
        "score": score,
        "max_score": max_score,
        "details": details,
    }).execute()
