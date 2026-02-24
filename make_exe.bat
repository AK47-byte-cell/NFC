@echo off
setlocal

cd /d %~dp0

py -m pip install --upgrade pip
py -m pip install faster-whisper pyinstaller
py BuildStandaloneExe.py

if %ERRORLEVEL% neq 0 (
  echo.
  echo Build failed.
  exit /b %ERRORLEVEL%
)

echo.
echo Build complete. EXE folder: %~dp0dist\AudioTranscriber
endlocal
