"""pytest 공통 설정.

- app/ 을 import 경로에 넣는다 (앱 모듈이 `from editor import ...` 처럼 평면 import 를 쓴다).
- MainWindow 를 띄우는 테스트는 실제 사용자 설정(HKCU\\Software\\EaglingSun\\MdReader)을
  건드리지 않도록 ORG 를 테스트 전용으로 바꾸고, 끝나면 값을 지운다(빈 키 HKCU\\Software\\EaglingSunTest 는
  남는다 — 창의 QSettings 가 살아 있는 동안 키를 지우면 위험하므로 그대로 둔다).
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

TEST_ORG = "EaglingSunTest"


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtCore import QSettings
    from PyQt6.QtWidgets import QApplication

    import main

    main.ORG = TEST_ORG
    # argv 가 비면 QtWebEngine(Chromium) 프로세스가 로그 없이 죽는다(exit 127) — argv[0] 은 넘긴다.
    app = QApplication.instance() or QApplication(sys.argv[:1])
    yield app
    QSettings(TEST_ORG, main.APP).clear()


@pytest.fixture
def window(qapp):
    import main

    win = main.MainWindow()
    yield win
    win.editor.bridge.mark_clean()
    win.close()
    win.deleteLater()
    # 이벤트 루프가 돌지 않으므로 deleteLater 를 여기서 실제로 처리한다. 안 하면 창(QWebEnginePage)이
    # 프로세스 끝까지 남아, 종료 때 QApplication · WebEngine 프로필이 먼저 정리되며 간헐 access violation.
    from PyQt6.QtCore import QCoreApplication, QEvent

    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
