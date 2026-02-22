@echo off
setlocal enableextensions

REM Ensure Python and pip
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

REM Build Windows app
pyinstaller --noconfirm --windowed --name Gripper-win ^
  --collect-all PySide6 ^
  --add-data "app;app" ^
  --add-data "domain;domain" ^
  --add-data "sim;sim" ^
  --add-data "persistence;persistence" ^
  main.py

REM Zip dist
powershell -NoProfile -Command "Compress-Archive -Path 'dist/Gripper-win/*' -DestinationPath 'dist/Gripper-win.zip' -Force"

echo Build completo. Zip em dist\Gripper-win.zip
endlocal

