"""Repository metadata (SQLite), safe ZIP extraction, and GitHub cloning."""
from __future__ import annotations

import io
import json
import logging
import re
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings
from ..errors import AppError
from ..parsers import LANG_BY_EXT

log = logging.getLogger(__name__)
IGNORED_DIRS = {"node_modules", ".git", "__pycache__", "target", "build", "dist", ".venv", "venv", ".idea", ".vscode", "out"}
GITHUB_RE = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")
MAX_UNCOMPRESSED = 300 * 1024 * 1024


# ---------------- SQLite metadata ----------------
def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(settings.db_path)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS repositories (
            repository_id TEXT PRIMARY KEY, repository_name TEXT NOT NULL, source_type TEXT NOT NULL,
            source_url TEXT, created_at TEXT NOT NULL, status TEXT NOT NULL, error TEXT, stats TEXT)""")


def _row(r: sqlite3.Row) -> dict:
    d = dict(r)
    d["stats"] = json.loads(d["stats"]) if d.get("stats") else {}
    return d


def create_repository(name: str, source_type: str, url: str | None = None) -> str:
    rid = uuid.uuid4().hex[:12]
    with _conn() as c:
        c.execute("INSERT INTO repositories VALUES (?,?,?,?,?,?,?,?)",
                  (rid, name, source_type, url, datetime.now(timezone.utc).isoformat(), "pending", None, None))
    return rid


def update_repository(rid: str, **fields) -> None:
    if "stats" in fields:
        fields["stats"] = json.dumps(fields["stats"])
    cols = ", ".join(f"{k}=?" for k in fields)
    with _conn() as c:
        c.execute(f"UPDATE repositories SET {cols} WHERE repository_id=?", (*fields.values(), rid))


def get_repository(rid: str) -> dict:
    with _conn() as c:
        r = c.execute("SELECT * FROM repositories WHERE repository_id=?", (rid,)).fetchone()
    if not r:
        raise AppError("Repository not found.", 404, "repository_not_found")
    return _row(r)


def list_repositories() -> list[dict]:
    with _conn() as c:
        return [_row(r) for r in c.execute("SELECT * FROM repositories ORDER BY created_at DESC")]


# ---------------- filesystem helpers ----------------
def repo_root(rid: str) -> Path:
    return settings.data_dir / "repos" / rid / "src"


def _allowed(rel: str) -> bool:
    p = Path(rel)
    return not any(part in IGNORED_DIRS or part.startswith(".") for part in p.parts[:-1]) and p.suffix.lower() in LANG_BY_EXT


def _safe_target(dest: Path, rel: str) -> Path:
    target = (dest / rel).resolve()
    if dest.resolve() not in target.parents:
        raise AppError("Unsafe path detected in archive (path traversal).", 400, "path_traversal")
    return target


def _looks_binary(data: bytes) -> bool:
    return b"\x00" in data[:2048]


def extract_zip(data: bytes, dest: Path) -> int:
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise AppError(f"ZIP too large (limit {settings.max_upload_mb} MB).", 413, "file_too_large")
    if not zipfile.is_zipfile(io.BytesIO(data)):
        raise AppError("Invalid ZIP file.", 400, "invalid_zip")
    count = total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = [i for i in zf.infolist() if not i.is_dir()]
        names = [i.filename.replace("\\", "/") for i in infos]
        for n in names:  # reject traversal up-front, even for files we would ignore
            if n.startswith("/") or ".." in Path(n).parts:
                raise AppError("Unsafe path detected in archive (path traversal).", 400, "path_traversal")
        tops = {n.split("/")[0] for n in names if "/" in n}
        strip = len(tops) == 1 and all("/" in n for n in names)
        for info, name in zip(infos, names):
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                continue  # symlink
            rel = name.split("/", 1)[1] if strip else name
            if not _allowed(rel) or info.file_size > settings.max_file_kb * 1024:
                continue
            total += info.file_size
            count += 1
            if total > MAX_UNCOMPRESSED or count > settings.max_files:
                raise AppError("Repository too large (too many files or too much data).", 413, "repo_too_large")
            content = zf.read(info)
            if _looks_binary(content):
                continue
            target = _safe_target(dest, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)  # written as data only, never executed
    return count


def copy_filtered(src: Path, dest: Path) -> int:
    count = 0
    for f in src.rglob("*"):
        if not f.is_file() or f.is_symlink():
            continue
        rel = f.relative_to(src).as_posix()
        if not _allowed(rel) or f.stat().st_size > settings.max_file_kb * 1024:
            continue
        data = f.read_bytes()
        if _looks_binary(data):
            continue
        count += 1
        if count > settings.max_files:
            raise AppError("Repository too large (too many files).", 413, "repo_too_large")
        target = _safe_target(dest, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return count


def validate_github_url(url: str) -> tuple[str, str]:
    m = GITHUB_RE.match(url.strip())
    if not m:
        raise AppError("Invalid GitHub URL. Expected https://github.com/<user>/<repo>.", 400, "invalid_github_url")
    return m.group(1), m.group(2)


def clone_github(url: str, dest: Path) -> int:
    user, repo = validate_github_url(url)
    clean = f"https://github.com/{user}/{repo}.git"
    tmp = Path(tempfile.mkdtemp(prefix="clone_"))
    try:
        subprocess.run(["git", "clone", "--depth", "1", "--single-branch", "--", clean, str(tmp / "repo")],
                       check=True, capture_output=True, timeout=180, text=True,
                       env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/usr/local/bin:/bin"})
        return copy_filtered(tmp / "repo", dest)
    except FileNotFoundError as exc:
        raise AppError("git is not installed on the server.", 500, "git_missing") from exc
    except subprocess.TimeoutExpired as exc:
        raise AppError("GitHub clone timed out.", 504, "clone_timeout") from exc
    except subprocess.CalledProcessError as exc:
        raise AppError(f"GitHub clone failed (is the repository public?): {(exc.stderr or '').strip()[-200:]}", 400, "clone_failed") from exc
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def safe_read_file(rid: str, rel_path: str) -> str:
    root = repo_root(rid).resolve()
    target = (root / rel_path).resolve()
    if root not in target.parents or not target.is_file():
        raise AppError("File not found.", 404, "file_not_found")
    return target.read_text(encoding="utf-8", errors="replace")


def list_files(rid: str) -> list[dict]:
    root = repo_root(rid)
    if not root.exists():
        return []
    return [{"path": f.relative_to(root).as_posix(), "language": LANG_BY_EXT.get(f.suffix.lower(), "text"),
             "size": f.stat().st_size} for f in sorted(root.rglob("*")) if f.is_file()]
