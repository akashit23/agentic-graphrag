"""Builds the knowledge graph (nodes + typed edges) dynamically from parsed files."""
from __future__ import annotations

import os
import re
from collections import defaultdict

import networkx as nx

from ..parsers.base import ParsedFile

TOKEN_RE = re.compile(r"[A-Za-z_]\w*")
FILE_EXTS = {".h", ".hpp", ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".c", ".cpp", ".mjs", ".cjs"}


def build_graph(repo_id: str, repo_name: str, parsed: list[ParsedFile], contents: dict[str, str]) -> dict:
    nodes: dict[str, dict] = {}
    edges: set[tuple[str, str, str]] = set()

    def add_node(nid: str, label: str, name: str, **props) -> None:
        nodes[nid] = {"id": nid, "label": label, "name": name, **props}

    def add_edge(s: str, t: str, typ: str) -> None:
        if s != t:
            edges.add((s, t, typ))

    repo_node = f"repo:{repo_id}"
    add_node(repo_node, "Repository", repo_name)
    stems: dict[str, list[str]] = defaultdict(list)
    class_index: dict[str, list[str]] = defaultdict(list)
    func_index: dict[str, list[str]] = defaultdict(list)
    func_calls: list[tuple[str, str, list[str]]] = []  # (func_id, file_path, calls)
    paths = {pf.path for pf in parsed}

    for pf in parsed:
        fid = f"file:{pf.path}"
        add_node(fid, "File", os.path.basename(pf.path), path=pf.path, language=pf.language,
                 start_line=1, end_line=pf.line_count)
        add_edge(repo_node, fid, "CONTAINS")
        stems[os.path.splitext(os.path.basename(pf.path))[0]].append(pf.path)
        class_ids: dict[str, str] = {}
        for c in pf.classes:
            cid = f"class:{pf.path}:{c.name}"
            class_ids[c.name] = cid
            add_node(cid, "Class", c.name, path=pf.path, start_line=c.start_line, end_line=c.end_line)
            add_edge(fid, cid, "CONTAINS")
            add_edge(cid, fid, "DEFINED_IN")
            class_index[c.name].append(cid)
        for f in pf.functions:
            label = "Method" if f.class_name else "Function"
            qual = f"{f.class_name}.{f.name}" if f.class_name else f.name
            nid = f"func:{pf.path}:{qual}:{f.start_line}"
            add_node(nid, label, f.name, qualified_name=qual, path=pf.path, class_name=f.class_name,
                     start_line=f.start_line, end_line=f.end_line)
            add_edge(class_ids.get(f.class_name, fid), nid, "CONTAINS")
            add_edge(nid, fid, "DEFINED_IN")
            func_index[f.name].append(nid)
            func_calls.append((nid, pf.path, f.calls))

    # --- class inheritance ---
    for pf in parsed:
        for c in pf.classes:
            cid = f"class:{pf.path}:{c.name}"
            for base in c.bases:
                for t in class_index.get(base, []):
                    add_edge(cid, t, "EXTENDS")
            for itf in c.interfaces:
                for t in class_index.get(itf.split("<")[0], []):
                    add_edge(cid, t, "IMPLEMENTS")

    # --- imports (file -> file or external Module) ---
    imported_files: dict[str, set[str]] = defaultdict(set)
    for pf in parsed:
        fid = f"file:{pf.path}"
        for imp in pf.imports:
            base = imp.split("/")[-1]
            ext = os.path.splitext(base)[1].lower()
            seg = os.path.splitext(base)[0] if ext in FILE_EXTS else base.split(".")[-1]
            cands = [p for p in stems.get(seg, []) if p != pf.path]
            if len(cands) > 1:
                narrow = [p for p in cands if imp.replace(".", "/") in p]
                cands = narrow or cands[:1]
            if cands:
                for p in cands:
                    add_edge(fid, f"file:{p}", "IMPORTS")
                    imported_files[pf.path].add(p)
            else:
                mid = f"module:{imp}"
                add_node(mid, "Module", imp)
                add_edge(fid, mid, "IMPORTS")

    # --- calls (function -> function / class) ---
    file_of = {nid: n["path"] for nid, n in nodes.items() if "path" in n}
    for fnid, path, calls in func_calls:
        for name in calls:
            if name in class_index:  # constructor call
                for cid in class_index[name][:2]:
                    add_edge(fnid, cid, "USES")
                    if file_of[cid] != path:
                        add_edge(f"file:{path}", cid, "USES")
            cands = [t for t in func_index.get(name, []) if t != fnid]
            if not cands:
                continue
            same = [t for t in cands if file_of[t] == path]
            imp = [t for t in cands if file_of[t] in imported_files[path]]
            chosen = same or imp or (cands if len(cands) == 1 else [])
            for t in chosen[:3]:
                add_edge(fnid, t, "CALLS")

    # --- file-level USES (type references) and DEPENDS_ON ---
    for pf in parsed:
        fid = f"file:{pf.path}"
        tokens = set(TOKEN_RE.findall(contents.get(pf.path, "")))
        for cname, cids in class_index.items():
            if len(cname) >= 3 and cname in tokens:
                for cid in cids:
                    if file_of[cid] != pf.path:
                        add_edge(fid, cid, "USES")
    file_deps: set[tuple[str, str]] = set()
    for s, t, typ in edges:
        if typ in ("IMPORTS", "USES", "CALLS", "EXTENDS", "IMPLEMENTS"):
            sp = file_of.get(s) if not s.startswith("file:") else s[5:]
            tp = file_of.get(t) if not t.startswith("file:") else t[5:]
            if sp in paths and tp in paths and sp != tp:
                file_deps.add((sp, tp))
    for sp, tp in file_deps:
        add_edge(f"file:{sp}", f"file:{tp}", "DEPENDS_ON")

    labels = [n["label"] for n in nodes.values()]
    return {
        "nodes": list(nodes.values()),
        "edges": [{"source": s, "target": t, "type": ty} for s, t, ty in sorted(edges)],
        "stats": {"files": labels.count("File"), "classes": labels.count("Class"),
                  "functions": labels.count("Function") + labels.count("Method"),
                  "relationships": len(edges)},
    }


class GraphData:
    """Read-only in-memory view of a stored graph. File-level dependencies use a NetworkX DiGraph,
    which is the lightweight local graph backend (no database server needed)."""

    def __init__(self, graph: dict) -> None:
        self.nodes: dict[str, dict] = {n["id"]: n for n in graph["nodes"]}
        self.edges = graph["edges"]
        self.out: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.inc: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.dep = nx.DiGraph()  # edge A -> B means "A depends on B"
        for n in graph["nodes"]:
            if n["label"] == "File":
                self.dep.add_node(n["path"])
        for e in self.edges:
            self.out[e["source"]].append((e["type"], e["target"]))
            self.inc[e["target"]].append((e["type"], e["source"]))
            if e["type"] == "DEPENDS_ON":
                self.dep.add_edge(e["source"][5:], e["target"][5:])

    def file_deps(self, path: str) -> list[str]:
        return sorted(self.dep.successors(path)) if path in self.dep else []

    def used_by(self, path: str) -> list[str]:
        return sorted(self.dep.predecessors(path)) if path in self.dep else []

    def impacted(self, path: str) -> list[str]:
        """Transitive reverse dependencies: every file that may break if `path` changes."""
        return sorted(nx.ancestors(self.dep, path)) if path in self.dep else []
