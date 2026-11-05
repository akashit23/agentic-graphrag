"""Hybrid GraphRAG: run the chosen tools, expand vector hits through the graph,
deduplicate, rank, and build the final LLM context."""
from ..config import settings
from ..graph.graph_store import load_graph
from . import graph_retriever as gr
from .vector_retriever import vector_search

TOOLS = {
    "vector_search": vector_search,
    "graph_search": gr.graph_search,
    "file_search": gr.file_search,
    "dependency_analysis": gr.dependency_analysis,
    "code_context": gr.code_context,
    "repository_summary": gr.repository_summary,
}


def expand_with_graph(repo_id: str, items: list[dict]) -> list[dict]:
    """Graph expansion: for each semantic hit, attach its callers/callees (1 hop)."""
    g, extra = load_graph(repo_id), []
    for it in [i for i in items if i["source"] == "vector" and i["function_name"]][:4]:
        for n in g.nodes.values():
            if n["label"] in ("Function", "Method") and n["path"] == it["file_path"] and n["name"] == it["function_name"] \
                    and n["start_line"] == it["start_line"]:
                facts = [f"{n['name']} -CALLS-> {g.nodes[t]['name']} ({g.nodes[t]['path']}:{g.nodes[t]['start_line']})"
                         for ty, t in g.out.get(n["id"], []) if ty == "CALLS"]
                facts += [f"{g.nodes[s]['name']} ({g.nodes[s]['path']}) -CALLS-> {n['name']}"
                          for ty, s in g.inc.get(n["id"], []) if ty == "CALLS"]
                if facts:
                    extra.append({**it, "source": "graph_expansion", "kind": "relationships", "text": "Call graph:\n" + "\n".join(facts[:12]),
                                  "score": it["score"] * 0.8})
                break
    return extra


def hybrid_retrieve(repo_id: str, question: str, tools: list[str]) -> list[dict]:
    raw: list[dict] = []
    for name in tools:
        fn = TOOLS.get(name)
        if fn:
            raw += fn(repo_id, question)
    raw += expand_with_graph(repo_id, raw)
    merged: dict[tuple, dict] = {}
    for it in raw:  # dedupe by location + kind; agreement between retrievers boosts the score
        key = (it["file_path"], it["start_line"], it["end_line"], it["kind"] == "relationships", it["kind"] == "dependencies")
        if key in merged:
            merged[key]["score"] += 0.15
            merged[key]["found_by"].add(it["source"])
        else:
            merged[key] = {**it, "found_by": {it["source"]}}
    ranked = sorted(merged.values(), key=lambda i: -i["score"])
    for r in ranked:
        r["found_by"] = sorted(r["found_by"])
    return ranked


def build_context(items: list[dict]) -> tuple[str, list[dict]]:
    parts, used, size = [], [], 0
    for i, it in enumerate(items, 1):
        loc = f"{it['file_path']}:{it['start_line']}-{it['end_line']}"
        label = " ".join(x for x in (f"class {it['class_name']}" if it["class_name"] else "",
                                     f"function {it['function_name']}" if it["function_name"] else "") if x)
        block = f"[{i}] ({it['kind']}) {loc} {label}\n{it['text']}\n"
        if size + len(block) > settings.max_context_chars:
            break
        parts.append(block)
        used.append(it)
        size += len(block)
    return "\n".join(parts), used
