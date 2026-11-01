# AI_docs reader

AI 시대의 문서 · 코드를 읽는 가벼운 Windows 뷰어 겸 마크다운 에디터. (옛 이름 **md-reader** — v1.4.0 에서 바꿈)

## 기능

- WYSIWYG 인라인 렌더링 (Vditor IR 모드)
- 한글/UTF-8, 코드 syntax highlighting, 표 편집, Mermaid 다이어그램
- HTML/PDF 내보내기, 다크 모드, 폴더 사이드바, 최근 파일
- **.md / .markdown** — 마크다운 편집 (넓은 표·본문은 창 폭에 맞춰 줄바꿈)
- **.txt** — 원문 그대로 표시 (마크다운으로 해석하지 않음, 긴 줄은 창 폭에서 줄바꿈)
- **.yaml / .yml / .json** — 자동으로 코드블록으로 감싸 syntax highlighting 표시 (저장 시 펜스 자동 제거)
- **코드 · 패치 (읽기 전용)** — `.py` `.c` `.h` `.patch` `.diff` (+ `.ps1` `.sh` `.js` `.toml` `.ini` `.log`) 를 색 · **줄 번호**와 함께 표시. 줄 번호 = 파일의 실제 줄 번호. 편집 · 저장은 막혀 있다(제목줄 `[읽기 전용]`) — 열어 보기만 해서는 파일이 바뀌지 않는다
- 파일을 열면 왼쪽 트리가 그 위치를 펼쳐 보여 줌 (트리 폴더 밖 파일이면 그 폴더로 이동)
- .md 파일 연결 (탐색기에서 더블클릭으로 열림)
- 탐색기 우클릭 「연결 프로그램」 목록에 바로 뜸 — 위 코드 · 데이터 · 텍스트 형식. **기본 앱은 바꾸지 않는다** (`.py` 더블클릭은 그대로 Python 실행)

---

## 설치 (사용자)

