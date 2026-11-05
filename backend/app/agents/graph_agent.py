"""LangGraph agent: plan -> retrieve (hybrid) -> build context -> answer (local Ollama LLM)."""
import json
import logging

from langgraph.graph import END, StateGraph

from ..config import settings
from ..errors import LLMUnavailable
from ..retrieval.hybrid_retriever import TOOLS, build_context, hybrid_retrieve
from .llm import generate
from .state import AgentState
from .tools import TOOL_DESCRIPTIONS, heuristic_plan

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Codebase AI Assistant, an expert software engineer answering questions about the user's uploaded repository.
Rules:
1. Answer ONLY from the retrieved repository context provided by the user message.
2. Never invent files, classes, functions or relationships that are not in the context.
3. If the answer is not in the context, say exactly: "I could not find this in the indexed repository."
4. Always mention file paths, and class/function names when available.
5. Explain relationships (who calls / uses / depends on whom) and show flows like A.java -> B.java -> C.java when relevant.
6. Keep the answer short, clear and developer-friendly.
7. Separate FACTS (from the code) from SUGGESTIONS (your recommendations).
Format: short answer, then 'Relevant files', then 'Flow' (if applicable), then 'Sources' as path:lines."""


def plan_node(state: AgentState) -> AgentState:
    """The agent decides which retrieval tools to use (rule-based by default; model-based if AGENT_PLANNER=llm)."""
    tools: list[str] = []
    if settings.agent_planner == "llm":
        try:
            catalogue = "\n".join(f"- {k}: {v}" for k, v in TOOL_DESCRIPTIONS.items())
            raw = generate([("user", f"Choose 1-3 retrieval tools for this question about a codebase.\n{catalogue}\n"
                                     f"Question: {state['question']}\nReply ONLY with a JSON list of tool names.")], 0)
            raw = raw[raw.index("["):raw.rindex("]") + 1]
            tools = [t for t in json.loads(raw) if t in TOOLS]
        except Exception as exc:
            log.info("LLM planner failed (%s); using rule-based plan", exc)
    return {"tools": tools or heuristic_plan(state["question"])}


def retrieve_node(state: AgentState) -> AgentState:
    return {"items": hybrid_retrieve(state["repo_id"], state["question"], state["tools"])}


def context_node(state: AgentState) -> AgentState:
    context, used = build_context(state["items"][:12])
    return {"context": context, "sources": used}


def answer_node(state: AgentState) -> AgentState:
    if not state["context"].strip():
        return {"answer": "I could not find anything relevant to this question in the indexed repository."}
    try:
        history = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in state.get("history", [])[-4:])
        user = (f"Conversation so far:\n{history}\n\nRetrieved repository context:\n{state['context']}\n\n"
                f"Question: {state['question']}")
        return {"answer": generate([("system", SYSTEM_PROMPT), ("user", user)])}
    except LLMUnavailable as exc:
        return {"llm_error": exc.message, "answer": ""}


def build_agent():
    g = StateGraph(AgentState)
    for name, fn in (("plan", plan_node), ("retrieve", retrieve_node), ("context", context_node), ("answer", answer_node)):
        g.add_node(name, fn)
    g.set_entry_point("plan")
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "context")
    g.add_edge("context", "answer")
    g.add_edge("answer", END)
    return g.compile()


_agent = None


def run_agent(repo_id: str, question: str, history: list[dict] | None = None) -> AgentState:
    global _agent
    _agent = _agent or build_agent()
    return _agent.invoke({"repo_id": repo_id, "question": question, "history": history or []})
