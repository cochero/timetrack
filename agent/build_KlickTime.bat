@echo off
REM Build KlickTime.exe (run this on Windows, in the agent folder)
echo Installing dependencies...
pip install -r requirements.txt
echo Building KlickTime.exe ...
pyinstaller --noconfirm --onefile --windowed --name KlickTime klicktime.py
echo.
echo Done. Your file is at:  dist\KlickTime.exe
echo (Copy KlickTime.exe and config.json next to it onto each employee PC.)
pause
