"""Local embeddings. Default: sentence-transformers (all-MiniLM-L6-v2) running on your CPU.
The model is loaded lazily on first use and is NEVER downloaded automatically: run
`python scripts/download_models.py` once. EMBEDDING_PROVIDER=hash is an offline fallback used by tests."""
import hashlib
import logging
import math
import re

from ..config import settings
from ..errors import EmbeddingError

log = logging.getLogger(__name__)
DIM = 384
_WORD = re.compile(r"[A-Za-z][a-z]+|[A-Z]+(?![a-z])|\d+")
_model = None


def embedding_id() -> str:
    """Identifies the embedding space; stored with each Chroma collection to detect mismatches."""
    return "hash" if settings.embedding_provider == "hash" else f"st:{settings.embedding_model}"


def _hash_embed(text: str) -> list[float]:
    toks = [t.lower() for t in _WORD.findall(text)]
    vec = [0.0] * DIM
    for tok in toks + [a + "_" + b for a, b in zip(toks, toks[1:])]:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        vec[h % DIM] += 1.0 if (h >> 64) & 1 else -1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _st_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError("sentence-transformers is not installed. Run: pip install -r requirements.txt") from exc
        try:
            _model = SentenceTransformer(settings.embedding_model, local_files_only=not settings.embedding_allow_download)
            _model.max_seq_length = 256
        except Exception as exc:
            raise EmbeddingError("The embedding model is not downloaded yet. Run once: python scripts/download_models.py") from exc
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if settings.embedding_provider == "hash":
        return [_hash_embed(t) for t in texts]
    if settings.embedding_provider != "sentence-transformers":
        raise EmbeddingError(f"Unknown EMBEDDING_PROVIDER '{settings.embedding_provider}'.")
    try:
        return _st_model().encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False).tolist()
    except EmbeddingError:
        raise
    except Exception as exc:
        raise EmbeddingError(f"Embedding failed: {exc}") from exc
