"""'Analyze Repository': summary built from real graph facts, written up by the local LLM when available."""
from ..agents.llm import generate
from ..errors import AppError, LLMUnavailable
from ..graph.graph_store import load_graph
from ..retrieval.graph_retriever import repository_summary
from . import repository_service as repos


def analyze(repo_id: str) -> dict:
    repo = repos.get_repository(repo_id)
    if repo["status"] != "indexed":
        raise AppError(f"Repository is not ready (status: {repo['status']}).", 409, "repository_not_ready")
    g = load_graph(repo_id)
    modules = sorted({n["name"] for n in g.nodes.values() if n["label"] == "Module"})[:20]
    per_file = []
    for n in g.nodes.values():
        if n["label"] == "File":
            children = [g.nodes[t] for ty, t in g.out[n["id"]] if ty == "CONTAINS"]
            per_file.append({"file": n["path"], "classes": [c["name"] for c in children if c["label"] == "Class"],
                             "functions": [c["name"] for c in children if c["label"] == "Function"],
                             "depends_on": g.file_deps(n["path"]), "used_by": g.used_by(n["path"])})
    per_file.sort(key=lambda f: -len(f["used_by"]))
    facts = {"overview": repository_summary(repo_id)[0]["text"], "files": per_file[:25], "external_modules": modules,
             "stats": repo["stats"]}

    def fallback(reason: str) -> dict:
        lines = [f"## Repository analysis (generated from the knowledge graph; LLM narrative unavailable: {reason})",
                 facts["overview"], "", "### Main modules / files"]
        for f in per_file[:12]:
            lines.append(f"- **{f['file']}** - classes: {', '.join(f['classes']) or '-'}; functions: {', '.join(f['functions'][:6]) or '-'}; "
                         f"depends on: {', '.join(f['depends_on']) or '-'}; used by: {', '.join(f['used_by']) or '-'}")
        lines.append(f"\n### External modules\n{', '.join(modules) or 'none'}")
        return {"summary": "\n".join(lines), "facts": facts, "llm_used": False}

    prompt = ("Write a developer-friendly analysis of this repository using ONLY the extracted facts below. Sections: "
              "Project overview, Main modules, Important classes, Important functions, Architecture, Dependencies, "
              "Possible entry points. Do not invent anything.\n\nFACTS:\n" + str(facts)[:7000])
    try:
        return {"summary": generate([("user", prompt)]), "facts": facts, "llm_used": True}
    except LLMUnavailable as exc:
        return fallback(exc.message)
