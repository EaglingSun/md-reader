import re
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QRect, QSettings, QTimer
from PyQt6.QtGui import QAction, QCursor, QFileSystemModel, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTreeView,
)

from editor import MarkdownEditor


def _icon_path() -> Path:
    """Resolve icon.ico in both dev and PyInstaller-frozen modes."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / "assets" / "icon.ico"


def _fit_to_screen(avail: QRect, width: int = 1600, height: int = 1000) -> QRect:
    """Shrink the default window size into 90% of the screen's available area, centered on it.

    Keeps the window on-screen on low-resolution / high-scaling laptops.
    """
    r = QRect(0, 0, min(width, int(avail.width() * 0.9)), min(height, int(avail.height() * 0.9)))
    r.moveCenter(avail.center())
    return r

ORG = "EaglingSun"
APP = "MdReader"
MAX_RECENT = 10

# Non-markdown extensions that we wrap as a fenced code block on load and
# unwrap on save. Vditor's hljs handles the syntax highlighting; .txt is shown
# verbatim instead of being interpreted as markdown.
CODE_FENCE_LANGS = {
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".json": "json",
    ".txt":  "text",
}

OPEN_FILTER = (
    "Markdown / 데이터 (*.md *.markdown *.txt *.yaml *.yml *.json);;"
    "Markdown (*.md *.markdown);;"
    "텍스트 (*.txt);;"
    "YAML (*.yaml *.yml);;"
    "JSON (*.json);;"
    "모든 파일 (*)"
)
FS_NAME_FILTERS = ["*.md", "*.markdown", "*.txt", "*.yaml", "*.yml", "*.json"]


def _wrap_as_code(body: str, lang: str) -> str:
    # The fence must be longer than any backtick run in the body, otherwise a
    # ``` line inside (common in .txt notes) would close the block early.
    longest = max((len(run) for run in re.findall(r"`+", body)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{lang}\n{body}\n{fence}\n"


def _unwrap_code(text: str, lang: str) -> tuple[str, bool]:
    """Extract body from a single ```{lang} ... ``` block (fence of 3+ backticks).

    Returns (body, is_pure_block). is_pure_block=True means the entire
    document is exactly one fence and unwrapping is lossless. False means
    the user added prose around the fence; saving as the original data
    extension would discard that prose.
    """
    pattern = rf"^\s*(`{{3,}}){re.escape(lang)}\s*\n(.*?)\n\1\s*$"
    m = re.match(pattern, text, re.DOTALL)
    if m:
        return m.group(2), True
    return text, False


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(ORG, APP)
        self.current_file: Path | None = None
        self.dark_mode: bool = bool(self.settings.value("dark_mode", False, type=bool))
        self._pending_html_path: str | None = None
        self._pending_open: Path | None = None

        self.setWindowTitle("md-reader")
        # 마우스가 있는 화면에 연다 (Windows 새 창 위치와 같은 기준).
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        self.setGeometry(_fit_to_screen(screen.availableGeometry()))

        self.editor = MarkdownEditor()
        self.editor.bridge.editorReady.connect(self._on_editor_ready)

        self.fs_model = QFileSystemModel()
        self.fs_model.setNameFilters(FS_NAME_FILTERS)
        self.fs_model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setHeaderHidden(True)
        for col in range(1, 4):
            self.tree.hideColumn(col)
        self.tree.clicked.connect(self._on_tree_clicked)

        last_folder = self.settings.value("folder", str(Path.home()))
        self._set_folder(last_folder)

        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 1120])
        self.setCentralWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("준비됨")

        self._build_menus()
        self._apply_theme()

        # 다크 모드 초기 적용 (Vditor 부팅 후 전송)
        QTimer.singleShot(800, self._send_initial_theme)

        # 제목 더티 표시 갱신용 폴링
        self._title_timer = QTimer(self)
        self._title_timer.setInterval(700)
        self._title_timer.timeout.connect(self._refresh_title)
        self._title_timer.start()

    # --- UI build -----------------------------------------------------

    def _build_menus(self) -> None:
        mb = self.menuBar()

        m_file = mb.addMenu("&파일")
        m_file.addAction(self._action("새 파일", "Ctrl+N", self.new_file))
        m_file.addAction(self._action("열기...", "Ctrl+O", self.open_file))
        m_file.addAction(self._action("폴더 열기...", "Ctrl+Shift+O", self.open_folder))
        m_file.addSeparator()
        m_file.addAction(self._action("저장", "Ctrl+S", self.save_file))
        m_file.addAction(self._action("다른 이름으로 저장...", "Ctrl+Shift+S", self.save_as))
        m_file.addSeparator()

        self.recent_menu = m_file.addMenu("최근 파일")
        self._rebuild_recent_menu()

        m_export = m_file.addMenu("내보내기")
        m_export.addAction(self._action("HTML로 내보내기...", "", self.export_html))
        m_export.addAction(self._action("PDF로 내보내기...", "", self.export_pdf))
        m_file.addSeparator()
        m_file.addAction(self._action("종료", "Ctrl+Q", self.close))

        m_view = mb.addMenu("&보기")
        self._action_dark = self._action("다크 모드", "Ctrl+D", self.toggle_dark)
        self._action_dark.setCheckable(True)
        self._action_dark.setChecked(self.dark_mode)
        m_view.addAction(self._action_dark)
        m_view.addAction(self._action("사이드바 토글", "Ctrl+B", self.toggle_sidebar))

        m_help = mb.addMenu("&도움말")
        m_help.addAction(self._action("정보", "", self.show_about))

    def _action(self, text: str, shortcut: str, slot) -> QAction:
        a = QAction(text, self)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        a.triggered.connect(slot)
        return a

    # --- File ops -----------------------------------------------------

    def new_file(self) -> None:
        if not self._confirm_discard():
            return
        self.current_file = None
        self.editor.load_markdown("")
        self._refresh_title()

    def open_file(self) -> None:
        if not self._confirm_discard():
            return
        start = str(self.current_file.parent if self.current_file else Path.home())
        path, _ = QFileDialog.getOpenFileName(self, "파일 열기", start, OPEN_FILTER)
        if path:
            self._load_path(Path(path))

    def open_folder(self) -> None:
        start = self.settings.value("folder", str(Path.home()))
        folder = QFileDialog.getExistingDirectory(self, "폴더 열기", start)
        if folder:
            self._set_folder(folder)

    def _set_folder(self, folder: str) -> None:
        self.fs_model.setRootPath(folder)
        self.tree.setRootIndex(self.fs_model.index(folder))
        self.settings.setValue("folder", folder)

    def _on_tree_clicked(self, index) -> None:
        # Single-click opens files. Folders just select / use disclosure
        # arrow to expand-collapse (Qt's default tree behavior).
        path = Path(self.fs_model.filePath(index))
        if path.is_file():
            if not self._confirm_discard():
                return
            self._load_path(path)

    def _load_path(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Windows 예전 파일 fallback
            text = path.read_text(encoding="cp949")
        # Normalize line endings so the wrap/unwrap regex behaves predictably.
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lang = CODE_FENCE_LANGS.get(path.suffix.lower())
        if lang:
            text = _wrap_as_code(text, lang)

        self.current_file = path
        self.editor.load_markdown(text)
        self._add_recent(path)
        self._reveal_in_tree(path)
        self.status.showMessage(f"{path} 열림", 4000)
        self._refresh_title()

    def _reveal_in_tree(self, path: Path) -> None:
        """연 파일을 사이드바 트리에 보여 준다.

        지금 트리 폴더 안이면 그 파일까지 펼쳐 선택하고, 밖이면 그 파일의 폴더를
        새 트리 루트로 삼는다(_set_folder 가 다음 실행용으로 기억).
        """
        if Path(self.fs_model.rootPath()) not in path.parents:
            self._set_folder(str(path.parent))
        index = self.fs_model.index(str(path))
        parent = index.parent()
        while parent.isValid() and parent != self.tree.rootIndex():
            self.tree.expand(parent)
            parent = parent.parent()
        self.tree.setCurrentIndex(index)
        self.tree.scrollTo(index)

    def save_file(self) -> None:
        if self.current_file is None:
            self.save_as()
            return
        self._write(self.current_file)

    def save_as(self) -> None:
        start = str(self.current_file if self.current_file else Path.home() / "untitled.md")
        path, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 저장", start,
            "Markdown (*.md);;텍스트 (*.txt);;YAML (*.yaml *.yml);;JSON (*.json);;모든 파일 (*)",
        )
        if path:
            p = Path(path)
            self.current_file = p
            self._write(p)
            self._add_recent(p)

    def _write(self, path: Path) -> None:
        text = self.editor.bridge.content()

        lang = CODE_FENCE_LANGS.get(path.suffix.lower())
        if lang:
            body, is_clean = _unwrap_code(text, lang)
            if is_clean:
                text = body
            else:
                # User added prose around (or removed) the fence. Saving as the
                # data extension would discard that prose or produce invalid
                # YAML/JSON. Offer to save as .md instead.
                md_path = path.with_suffix(".md")
                r = QMessageBox.question(
                    self,
                    "형식 부적합",
                    f"이 문서는 {path.suffix} 단일 코드블록 형식이 아닙니다.\n"
                    f"마크다운 형식으로 안전하게 저장하려면\n  {md_path.name}\n"
                    f"으로 저장하시겠습니까?\n\n"
                    f"(아니오: 그대로 {path.suffix}로 저장 — 외부 도구가 못 읽을 수 있음)",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes,
                )
                if r == QMessageBox.StandardButton.Cancel:
                    return
                if r == QMessageBox.StandardButton.Yes:
                    path = md_path
                    self.current_file = md_path
                    # text stays as-is (markdown body)

        path.write_text(text, encoding="utf-8")
        self.editor.bridge.mark_clean()
        self.status.showMessage(f"{path} 저장됨", 3000)
        self._refresh_title()

    # --- Export -------------------------------------------------------

    def export_html(self) -> None:
        default = (
            str(self.current_file.with_suffix(".html"))
            if self.current_file
            else str(Path.home() / "export.html")
        )
        path, _ = QFileDialog.getSaveFileName(self, "HTML 내보내기", default, "HTML (*.html)")
        if not path:
            return
        self._pending_html_path = path
        self.editor.bridge.htmlReady.connect(self._on_html_ready_once)
        self.editor.export_html_async()

    def _on_html_ready_once(self, html: str) -> None:
        try:
            self.editor.bridge.htmlReady.disconnect(self._on_html_ready_once)
        except TypeError:
            pass
        if not self._pending_html_path:
            return
        full = self._wrap_html_doc(html)
        Path(self._pending_html_path).write_text(full, encoding="utf-8")
        self.status.showMessage(f"{self._pending_html_path} 로 내보냄", 3000)
        self._pending_html_path = None

    def _wrap_html_doc(self, body: str) -> str:
        title = self.current_file.stem if self.current_file else "export"
        return (
            f'<!DOCTYPE html>\n<html lang="ko"><head><meta charset="UTF-8">'
            f"<title>{title}</title><style>"
            'body{font-family:"Malgun Gothic","맑은 고딕",sans-serif;'
            "max-width:820px;margin:2em auto;padding:0 1em;line-height:1.7;}"
            "pre{background:#f6f8fa;padding:1em;border-radius:6px;overflow:auto;}"
            "code{font-family:Consolas,Menlo,monospace;}"
            "table{border-collapse:collapse;}"
            "th,td{border:1px solid #ddd;padding:.4em .8em;}"
            "img{max-width:100%;}"
            f"</style></head><body>{body}</body></html>"
        )

    def export_pdf(self) -> None:
        default = (
            str(self.current_file.with_suffix(".pdf"))
            if self.current_file
            else str(Path.home() / "export.pdf")
        )
        path, _ = QFileDialog.getSaveFileName(self, "PDF 내보내기", default, "PDF (*.pdf)")
        if path:
            self.editor.export_pdf(path)
            self.status.showMessage(f"{path} 로 내보냄", 3000)

    # --- View ---------------------------------------------------------

    def toggle_dark(self) -> None:
        self.dark_mode = self._action_dark.isChecked()
        self.settings.setValue("dark_mode", self.dark_mode)
        self.editor.set_theme("dark" if self.dark_mode else "light")
        self._apply_theme()

    def toggle_sidebar(self) -> None:
        self.tree.setVisible(not self.tree.isVisible())

    def _send_initial_theme(self) -> None:
        if self.dark_mode:
            self.editor.set_theme("dark")

    def queue_open(self, path: Path) -> None:
        """Vditor 부팅 완료 후에 열도록 예약. argv로 파일 받았을 때 사용."""
        self._pending_open = path

    def _on_editor_ready(self) -> None:
        if self._pending_open is not None:
            path = self._pending_open
            self._pending_open = None
            self._load_path(path)

    def _apply_theme(self) -> None:
        if self.dark_mode:
            self.setStyleSheet(
                "QMainWindow,QWidget{background:#1e1e1e;color:#ddd;}"
                "QTreeView{background:#252526;color:#ddd;border:0;}"
                "QTreeView::item:selected{background:#094771;}"
                "QStatusBar{background:#007acc;color:white;}"
                "QMenuBar{background:#2d2d30;color:#ddd;}"
                "QMenuBar::item:selected{background:#094771;}"
                "QMenu{background:#2d2d30;color:#ddd;border:1px solid #3e3e42;}"
                "QMenu::item:selected{background:#094771;}"
            )
        else:
            self.setStyleSheet("")

    # --- Recent files -------------------------------------------------

    def _add_recent(self, path: Path) -> None:
        recents = self._recents()
        s = str(path)
        if s in recents:
            recents.remove(s)
        recents.insert(0, s)
        recents = recents[:MAX_RECENT]
        self.settings.setValue("recent", recents)
        self._rebuild_recent_menu()

    def _recents(self) -> list[str]:
        return list(self.settings.value("recent", []) or [])

    def _rebuild_recent_menu(self) -> None:
        self.recent_menu.clear()
        recents = self._recents()
        if not recents:
            a = self.recent_menu.addAction("(없음)")
            a.setEnabled(False)
            return
        for s in recents:
            a = self.recent_menu.addAction(s)
            a.triggered.connect(lambda checked=False, p=s: self._open_recent(p))
        self.recent_menu.addSeparator()
        clear = self.recent_menu.addAction("최근 파일 지우기")
        clear.triggered.connect(self._clear_recent)

    def _open_recent(self, path_str: str) -> None:
        if not self._confirm_discard():
            return
        p = Path(path_str)
        if not p.exists():
            QMessageBox.warning(self, "오류", f"파일을 찾을 수 없습니다:\n{p}")
            return
        self._load_path(p)

    def _clear_recent(self) -> None:
        self.settings.setValue("recent", [])
        self._rebuild_recent_menu()

    # --- Misc ---------------------------------------------------------

    def _refresh_title(self) -> None:
        name = self.current_file.name if self.current_file else "Untitled"
        dirty = "● " if self.editor.bridge.is_dirty() else ""
        self.setWindowTitle(f"{dirty}{name} — md-reader")

    def _confirm_discard(self) -> bool:
        if not self.editor.bridge.is_dirty():
            return True
        r = QMessageBox.question(
            self,
            "변경사항 저장",
            "저장되지 않은 변경사항이 있습니다. 저장할까요?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if r == QMessageBox.StandardButton.Cancel:
            return False
        if r == QMessageBox.StandardButton.Save:
            self.save_file()
        return True

    def closeEvent(self, e) -> None:
        if self._confirm_discard():
            e.accept()
        else:
            e.ignore()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "md-reader 정보",
            "<h3>md-reader v1.3.1</h3>"
            "<p>가벼운 Windows 마크다운 에디터<br>"
            "PyQt6 + Vditor (IR mode)</p>"
            "<p style='color:#666;font-size:11px;'>"
            "지원 형식: .md / .markdown / .txt / .yaml / .yml / .json"
            "</p>"
            "<hr>"
            "<p>EaglingSun</p>"
            "<p style='color:#666;font-size:11px;'>"
            "GPL-3.0 라이선스 · 어떠한 보증도 없음<br>"
            "소스: https://github.com/EaglingSun/md-reader"
            "</p>",
        )


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setOrganizationName(ORG)

    icon_file = _icon_path()
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    win = MainWindow()
    win.show()

    # Windows 파일 연결: 더블클릭 시 argv[1]로 경로가 들어옴
    if len(sys.argv) > 1:
        try:
            arg_path = Path(sys.argv[1]).resolve()
            if arg_path.is_file():
                win.queue_open(arg_path)
        except (OSError, ValueError):
            pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
