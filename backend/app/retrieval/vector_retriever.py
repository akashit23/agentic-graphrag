"""Semantic search over ChromaDB code chunks."""
from ..vector.chroma_client import query


def vector_search(repo_id: str, question: str, k: int = 8) -> list[dict]:
    items = []
    for hit in query(repo_id, question, k):
        m = hit["metadata"]
        items.append({"source": "vector", "kind": m["kind"], "file_path": m["file_path"], "class_name": m["class_name"],
                      "function_name": m["function_name"], "start_line": m["start_line"], "end_line": m["end_line"],
                      "text": hit["text"], "score": hit["score"]})
    return items
