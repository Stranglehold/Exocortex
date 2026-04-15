@echo off
REM Exocortex Host Control Daemon launcher
REM Uses the miniconda Python that ships with the host environment.

set DAEMON_DIR=%~dp0
set PYTHON=C:\Users\Jake\miniconda3\python.exe

if not exist "%PYTHON%" (
    echo ERROR: Python not found at %PYTHON%
    echo Edit this file to point at your Python interpreter.
    pause
    exit /b 1
)

echo Starting Exocortex host control daemon...
echo Press Ctrl+C to stop.
echo.
"%PYTHON%" "%DAEMON_DIR%host_daemon.py"
