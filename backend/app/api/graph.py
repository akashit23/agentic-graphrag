from fastapi import APIRouter

from ..graph.graph_store import load_graph
from ..services import repository_service as repos

router = APIRouter(prefix="/repositories", tags=["graph"])


@router.get("/{rid}/graph")
def get_graph(rid: str, level: str = "file", limit: int = 500):
    """level=file -> files + DEPENDS_ON; level=full -> files, classes, functions and all relations."""
    repos.get_repository(rid)
    g = load_graph(rid)
    if level == "file":
        keep = {i for i, n in g.nodes.items() if n["label"] == "File"}
        edges = [e for e in g.edges if e["type"] == "DEPENDS_ON"]
    else:
        keep = {i for i, n in g.nodes.items() if n["label"] in ("File", "Class", "Function", "Method")}
        edges = [e for e in g.edges if e["type"] not in ("DEFINED_IN", "DEPENDS_ON")]
    nodes = [g.nodes[i] for i in list(keep)[:limit]]
    ids = {n["id"] for n in nodes}
    return {"nodes": nodes, "edges": [e for e in edges if e["source"] in ids and e["target"] in ids],
            "truncated": len(keep) > limit}
