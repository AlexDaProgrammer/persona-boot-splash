@echo off
rem Removes the sign-in task. The files stay where they are.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0splash_task.ps1" -Remove
pause
