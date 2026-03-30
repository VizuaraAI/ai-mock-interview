# Sprint v1 — PRD: AI Mock Interview Agent

## Overview
Build a full-stack AI-powered mock interview system that parses a candidate's resume PDF (via OpenAI), conducts a realistic 5-phase ML Engineering interview through a React chat interface with voice I/O (Whisper STT + ElevenLabs TTS), evaluates responses with custom metrics (Socrates depth, factual accuracy, behavioral rubrics), and generates a final scorecard report. All data persisted in Supabase.

## Goals
- Candidate uploads resume PDF → parsed into structured sections via OpenAI and stored in Supabase
- 5-phase interview runs end-to-end: Background → Project Deep-Dive 1 → Project Deep-Dive 2 → Factual ML → Behavioral
- Voice input (Whisper) and voice output (ElevenLabs, Dr. Raj Dandekar clone) with text fallback
- Russian Doll / Socratic drilling in Phases 2-3 with hint system and depth tracking
- ML question bank (80 questions, 384-dim embeddings) with similarity-based retrieval per candidate field
- Anxiety detection from speech patterns (fast rate, stuttering) → automatic calming intervention
- Evaluation engine produces per-phase scores and a final PDF/HTML report
- Professional interviewer tone — no enthusiasm, no praise, concise and direct

## User Stories
- As a candidate, I want to upload my resume and start a mock interview, so I can practice for ML engineering roles
- As a candidate, I want the interviewer to drill deep into my projects using follow-up questions, so I can identify gaps in my knowledge
- As a candidate, I want voice interaction that sounds like a real interviewer, so the experience feels authentic
- As a candidate, I want hints when I'm stuck, so I can learn during the interview
- As a candidate, I want a detailed evaluation report after the interview, so I know exactly where to improve
- As a candidate, I want the system to detect when I'm anxious and give me a moment to breathe, so the experience isn't overwhelming

## Technical Architecture

### Tech Stack
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: Python FastAPI
- **LLM**: OpenAI GPT-5.4 (reasoning model) via `client.responses.create()`
- **STT**: OpenAI Whisper API
- **TTS**: ElevenLabs API (voice clone ID: `lZORFNDokoBmfd0S06vf`)
- **Database**: Supabase (PostgreSQL)
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (384-dim)
- **Similarity Search**: FAISS

### Component Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Resume   │  │ Chat      │  │ Voice    │  │ Report    │  │
│  │ Upload   │  │ Interface │  │ Controls │  │ Viewer    │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │             │              │         │
└───────┼──────────────┼─────────────┼──────────────┼─────────┘
        │              │             │              │
        ▼              ▼             ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Resume   │  │ Interview │  │ Voice    │  │ Evaluation│  │
