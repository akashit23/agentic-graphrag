"""Tool catalogue exposed to the planner + heuristic fallback planner."""
import re

TOOL_DESCRIPTIONS = {
    "vector_search": "semantic search over code chunks; best for 'where/how is X implemented' questions",
    "graph_search": "relationships (calls/uses/extends/imports) of entities named in the question",
    "file_search": "keyword search across source files; best for exact identifiers or strings",
    "dependency_analysis": "depends-on / used-by / impact analysis for a named file",
    "code_context": "actual source code of classes/functions named in the question",
    "repository_summary": "high-level repository facts, important files, entry points",
}


def heuristic_plan(question: str) -> list[str]:
    q = question.lower()
    tools = ["vector_search"]
    if re.search(r"affect|impact|depend|modify|change|break|used by|who uses|callers?", q):
        tools += ["dependency_analysis", "graph_search"]
    elif re.search(r"overview|summary|summari[sz]e|architecture|structure|entry point|what does this (project|repo)", q):
        tools += ["repository_summary", "graph_search"]
    elif re.search(r"where|find|locate|implemented|defined|validation|validate", q):
        tools += ["file_search", "code_context"]
    else:
        tools += ["graph_search", "code_context"]
    return list(dict.fromkeys(tools))
