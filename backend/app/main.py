import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import chat, dependencies, graph, repositories
from .config import settings
from .agents.llm import ollama_status
from .errors import AppError
from .graph.neo4j_client import neo4j_client
from .services.repository_service import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

app = FastAPI(title="Agentic GraphRAG Codebase Assistant", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
init_db()

for r in (repositories.router, graph.router, dependencies.router, chat.router):
    app.include_router(r, prefix="/api")


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "code": exc.code})


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": "Invalid request: " + "; ".join(
        f"{'.'.join(map(str, e['loc'][1:]))}: {e['msg']}" for e in exc.errors()), "code": "validation_error"})


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error.", "code": "internal_error"})


@app.get("/api/health")
def health():
    st = ollama_status()
    return {"status": "ok", "llm_provider": settings.llm_provider, "ollama_running": st["running"],
            "ollama_model": st["model"], "ollama_model_installed": st["model_installed"],
            "embedding_provider": settings.embedding_provider, "embedding_model": settings.embedding_model,
            "graph_backend": settings.graph_backend,
            "neo4j": neo4j_client.available() if settings.graph_backend == "neo4j" else None}
