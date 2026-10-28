@echo off
REM BorrowBetter launcher for Windows.
REM Keep this file ASCII-only: cmd.exe parses .cmd files with the OEM code page,
REM so non-ASCII text breaks the parser.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py %*
) else (
    echo [!] .venv not found - falling back to the system Python.
    echo     If dependencies are missing, run:
    echo         python -m venv .venv
    echo         .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    python run.py %*
)

REM Pause only for double-click usage (no arguments), not for CLI calls.
if "%~1"=="" pause
endlocal
