"""JSON persistence + cache for graphs."""
import json
from pathlib import Path

from ..config import settings
from ..errors import AppError
from .graph_builder import GraphData

_cache: dict[str, tuple[float, GraphData]] = {}


def _path(repo_id: str) -> Path:
    return settings.data_dir / "graphs" / f"{repo_id}.json"


def save_graph(repo_id: str, graph: dict) -> None:
    _path(repo_id).write_text(json.dumps(graph), encoding="utf-8")
    _cache.pop(repo_id, None)


def load_graph(repo_id: str) -> GraphData:
    p = _path(repo_id)
    if not p.exists():
        raise AppError("Graph not found. Is the repository indexed yet?", 404, "graph_not_found")
    mtime = p.stat().st_mtime
    if repo_id in _cache and _cache[repo_id][0] == mtime:
        return _cache[repo_id][1]
    data = GraphData(json.loads(p.read_text(encoding="utf-8")))
    _cache[repo_id] = (mtime, data)
    return data
