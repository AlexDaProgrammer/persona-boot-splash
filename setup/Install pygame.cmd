@echo off
rem One-time install of pygame-ce, which draws the animation.
set "PY=%LOCALAPPDATA%\Programs\Thonny\python.exe"
if not exist "%PY%" set "PY=python"
echo Installing pygame-ce...
"%PY%" -m pip install -r "%~dp0..\requirements.txt"
echo.
echo Done. Double-click launchers\Boot Splash.vbs to try it.
pause
