@echo off
setlocal
cd /d "%~dp0..\.."

set BUNDLED_PYTHON=src\python\windows\python.exe

if exist "%BUNDLED_PYTHON%" (
    "%BUNDLED_PYTHON%" run.py %*
) else (
    py run.py %*
)
endlocal