│  │ Parser   │  │ Engine    │  │ Pipeline │  │ Engine    │  │
│  │(OpenAI)  │  │(GPT-5.4) │  │(Whisper+ │  │(Scoring + │  │
│  │          │  │           │  │ElevenLabs│  │ Report)   │  │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────┬─────┘  │
│       │              │             │              │         │
│  ┌────┴──────────────┴─────────────┴──────────────┴─────┐  │
│  │              Interview State Machine                  │  │
│  │  Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5     │  │
│  │  (Intro)   (Drill1)  (Drill2)  (Factual) (Behavioral)│  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Supabase                               │
│  ┌────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │ candidates │ │resume_sections│ │ interview_sessions    │ │
│  │            │ │              │ │ conversation_history   │ │
│  │            │ │              │ │ evaluations            │ │
│  │            │ │              │ │ final_reports          │ │
│  └────────────┘ └──────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
1. Candidate uploads PDF → Backend sends to OpenAI for parsing → Structured sections stored in Supabase
2. Interview starts → State machine advances through 5 phases
3. Each turn: Candidate speaks → Whisper transcribes → GPT-5.4 generates response → ElevenLabs speaks
4. Phase 2-3: Depth tracker increments on each follow-up, hint counter tracks nudges given
5. Phase 4: Resume embeddings → FAISS similarity search → retrieve relevant ML questions
6. Interview ends → Evaluation engine scores all phases → Final report generated and stored

### Database Schema
```sql
-- Candidates
candidates (id UUID PK, name TEXT, email TEXT, resume_raw TEXT, created_at TIMESTAMPTZ)

-- Parsed resume sections
resume_sections (id UUID PK, candidate_id UUID FK, section_type TEXT, content JSONB, created_at TIMESTAMPTZ)
-- section_type: education | experience | projects | publications | skills

-- Interview sessions
interview_sessions (id UUID PK, candidate_id UUID FK, current_phase INT DEFAULT 1,
                    phase_config JSONB, status TEXT DEFAULT 'active',
                    started_at TIMESTAMPTZ, ended_at TIMESTAMPTZ)

-- Conversation history
conversation_history (id UUID PK, session_id UUID FK, role TEXT, content TEXT,
                      phase INT, depth_level INT DEFAULT 0, is_hint BOOLEAN DEFAULT FALSE,
                      audio_url TEXT, speech_rate FLOAT, created_at TIMESTAMPTZ)

-- Per-phase evaluations
evaluations (id UUID PK, session_id UUID FK, phase INT, metric_name TEXT,
             score FLOAT, max_score FLOAT, details JSONB, created_at TIMESTAMPTZ)

-- Final reports
final_reports (id UUID PK, session_id UUID FK, overall_score FLOAT,
               phase_scores JSONB, report_text TEXT, created_at TIMESTAMPTZ)
```

### Evaluation Metrics

| Phase | Metric | How It Works |
|-------|--------|--------------|
| Phase 1 | None | Warm-up, no scoring |
| Phase 2 | Socrates Depth Score | `depth_reached / max_possible_depth` (0-1). Tracks how many levels deep the candidate answered correctly before failing |
| Phase 2 | Hint Utilization | `correct_after_hint / total_hints_given` (0-1). Did hints help them recover? |
| Phase 3 | Socrates Depth Score | Same as Phase 2, different project |
| Phase 3 | Hint Utilization | Same as Phase 2 |
| Phase 4 | Factual Accuracy | `correct_answers / total_questions` (0-1) |
| Phase 5 | Visionary Thinking | 1-5 scale: Does the candidate have a clear long-term vision? |
| Phase 5 | Groundedness | 1-5 scale: Are their goals realistic and well-reasoned? |
| Phase 5 | Team Player | 1-5 scale: Do they demonstrate collaboration and empathy? |
| Overall | Composite Score | Weighted average: Phase 2 (30%) + Phase 3 (25%) + Phase 4 (25%) + Phase 5 (20%) |

### Interviewer Prompt Engineering (Tone Rules)
```
SYSTEM PROMPT RULES:
- You are a senior ML engineering interviewer at a top tech company
- Be professional, concise, and direct
- NEVER say: "Great answer", "Excellent", "Incredible", "That's right", "Perfect"
- NEVER show enthusiasm or excitement
- When a candidate answers, acknowledge minimally ("Noted." / "I see." / "Understood.")
  then immediately ask the next question
- Do NOT agree with the candidate's answer — simply move forward
- Keep your responses under 3 sentences unless asking a multi-part question
- If the candidate is struggling, offer ONE concise hint, then move on
- You are evaluating, not teaching — maintain professional distance
```

## Out of Scope (v2+)
- CI/CD pipeline (GitHub Actions → AWS Deploy)
- Anti-cheating system (tab switching detection, copy-paste monitoring)
- Video-based anxiety detection (webcam feed analysis)
- Multi-role support (beyond ML Engineering)
- Interview scheduling and calendar integration
- Collaborative review (multiple interviewers)
- Custom question bank upload
