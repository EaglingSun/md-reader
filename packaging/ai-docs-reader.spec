# PyInstaller spec for AI_docs reader (formerly md-reader).
# Run from project root: pyinstaller packaging/ai-docs-reader.spec
# Output: dist/ai-docs-reader/ai-docs-reader.exe (folder bundle, ~150 MB).

import os

# SPECPATH is provided by PyInstaller and points to the directory of this spec.
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
APP = os.path.join(ROOT, "app")
ICON = os.path.join(APP, "assets", "icon.ico")

block_cipher = None

a = Analysis(
    [os.path.join(APP, "main.py")],
    pathex=[APP],
    binaries=[],
    datas=[
        # Bundle the web/ directory at the bundle root so editor.py's
        # _resource_path("web/editor.html") resolves under sys._MEIPASS.
        (os.path.join(APP, "web"), "web"),
        # Bundle assets so the runtime QApplication.setWindowIcon can find icon.ico.
        (os.path.join(APP, "assets"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ai-docs-reader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,        # GUI app - no console window flash
    icon=ICON,            # app/assets/icon.ico (multi-size)
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ai-docs-reader",
)
