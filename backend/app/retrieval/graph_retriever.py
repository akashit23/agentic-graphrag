"""Graph-based retrieval: name matching, relationship facts, dependency analysis, grep, summaries."""
import re

from ..graph.graph_store import load_graph
from ..services.repository_service import list_files, safe_read_file

STOP = {"the", "and", "how", "what", "where", "which", "does", "work", "works", "file", "files", "code", "class",
        "function", "method", "this", "that", "for", "from", "with", "are", "is", "in", "of", "to", "me", "my", "i",
        "if", "modify", "change", "affected", "explain", "show", "find", "used", "use", "implemented", "stored",
        "store", "defined", "there", "any", "all", "about", "project", "repository", "can", "you", "tell", "get"}


def _subtokens(word: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", word)]


def question_terms(question: str) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z]{1,4})?", question)
    return [w for w in dict.fromkeys(words) if w.lower() not in STOP and len(w) >= 3]


def _score_name(node: dict, terms: list[str]) -> float:
    name = node["name"].lower()
    best = 0.0
    for t in terms:
        tl = t.lower().split(".")[0]
        sub = set(_subtokens(node["name"]))
        if tl == name:
            best = max(best, 1.0)
        elif tl in sub or (len(tl) > 3 and tl.rstrip("s") in sub):
            best = max(best, 0.75)
        elif len(tl) > 3 and tl in name:
            best = max(best, 0.6)
    return best


def match_nodes(repo_id: str, question: str, labels: tuple[str, ...], limit: int = 6) -> list[tuple[dict, float]]:
    g, terms = load_graph(repo_id), question_terms(question)
    scored = [(n, _score_name(n, terms)) for n in g.nodes.values() if n["label"] in labels]
    return sorted([x for x in scored if x[1] > 0], key=lambda x: -x[1])[:limit]


def _slice(repo_id: str, path: str, start: int, end: int, cap: int = 60) -> str:
    return "\n".join(safe_read_file(repo_id, path).splitlines()[start - 1:min(end, start + cap - 1)])


def _item(source: str, node: dict, text: str, score: float, kind: str) -> dict:
    cls = node["name"] if node["label"] == "Class" else node.get("class_name", "")
    fn = node["name"] if node["label"] in ("Function", "Method") else ""
    return {"source": source, "kind": kind, "file_path": node["path"], "class_name": cls, "function_name": fn,
            "start_line": node.get("start_line", 1), "end_line": node.get("end_line", 1), "text": text, "score": score}


def graph_search(repo_id: str, question: str) -> list[dict]:
    """Relationship facts (who calls / uses / extends whom) for entities named in the question."""
    g, items = load_graph(repo_id), []
    for node, sc in match_nodes(repo_id, question, ("File", "Class", "Function", "Method")):
        facts = []
        for typ, tgt in g.out.get(node["id"], []):
            if typ in ("CALLS", "USES", "EXTENDS", "IMPLEMENTS", "IMPORTS", "DEPENDS_ON") and tgt in g.nodes:
                facts.append(f"{node['name']} -{typ}-> {g.nodes[tgt]['name']} ({g.nodes[tgt].get('path', 'external')})")
        for typ, src in g.inc.get(node["id"], []):
            if typ in ("CALLS", "USES", "EXTENDS", "IMPLEMENTS", "IMPORTS", "DEPENDS_ON") and src in g.nodes:
                facts.append(f"{g.nodes[src]['name']} ({g.nodes[src].get('path', '')}) -{typ}-> {node['name']}")
        if node["label"] != "Repository" and facts:
            items.append(_item("graph", node, "Relationships:\n" + "\n".join(facts[:20]), 0.7 * sc, "relationships"))
    return items


def code_context(repo_id: str, question: str) -> list[dict]:
    """Actual source code of the classes/functions whose names appear in the question."""
    items = []
    for node, sc in match_nodes(repo_id, question, ("Class", "Function", "Method"), limit=4):
        items.append(_item("code_context", node, _slice(repo_id, node["path"], node["start_line"], node["end_line"]),
                           0.65 * sc, "code"))
    return items


