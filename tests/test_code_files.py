"""R1 · R2 · R3 — 코드 · 패치 파일을 어떻게 감싸 보여 주는가 (창 없이 도는 순수 함수)."""
import re
from pathlib import Path

import pytest

import main

CODE_EXTS = {
    ".py": "python",
    ".c": "c",
    ".h": "c",
    ".patch": "diff",
    ".diff": "diff",
    ".ps1": "powershell",
    ".sh": "bash",
    ".js": "javascript",
    ".toml": "text",
    ".ini": "text",
    ".log": "text",
}
EDITABLE_EXTS = [".md", ".markdown", ".txt", ".yaml", ".yml", ".json"]


def _fence_body_lines(editor_text: str) -> list[str]:
    """editor_text 가 정확히 펜스 하나일 때 그 안의 줄들을 돌려준다."""
    m = re.fullmatch(r"(`{3,})(\w*)\n(.*)\n\1\n", editor_text, re.DOTALL)
    assert m, f"단일 펜스가 아님: {editor_text!r}"
    return m.group(3).split("\n")


@pytest.mark.parametrize("ext,lang", CODE_EXTS.items())
def test_code_extension_maps_to_hljs_language(ext, lang):
    assert main.CODE_FENCE_LANGS[ext] == lang


@pytest.mark.parametrize("ext", CODE_EXTS)
def test_code_files_are_read_only(ext):
    assert main.is_read_only(Path(f"after{ext}"))
    assert main.is_read_only(Path(f"AFTER{ext.upper()}"))


@pytest.mark.parametrize("ext", EDITABLE_EXTS)
def test_markdown_and_data_files_stay_editable(ext):
    assert not main.is_read_only(Path(f"note{ext}"))


@pytest.mark.parametrize(
    "raw",
    [
        "int a;\nint b;\n",          # 끝 개행 있음 (보통 파일)
        "int a;\nint b;",            # 끝 개행 없음
        "int a;\r\nint b;\r\n",      # CRLF
        "a\n\nb\n\n",                # 빈 줄 · 마지막 줄이 빈 줄
        "```\nfenced\n```\n",       # 본문 안 백틱 펜스
    ],
)
def test_code_file_fence_lines_equal_file_lines(raw):
    """R3: 펜스 안 줄 = 파일 줄. 끝 개행 때문에 빈 번호가 하나 더 붙으면 안 된다."""
    file_lines = raw.replace("\r\n", "\n").splitlines()
    body = _fence_body_lines(main.to_editor_text(raw, ".c"))
    assert body == file_lines


@pytest.mark.parametrize("ext", [".yaml", ".json", ".txt"])
def test_data_file_round_trip_unchanged(ext):
    """기존 동작 유지: 데이터 파일은 감쌌다 풀면 원문(끝 개행 포함) 그대로."""
    raw = "key: 1\nlist:\n  - a\n"
    text = main.to_editor_text(raw, ext)
    body, clean = main._unwrap_code(text, main.CODE_FENCE_LANGS[ext])
    assert clean and body == raw


def test_markdown_is_not_wrapped():
    assert main.to_editor_text("# 제목\r\n본문\n", ".md") == "# 제목\n본문\n"


@pytest.mark.parametrize("ext", list(CODE_EXTS) + [".md", ".markdown", ".txt", ".yaml", ".yml", ".json"])
def test_every_supported_extension_shows_in_sidebar_and_open_dialog(ext):
    assert f"*{ext}" in main.FS_NAME_FILTERS
    first_filter = main.OPEN_FILTER.split(";;")[0]
    assert f"*{ext}" in first_filter.split("(")[1]


def test_open_dialog_has_code_line():
    assert "코드 (*.py *.c *.h *.patch *.diff)" in main.OPEN_FILTER.split(";;")
