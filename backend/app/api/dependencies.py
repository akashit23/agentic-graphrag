from fastapi import APIRouter

from ..errors import AppError
from ..graph.graph_store import load_graph
from ..models.schemas import DependencyOut
from ..services import repository_service as repos

router = APIRouter(prefix="/repositories", tags=["dependencies"])


@router.get("/{rid}/dependencies", response_model=DependencyOut)
def dependencies(rid: str, file: str):
    repos.get_repository(rid)
    g = load_graph(rid)
    if f"file:{file}" not in g.nodes:
        raise AppError("File is not part of the indexed graph.", 404, "file_not_found")
    deps, used, impacted = g.file_deps(file), g.used_by(file), g.impacted(file)
    ids = {f"file:{p}" for p in [file, *deps, *used, *impacted]}
    nodes = [g.nodes[i] for i in ids]
    edges = [e for e in g.edges if e["type"] == "DEPENDS_ON" and e["source"] in ids and e["target"] in ids]
    return {"file": file, "depends_on": deps, "used_by": used, "impacted": impacted, "nodes": nodes, "edges": edges}
