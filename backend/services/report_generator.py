from backend.database import get_supabase
from backend.services.evaluation import evaluate_interview


async def generate_report(session_id: str) -> dict:
    """Generate and store the final interview report."""
    db = get_supabase()

    # Run evaluation
    eval_result = await evaluate_interview(session_id)

    # Build narrative report
    ps = eval_result["phase_scores"]
    overall = eval_result["overall_score"]

    report_text = f"""# Interview Evaluation Report

## Overall Score: {overall}/100

---

## Phase 2: Technical Deep-Dive (Project 1)
- **Socrates Depth Score**: {ps['phase2_socrates_depth']}% — Candidate reached depth level {eval_result['details']['phase2']['depth_reached']}/8
- **Hint Utilization**: {ps['phase2_hint_utilization']}% — {eval_result['details']['phase2']['hints_given']} hints given, {eval_result['details']['phase2']['recoveries']} successful recoveries

## Phase 3: Technical Deep-Dive (Project 2)
- **Socrates Depth Score**: {ps['phase3_socrates_depth']}% — Candidate reached depth level {eval_result['details']['phase3']['depth_reached']}/8
- **Hint Utilization**: {ps['phase3_hint_utilization']}% — {eval_result['details']['phase3']['hints_given']} hints given, {eval_result['details']['phase3']['recoveries']} successful recoveries

## Phase 4: Factual ML Questions
- **Accuracy**: {ps['phase4_factual_accuracy']}% — {eval_result['details']['phase4']['correct']}/{eval_result['details']['phase4']['total']} correct
"""
    # Add per-question breakdown
    for qr in eval_result["details"]["phase4"].get("question_results", []):
        status = "Correct" if qr["correct"] else "Incorrect"
        report_text += f"  - [{status}] {qr['question']}: {qr['explanation']}\n"

    report_text += f"""
## Phase 5: Behavioral Assessment
- **Visionary Thinking**: {ps['phase5_visionary']}/5
- **Groundedness**: {ps['phase5_groundedness']}/5
- **Team Player**: {ps['phase5_team_player']}/5

---

## Scoring Weights
- Phase 2 Technical Depth: 30%
- Phase 3 Technical Depth: 25%
- Phase 4 Factual Knowledge: 25%
- Phase 5 Behavioral: 20%
"""

    # Store report
    db.table("final_reports").insert({
        "session_id": session_id,
        "overall_score": overall,
        "phase_scores": ps,
        "report_text": report_text,
    }).execute()

    return {
        "overall_score": overall,
        "phase_scores": ps,
        "report_text": report_text,
        "details": eval_result["details"],
    }
