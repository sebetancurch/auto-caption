@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
    echo Drag ^& drop a video or audio file onto this .bat to caption it.
    pause
    exit /b 1
)
for %%F in (%*) do (
    echo === Captioning %%~nxF ===
    ".venv\Scripts\python.exe" -m autocaption "%%~F"
)
pause
