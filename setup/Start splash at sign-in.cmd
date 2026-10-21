@echo off
rem Registers a Task Scheduler task that plays the splash the moment you sign in.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0splash_task.ps1"
if errorlevel 1 (
  echo.
  echo That needs administrator rights. Right-click this file and choose "Run as administrator".
)
pause