[Releases](https://github.com/EaglingSun/ai-docs-reader/releases)에서 받은 `ai-docs-reader-setup-X.Y.Z.exe`를 더블클릭 → 마법사 따라가기.

- 관리자 권한 불필요 (`%LocalAppData%\Programs\ai-docs-reader\`에 설치)
- 사전 설치 필요 없음 (Python 포함된 단일 인스톨러)
- "Associate .md files" 체크하면 .md 더블클릭으로 열림
- 서명되지 않은 설치 파일이라 Windows SmartScreen 경고가 뜰 수 있음 → 「추가 정보」 → 「실행」

업데이트: 새 버전 `ai-docs-reader-setup-X.Y.Z.exe`를 그대로 실행 — 제거할 필요 없음 (같은 폴더에 덮어 설치, 설정·최근 파일 유지).

md-reader(v1.0 ~ v1.3.1)에서 올리기: **열린 md-reader 창을 먼저 닫고** 새 설치 파일을 실행한다 (켜 둔 채로 실행하면 설치 파일이 자동으로 닫지 못해 「응용 프로그램을 자동으로 닫지 못했습니다」가 뜬다 — 그때 창을 닫고 「다시 시도」).

- 앱 목록에는 하나만 남고(이름이 AI_docs reader 로 바뀜), 설치 폴더는 기존 `%LocalAppData%\Programs\md-reader\` 를 그대로 쓴다. 설정 · 최근 파일은 그대로.
- 옛 `md-reader.exe` · 시작 메뉴 · 바탕화면 바로가기는 설치 파일이 정리한다.
- 「항상 이 앱으로 열기」로 md-reader 를 골라 둔 형식(예: .txt)은 새 실행 파일로 이어진다.
- 「항상」을 고르지 않고 최근에 md-reader 로 열던 형식(예: .md)은 실행 파일 이름이 바뀌어 다른 앱으로 열릴 수 있다 → 파일 우클릭 → 연결 프로그램 → 다른 앱 선택 → AI_docs reader → 「항상」 한 번.

기본 앱이 정해져 있지 않던 형식(예: VS Code 만 등록돼 있던 .yml)은 이 앱이 「연결 프로그램」에 더해지면서 더블클릭 때 앱을 고르라는 창이 뜰 수 있다 (한 번 고르면 끝). 기본 앱이 정해진 형식(.py · .json · .txt 등)은 그대로다.

제거: 설정 → 앱 → AI_docs reader → 제거.

## 단축키


| 동작      | 키           | 동작               | 키           |
| --------- | ------------ | ------------------ | ------------ |
| 새 파일   | Ctrl+N       | 다른 이름으로 저장 | Ctrl+Shift+S |
| 열기      | Ctrl+O       | 다크 모드          | Ctrl+D       |
| 폴더 열기 | Ctrl+Shift+O | 사이드바           | Ctrl+B       |
| 저장      | Ctrl+S       | 종료               | Ctrl+Q       |

내보내기: 파일 → 내보내기 → HTML / PDF. 읽기 전용 문서에서는 저장 · 다른 이름으로 저장이 꺼진다.

---

## 개발 / 빌드 (개발자만)

https://github.com/EaglingSun/ai-docs-reader

### 폴더 구조

```
ai-docs-reader/
├── app/                  앱 코드
│   ├── main.py           MainWindow / 메뉴 / 사이드바 · 이름 · 버전 · 확장자 목록(정본)
│   ├── editor.py         QWebEngineView 래퍼
│   ├── bridge.py         QWebChannel
│   ├── web/              Vditor 호스트 (HTML/JS/CSS) · vendor/ (받아 둔 Vditor, git 제외)
│   └── assets/icon.ico   앱 아이콘
├── packaging/            배포 빌드
│   ├── ai-docs-reader.spec  PyInstaller spec
│   ├── installer.iss     Inno Setup
│   ├── fetch_vditor.py   Vditor 받기 · 해시 검증 (build.ps1 · run.bat 이 부름)
│   └── build.ps1         원샷 빌드
├── samples/              기능 확인용 샘플 (md · yaml · json · c · py · patch)
├── tests/                pytest (창 없이 · 설치 스크립트 정적 검사) + manual/ 렌더 실측
├── requirements.txt
├── run.bat               개발용 런처
├── LICENSE               GPL-3.0
└── README.md
```

### 사전 요구

- Python 3.13
- (인스톨러 빌드 시) [Inno Setup 6](https://jrsoftware.org/isinfo.php)
  ```powershell
  winget install JRSoftware.InnoSetup
  ```

### 개발 실행

```powershell
python -m pip install -r requirements.txt
python packaging\fetch_vditor.py   # Vditor 를 app\web\vendor 에 받기 (판 · sha512 고정, 저장소에는 안 넣음) — run.bat 이 없으면 알아서 부른다
.\run.bat
```

### 테스트

```powershell
python -m pytest tests -q                                          # 단위 · 정적 검사
python tests\manual\check_code_view.py out samples\sample.c samples\sample.py samples\sample.patch   # 렌더 실측(창이 뜬다)
python tests\manual\check_pdf_export.py out                        # PDF 내보내기 실측 — 문서 끝까지 들어가는지(창이 뜬다 · PyMuPDF 필요)
```

### 인스톨러 빌드

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

산출물: `dist/installer/ai-docs-reader-setup-X.Y.Z.exe`. Inno Setup이 없으면 `dist/ai-docs-reader/` 폴더까지만 생성됨.

버전 변경: `app/main.py` 의 `APP_VERSION` 과 `packaging/installer.iss` 의 `#define AppVersion` 을 같이 수정 (`tests/test_packaging.py` 가 대조). 확장자를 늘리면 `app/main.py` 의 `READ_ONLY_FENCE_LANGS` 와 `installer.iss` 의 `OpenWithProgids` 줄을 같이 (역시 테스트가 대조).

### 아키텍처

- **PyQt6**: 메인 윈도우, 메뉴, 파일시스템
- **QWebEngineView + Vditor**: 본체 에디터 (IR 모드 = 입력 즉시 인라인 렌더링)
- **QWebChannel**: Python ↔ JS 양방향 시그널/슬롯
- Vditor 3.10.9 는 설치본에 들어 있다 (`app/web/vendor/vditor`) — 인터넷 없이 그린다 (v1.4.0 부터. 그 전에는 jsdelivr CDN)

### 크레딧

- [Vditor](https://github.com/Vanessa219/vditor) — MIT (Vanessa219), 설치본에 동봉 (`vendor/vditor/LICENSE`). Vditor 가 함께 싣는 lute · highlight.js · mermaid · KaTeX 등은 각자의 라이선스를 따른다
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) · PyQt6-WebEngine — GPL v3 / Commercial
- [Qt 6](https://www.qt.io/) — LGPL v3 (PyQt6-Qt6 휠, 설치본 `_internal` 에 DLL 로 동봉)
- [PyInstaller](https://pyinstaller.org/), [Inno Setup](https://jrsoftware.org/isinfo.php)

## 라이선스

[GPL-3.0](LICENSE) — GNU General Public License v3.0.
PyQt6 가 GPL v3 이므로 이 앱도 GPL v3 로 배포한다. 수정본을 배포할 때는 소스도 같은 라이선스로 공개해야 한다.

Copyright (C) 2026 EaglingSun

## 문의

EaglingSun — [Issues](https://github.com/EaglingSun/ai-docs-reader/issues)