def _resolve_files(repo_id: str, question: str) -> list[str]:
    paths = [f["path"] for f in list_files(repo_id)]
    out = []
    for t in question_terms(question):
        tl = t.lower()
        for p in paths:
            base = p.rsplit("/", 1)[-1].lower()
            if tl == base or tl == base.rsplit(".", 1)[0]:
                out.append(p)
    return list(dict.fromkeys(out))


def dependency_analysis(repo_id: str, question: str) -> list[dict]:
    g, items = load_graph(repo_id), []
    for path in _resolve_files(repo_id, question)[:3]:
        node = g.nodes[f"file:{path}"]
        text = (f"File {path}\nDepends on: {', '.join(g.file_deps(path)) or 'nothing'}\n"
                f"Directly used by: {', '.join(g.used_by(path)) or 'nothing'}\n"
                f"Potentially affected if modified (transitive): {', '.join(g.impacted(path)) or 'nothing'}")
        items.append(_item("dependency", node, text, 0.9, "dependencies"))
    return items


def file_search(repo_id: str, question: str) -> list[dict]:
    """Keyword (grep-like) search over source files."""
    terms = [t.split(".")[0].lower() for t in question_terms(question)][:6]
    if not terms:
        return []
    hits = []
    for f in list_files(repo_id):
        lines = safe_read_file(repo_id, f["path"]).splitlines()
        for i, line in enumerate(lines):
            low = line.lower()
            n = sum(1 for t in terms if t in low)
            if n:
                hits.append((n, f["path"], i + 1, lines))
    hits.sort(key=lambda h: -h[0])
    items = []
    for n, path, ln, lines in hits[:6]:
        s, e = max(1, ln - 3), min(len(lines), ln + 6)
        items.append({"source": "file_search", "kind": "keyword_match", "file_path": path, "class_name": "",
                      "function_name": "", "start_line": s, "end_line": e, "text": "\n".join(lines[s - 1:e]),
                      "score": min(0.6, 0.2 + 0.15 * n)})
    return items


def repository_summary(repo_id: str, question: str = "") -> list[dict]:
    g = load_graph(repo_id)
    files = [n for n in g.nodes.values() if n["label"] == "File"]
    ranked = sorted(files, key=lambda n: -len(g.used_by(n["path"])))[:6]
    classes = [n for n in g.nodes.values() if n["label"] == "Class"]
    imp = sorted(classes, key=lambda c: -sum(1 for t, _ in g.inc.get(c["id"], []) if t in ("USES", "CALLS", "EXTENDS")))[:6]
    entries = []
    for f in files:
        src = safe_read_file(repo_id, f["path"])
        if re.search(r"public static void main|if __name__ ?== ?['\"]__main__|int main\s*\(|app\.listen|createRoot\(", src):
            entries.append(f["path"])
    dep_files = [n["path"] + " (" + str(len(g.used_by(n["path"]))) + " dependents)" for n in ranked]
    imp_classes = [c["name"] + " (" + c["path"] + ")" for c in imp]
    fn_count = sum(1 for n in g.nodes.values() if n["label"] in ("Function", "Method"))
    text = (f"Repository facts: {len(files)} files, {len(classes)} classes, "
            f"{fn_count} functions/methods, {len(g.edges)} relationships.\n"
            f"Most depended-on files: {', '.join(dep_files)}\n"
            f"Most used classes: {', '.join(imp_classes)}\n"
            f"Possible entry points: {', '.join(entries) or 'none detected'}")
    return [{"source": "summary", "kind": "summary", "file_path": ranked[0]["path"] if ranked else "", "class_name": "",
             "function_name": "", "start_line": 1, "end_line": 1, "text": text, "score": 0.5}]
