# Agentic GraphRAG Framework for Intelligent Codebase Analysis and Context-Aware Developer Assistance
**100% local and free:** Ollama (local LLM) + sentence-transformers (local embeddings) + ChromaDB + NetworkX (Neo4j optional). No API key, no credit card, no cloud calls for AI.

Upload a ZIP (or public GitHub URL) -> the code is parsed, a knowledge graph and local embeddings are built -> a LangGraph agent picks retrieval tools (vector / graph / file / dependency / code-context / summary), fuses results, and your local model answers **only from your code**, with file paths and line numbers.

## Architecture
```
ZIP / GitHub -> safe extract -> parsers (Python ast; regex parsers for Java/JS/TS/C/C++)
  -> knowledge graph (NetworkX + JSON on disk; Neo4j optional) -> chunks -> sentence-transformers -> ChromaDB
Question -> LangGraph agent: plan -> hybrid retrieve (vector + graph + keyword + dependency) -> context -> Ollama -> answer + sources
```
Stack: React + Vite + Tailwind + Axios + Cytoscape | FastAPI | LangGraph | Ollama | sentence-transformers | ChromaDB | NetworkX / Neo4j | SQLite metadata.

## Windows setup (VS Code), step by step
1. **Install**: Python 3.11 (tick "Add to PATH"), Node.js 20 LTS, Git, VS Code, and Ollama from https://ollama.com.
2. **Open folder**: VS Code -> File -> Open Folder -> `agentic-graphrag`. Open a terminal (Ctrl+`) and use **Command Prompt** (dropdown next to `+`).
3. **Backend deps**:
   ```
   cd backend
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   copy .env.example .env
   ```
4. **Frontend deps** (new terminal): `cd frontend` then `npm install`.
5. **Download models once** (internet needed only here), backend terminal:
   ```
   python scripts/download_models.py
   ollama pull qwen2.5-coder:3b
   ```
   The Ollama app must be running (it starts with Windows; otherwise run `ollama serve`).
6. **Start backend**: `uvicorn app.main:app --reload --port 8000` (docs: http://localhost:8000/docs).
7. **Start frontend**: `cd frontend` then `npm run dev` -> http://localhost:5173.
8. **Sample repo**: click **Load sample project** (or zip `sample-repository` and use **Upload ZIP**). Wait until status is `indexed`.
9. **Test questions** (Chat tab): "Where are student marks stored?" -> cites `services/StudentService.java` (`saveMarks`) and `db/Database.java`. "If I modify StudentService.java, which files may be affected?" -> `auth/Login.java`, `Main.java`. "Explain how login works." "Where is password validation implemented?" -> `auth/AuthService.java` (`validatePassword`). Check each source link opens the real file at those lines. Settings tab shows Ollama/model status.

First answers on a CPU laptop can take 20-90 s. Smaller/faster: `OLLAMA_MODEL=qwen2.5-coder:1.5b`. Better quality: `qwen2.5-coder:7b` (needs ~8 GB RAM).

## Configuration (`backend/.env`)
`LLM_PROVIDER=ollama`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT`, `EMBEDDING_PROVIDER=sentence-transformers`, `EMBEDDING_MODEL`, `GRAPH_BACKEND=networkx|neo4j`, `AGENT_PLANNER=heuristic|llm`, `MAX_CONTEXT_CHARS`. The app runs with no `.env` at all (defaults are local). The embedding model is never downloaded at app start; if missing you get a clear error.

## Optional: Neo4j Community
`pip install -r requirements-neo4j.txt`, run `docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:5.24`, set `GRAPH_BACKEND=neo4j`, re-index. Queries still run on the local graph; Neo4j holds a copy for exploration at http://localhost:7474.

## Docker (optional)
Install Ollama on the host, `ollama pull qwen2.5-coder:3b`, then `docker compose up --build` (UI http://localhost:3000). Download the embedding model once inside the container: `docker compose exec backend python scripts/download_models.py`. Add `--profile neo4j` for Neo4j.

## API
`POST /api/repositories/upload|github|sample` - `GET /api/repositories[/{id}]` - `GET .../files` - `GET .../file?path=` - `POST .../analyze` - `GET .../graph?level=file|full` - `GET .../dependencies?file=` - `POST /api/chat` - `GET /api/health`. Errors: `{"detail","code"}`.

## Security
ZIP traversal/symlink checks, size limits, binaries and `node_modules/.git/__pycache__/target/build/dist/.venv` skipped, uploaded code never executed, strict GitHub URL validation, no secrets in the frontend.

## Tests
`cd backend && pytest` (parser, graph, ZIP validation, vector/hybrid retrieval, agent, API, Ollama error handling). Tests use hash embeddings and need no Ollama or model downloads.

## Limits
Non-Python parsers are regex-based (swap in Tree-sitter via `BaseParser`); call resolution is name-based; no `Variable` nodes; a 3B model gives simpler answers than cloud models, so always check the Sources list.

## Troubleshooting
| Message / problem | Fix |
|---|---|
| "Ollama is not running" | Open the Ollama app or run `ollama serve` |
| "Model ... is not downloaded" | `ollama pull qwen2.5-coder:3b` |
| "embedding model is not downloaded" | `python scripts/download_models.py` |
| "indexed with a different embedding model" | Re-upload the repository |
| Very slow answers | Use `qwen2.5-coder:1.5b`, lower `MAX_CONTEXT_CHARS` |
| `pip` fails building chromadb | Use Python 3.11; install "Microsoft C++ Build Tools" |
| Frontend cannot reach API | Backend must run on port 8000 |
