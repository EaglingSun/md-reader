"""R4 · R5 · R6 — 설치 스크립트 · 빌드 설정을 앱 코드의 값과 대조한다 (빌드 없이 도는 정적 검사).

확장자 목록 · 이름 · 버전의 정본은 app/main.py 다. 설치 스크립트가 따라오지 않으면 여기서 깨진다.
"""
import re
from pathlib import Path

import pytest

import main

ROOT = Path(__file__).resolve().parent.parent
ISS = (ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
SPEC = (ROOT / "packaging" / "ai-docs-reader.spec").read_text(encoding="utf-8")
BUILD = (ROOT / "packaging" / "build.ps1").read_text(encoding="utf-8")
MAIN_SRC = (ROOT / "app" / "main.py").read_text(encoding="utf-8")

APP_ID = "{{8F1F9B9E-1A2B-4C3D-9E8F-7A6B5C4D3E2F}"
R4_EXTS = [".py", ".c", ".h", ".patch", ".diff", ".json", ".yml", ".yaml", ".txt"]


def iss_define(name: str) -> str:
    m = re.search(rf'^#define\s+{name}\s+"([^"]*)"', ISS, re.MULTILINE)
    assert m, f"#define {name} 없음"
    return m.group(1)


def iss_section(name: str) -> str:
    """줄 머리 [name] 부터 다음 절 머리 전까지 (주석 속 [name] 글자는 무시)."""
    m = re.search(rf"^\[{name}\]\s*$(.*?)(?=^\[\w+\]\s*$|\Z)", ISS, re.MULTILINE | re.DOTALL)
    assert m, f"[{name}] 절 없음"
    return m.group(1)


def registry_entries() -> list[dict]:
    """[Registry] 절의 항목을 (줄 이음 \\ 를 풀어) key: value 사전으로."""
    sec = iss_section("Registry")
    sec = re.sub(r"\\\s*\n\s*", " ", sec)
    out = []
    for line in sec.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        entry = {}
        for part in re.findall(r'(\w+):\s*("(?:[^"]|"")*"|[^;]+)', line):
            k, v = part
            v = v.strip()
            if v.startswith('"'):
                v = v[1:-1].replace('""', '"')
            entry[k] = v
        out.append(entry)
    return out


def expand(s: str) -> str:
    for name in ("AppName", "AppExeName", "OldExeName", "ProgIdText", "ProgIdMarkdown"):
        if f"{{#{name}}}" in s:
            s = s.replace(f"{{#{name}}}", iss_define(name))
    return s


# --- R5 이름 · R6 버전 ----------------------------------------------------

def test_visible_name_is_ai_docs_reader():
    assert main.APP_NAME == "AI_docs reader"
    assert iss_define("AppName") == main.APP_NAME


def test_file_names_use_ai_docs_reader():
    assert iss_define("AppExeName") == "ai-docs-reader.exe"
    assert re.search(r'^OutputBaseFilename=\{#AppFileName\}-setup-\{#AppVersion\}$', ISS, re.MULTILINE)
    assert iss_define("AppFileName") == "ai-docs-reader"
    assert len(re.findall(r'name="ai-docs-reader"', SPEC)) == 2   # EXE · COLLECT
    assert '"ai-docs-reader"' in BUILD and "md-reader.spec" not in BUILD
    assert r'Source: "..\dist\{#AppFileName}\*"' in ISS


def test_version_is_one_place_in_app_and_matches_installer():
    assert main.APP_VERSION == "1.4.0"
    assert iss_define("AppVersion") == main.APP_VERSION
    assert "v1.3.1" not in MAIN_SRC  # show_about 이 상수를 쓴다


def test_upgrade_keys_unchanged():
    """AppId · QSettings 키를 바꾸면 v1.3.1 과 나란히 깔리거나 최근 파일이 사라진다."""
    assert iss_define("AppId") == APP_ID
    assert re.search(r'^ORG = "EaglingSun"$', MAIN_SRC, re.MULTILINE)
    assert re.search(r'^APP = "MdReader"$', MAIN_SRC, re.MULTILINE)
    assert iss_define("ProgIdMarkdown") == "MdReader.MarkdownFile"
    assert "PrivilegesRequired=lowest" in ISS


# --- R4 연결 프로그램 -------------------------------------------------------

def _open_with_progids() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for e in registry_entries():
        m = re.fullmatch(r"Software\\Classes\\(\.[\w]+)\\OpenWithProgids", expand(e.get("Subkey", "")))
        if m:
            found.setdefault(m.group(1), set()).add(expand(e["ValueName"]))
    return found


@pytest.mark.parametrize("ext", sorted(set(R4_EXTS) | set(main.CODE_FENCE_LANGS)))
def test_every_opened_extension_is_in_open_with(ext):
    progids = _open_with_progids().get(ext, set())
    assert progids, f"{ext} OpenWithProgids 없음"
    for pid in progids:
        cmd = [e for e in registry_entries()
               if expand(e.get("Subkey", "")) == rf"Software\Classes\{pid}\shell\open\command"]
        assert cmd and expand(cmd[0]["ValueData"]) == r'"{app}\ai-docs-reader.exe" "%1"'


def test_never_sets_default_app_of_any_extension():
    """.py 등 기본 앱을 바꾸지 않는다: 확장자 키 자체의 기본값 · UserChoice 를 쓰지 않는다."""
    for e in registry_entries():
        sub = expand(e.get("Subkey", ""))
        assert "UserChoice" not in sub
        if re.fullmatch(r"Software\\Classes\\\.[\w]+", sub):
            assert e.get("ValueName", "") != "", f"확장자 기본값을 씀: {e}"


def test_markdown_association_still_behind_task():
    for ext in (".md", ".markdown"):
        entries = [e for e in registry_entries()
                   if expand(e.get("Subkey", "")) == rf"Software\Classes\{ext}\OpenWithProgids"]
        assert entries and all(e.get("Tasks") == "associatemd" for e in entries)


def test_friendly_app_name_is_visible_name():
    fan = [e for e in registry_entries() if e.get("ValueName") == "FriendlyAppName"
           and expand(e["Subkey"]) == r"Software\Classes\Applications\ai-docs-reader.exe"]
    assert fan and expand(fan[0]["ValueData"]) == "AI_docs reader"


# --- 덮어 설치(v1.3.1 → v1.4.0) 정리 ------------------------------------------

def test_upgrade_removes_old_exe_and_shortcuts():
    sec = iss_section("InstallDelete")
    assert r'Name: "{app}\{#OldExeName}"' in sec
    assert r'Name: "{autoprograms}\{#OldAppName}"' in sec
    assert r'Name: "{userdesktop}\{#OldAppName}.lnk"' in sec
    assert "UsePreviousGroup=no" in ISS


def test_old_applications_key_is_repointed_not_deleted():
    """옛 Applications\\md-reader.exe 를 UserChoice 로 쓰는 확장자(.txt 등)가 깨지지 않게 새 exe 를 가리킨다.

    목록에 같은 앱이 두 번 뜨지 않도록 NoOpenWith. 새로 까는 PC 에는 만들지 않는다(Check).
    """
    old = [e for e in registry_entries() if expand(e.get("Subkey", "")).startswith(
        r"Software\Classes\Applications\md-reader.exe")]
    assert old and all(e.get("Check") == "HadOldExeKey" for e in old)
    cmd = [e for e in old if expand(e["Subkey"]).endswith(r"shell\open\command")]
    assert cmd and expand(cmd[0]["ValueData"]) == r'"{app}\ai-docs-reader.exe" "%1"'
    assert any(e.get("ValueName") == "NoOpenWith" for e in old)
