"""코드 보기 렌더 실측 (R2 · R3) — 실제 앱 창을 띄워 잰다. pytest 대상 아님.

    python tests/manual/check_code_view.py <out_dir> <file> [<file> ...]

파일마다:
  rows      줄 번호 개수 == 파일 줄 수
  align     번호와 글줄 첫 화면줄의 세로 어긋남(px) 최대값 ≤ 1.5
  locked    IR 편집 영역 contenteditable == "false" (읽기 전용 파일만)
  typing    키를 쳐도 더티가 안 되고 파일 바이트가 그대로
첫 파일은 다크 모드로 바꿔 한 번 더 재고(잠금 유지), 코드 블록을 클릭한 뒤 줄 번호가 보이는지도 본다.
캡처: <out_dir>/<파일명>[-dark|-clicked].png

오프라인 확인: QTWEBENGINE_CHROMIUM_FLAGS="--proxy-server=http://127.0.0.1:9" 로 네트워크를 막고 돌린다(offline 판정).
전제: 창을 띄울 수 있는 데스크톱 세션. 설정은 테스트 ORG(EaglingSunTest)에 쓰고 끝나면 지운다.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))

from PyQt6.QtCore import QPoint, QSettings, Qt, QTimer  # noqa: E402
from PyQt6.QtTest import QTest  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import main  # noqa: E402

main.ORG = "EaglingSunTest"
WAIT_MS = 2500
ALIGN_TOL_PX = 1.5

MEASURE_JS = r"""
(() => {
  const ir = document.querySelector('.vditor-ir pre.vditor-reset');
  const code = [...document.querySelectorAll('#vditor code.vditor-linenumber')]
      .find(c => c.offsetParent !== null);
  const visible = el => el && el.offsetParent !== null && el.getBoundingClientRect().height > 0;
  const toolbar = document.querySelector('.vditor-toolbar');
  const out = {editable: ir ? ir.getAttribute('contenteditable') : null,
               opacity: ir ? getComputedStyle(ir).opacity : null,
               expanded: document.querySelectorAll('.vditor-ir__node--expand').length,
               rawVisible: [...document.querySelectorAll('.vditor-ir__marker--pre')].some(visible),
               toolbarVisible: visible(toolbar),
               // R7: 화면을 그리는 데 원격 자원을 쓰지 않는다 (Vditor · lute · hljs 모두 vendor/)
               remote: performance.getEntriesByType('resource').map(e => e.name).filter(u => /^https?:/.test(u)),
               lute: typeof Lute !== 'undefined',
               mermaidSvg: document.querySelectorAll('.language-mermaid svg').length};
  if (!code) { out.rows = 0; return JSON.stringify(out); }
  const rows = [...code.querySelectorAll('.vditor-linenumber__rows > span')];
  const lh = parseFloat(getComputedStyle(code).lineHeight);
  const walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT, {acceptNode: n =>
      n.parentElement.closest('.vditor-linenumber__rows') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT});
  const firsts = [];  // 줄마다 첫 글자의 rect (빈 줄은 null)
  let atStart = true, n;
  while ((n = walker.nextNode())) {
    const t = n.textContent;
    for (let i = 0; i < t.length; i++) {
      if (t[i] === '\n') { if (atStart) firsts.push(null); atStart = true; continue; }
      if (atStart) {
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        firsts.push(r.getBoundingClientRect()); atStart = false;
      }
    }
  }
  const deltas = [];
  firsts.forEach((r, i) => {
    if (!r || !rows[i]) return;
    const lineBoxTop = r.top - (lh - r.height) / 2;
    deltas.push(Math.abs(rows[i].getBoundingClientRect().top - lineBoxTop));
  });
  out.rows = rows.length;
  out.textLines = firsts.length;
  out.maxDelta = deltas.length ? Math.max(...deltas) : null;
  out.firstRowNumberVisible = getComputedStyle(rows[0], '::before').content;
  const cr = code.getBoundingClientRect();
  out.codeCenter = [Math.round(cr.left + cr.width / 2), Math.round(cr.top + 40)];
  return JSON.stringify(out);
})()
"""


class Runner:
    def __init__(self, out_dir: Path, files: list[Path]) -> None:
        self.app = QApplication(sys.argv[:1])
        self.win = main.MainWindow()
        self.win.resize(1300, 900)
        self.win.show()
        self.out_dir = out_dir
        self.files = files
        self.results: list[dict] = []
        self.started = False
        self.win.editor.bridge.editorReady.connect(self._ready)

    def _ready(self) -> None:
        if self.started:
            return  # 테마 전환으로 Vditor 를 다시 만들면 editorReady 가 또 온다
        self.started = True
        self._next(0)

    def _js(self, cb) -> None:
        self.win.editor.page().runJavaScript(MEASURE_JS, lambda res: cb(json.loads(res)))

    def _next(self, i: int) -> None:
        if i >= len(self.files):
            self._dark_and_click()
            return
        path = self.files[i]
        self.win._load_path(path)
        QTimer.singleShot(WAIT_MS, lambda: self._js(lambda m: self._typed(i, path, m)))

    def _typed(self, i: int, path: Path, m: dict) -> None:
        before = path.read_bytes()
        target = self.win.editor.focusProxy() or self.win.editor
        target.setFocus()
        QTest.keyClicks(target, "zzz")
        QTest.keyClick(target, Qt.Key.Key_Return)

        def after():
            m["file"] = path.name
            m["expectedRows"] = len(path.read_text(encoding="utf-8").splitlines())
            m["readOnly"] = self.win.read_only
            m["dirtyAfterTyping"] = self.win.editor.bridge.is_dirty()
            m["bytesUnchanged"] = path.read_bytes() == before
            m["title"] = self.win.windowTitle()
            self.win.grab().save(str(self.out_dir / f"{path.name}.png"))
            self.results.append(m)
            if not self.win.read_only:
                self.win.editor.bridge.mark_clean()  # 편집 가능한 파일은 타이핑이 들어간 게 정상
            self._next(i + 1)

        QTimer.singleShot(600, after)

    def _dark_and_click(self) -> None:
        path = self.files[0]
        self.win._load_path(path)

        def go_dark():
            self.win._action_dark.setChecked(True)
            self.win.toggle_dark()
            QTimer.singleShot(WAIT_MS + 1000, lambda: self._js(dark_measured))

        def dark_measured(m):
            m["file"] = path.name + " (dark)"
            m["expectedRows"] = len(path.read_text(encoding="utf-8").splitlines())
            m["readOnly"] = self.win.read_only
            self.win.grab().save(str(self.out_dir / f"{path.name}-dark.png"))
            self.results.append(m)
            x, y = m.get("codeCenter", [600, 300])
            target = self.win.editor.focusProxy() or self.win.editor
            QTest.mouseClick(target, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(x, y))
            QTimer.singleShot(800, lambda: self._js(clicked))

        def clicked(m):
            m["file"] = path.name + " (dark, clicked)"
            m["expectedRows"] = len(path.read_text(encoding="utf-8").splitlines())
            m["readOnly"] = self.win.read_only
            self.win.grab().save(str(self.out_dir / f"{path.name}-clicked.png"))
            self.results.append(m)
            self.win._action_dark.setChecked(False)
            self.win.toggle_dark()
            QTimer.singleShot(1500, self.app.quit)

        QTimer.singleShot(WAIT_MS, go_dark)

    def run(self) -> int:
        QTimer.singleShot(120000, self.app.quit)
        self.app.exec()
        QSettings(main.ORG, main.APP).clear()
        ok = True
        for m in self.results:
            if not m["readOnly"]:
                # 편집 가능한 문서(.md · 데이터)는 지금처럼: 편집 가능 · 툴바 보임. 줄 번호 수는 재지 않는다
                # (데이터 파일은 저장 왕복을 지키려고 끝 개행을 남기므로 빈 번호가 하나 더 붙는다 — 기존 동작).
                checks = {"editable": m.get("editable") == "true", "toolbar": m.get("toolbarVisible") is True}
            else:
                checks = {
                    "rows": m.get("rows") == m["expectedRows"],
                    "align": m.get("maxDelta") is not None and m["maxDelta"] <= ALIGN_TOL_PX,
                }
            checks["offline"] = m.get("remote") == [] and m.get("lute") is True
            if m["readOnly"]:
                checks["locked"] = m.get("editable") == "false"
                checks["notDimmed"] = m.get("opacity") == "1"
                checks["noRawBox"] = m.get("rawVisible") is False
                checks["noToolbar"] = m.get("toolbarVisible") is False
                if "dirtyAfterTyping" in m:
                    checks["typing"] = (not m["dirtyAfterTyping"]) and m["bytesUnchanged"]
            m["checks"] = checks
            ok &= all(checks.values())
            m.pop("codeCenter", None)
            print(json.dumps(m, ensure_ascii=False))
        print("RESULT:", "PASS" if ok and len(self.results) == len(self.files) + 2 else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(Runner(out, [Path(p).resolve() for p in sys.argv[2:]]).run())
