"""R7 — 인터넷 없이 화면이 그려진다: Vditor 를 설치본에 넣는다.

- 웹 파일은 원격 주소를 하나도 부르지 않는다 (CDN → app/web/vendor/vditor).
- packaging/fetch_vditor.py 는 고정한 판 · 해시만 받아 들이고, dist 와 LICENSE 만 꺼낸다.
"""
import base64
import hashlib
import io
import re
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
sys.path.insert(0, str(ROOT / "packaging"))

import fetch_vditor  # noqa: E402


@pytest.mark.parametrize("name", ["editor.html", "editor.js", "editor.css"])
def test_web_files_reference_no_remote_urls(name):
    text = (WEB / name).read_text(encoding="utf-8")
    assert not re.search(r"https?://", text), f"{name} 에 원격 주소"


def test_pinned_version_matches_editor_reference():
    html = (WEB / "editor.html").read_text(encoding="utf-8")
    assert "vendor/vditor/dist/index.min.js" in html
    assert fetch_vditor.VERSION == "3.10.9"


def _integrity(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def test_verify_rejects_tampered_tarball():
    with pytest.raises(fetch_vditor.IntegrityError):
        fetch_vditor.verify(b"not the real tarball", fetch_vditor.INTEGRITY)


def test_verify_accepts_matching_hash():
    fetch_vditor.verify(b"abc", _integrity(b"abc"))


def _tgz(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_extract_takes_only_dist_and_license(tmp_path):
    data = _tgz({
        "package/dist/index.min.js": b"js",
        "package/dist/js/lute/lute.min.js": b"lute",
        "package/LICENSE": b"MIT",
        "package/src/index.ts": b"src",
        "package/package.json": b"{}",
    })
    dest = tmp_path / "vditor"
    fetch_vditor.extract(data, dest)
    files = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
    assert files == ["LICENSE", "VERSION", "dist/index.min.js", "dist/js/lute/lute.min.js"]
    assert (dest / "VERSION").read_text(encoding="utf-8").strip() == fetch_vditor.VERSION


def test_extract_refuses_path_traversal(tmp_path):
    data = _tgz({"package/dist/../../../evil.js": b"x", "package/dist/ok.js": b"ok"})
    dest = tmp_path / "out" / "vditor"
    with pytest.raises(Exception):
        fetch_vditor.extract(data, dest)
    assert not (tmp_path / "evil.js").exists()
