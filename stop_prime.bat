@echo off
echo Shutting down IP Prime...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
taskkill /F /IM electron.exe /T 2>nul
echo Done. All IP Prime processes stopped.
pause
