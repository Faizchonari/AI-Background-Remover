@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo Running AI Background Remover Test Suite
echo =======================================================

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe.
    exit /b 1
)

echo Running unit tests with unittest...
.\.venv\Scripts\python.exe -m unittest discover -s tests -v

if %errorlevel% neq 0 (
    echo [ERROR] Tests failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] All tests passed successfully.
echo =======================================================
