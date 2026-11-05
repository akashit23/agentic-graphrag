import pytest

from app.agents import llm
from app.errors import EmbeddingError, LLMUnavailable


class FakeResp:
    def __init__(self, status=200, body=None, text=""):
        self.status_code, self._body, self.text = status, body or {}, text

    def json(self):
        return self._body


def test_ollama_not_running_gives_actionable_error():
    with pytest.raises(LLMUnavailable) as e:
        llm.generate([("user", "hi")])
    assert "Ollama is not running" in e.value.message


def test_model_not_downloaded(monkeypatch):
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: FakeResp(404, text="model not found"))
    with pytest.raises(LLMUnavailable) as e:
        llm.generate([("user", "hi")])
    assert "ollama pull" in e.value.message


def test_successful_generation_and_empty_answer(monkeypatch):
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: FakeResp(200, {"message": {"content": " hello "}}))
    assert llm.generate([("user", "hi")]) == "hello"
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: FakeResp(200, {"message": {"content": ""}}))
    with pytest.raises(LLMUnavailable):
        llm.generate([("user", "hi")])


def test_status_when_ollama_down():
    st = llm.ollama_status()
    assert st["running"] is False and st["model_installed"] is False


def test_hash_embeddings_are_384_dim_and_deterministic():
    from app.vector.embeddings import embed_texts
    a, b = embed_texts(["validate password"]), embed_texts(["validate password"])
    assert len(a[0]) == 384 and a == b


def test_missing_sentence_transformer_model_is_reported(monkeypatch):
    from app.config import settings
    from app.vector import embeddings
    monkeypatch.setattr(settings, "embedding_provider", "sentence-transformers")
    monkeypatch.setattr(settings, "embedding_model", "does-not-exist/none")
    monkeypatch.setattr(embeddings, "_model", None)
    with pytest.raises(EmbeddingError):
        embeddings.embed_texts(["x"])
