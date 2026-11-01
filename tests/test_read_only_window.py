"""R2 — 코드 파일을 열면 저장 경로가 모두 막히고, 마크다운 · 데이터 파일은 지금처럼 저장된다.

MainWindow 를 실제로 만든다(웹뷰 로딩은 기다리지 않음). 설정은 conftest 의 테스트 ORG 에 쓴다.
"""
from pathlib import Path

import pytest


def _load(window, path: Path) -> list[tuple]:
    """_load_path 를 부르고, 그때 JS 로 보낸 loadContent 인자를 모아 돌려준다."""
    sent: list[tuple] = []
    window.editor.bridge.loadContent.connect(lambda *a: sent.append(a))
    window._load_path(path)
    return sent


def test_code_file_disables_save_actions_and_tags_title(window, tmp_path):
    src = tmp_path / "after.c"
    src.write_text("int main(void)\n{\n    return 0;\n}\n", encoding="utf-8")

    _load(window, src)

    assert window.read_only
    assert not window.action_save.isEnabled()
    assert not window.action_save_as.isEnabled()
    window._refresh_title()
    assert "[읽기 전용]" in window.windowTitle()


def test_code_file_tells_editor_to_lock_input(window, tmp_path):
    src = tmp_path / "eval.py"
    src.write_text("print('x')\n", encoding="utf-8")

    sent = _load(window, src)

    assert len(sent) == 1
    _md, code_only, read_only = sent[0]
    assert code_only is True and read_only is True


def test_save_on_code_file_never_writes(window, tmp_path):
    src = tmp_path / "diff.patch"
    original = b"--- a/x.c\r\n+++ b/x.c\r\n@@ -1 +1 @@\r\n-a\r\n+b\r\n"
    src.write_bytes(original)
    _load(window, src)

    # 편집 이벤트가 어떻게든 들어와 더티가 되어도 저장 · 닫기 확인으로 파일이 바뀌면 안 된다.
    window.editor.bridge.onChange("tampered")
    window.save_file()
    assert window._confirm_discard() is True

    assert src.read_bytes() == original


@pytest.mark.parametrize("name,body", [("note.md", "# 제목\n"), ("conf.yaml", "a: 1\n"), ("d.json", "{}\n")])
def test_markdown_and_data_files_stay_saveable(window, tmp_path, name, body):
    src = tmp_path / name
    src.write_text(body, encoding="utf-8")

    sent = _load(window, src)

    assert not window.read_only
    assert window.action_save.isEnabled() and window.action_save_as.isEnabled()
    assert sent[0][2] is False
    window._refresh_title()
    assert "[읽기 전용]" not in window.windowTitle()


def test_opening_markdown_after_code_file_unlocks(window, tmp_path):
    code = tmp_path / "a.py"
    code.write_text("x = 1\n", encoding="utf-8")
    md = tmp_path / "b.md"
    md.write_text("# b\n", encoding="utf-8")

    _load(window, code)
    _load(window, md)

    assert not window.read_only and window.action_save.isEnabled()


def test_new_file_after_code_file_unlocks(window, tmp_path):
    code = tmp_path / "a.h"
    code.write_text("#pragma once\n", encoding="utf-8")
    _load(window, code)

    window.new_file()

    assert not window.read_only and window.action_save.isEnabled()
