$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --windowed --name Gripper-win `
  --collect-all PySide6 `
  --add-data "app;app" `
  --add-data "domain;domain" `
  --add-data "sim;sim" `
  --add-data "persistence;persistence" `
  main.py

Compress-Archive -Path "dist/Gripper-win/*" -DestinationPath "dist/Gripper-win.zip" -Force
Write-Host "Build completo. Zip: dist/Gripper-win.zip"

