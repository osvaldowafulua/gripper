#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install --no-compile -r requirements.txt pyinstaller

PYTHONDONTWRITEBYTECODE=1 python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --name Gripper \
  --collect-all PySide6 \
  main.py

echo "Build concluído: dist/Gripper.app"
