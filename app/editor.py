import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView

from bridge import Bridge


def _resource_path(relative: str) -> Path:
    """Resolve a bundled resource path in both dev and PyInstaller-frozen modes.

    PyInstaller unpacks data files into sys._MEIPASS at runtime; in dev,
    files sit next to this source file.
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative


class MarkdownEditor(QWebEngineView):
    """Vditor를 호스팅하는 웹뷰.

    web/editor.html을 file:// URL로 로드하고, QWebChannel로 Bridge를 노출한다.
    Vditor 는 web/vendor/vditor (설치본 동봉)에서 file:// 로 읽는다.
    LocalContentCanAccessRemoteUrls 는 문서 안의 원격 이미지(https)를 보여 주려고 켜 둔다 (기본 False).
    """

    def __init__(self) -> None:
        super().__init__()
        self.bridge = Bridge()

        s = self.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)

        channel = QWebChannel(self.page())
        channel.registerObject("bridge", self.bridge)
        self.page().setWebChannel(channel)
        self.page().pdfPrintingFinished.connect(self._finish_print)

        html_path = _resource_path("web/editor.html")
        self.load(QUrl.fromLocalFile(str(html_path.resolve())))

    def load_markdown(self, text: str, code_only: bool = False, read_only: bool = False) -> None:
        self.bridge.reset_content(text)
        self.bridge.loadContent.emit(text, code_only, read_only)

    def request_save(self) -> None:
        self.bridge.requestSave.emit()

    def set_theme(self, theme: str) -> None:
        # "light" | "dark"
        self.bridge.themeChanged.emit(theme)

    def set_mode(self, mode: str) -> None:
        # "ir" | "wysiwyg" | "sv"
        self.bridge.modeChanged.emit(mode)

    def export_html_async(self) -> None:
        self.bridge.requestExportHTML.emit()

    def export_pdf(self, path: str) -> None:
        """인쇄용 줄 번호 사본을 만든 뒤(editor.js preparePrint) 인쇄하고, 끝나면 지운다(finishPrint).

        순서를 여기서 잡는 이유: beforeprint 에서 바꾼 DOM 은 printToPdf 결과에 들어가지 않는다(2026-11-01 실측).
        """
        page = self.page()

        def print_now(prepared) -> None:
            if not isinstance(prepared, (int, float)):
                # 사본을 못 만들었어도 PDF 는 낸다(본문은 다 들어간다) — 줄 번호만 화면 기준이 된다. 숨기지 않고 알린다.
                print(f"export_pdf: preparePrint 실패 ({prepared!r}) — 줄 번호 사본 없이 인쇄", file=sys.stderr)
            page.printToPdf(path)

        page.runJavaScript("preparePrint()", print_now)

    def _finish_print(self, _path: str, _ok: bool) -> None:
        self.page().runJavaScript("finishPrint()")
