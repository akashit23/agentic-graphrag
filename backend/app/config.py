"""Central configuration loaded from environment variables / .env. Every default is local-only."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes")


class Settings:
    def __init__(self) -> None:
        self.data_dir = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
        # --- local LLM (Ollama) ---
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "300"))
        self.ollama_num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
        # --- local embeddings ---
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_allow_download = _bool("EMBEDDING_ALLOW_DOWNLOAD")  # only the download script sets this
        # --- graph ---
        self.graph_backend = os.getenv("GRAPH_BACKEND", "networkx").strip().lower()
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password123")
        # --- agent / limits ---
        self.agent_planner = os.getenv("AGENT_PLANNER", "heuristic").strip().lower()
        self.max_context_chars = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))
        self.max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
        self.max_files = int(os.getenv("MAX_FILES", "5000"))
        self.max_file_kb = int(os.getenv("MAX_FILE_KB", "512"))
        self.cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
        self.sample_repo_dir = Path(os.getenv("SAMPLE_REPO_DIR", str(BASE_DIR.parent / "sample-repository")))
        for sub in ("repos", "graphs", "chroma"):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.data_dir / "metadata.db"


settings = Settings()
