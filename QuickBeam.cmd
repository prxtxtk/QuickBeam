@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Prefer the folder build: it never extracts to TEMP, so it starts reliably
rem even on machines that lock down the temporary directory.
set "QB_EXE=%~dp0dist\onedir\quickbeam\quickbeam.exe"
if not exist "%QB_EXE%" set "QB_EXE=%~dp0onedir\quickbeam\quickbeam.exe"
if not exist "%QB_EXE%" set "QB_EXE=%~dp0quickbeam.exe"
if not exist "%QB_EXE%" set "QB_EXE=%~dp0dist\quickbeam.exe"
if not exist "%QB_EXE%" (
    echo [X] QuickBeam binary not found.
    echo     Build it first:  python scripts\build_binary.py
    echo     Or build the folder variant:  python scripts\build_binary.py --onedir
    echo.
    pause
    exit /b 1
)

rem Keep PyInstaller's runtime extraction inside this folder instead of %TEMP%.
set "QB_RUNTIME=%~dp0runtime"
if not exist "%QB_RUNTIME%" mkdir "%QB_RUNTIME%" >nul 2>&1
set "TEMP=%QB_RUNTIME%"
set "TMP=%QB_RUNTIME%"

echo ============================================================
echo  QuickBeam file bridge - keep this window open
echo ============================================================
echo.

"%QB_EXE%" %*
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" echo [!] QuickBeam exited with code %RC%.
pause
