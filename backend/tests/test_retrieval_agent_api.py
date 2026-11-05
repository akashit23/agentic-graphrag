import pytest
from fastapi.testclient import TestClient

from app.agents.graph_agent import run_agent
from app.agents.tools import heuristic_plan
from app.retrieval.hybrid_retriever import build_context, hybrid_retrieve
from app.vector.chroma_client import query


def test_vector_retrieval_returns_metadata(indexed_repo):
    hits = query(indexed_repo, "validate password length", k=5)
    assert hits and all({"file_path", "start_line", "end_line", "language"} <= set(h["metadata"]) for h in hits)
    assert any("AuthService" in h["metadata"]["file_path"] for h in hits[:3])


def test_hybrid_retrieval_dedupes_and_ranks(indexed_repo):
    items = hybrid_retrieve(indexed_repo, "Where are student marks stored?", ["vector_search", "file_search", "graph_search", "code_context"])
    keys = [(i["file_path"], i["start_line"], i["end_line"], i["kind"]) for i in items]
    assert len(keys) == len(set(keys))
    assert [i["score"] for i in items] == sorted((i["score"] for i in items), reverse=True)
    ctx, used = build_context(items)
    assert "StudentService.java" in ctx or "Marks.java" in ctx


def test_dependency_analysis_tool(indexed_repo):
    items = hybrid_retrieve(indexed_repo, "What files are affected if I modify Database.java?", ["dependency_analysis"])
    assert "StudentService.java" in items[0]["text"]


def test_planner_chooses_tools():
    assert "dependency_analysis" in heuristic_plan("What is affected if I modify AuthService?")
    assert "file_search" in heuristic_plan("Where is password validation implemented?")


def test_agent_workflow_without_llm(indexed_repo):
    state = run_agent(indexed_repo, "Explain how login works", [])
    assert state["tools"] and state["sources"] and state.get("llm_error")


@pytest.fixture(scope="module")
def client():
    from app.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_repository_endpoints(client, indexed_repo):
    assert any(r["repository_id"] == indexed_repo for r in client.get("/api/repositories").json())
    files = client.get(f"/api/repositories/{indexed_repo}/files").json()
    assert len(files) == 8
    assert "class Database" in client.get(f"/api/repositories/{indexed_repo}/file", params={"path": "db/Database.java"}).json()["content"]
    assert client.get(f"/api/repositories/{indexed_repo}/file", params={"path": "../../etc/passwd"}).status_code == 404
    dep = client.get(f"/api/repositories/{indexed_repo}/dependencies", params={"file": "services/StudentService.java"}).json()
    assert "db/Database.java" in dep["depends_on"] and "auth/Login.java" in dep["used_by"]
    assert client.get(f"/api/repositories/{indexed_repo}/graph?level=full").json()["nodes"]
    assert client.post(f"/api/repositories/{indexed_repo}/analyze").status_code == 200


def test_chat_and_errors(client, indexed_repo):
    r = client.post("/api/chat", json={"repository_id": indexed_repo, "question": "Where are student marks stored?"})
    assert r.status_code == 200 and r.json()["sources"]
    assert client.post("/api/chat", json={"repository_id": "nope", "question": "hello there"}).status_code == 404
    assert client.post("/api/chat", json={"repository_id": indexed_repo, "question": "?"}).status_code == 422
    assert client.post("/api/repositories/github", json={"url": "https://evil.com/x/y"}).status_code == 400
    assert client.post("/api/repositories/upload", files={"file": ("a.zip", b"junk", "application/zip")}).status_code == 400
