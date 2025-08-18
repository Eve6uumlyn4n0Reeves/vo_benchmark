@echo off

echo VO-Benchmark Quick Start
echo =========================

powershell.exe -NoLogo -ExecutionPolicy Bypass -File "%~dp0start_win.ps1"

if errorlevel 1 (
  echo.
  echo Script failed. Try running manually:
  echo powershell -ExecutionPolicy Bypass -File "%~dp0start_win.ps1"
  pause
)

pause
