"""Full indexing pipeline: parse -> graph -> Neo4j -> chunks -> embeddings -> ChromaDB."""
import logging

from ..config import settings
from ..errors import AppError
from ..graph.graph_builder import build_graph
from ..graph.graph_store import save_graph
from ..graph.neo4j_client import neo4j_client
from ..parsers import parse_file
from ..parsers.base import ParsedFile
from ..vector.chroma_client import add_chunks
from . import repository_service as repos

log = logging.getLogger(__name__)
WINDOW = 80


def make_chunks(repo_name: str, pf: ParsedFile, lines: list[str]) -> list[dict]:
    """Semantic chunks: one per function/method, one per class header, plus a file overview."""
    chunks: list[dict] = []

    def add(kind: str, start: int, end: int, cls: str = "", fn: str = "") -> None:
        for s in range(start, end + 1, WINDOW - 10):  # long bodies are split into overlapping windows
            e = min(end, s + WINDOW - 1)
            text = "\n".join(lines[s - 1:e])
            if not text.strip():
                continue
            head = f"File: {pf.path} | Class: {cls} | Function: {fn} | Kind: {kind}"
            chunks.append({
                "id": f"{pf.path}:{s}-{e}:{kind}",
                "text": text, "embed_text": f"{head}\n{text}",
                "metadata": {"repository": repo_name, "file_path": pf.path, "language": pf.language, "kind": kind,
                             "class_name": cls, "function_name": fn, "start_line": s, "end_line": e}})
            if e >= end:
                break

    overview = (f"File {pf.path} ({pf.language}). Classes: {', '.join(c.name for c in pf.classes) or 'none'}. "
                f"Functions: {', '.join(f.name for f in pf.functions) or 'none'}. Imports: {', '.join(pf.imports[:15]) or 'none'}.")
    chunks.append({"id": f"{pf.path}:overview", "text": "\n".join(lines[:25]), "embed_text": overview + "\n" + "\n".join(lines[:25]),
                   "metadata": {"repository": repo_name, "file_path": pf.path, "language": pf.language, "kind": "file",
                                "class_name": "", "function_name": "", "start_line": 1, "end_line": min(25, max(1, len(lines)))}})
    for c in pf.classes:
        first_fn = min((f.start_line for f in pf.functions if f.class_name == c.name), default=c.end_line + 1)
        if first_fn - c.start_line >= 2:
            add("class", c.start_line, min(c.end_line, first_fn - 1), cls=c.name)
    for f in pf.functions:
        add("function", f.start_line, f.end_line, cls=f.class_name, fn=f.name)
    if not pf.functions and not pf.classes:
        add("file", 1, len(lines))
    return chunks


def index_repository(rid: str) -> None:
    """Runs in a background task; always leaves the repository in 'indexed' or 'failed'."""
    try:
        repos.update_repository(rid, status="indexing", error=None)
        repo = repos.get_repository(rid)
        root = repos.repo_root(rid)
        parsed, contents, chunks = [], {}, []
        for f in repos.list_files(rid):
            text = repos.safe_read_file(rid, f["path"])
            pf = parse_file(f["path"], text)
            if pf is None:
                continue
            if pf.error:
                log.warning("Parse issue in %s: %s", f["path"], pf.error)
            parsed.append(pf)
            contents[f["path"]] = text
            chunks += make_chunks(repo["repository_name"], pf, text.splitlines())
        if not parsed:
            raise AppError("No supported source files found (supported: Python, Java, JS, TS, C, C++).", 400, "empty_repository")
        graph = build_graph(rid, repo["repository_name"], parsed, contents)
        save_graph(rid, graph)
        neo4j_ok = None  # None = Neo4j not used (GRAPH_BACKEND=networkx)
        if settings.graph_backend == "neo4j":
            try:
                neo4j_client.write_graph(rid, graph)
                neo4j_ok = True
            except Exception as exc:  # graph is still fully usable from the local NetworkX/JSON store
                neo4j_ok = False
                log.warning("Neo4j write failed (continuing with local graph): %s", exc)
        n_chunks = add_chunks(rid, chunks)
        langs: dict[str, int] = {}
        for pf in parsed:
            langs[pf.language] = langs.get(pf.language, 0) + 1
        stats = {**graph["stats"], "chunks": n_chunks, "languages": langs, "graph_backend": settings.graph_backend,
                 "neo4j_synced": neo4j_ok, "embedding": settings.embedding_model if settings.embedding_provider != "hash" else "hash"}
        repos.update_repository(rid, status="indexed", stats=stats)
        log.info("Indexed %s: %s", rid, stats)
    except AppError as exc:
        repos.update_repository(rid, status="failed", error=exc.message)
    except Exception as exc:
        log.exception("Indexing failed")
        repos.update_repository(rid, status="failed", error=f"Indexing failed: {exc}")
