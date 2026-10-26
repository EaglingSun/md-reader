# md-reader

가벼운 Windows 마크다운 에디터.

## 기능

- WYSIWYG 인라인 렌더링 (Vditor IR 모드)
- 한글/UTF-8, 코드 syntax highlighting, 표 편집, Mermaid 다이어그램
- HTML/PDF 내보내기, 다크 모드, 폴더 사이드바, 최근 파일
- **.md / .markdown** — 마크다운 편집 (넓은 표·본문은 창 폭에 맞춰 줄바꿈)
- **.txt** — 원문 그대로 표시 (마크다운으로 해석하지 않음, 긴 줄은 창 폭에서 줄바꿈)
- **.yaml / .yml / .json** — 자동으로 코드블록으로 감싸 syntax highlighting 표시 (저장 시 펜스 자동 제거)
- 파일을 열면 왼쪽 트리가 그 위치를 펼쳐 보여 줌 (트리 폴더 밖 파일이면 그 폴더로 이동)
- .md 파일 연결 (탐색기에서 더블클릭으로 열림)

---

## 설치 (사용자)

[Releases](https://github.com/EaglingSun/md-reader/releases)에서 받은 `md-reader-setup-X.Y.Z.exe`를 더블클릭 → 마법사 따라가기.

- 관리자 권한 불필요 (`%LocalAppData%\Programs\md-reader\`에 설치)
- 사전 설치 필요 없음 (Python 포함된 단일 인스톨러)
- "Associate .md files" 체크하면 .md 더블클릭으로 열림

업데이트: 새 버전 `md-reader-setup-X.Y.Z.exe`를 그대로 실행 — 제거할 필요 없음 (같은 폴더에 덮어 설치, 설정·최근 파일 유지).

제거: 설정 → 앱 → md-reader → 제거.

## 단축키


| 동작      | 키           | 동작               | 키           |
| --------- | ------------ | ------------------ | ------------ |
| 새 파일   | Ctrl+N       | 다른 이름으로 저장 | Ctrl+Shift+S |
| 열기      | Ctrl+O       | 다크 모드          | Ctrl+D       |
| 폴더 열기 | Ctrl+Shift+O | 사이드바           | Ctrl+B       |
| 저장      | Ctrl+S       | 종료               | Ctrl+Q       |

내보내기: 파일 → 내보내기 → HTML / PDF.

---

## 개발 / 빌드 (개발자만)

https://github.com/EaglingSun/md-reader

### 폴더 구조

```
md-reader/
├── app/                  앱 코드
│   ├── main.py           MainWindow / 메뉴 / 사이드바
│   ├── editor.py         QWebEngineView 래퍼
│   ├── bridge.py         QWebChannel
│   ├── web/              Vditor 호스트 (HTML/JS/CSS)
│   └── assets/icon.ico   앱 아이콘
├── packaging/            배포 빌드
│   ├── md-reader.spec    PyInstaller spec
│   ├── installer.iss     Inno Setup
│   └── build.ps1         원샷 빌드
├── samples/                기능 확인용 샘플
│   ├── sample.md
│   ├── sample.yaml
│   └── sample.json
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
.\run.bat
```

### 인스톨러 빌드

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build.ps1
```

산출물: `dist/installer/md-reader-setup-X.Y.Z.exe`. Inno Setup이 없으면 `dist/md-reader/` 폴더까지만 생성됨.

버전 변경: `packaging/installer.iss`의 `#define AppVersion`과 `app/main.py` 정보 창(`show_about`)의 버전 문자열을 같이 수정.

### 아키텍처

- **PyQt6**: 메인 윈도우, 메뉴, 파일시스템
- **QWebEngineView + Vditor**: 본체 에디터 (IR 모드 = 입력 즉시 인라인 렌더링)
- **QWebChannel**: Python ↔ JS 양방향 시그널/슬롯
- Vditor 자원은 jsdelivr.net CDN 로드

### 크레딧

- [Vditor](https://github.com/Vanessa219/vditor) — MIT (Vanessa219), 실행 시 jsdelivr CDN 에서 로드
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) · PyQt6-WebEngine — GPL v3 / Commercial
- [Qt 6](https://www.qt.io/) — LGPL v3 (PyQt6-Qt6 휠, 설치본 `_internal` 에 DLL 로 동봉)
- [PyInstaller](https://pyinstaller.org/), [Inno Setup](https://jrsoftware.org/isinfo.php)

## 라이선스

[GPL-3.0](LICENSE) — GNU General Public License v3.0.
PyQt6 가 GPL v3 이므로 이 앱도 GPL v3 로 배포한다. 수정본을 배포할 때는 소스도 같은 라이선스로 공개해야 한다.

Copyright (C) 2026 EaglingSun

## 문의

EaglingSun — [Issues](https://github.com/EaglingSun/md-reader/issues)
