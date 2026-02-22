Param()
$ErrorActionPreference = 'Stop'

py -m pip install --upgrade pip
py -m pip install -r requirements.txt pyinstaller

py -m PyInstaller `
  --noconfirm `
  --windowed `
  --name Gripper `
  --collect-all PySide6 `
  main.py

Write-Host "Build concluído: dist/Gripper.exe"

