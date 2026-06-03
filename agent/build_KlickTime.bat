@echo off
REM Build KlickTime as a single-process one-folder app (run on Windows, in this agent folder)
echo Installing dependencies...
pip install -r requirements.txt
echo Building KlickTime (one folder, single process) ...
pyinstaller --noconfirm --onedir --windowed --icon ke.ico --name KlickTime klicktime.py
echo.
echo Done. Your program folder is: dist\KlickTime\  (run dist\KlickTime\KlickTime.exe)
echo Next: compile KlickTime.iss with Inno Setup to make KlickTimeSetup.exe
pause
