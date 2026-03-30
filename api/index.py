"""Vercel serverless entry point — exposes the FastAPI app."""
import sys
from pathlib import Path

# Add project root to path so backend imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import app  # noqa: E402
