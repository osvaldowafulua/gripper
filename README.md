# Gripper – Painel Opta WiFi + A0602

Aplicação industrial (painel web + app desktop) para operar e monitorizar um sistema com Arduino Opta WiFi e expansão A0602. Inclui simulação local, proxy HTTP ao sketch e integração Modbus TCP.

## Funcionalidades
- Painel web em `http://localhost:8000/` com:
  - Controlo START/STOP/RESET/EMERGÊNCIA
  - Sensores e saídas (I1..I8, Q1..Q7)
  - “Conectar Opta” (auto‑detecta HTTP do sketch ou Modbus TCP)
  - Indicadores Wi‑Fi: barras e dBm (App) e latência/RSSI do Opta
  - Parâmetros do ciclo com unidades (seg/ms/min) e PRESET
- App macOS (PySide6 + PyInstaller): DMG pronto em `dist/`
- Build Windows via GitHub Actions e scripts locais

## Arranque rápido (web)
```bash
python -m web.server
# abrir no browser
http://localhost:8000/
```

## macOS – App Desktop
- Builds em `dist/Gripper-v*.app` e DMG `dist/Gripper-v*.dmg`
- Primeira execução: clique direito → Abrir (Gatekeeper)
- Logs: `~/Library/Logs/Gripper/app.log`
- DB: `~/Library/Application Support/Gripper/gripper.db`

## Windows – Executável
- CI: GitHub Actions workflow `.github/workflows/build-windows.yml`
  - Saída: artifact `Gripper-win.zip`
- Local (PowerShell em Windows):
```powershell
scripts\build-windows.ps1
# zip em dist\Gripper-win.zip
```

## Integração com o Opta
- Modo HTTP: o sketch deve expor JSON em `http://<IP>/` com `state, cycles, emg, latched, step, sacode, toggle, max` (opcional `rssi`)
- Modo Modbus TCP (porta 502):
  - Snapshot: HR0..63
  - HR9 = inputs bitmask (I1..I8), HR10 = outputs bitmask (Q1..Q4)
  - Setpoints: HR20..23; PRESET: HR24
  - Coils: C0 start, C1 stop, C2 reset, C4 aplicar ciclo, C5 aplicar geral

## Estrutura
- `web/` servidor + UI web
- `app/` app PySide6 (tabs: Configurações, Mapa X1/X2, Simulador, Exportar PDF, Proteções)
- `sim/` máquina de estados e simulação
- `persistence/` JSON/SQLite

## Publicação no GitHub
1. Inicializar git e commit:
```bash
git init -b main
git add .
git commit -m "Release inicial: v4 macOS, painel web, Modbus, CI Windows"
```
2. Criar repositório no GitHub e associar:
```bash
git remote add origin https://github.com/<seu-usuario>/<seu-repo>.git
git push -u origin main
```
3. Ação “build-windows” nas Actions gerará `Gripper-win.zip` como artefacto.

## Licença
Defina aqui a licença (MIT/GPL/Proprietária).

