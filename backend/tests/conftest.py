import os
import tempfile
from pathlib import Path

# Configure BEFORE the app is imported: isolated data dir, offline hash embeddings (no model download),
# Ollama pointed at a closed port (so the "Ollama not running" path is tested), NetworkX graph backend.
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="graphrag_test_")
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:1"
os.environ["EMBEDDING_PROVIDER"] = "hash"
os.environ["GRAPH_BACKEND"] = "networkx"
SAMPLE = Path(__file__).resolve().parents[2] / "sample-repository"
os.environ["SAMPLE_REPO_DIR"] = str(SAMPLE)

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def sample_dir() -> Path:
    return SAMPLE


@pytest.fixture(scope="session")
def indexed_repo(sample_dir):
    from app.services import repository_service as repos
    from app.services.indexing_service import index_repository
    repos.init_db()
    rid = repos.create_repository("sample", "sample")
    dest = repos.repo_root(rid)
    dest.mkdir(parents=True)
    repos.copy_filtered(sample_dir, dest)
    index_repository(rid)
    assert repos.get_repository(rid)["status"] == "indexed"
    return rid
