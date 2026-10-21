@echo off
rem Plays the splash with a console window so any error is visible.
set "PY=%LOCALAPPDATA%\Programs\Thonny\python.exe"
if not exist "%PY%" set "PY=python"
echo Running the startup splash in test mode...
"%PY%" "%~dp0..\src\boot_animation.pyw"
echo.
echo Finished. If there is an error above, it explains what went wrong.
pause
