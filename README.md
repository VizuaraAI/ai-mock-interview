# AI Mock Interview Agent

A full-stack AI-powered mock interview system for ML Engineering roles. Conducts a realistic 5-phase interview with voice I/O, Socratic drilling, and automated evaluation.

## Architecture

```
React (Vite + Tailwind) → FastAPI → GPT-5.4 / Whisper / ElevenLabs → Supabase
```

### 5 Interview Phases

| Phase | What Happens | Evaluation |
|-------|-------------|------------|
| 1. Background | "Tell me about yourself" from resume | No scoring |
| 2. Project Deep-Dive 1 | Socratic drilling into primary project | Depth Score + Hint Utilization |
| 3. Project Deep-Dive 2 | Socratic drilling into secondary project | Depth Score + Hint Utilization |
| 4. Factual ML Questions | 4-5 questions matched to candidate's field | Accuracy (correct/total) |
| 5. Behavioral | Vision, challenges, teamwork | Visionary, Grounded, Team Player (1-5) |

### Key Features

- **Resume Parsing**: OpenAI-powered PDF parsing into structured sections
- **Socratic Method**: Russian Doll drilling with depth tracking and hint system
- **80 ML Question Bank**: Embedded with 384-dim vectors, similarity-matched to candidate
- **Voice I/O**: Whisper STT + ElevenLabs TTS (Dr. Raj Dandekar voice clone)
- **Anxiety Detection**: Speech rate + stuttering analysis → automatic calming intervention
- **Professional Tone**: No enthusiasm, no praise — real interviewer behavior

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys: OpenAI, ElevenLabs, Supabase

### 1. Environment

```bash
cp .env.example .env
# Fill in your API keys
```

`.env` requires:
```
OPENAI_API_KEY=sk-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
ELEVENLABS_API_KEY=sk_...
```

### 2. Backend

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/upload-resume` | Upload PDF, get parsed resume |
| POST | `/api/interview/start` | Start interview session |
| POST | `/api/interview/respond` | Send candidate response |
| GET | `/api/interview/{id}/report` | Get evaluation report |
| POST | `/api/voice/transcribe` | Audio → text (Whisper) |
| POST | `/api/voice/synthesize` | Text → audio (ElevenLabs) |

## Scoring

**Overall = Phase 2 (30%) + Phase 3 (25%) + Phase 4 (25%) + Phase 5 (20%)**

- **Socrates Depth**: `depth_reached / 8` — how deep before candidate fails
- **Hint Utilization**: `recovered_after_hint / hints_given`
- **Factual Accuracy**: `correct / total`
- **Behavioral**: GPT-graded on visionary, groundedness, team player (1-5 each)
