"""Run ONCE (needs internet for this one step): python scripts/download_models.py
Downloads the local embedding model into the Hugging Face cache and checks Ollama."""
import os
import sys
from pathlib import Path

os.environ["EMBEDDING_ALLOW_DOWNLOAD"] = "true"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.llm import ollama_status  # noqa: E402
from app.config import settings  # noqa: E402

print(f"Downloading embedding model: {settings.embedding_model} (~90 MB, one time)...")
from sentence_transformers import SentenceTransformer  # noqa: E402

SentenceTransformer(settings.embedding_model)
print("Embedding model ready.\n")

st = ollama_status()
if not st["running"]:
    print("Ollama is NOT running. Install it from https://ollama.com, start it, then run:")
    print(f"    ollama pull {settings.ollama_model}")
elif not st["model_installed"]:
    print(f"Ollama is running but model '{settings.ollama_model}' is missing. Run:  ollama pull {settings.ollama_model}")
else:
    print(f"Ollama is running and '{settings.ollama_model}' is installed. You are ready.")
