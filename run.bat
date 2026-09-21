@echo off
title J.A.R.V.I.S. Desktop Voice Assistant
color 0B
echo ===================================================
echo     Launching J.A.R.V.I.S. Voice Assistant...
echo ===================================================
echo.

:: Detect Python executable
set "PY_CMD="

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=python"
    goto :found_python
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PY_CMD=py"
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    goto :found_python
)

if exist "%ProgramFiles%\Python311\python.exe" (
    set "PY_CMD=%ProgramFiles%\Python311\python.exe"
    goto :found_python
)

echo [ERROR] Python is not found on your system PATH!
echo.
echo Please install Python 3.11:
echo 1. Open PowerShell and run: winget install Python.Python.3.11
echo    OR download from https://www.python.org/downloads/
echo 2. Check the box "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found_python
echo Using Python launcher: %PY_CMD%
echo.

:: Launch Jarvis Main Entrypoint
"%PY_CMD%" main.py

if %errorlevel% neq 0 (
    echo.
    echo Jarvis exited with code: %errorlevel%
    pause
)
