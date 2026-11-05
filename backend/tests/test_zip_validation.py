import io
import zipfile

import pytest

from app.errors import AppError
from app.services.repository_service import extract_zip, validate_github_url


def make_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_valid_zip_ignores_junk_dirs(tmp_path):
    z = make_zip({"p/A.java": b"class A {}", "p/node_modules/x.js": b"x", "p/img.png": b"\x00\x01", "p/.git/c.py": b"x"})
    assert extract_zip(z, tmp_path) == 1
    assert (tmp_path / "A.java").exists()


def test_invalid_zip(tmp_path):
    with pytest.raises(AppError) as e:
        extract_zip(b"not a zip", tmp_path)
    assert e.value.code == "invalid_zip"


def test_path_traversal_blocked(tmp_path):
    with pytest.raises(AppError) as e:
        extract_zip(make_zip({"../evil.py": b"print(1)"}), tmp_path)
    assert e.value.code == "path_traversal"


def test_github_url_validation():
    assert validate_github_url("https://github.com/user/project") == ("user", "project")
    for bad in ("http://github.com/a/b", "https://evil.com/a/b", "https://github.com/a/b; rm -rf /", "git@github.com:a/b"):
        with pytest.raises(AppError):
            validate_github_url(bad)
