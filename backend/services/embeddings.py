import re
import json
import numpy as np
from pathlib import Path

# We'll use a lightweight approach: compute embeddings using OpenAI's embedding API
# instead of loading sentence-transformers locally (faster startup, no torch dependency issues)
from openai import OpenAI
from backend.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

QUESTIONS_FILE = Path(__file__).parent.parent / "data" / "ml_questions.md"
EMBEDDINGS_CACHE = Path(__file__).parent.parent / "data" / "embeddings_cache.json"


def parse_questions_from_markdown() -> list[dict]:
    """Parse ML questions from the markdown file."""
    content = QUESTIONS_FILE.read_text()
    questions = []

    # Split by ### Q pattern
    pattern = r'### Q(\d+): (.+?)\n\*\*Answer:\*\* (.+?)\n\*\*Field:\*\* (\w+)'
    matches = re.findall(pattern, content, re.DOTALL)

    for match in matches:
        q_num, question, answer, field = match
        questions.append({
            "id": int(q_num),
            "question": question.strip(),
            "answer": answer.strip(),
            "field": field.strip(),
        })

    return questions


def get_embedding(text: str) -> list[float]:
    """Get embedding using OpenAI's embedding API (1536 dims, but we'll use text-embedding-3-small for cost efficiency)."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        dimensions=384,  # Request 384 dims to match our spec
    )
    return response.data[0].embedding


def build_embeddings_cache():
    """Build and cache embeddings for all questions."""
    questions = parse_questions_from_markdown()

    # Check if cache exists and is valid
    if EMBEDDINGS_CACHE.exists():
        cache = json.loads(EMBEDDINGS_CACHE.read_text())
        if len(cache) == len(questions):
            return cache

    # Build embeddings
    cache = []
    for q in questions:
        embedding = get_embedding(q["question"] + " " + q["answer"])
        cache.append({
            **q,
            "embedding": embedding,
        })

    # Save cache
    EMBEDDINGS_CACHE.write_text(json.dumps(cache))
    return cache


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


def retrieve_questions(resume_text: str, n: int = 5) -> list[dict]:
    """Retrieve the most relevant ML questions based on the candidate's resume."""
    cache = build_embeddings_cache()

    # Get embedding for resume
    resume_embedding = get_embedding(resume_text)

    # Compute similarities
    scored = []
    for item in cache:
        sim = cosine_similarity(resume_embedding, item["embedding"])
        scored.append((sim, item))

    # Sort by similarity (descending)
    scored.sort(key=lambda x: x[0], reverse=True)

    # Return top N, but ensure diversity across fields
    selected = []
    fields_seen = {}

    for sim, item in scored:
        field = item["field"]
        if fields_seen.get(field, 0) < 2:  # Max 2 per field
            selected.append({
                "id": item["id"],
                "question": item["question"],
                "answer": item["answer"],
                "field": item["field"],
                "similarity": sim,
            })
            fields_seen[field] = fields_seen.get(field, 0) + 1
        if len(selected) >= n:
            break

    return selected
