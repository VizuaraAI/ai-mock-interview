# Sprint v1 — Tasks

## Status: Complete

- [x] Task 1: Project scaffolding + Supabase setup (P0)
  - Initialize Python backend (FastAPI) with proper project structure, .env config, .gitignore
  - Initialize React frontend (Vite + Tailwind CSS)
  - Create Supabase project via Management API and set up all 6 database tables (candidates, resume_sections, interview_sessions, conversation_history, evaluations, final_reports)
  - Wire up Supabase Python client in backend
  - Acceptance: `uvicorn` starts, `npm run dev` starts, Supabase tables exist, .env has all keys, secrets are gitignored
  - Files: backend/ (main.py, config.py, database.py, requirements.txt), frontend/ (package.json, vite.config, tailwind.config), .env, .gitignore

- [x] Task 2: Resume upload + OpenAI parsing pipeline (P0)
  - Build POST /api/upload-resume endpoint that accepts PDF
  - Send PDF to OpenAI API (base64 encoded) for structured parsing into sections: education, experience, projects, publications, skills, contact info
  - Store raw + parsed sections in Supabase (candidates + resume_sections tables)
  - Return structured JSON to frontend
  - Acceptance: Upload a PDF → get back structured JSON with all resume sections → data persisted in Supabase
  - Files: backend/routers/resume.py, backend/services/resume_parser.py

- [x] Task 3: Interview engine — state machine + Phase 1 (Background) (P0)
  - Build the interview state machine that tracks current phase (1-5), conversation history, and depth level
  - Implement Phase 1: Generate "tell me about yourself" style questions from parsed resume background/education
  - Build POST /api/interview/start (creates session) and POST /api/interview/respond (processes candidate response, returns next question)
  - Wire up GPT-5.4 with the professional interviewer system prompt (no enthusiasm, concise, direct)
  - Phase 1 asks 2-3 background questions then auto-transitions to Phase 2
  - Acceptance: Start interview → get background questions → respond → auto-transition to Phase 2
  - Files: backend/routers/interview.py, backend/services/interview_engine.py, backend/services/prompts.py

- [x] Task 4: Interview engine — Phases 2 & 3 (Socratic deep-dive) (P0)
  - Implement Russian Doll / Socratic drilling for Phases 2 and 3
  - Phase 2: Auto-select the most important project from resume, begin with "What did you build?" then drill progressively deeper into ML concepts
  - Phase 3: Select a different project/internship, same drilling approach
  - Track depth_level per question (increments on each follow-up)
  - Implement hint system: detect when candidate is stuck (vague/short answers, "I don't know"), provide ONE concise nudge, track hint usage
  - After ~6-8 questions per phase or when candidate bottoms out, transition to next phase
  - Acceptance: Phase 2 drills into project 1 with increasing depth, hints work, transitions to Phase 3 which drills project 2, then transitions to Phase 4
  - Files: backend/services/interview_engine.py (extend), backend/services/drill_down.py

- [x] Task 5: ML question bank + Phase 4 (Factual questions) (P0)
  - Store all 80 MLQuestions (from fetched GitHub data) in a markdown file
  - Generate 384-dim embeddings for each question using sentence-transformers all-MiniLM-L6-v2
  - Build FAISS index over question embeddings
  - At Phase 4 start: embed the candidate's resume/field keywords → similarity search → retrieve 4-5 relevant questions
  - Present questions one at a time, store candidate answers alongside correct answers
  - Acceptance: Phase 4 retrieves field-relevant questions, asks 4-5, stores answers with ground truth
  - Files: backend/data/ml_questions.md, backend/services/question_bank.py, backend/services/embeddings.py

- [x] Task 6: Phase 5 (Behavioral) + Evaluation engine + Final report (P0)
  - Implement Phase 5: Ask behavioral questions (5-year vision, challenges, teamwork, questions for interviewer)
  - Build evaluation engine that scores all phases after interview ends:
    - Phase 2-3: Socrates Depth Score (depth_reached / max_depth) + Hint Utilization (recovered_after_hint / hints_given)
    - Phase 4: Factual accuracy (correct / total) — use GPT-5.4 to grade answers against ground truth
    - Phase 5: GPT-5.4 rates visionary (1-5), groundedness (1-5), team player (1-5)
    - Overall composite: weighted average (P2: 30%, P3: 25%, P4: 25%, P5: 20%)
  - Generate final report (structured JSON + narrative text) and store in Supabase
  - GET /api/interview/{session_id}/report endpoint
  - Acceptance: Full interview completes → evaluation runs → report with per-phase scores + overall score returned
  - Files: backend/services/evaluation.py, backend/services/report_generator.py, backend/routers/interview.py (extend)

- [x] Task 7: Voice pipeline — Whisper STT + ElevenLabs TTS + anxiety detection (P0)
  - Build POST /api/voice/transcribe — accepts audio blob, sends to Whisper API, returns text + metadata (duration, word timestamps)
  - Build POST /api/voice/synthesize — accepts text, sends to ElevenLabs API (voice ID: lZORFNDokoBmfd0S06vf), returns audio stream
  - Implement speech anxiety detection: calculate words-per-minute from Whisper output, detect stuttering patterns (repeated words/syllables), detect long pauses (>3s gaps between words)
  - When anxiety detected: inject a calming intervention ("Let's take a moment. There's no rush — take a breath and continue when you're ready.") before the next question
  - Acceptance: Audio in → transcription out, text in → Dr. Raj voice audio out, fast/stuttering speech triggers calming message
  - Files: backend/routers/voice.py, backend/services/speech_to_text.py, backend/services/text_to_speech.py, backend/services/anxiety_detector.py

- [x] Task 8: React frontend — Resume upload + Chat UI + Voice controls (P0)
  - Build resume upload page: drag-and-drop PDF upload, show parsed sections preview, "Start Interview" button
  - Build chat interface: message bubbles (interviewer left, candidate right), auto-scroll, phase indicator banner at top showing current phase
  - Build voice controls: record button (hold-to-talk or toggle), audio playback for interviewer responses, visual waveform/indicator during recording
  - Integrate with all backend APIs: upload, interview start/respond, voice transcribe/synthesize
  - Build report view: scorecard with per-phase scores, overall score, detailed breakdown, visual indicators (progress bars, color coding)
  - Acceptance: Full end-to-end flow works: upload PDF → see parsed resume → start interview → chat via voice or text → complete all 5 phases → view final report
  - Files: frontend/src/pages/ (Upload, Interview, Report), frontend/src/components/ (Chat, VoiceControls, PhaseIndicator, ReportCard), frontend/src/api/

- [x] Task 9: Integration testing + polish (P1)
  - End-to-end test: upload the reference resume (Aadi Krishna Vikram), run through all 5 phases, verify report generation
  - Fix any phase transition bugs, ensure conversation context is maintained across phases
  - Verify voice pipeline works end-to-end (record → transcribe → respond → speak)
  - Verify anxiety detection triggers appropriately
  - Polish interviewer tone: verify no enthusiasm leaks, test edge cases (empty answers, very long answers, off-topic responses)
  - Acceptance: Complete interview runs without errors, report generates correctly, voice works, tone is professional throughout
  - Files: tests/, any bug fixes across codebase

- [x] Task 10: README + demo prep (P2)
  - Write README.md with setup instructions, architecture overview, and usage guide
  - Ensure `npm run dev` + `uvicorn` starts the full stack cleanly
  - Acceptance: A new developer can clone, set up .env, and run the full system following README instructions
  - Files: README.md
