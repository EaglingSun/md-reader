@echo off
REM md-reader dev launcher (uses installed Python).
REM End users should install via the .exe installer instead.
setlocal
set PY=%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe
if not exist "%PY%" set PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
"%PY%" "%~dp0app\main.py" %*
endlocal
