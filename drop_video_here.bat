@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
    echo Drag ^& drop a video or audio file onto this .bat to caption it.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" goto :process

echo ================================================
echo   auto-caption - first-time setup
echo   Installing... this takes a few minutes.
echo ================================================
echo.

set "PY_CMD="
py -3 --version >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD (
    python --version >nul 2>nul && set "PY_CMD=python"
)
if not defined PY_CMD (
    echo Python was not found on this computer.
    echo.
    echo   1. Install it from https://www.python.org/downloads/
    echo      IMPORTANT: tick "Add python.exe to PATH" in the installer
    echo   2. Try again
    echo.
    pause
    exit /b 1
)

%PY_CMD% -m venv .venv
if errorlevel 1 (
    echo.
    echo Could not create the Python environment. See the messages above.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
echo Downloading and installing components...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo.
    echo Install failed. See the messages above.
    pause
    exit /b 1
)
echo.

:process
for %%F in (%*) do (
    echo === Captioning %%~nxF ===
    ".venv\Scripts\python.exe" -m autocaption "%%~F"
)
pause
