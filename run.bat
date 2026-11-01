@echo off
REM AI_docs reader dev launcher (uses installed Python).
REM End users should install via the .exe installer instead.
setlocal
set PY=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe
if not exist "%PY%" set PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
REM Bundled Vditor (app\web\vendor) is not in git - fetch it once (pinned version, sha512 checked).
if not exist "%~dp0app\web\vendor\vditor\dist\index.min.js" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%~dp0packaging\fetch_vditor.py" || exit /b 1
)
"%PY%" "%~dp0app\main.py" %*
endlocal
