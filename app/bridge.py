from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class Bridge(QObject):
    """JS <-> Python 통신 다리 (QWebChannel).

    JS(Vditor)에서 변경 이벤트가 오면 _content/_html을 캐시한다.
    Python에서 파일 로드 시 loadContent를 emit하면 JS가 setValue 한다.
    """

    # (markdown, code_only, read_only)
    #   code_only — 문서 전체가 감싼 코드 펜스 하나 (YAML/JSON/TXT/코드). 긴 코드 스크롤 · 줄바꿈 CSS 를 켠다.
    #   read_only — 코드 · 패치 파일. Vditor 입력을 막는다 (테마 전환으로 다시 만들어도 유지).
    loadContent = pyqtSignal(str, bool, bool)
    requestSave = pyqtSignal()
    requestExportHTML = pyqtSignal()
    requestExportPDF = pyqtSignal()
    themeChanged = pyqtSignal(str)
    modeChanged = pyqtSignal(str)
    htmlReady = pyqtSignal(str)
    editorReady = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._content: str = ""
        self._html: str = ""
        self._dirty: bool = False

    @pyqtSlot(str)
    def onChange(self, markdown: str) -> None:
        self._content = markdown
        self._dirty = True

    @pyqtSlot(str)
    def onHTMLReady(self, html: str) -> None:
        self._html = html
        self.htmlReady.emit(html)

    def content(self) -> str:
        return self._content

    def html(self) -> str:
        return self._html

    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False

    def reset_content(self, markdown: str) -> None:
        """Python에서 문서를 열 때 호출 — 저장할 내용을 연 원문으로 맞추고 깨끗한 상태로 둔다.

        Vditor setValue 는 input 이벤트를 내지 않아(onChange 미호출), 이걸 안 하면
        열자마자 저장할 때 이전 문서(또는 빈 문자열)가 써진다.
        """
        self._content = markdown
        self._dirty = False

    @pyqtSlot()
    def onEditorReady(self) -> None:
        """Vditor `after:` 콜백에서 호출. 부팅 완료 신호."""
        self.editorReady.emit()
