import logging

from ..agents.graph_agent import run_agent
from ..errors import AppError
from . import repository_service as repos

log = logging.getLogger(__name__)


def answer_question(repo_id: str, question: str, history: list[dict]) -> dict:
    repo = repos.get_repository(repo_id)
    if repo["status"] != "indexed":
        raise AppError(f"Repository is not ready (status: {repo['status']}).", 409, "repository_not_ready")
    if not any(c.isalpha() for c in question):
        raise AppError("Please ask a question about the codebase.", 422, "invalid_question")
    state = run_agent(repo_id, question, history)
    sources = [{"file_path": s["file_path"], "class_name": s["class_name"], "function_name": s["function_name"],
                "start_line": s["start_line"], "end_line": s["end_line"], "kind": s["kind"],
                "found_by": s.get("found_by", [s["source"]]), "score": round(s["score"], 3), "snippet": s["text"][:600]}
               for s in state.get("sources", [])]
    answer = state.get("answer", "")
    if not answer and state.get("llm_error"):
        answer = ("The local LLM could not answer (see the warning). These are the most relevant code locations "
                  "retrieved from your repository - open them under Sources.")
    return {"answer": answer, "sources": sources, "tools_used": state.get("tools", []),
            "files": list(dict.fromkeys(s["file_path"] for s in sources if s["file_path"])),
            "llm_error": state.get("llm_error")}
