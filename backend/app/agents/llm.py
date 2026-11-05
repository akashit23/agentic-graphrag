"""Local LLM access through Ollama's HTTP API (http://localhost:11434). No API key, no cloud."""
import logging

import httpx

from ..config import settings
from ..errors import LLMUnavailable

log = logging.getLogger(__name__)


def ollama_status() -> dict:
    """Is Ollama running, and is the configured model downloaded?"""
    base = {"running": False, "model": settings.ollama_model, "model_installed": False, "installed_models": []}
    try:
        r = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        r.raise_for_status()
        names = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return base
    want = settings.ollama_model
    installed = any(n == want or n == f"{want}:latest" for n in names)
    return {**base, "running": True, "model_installed": installed, "installed_models": names}


def generate(messages: list[tuple[str, str]], temperature: float = 0.1) -> str:
    """messages = [("system", "..."), ("user", "...")]. Raises LLMUnavailable with an actionable message."""
    if settings.llm_provider != "ollama":
        raise LLMUnavailable(f"LLM_PROVIDER='{settings.llm_provider}' is not supported. Set LLM_PROVIDER=ollama.")
    payload = {"model": settings.ollama_model, "stream": False,
               "messages": [{"role": role, "content": content} for role, content in messages],
               "options": {"temperature": temperature, "num_ctx": settings.ollama_num_ctx}}
    try:
        r = httpx.post(f"{settings.ollama_base_url}/api/chat", json=payload,
                       timeout=httpx.Timeout(settings.ollama_timeout, connect=5))
    except httpx.ConnectError as exc:
        raise LLMUnavailable("Ollama is not running. Start the Ollama app (or run `ollama serve`) and try again.") from exc
    except httpx.TimeoutException as exc:
        raise LLMUnavailable("Ollama took too long to answer. Try a smaller model or raise OLLAMA_TIMEOUT in .env.") from exc
    except httpx.HTTPError as exc:
        raise LLMUnavailable(f"Could not talk to Ollama: {exc}") from exc
    if r.status_code == 404:
        raise LLMUnavailable(f"Model '{settings.ollama_model}' is not downloaded. Run: ollama pull {settings.ollama_model}")
    if r.status_code != 200:
        raise LLMUnavailable(f"Ollama returned HTTP {r.status_code}: {r.text[:200]}")
    content = (r.json().get("message") or {}).get("content", "").strip()
    if not content:
        raise LLMUnavailable("Ollama returned an empty answer.")
    return content
