from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    repo_id: str
    question: str
    history: list[dict]
    tools: list[str]
    items: list[dict]
    context: str
    sources: list[dict]
    answer: str
    llm_error: str
