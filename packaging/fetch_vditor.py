"""Vditor 를 app/web/vendor/vditor 에 받아 둔다 — 설치본이 인터넷 없이 화면을 그리게 (R7).

    python packaging/fetch_vditor.py                 # npm 레지스트리에서 받기
    python packaging/fetch_vditor.py --from x.tgz    # 이미 받은 tarball 쓰기 (해시는 똑같이 검사)

고정한 판(VERSION)과 npm 레지스트리 dist.integrity(sha512)가 맞을 때만 풀고, 아니면 멈춘다.
tarball 에서 package/dist/** 와 package/LICENSE 만 꺼낸다. 이미 같은 판이 있으면 아무것도 안 한다.
build.ps1 이 PyInstaller 전에 부르고, run.bat 은 vendor 가 비었을 때 부른다.
vendor/ 는 저장소에 넣지 않는다 (app/web/vendor/.gitignore).
"""
import argparse
import base64
import hashlib
import io
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path, PurePosixPath

VERSION = "3.10.9"
TARBALL = f"https://registry.npmjs.org/vditor/-/vditor-{VERSION}.tgz"
# npm view vditor@3.10.9 dist.integrity
INTEGRITY = "sha512-cJE/pMv/kg3dW9TIoAe2VBM4CI1JuTEjsD8YhveqYZm8h4pjcXSmYtu/0QVqH6/KA2BeUXvZilryOXlwho2QZg=="

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "app" / "web" / "vendor" / "vditor"


class IntegrityError(RuntimeError):
    pass


def verify(data: bytes, integrity: str) -> None:
    algo, _, expected = integrity.partition("-")
    if algo != "sha512":
        raise IntegrityError(f"unsupported integrity algorithm: {algo}")
    actual = base64.b64encode(hashlib.sha512(data).digest()).decode()
    if actual != expected:
        raise IntegrityError(f"vditor tarball hash mismatch: expected {expected}, got {actual}")


def extract(data: bytes, dest: Path) -> None:
    """package/dist/** · package/LICENSE 만 dest 아래로. 경로가 dest 밖으로 나가면 멈춘다."""
    tmp = dest.with_name(dest.name + ".tmp")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    root = tmp.resolve()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            if m.name == "package/LICENSE":
                rel = PurePosixPath("LICENSE")
            elif m.name.startswith("package/dist/"):
                rel = PurePosixPath(m.name[len("package/"):])
            else:
                continue
            target = (tmp / rel).resolve()
            if not target.is_relative_to(root):
                shutil.rmtree(tmp)
                raise ValueError(f"unsafe path in tarball: {m.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tf.extractfile(m).read())
    (tmp / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
    if dest.exists():
        shutil.rmtree(dest)
    tmp.rename(dest)


def is_current(dest: Path) -> bool:
    ver = dest / "VERSION"
    return (ver.is_file() and ver.read_text(encoding="utf-8").strip() == VERSION
            and (dest / "dist" / "index.min.js").is_file())


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", type=Path, help="local vditor tarball (still hash-checked)")
    args = ap.parse_args(argv)

    if is_current(DEST):
        print(f"vditor {VERSION} already in {DEST}")
        return 0
    if args.src:
        data = args.src.read_bytes()
    else:
        print(f"downloading {TARBALL}")
        with urllib.request.urlopen(TARBALL, timeout=120) as r:
            data = r.read()
    verify(data, INTEGRITY)
    extract(data, DEST)
    count = sum(1 for p in DEST.rglob("*") if p.is_file())
    print(f"vditor {VERSION}: {count} files -> {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
