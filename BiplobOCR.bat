@echo off
REM BiplobOCR Launcher
REM This batch file ensures proper working directory and Python execution

cd /d "%~dp0"
py "%~dp0run.py" %*
