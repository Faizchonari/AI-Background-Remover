@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo Building AI Background Remover Standalone Executable
echo =======================================================

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe.
    echo Please create the virtual environment and install requirements first.
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Running PyInstaller...
pyinstaller ai_background_remover.spec --noconfirm --clean

if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Application built successfully in dist\AI-Background-Remover\
echo =======================================================
