@echo off
REM Build KlickTime.exe (run on Windows, in this agent folder)
echo Installing dependencies...
pip install -r requirements.txt
echo Building KlickTime.exe ...
pyinstaller --noconfirm --onefile --windowed --icon ke.ico --name KlickTime klicktime.py
echo.
echo Done. Your file is at:  dist\KlickTime.exe
echo Next: compile KlickTime.iss with Inno Setup to make KlickTimeSetup.exe
pause
