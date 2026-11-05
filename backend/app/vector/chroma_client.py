"""ChromaDB persistent store, one collection per repository."""
import logging

import chromadb

from ..config import settings
from ..errors import AppError
from .embeddings import embed_texts, embedding_id

log = logging.getLogger(__name__)
_client = None


def _chroma():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.data_dir / "chroma"))
    return _client


def _name(repo_id: str) -> str:
    return f"repo_{repo_id}"


def reset_collection(repo_id: str):
    try:
        _chroma().delete_collection(_name(repo_id))
    except Exception:
        pass
    return _chroma().create_collection(_name(repo_id), metadata={"hnsw:space": "cosine", "embedding": embedding_id()})


def add_chunks(repo_id: str, chunks: list[dict]) -> int:
    col = reset_collection(repo_id)
    for i in range(0, len(chunks), 64):
        batch = chunks[i:i + 64]
        col.add(ids=[c["id"] for c in batch], documents=[c["text"] for c in batch],
                metadatas=[c["metadata"] for c in batch], embeddings=embed_texts([c["embed_text"] for c in batch]))
    return len(chunks)


def query(repo_id: str, question: str, k: int = 8) -> list[dict]:
    try:
        col = _chroma().get_collection(_name(repo_id))
    except Exception as exc:
        raise AppError("Vector index not found for this repository.", 404, "vector_index_missing") from exc
    current_emb = embedding_id()
    col_emb = (col.metadata or {}).get("embedding")
    if col_emb != current_emb:
        log.warning("Embedding model mismatch (collection: %s, active: %s).", col_emb, current_emb)
        raise AppError("This repository was indexed with a different embedding model. Please click 'Load sample project' or re-upload to index with the current model.", 409, "embedding_mismatch")
    if col.count() == 0:
        return []
    res = col.query(query_embeddings=embed_texts([question]), n_results=min(k, col.count()))
    return [{"text": d, "metadata": m, "score": round(1 - dist, 4)}
            for d, m, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0])]
