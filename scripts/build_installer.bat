@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo Building AI Background Remover Windows Installer
echo =======================================================

cd /d "%~dp0\.."

set "ISCC="

if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>nul
    if !errorlevel! equ 0 (
        set "ISCC=iscc"
    )
)

if "%ISCC%"=="" (
    echo [ERROR] Inno Setup 6 (ISCC.exe) was not found.
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    exit /b 1
)

if not exist "dist\AI-Background-Remover\AI-Background-Remover.exe" (
    echo [WARNING] dist\AI-Background-Remover\AI-Background-Remover.exe not found.
    echo Building executable first...
    call "%~dp0build_executable.bat"
    if !errorlevel! neq 0 exit /b !errorlevel!
)

if not exist "release" mkdir release

echo Compiling installer using: "%ISCC%"
"%ISCC%" "installer\inno_setup_script.iss"

if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed with exit code %errorlevel%.
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Windows installer generated in release\AI-Background-Remover-Setup.exe
echo =======================================================
