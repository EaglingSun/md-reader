"""PDF 내보내기 실측 — 실제 앱 창을 띄워 문서 끝까지 PDF 에 들어가는지 잰다. pytest 대상 아님.

    python tests/manual/check_pdf_export.py <out_dir>

시료: samples/sample.md · <out_dir> 에 만드는 long.md(80행 표 + 150줄 코드 블록) · long.yaml(200줄, 원문 표시) ·
long.py(300줄, 읽기 전용) · wide.md · wide.py(한 줄 걸러 종이 폭을 넘는 긴 줄, 줄마다 `Lnn` 으로 시작).
파일마다 앱이 부르는 경로(MarkdownEditor.export_pdf)로 내보내고 PyMuPDF 로 본다.
  cover          원문 토큰(한글 · 영숫자 2자 이상) 중 PDF 글자에 있는 비율 ≥ 0.99
                 (코드 펜스 줄 · mermaid 블록은 그림 · 표지라 뺀다. PDF 글자는 공백을 지우고 대조)
  lastFound      원문 마지막 토큰이 PDF 에 있다
  noToolbar      1쪽 위 30pt 띠에 글자 · 도형이 없다 (편집 툴바 아이콘 · 글자 수 표시)
  noHeadingMarks PDF 에 IR 제목 표지 글자(H1~H6)가 없다
  noCopyIcon     쪽 오른쪽 60pt 띠에 작은 도형(≤20pt)이 없다 — 코드 블록 복사 아이콘. 마우스가 코드 블록 위에 있으면
                 hover 로 보이던 것이 그대로 찍혀 첫 줄 끝을 가렸다. 재기 전에 hover 와 같은 상태를 만든다(HOVER_JS)
  lineAlign      (wide.*) 줄 번호 k 와 k번째 줄 첫 글자의 쪽 · 높이가 같다(차이 ≤ 2pt)
  lineOrder      (wide.*) 번호가 아래로 차례대로 놓였다(앞 번호보다 5pt 이상 아래) — 빈 줄이 접히면 번호가 겹친다
쪽 수만 보면 안 된다 — 고치기 전에도 long.md 는 4쪽이 나왔지만 글자는 12% 만 들어 있었다(2026-11-01 실측).

전제: 창을 띄울 수 있는 데스크톱 세션 · PyMuPDF(`python -m pip install pymupdf`). 설정은 테스트 ORG 에 쓰고 끝나면 지운다.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "app"))

import fitz  # noqa: E402  PyMuPDF — 없으면 여기서 멈춘다(건너뛰지 않는다)
from PyQt6.QtCore import QSettings, QTimer  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

import main  # noqa: E402

main.ORG = "EaglingSunTest"
WAIT_MS = 2500
# 코드 블록 복사 버튼은 Vditor 가 `.vditor-reset pre:hover div.vditor-copy { display:block }` 로만 보인다 — 인쇄 때
# 마우스가 코드 블록 위에 있으면 그대로 찍힌다. 마우스를 움직이지 않고(QTest.mouseMove 는 실제 포인터를 옮긴다)
# 같은 구체성의 규칙을 넣어 "hover 로 보이는 상태"를 만든다. 보이게 된 버튼 수를 돌려준다.
HOVER_JS = r"""
(() => {
  if (!document.getElementById('check-hover')) {
    const s = document.createElement('style'); s.id = 'check-hover';
    s.textContent = '.vditor-reset pre div.vditor-copy { display: block; }';
    document.head.appendChild(s);
  }
  return [...document.querySelectorAll('#vditor div.vditor-copy')].filter(d => d.offsetParent !== null).length;
})()
"""
COVER_MIN = 0.99
TOOLBAR_BAND_PT = 30
ALIGN_TOL_PT = 2
MIN_STEP_PT = 5
RIGHT_BAND_PT = 60
TOKEN = re.compile(r"[0-9A-Za-z_가-힣]{2,}")


def wide_lines() -> list[str]:
    """줄 i 는 `Lii` 로 시작 · 홀수 줄은 종이 폭을 넘는다 · 5번째 줄은 빈 줄(높이가 0 으로 접히면 번호가 밀린다)."""
    return ["" if i == 5 else f"L{i:02d} " + " ".join(f"w{i:02d}x{j:02d}" for j in range(30 if i % 2 else 2))
            for i in range(1, 10)]


def make_samples(out: Path) -> list[Path]:
    md = ["# 긴 문서 시료", "", "## 1. 긴 표", "", "| 번호 | 이름 | 설명 |", "|---|---|---|"]
    md += [f"| {i} | 항목{i:03d} | 설명줄{i:03d} 끝 |" for i in range(1, 81)]
    md += ["", "## 2. 긴 코드 블록", "", "```python"]
    md += [f"value_{i:03d} = {i}  # 코드줄{i:03d}" for i in range(1, 151)]
    md += ["```", "", "## 3. 마지막 절", "", "마지막문장 끝표지"]
    (out / "long.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "long.yaml").write_text("\n".join(f"key_{i:03d}: 값{i:03d}" for i in range(1, 201)) + "\n", encoding="utf-8")
    (out / "long.py").write_text("\n".join(f"line_{i:03d} = '줄{i:03d}'" for i in range(1, 301)) + "\n", encoding="utf-8")
    (out / "wide.md").write_text("# 긴 줄\n\n```text\n" + "\n".join(wide_lines()) + "\n```\n", encoding="utf-8")
    (out / "wide.py").write_text("\n".join("# " + l if l else "" for l in wide_lines()) + "\n", encoding="utf-8")
    return [ROOT / "samples" / "sample.md", out / "long.md", out / "long.yaml", out / "long.py",
            out / "wide.md", out / "wide.py"]


def line_alignment(doc) -> tuple[int, int, float | None, bool]:
    """(줄 시작 수, 번호 수, 최대 어긋남 pt, 번호가 아래로 차례대로 놓였나).

    어긋남: 번호 k 와 `Lkk` 의 높이 차 — 다른 쪽에 있으면 inf.
    차례: 번호 k+1 이 k 보다 MIN_STEP_PT 이상 아래(또는 다음 쪽). 빈 줄 높이가 0 으로 접히면 두 번호가 겹쳐 False.
    """
    words = [(i, w) for i, pg in enumerate(doc) for w in pg.get_text("words")]
    starts = {int(w[4][1:]): (i, w) for i, w in words if re.fullmatch(r"L\d\d", w[4])}
    if not starts:
        return 0, 0, None, True
    left = min(w[0] for _, w in starts.values())
    nums: dict[int, tuple] = {}
    for i, w in words:
        if re.fullmatch(r"\d{1,3}", w[4]) and w[2] <= left:
            nums.setdefault(int(w[4]), (i, w))
    deltas = []
    for k, (pi, w) in starts.items():
        if k not in nums:
            deltas.append(float("inf"))
            continue
        ni, nw = nums[k]
        deltas.append(abs(nw[1] - w[1]) if ni == pi else float("inf"))
    seq = [nums[k] for k in sorted(nums)]
    ordered = all(b[0] > a[0] or (b[0] == a[0] and b[1][1] - a[1][1] >= MIN_STEP_PT) for a, b in zip(seq, seq[1:]))
    return len(starts), len(nums), max(deltas), ordered


def source_tokens(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```mermaid.*?```", "", text, flags=re.S)
    if path.suffix == ".md":
        text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("```"))
    return TOKEN.findall(text)


class Runner:
    def __init__(self, out_dir: Path, files: list[Path]) -> None:
        self.app = QApplication(sys.argv[:1])
        self.win = main.MainWindow()
        self.win.resize(1300, 900)
        self.win.show()
        self.out_dir = out_dir
        self.files = files
        self.i = 0
        self.done: list[tuple[Path, Path, bool, bool]] = []
        self.started = False
        self.win.editor.bridge.editorReady.connect(self._ready)

    def _ready(self) -> None:
        if self.started:
            return
        self.started = True
        self.win.editor.page().pdfPrintingFinished.connect(self._printed)
        self._next()

    def _next(self) -> None:
        if self.i >= len(self.files):
            QTimer.singleShot(300, self.app.quit)
            return
        self.win._load_path(self.files[self.i])
        QTimer.singleShot(WAIT_MS, self._hover_code)

    def _hover_code(self) -> None:
        """복사 버튼이 hover 로 보이는 상태를 만든 뒤 내보낸다(HOVER_JS)."""
        def go(visible) -> None:
            self.hovered = isinstance(visible, (int, float)) and visible > 0
            QTimer.singleShot(200, self._export)

        self.win.editor.page().runJavaScript(HOVER_JS, go)

    def _export(self) -> None:
        pdf = self.out_dir / (self.files[self.i].name + ".pdf")
        if pdf.exists():
            pdf.unlink()
        self.win.editor.export_pdf(str(pdf))

    def _printed(self, path: str, ok: bool) -> None:
        self.done.append((self.files[self.i], Path(path), ok, self.win.read_only, self.hovered))
        self.win.editor.bridge.mark_clean()
        self.i += 1
        QTimer.singleShot(300, self._next)

    def run(self) -> int:
        QTimer.singleShot(120000, self.app.quit)
        self.app.exec()
        QSettings(main.ORG, main.APP).clear()
        ok = len(self.done) == len(self.files)
        for src, pdf, printed, read_only, hovered in self.done:
            # 복사 버튼을 보이게 못 했으면(코드 블록 없음) 복사 아이콘 판정이 빈 자물쇠가 된다 — 실패로 센다.
            ok &= hovered
            toks = source_tokens(src)
            doc = fitz.open(pdf)
            text = re.sub(r"\s+", "", "".join(p.get_text() for p in doc))
            miss = [t for t in toks if t not in text]
            cover = 1 - len(miss) / max(len(toks), 1)
            p1 = doc[0]
            band = [w[4] for w in p1.get_text("words") if w[3] < TOOLBAR_BAND_PT]
            band += ["<도형>" for d in p1.get_drawings() if d["rect"].y1 < TOOLBAR_BAND_PT]
            marks = [w[4] for pg in doc for w in pg.get_text("words")
                     if re.fullmatch(r"H[1-6]", w[4]) and w[4] not in toks]
            icons = [d["rect"] for pg in doc for d in pg.get_drawings()
                     if d["rect"].width <= 20 and d["rect"].height <= 20 and d["rect"].x0 > pg.rect.width - RIGHT_BAND_PT]
            checks = {"printed": printed, "cover": cover >= COVER_MIN, "lastFound": bool(toks) and toks[-1] in text,
                      "noToolbar": not band, "noHeadingMarks": not marks, "noCopyIcon": not icons}
            n_starts, n_nums, max_delta, ordered = line_alignment(doc)
            if src.name.startswith("wide."):
                lines = wide_lines()
                checks["lineAlign"] = (n_nums == len(lines) and n_starts == sum(1 for l in lines if l)
                                       and max_delta <= ALIGN_TOL_PT)
                checks["lineOrder"] = ordered
            ok &= all(checks.values())
            print(json.dumps({"file": src.name, "readOnly": read_only, "hovered": hovered, "pages": doc.page_count,
                              "tokens": len(toks), "cover": round(cover, 3), "missSample": miss[:5],
                              "toolbarBand": len(band), "headingMarks": len(marks),
                              "align": [n_starts, n_nums, None if max_delta is None else round(max_delta, 1)],
                              "checks": checks}, ensure_ascii=False))
        print("RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(Runner(out, make_samples(out)).run())
