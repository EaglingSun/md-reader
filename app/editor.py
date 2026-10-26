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
    file:// 페이지에서 CDN(https) 자원을 가져오려면
    LocalContentCanAccessRemoteUrls를 명시적으로 켜야 한다 (기본 False).
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

        html_path = _resource_path("web/editor.html")
        self.load(QUrl.fromLocalFile(str(html_path.resolve())))

    def load_markdown(self, text: str) -> None:
        self.bridge.reset_content(text)
        self.bridge.loadContent.emit(text)

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
        self.page().printToPdf(path)
