import shutil

from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from ..config import settings
from ..errors import AppError
from ..models.schemas import AnalysisOut, FileEntry, GithubRequest, RepositoryOut
from ..services import analysis_service, repository_service as repos
from ..services.indexing_service import index_repository

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _start(bg: BackgroundTasks, name: str, source: str, url: str | None, fill) -> dict:
    rid = repos.create_repository(name, source, url)
    dest = repos.repo_root(rid)
    dest.mkdir(parents=True, exist_ok=True)
    try:
        if fill(dest) == 0:
            raise AppError("Empty repository: no supported source files found.", 400, "empty_repository")
    except Exception:
        shutil.rmtree(dest.parent, ignore_errors=True)
        repos.update_repository(rid, status="failed", error="Could not read repository.")
        raise
    bg.add_task(index_repository, rid)
    return repos.get_repository(rid)


@router.post("/upload", response_model=RepositoryOut, status_code=202)
async def upload_zip(bg: BackgroundTasks, file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".zip"):
        raise AppError("Please upload a .zip file.", 400, "invalid_zip")
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    name = (file.filename or "repository").rsplit(".", 1)[0]
    return _start(bg, name, "zip", None, lambda d: repos.extract_zip(data, d))


@router.post("/github", response_model=RepositoryOut, status_code=202)
def add_github(req: GithubRequest, bg: BackgroundTasks):
    _, name = repos.validate_github_url(req.url)
    return _start(bg, name, "github", req.url, lambda d: repos.clone_github(req.url, d))


@router.post("/sample", response_model=RepositoryOut, status_code=202)
def add_sample(bg: BackgroundTasks):
    if not settings.sample_repo_dir.exists():
        raise AppError("Sample repository folder not found (check SAMPLE_REPO_DIR).", 404, "sample_missing")
    return _start(bg, "StudentManagement (sample)", "sample", None, lambda d: repos.copy_filtered(settings.sample_repo_dir, d))


@router.get("", response_model=list[RepositoryOut])
def list_repos():
    return repos.list_repositories()


@router.get("/{rid}", response_model=RepositoryOut)
def get_repo(rid: str):
    return repos.get_repository(rid)


@router.get("/{rid}/files", response_model=list[FileEntry])
def files(rid: str):
    repos.get_repository(rid)
    return repos.list_files(rid)


@router.get("/{rid}/file")
def file_content(rid: str, path: str):
    repos.get_repository(rid)
    return {"path": path, "content": repos.safe_read_file(rid, path)}


@router.post("/{rid}/analyze", response_model=AnalysisOut)
def analyze(rid: str):
    return analysis_service.analyze(rid)
