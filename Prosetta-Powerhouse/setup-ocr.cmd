@echo off
setlocal
cd /d "%~dp0"
set "RITU_ENV=%~dp0..\ocr-env"
set "PIP_CACHE_DIR=%~dp0..\pip-cache"
set "RITU_BOOTSTRAP=C:\Users\Prashant Sharma\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%RITU_BOOTSTRAP%" (
  echo Python bootstrap runtime was not found.
  pause
  exit /b 1
)
if not exist "%RITU_ENV%\Scripts\python.exe" (
  "%RITU_BOOTSTRAP%" -m venv "%RITU_ENV%"
)
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
"%RITU_ENV%\Scripts\python.exe" -m pip install --upgrade pip
"%RITU_ENV%\Scripts\python.exe" -m pip install -r requirements-ocr.txt
echo.
echo RapidOCR is ready. Start Ritu with start-ritu.cmd
pause
