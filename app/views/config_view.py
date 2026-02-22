from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QLabel, QLineEdit,
    QComboBox, QPushButton, QGridLayout, QDoubleSpinBox
)
import urllib.request
import json


def _api(path: str, payload: dict | None = None):
    try:
        if payload is None:
            with urllib.request.urlopen(f"http://localhost:8000{path}", timeout=1.5) as r:
                return json.loads(r.read().decode("utf-8"))
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"http://localhost:8000{path}", data=data,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


class ConfigView(QWidget):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)

        card_net = QFrame(); card_net.setObjectName("panel")
        lay_net = QFormLayout(card_net)
        self.cmb_mode = QComboBox(); self.cmb_mode.addItems(["sim","proxy","modbus"])
        self.ed_base = QLineEdit(); self.ed_base.setPlaceholderText("http://192.168.0.10/ ou 192.168.0.10:502")
        lay_net.addRow(QLabel("Modo API"), self.cmb_mode)
        lay_net.addRow(QLabel("Base/IP"), self.ed_base)
        row_btns = QHBoxLayout()
        self.btn_apply = QPushButton("Aplicar Rede")
        self.btn_connect = QPushButton("Conectar Opta")
        self.lbl_net = QLabel("")
        row_btns.addWidget(self.btn_apply)
        row_btns.addWidget(self.btn_connect)
        row_btns.addWidget(self.lbl_net)
        lay_net.addRow(row_btns)

        card_par = QFrame(); card_par.setObjectName("panel")
        lay_par = QGridLayout(card_par)
        self.spin_step = QDoubleSpinBox(); self.spin_step.setRange(0.1, 1200.0); self.spin_step.setSingleStep(0.1); self.spin_step.setValue(5.0)
        self.unit_step = QComboBox(); self.unit_step.addItems(["seg","ms","min"])
        self.spin_sac = QDoubleSpinBox(); self.spin_sac.setRange(0.1, 3600.0); self.spin_sac.setSingleStep(0.1); self.spin_sac.setValue(5.0)
        self.unit_sac = QComboBox(); self.unit_sac.addItems(["seg","ms","min"])
        self.spin_move = QDoubleSpinBox(); self.spin_move.setRange(0.05, 60.0); self.spin_move.setSingleStep(0.05); self.spin_move.setValue(0.9)
        self.unit_move = QComboBox(); self.unit_move.addItems(["seg","ms","min"])
        self.spin_max = QDoubleSpinBox(); self.spin_max.setRange(1.0, 3600.0); self.spin_max.setSingleStep(0.1); self.spin_max.setValue(25.0)
        self.unit_max = QComboBox(); self.unit_max.addItems(["seg","ms","min"])
        self.cmb_preset = QComboBox(); self.cmb_preset.addItems(["0 (LENTO)","1 (NORMAL)","2 (RÁPIDO)"])
        self.btn_apply_cycle = QPushButton("Aplicar Ciclo")
        self.btn_apply_all = QPushButton("APLICAR GERAL")
        self.lbl_par = QLabel("")
        r = 0
        lay_par.addWidget(QLabel("STEP"), r, 0); lay_par.addWidget(self.spin_step, r, 1); lay_par.addWidget(self.unit_step, r, 2); r += 1
        lay_par.addWidget(QLabel("SACODE"), r, 0); lay_par.addWidget(self.spin_sac, r, 1); lay_par.addWidget(self.unit_sac, r, 2); r += 1
        lay_par.addWidget(QLabel("MOVE TIMEOUT"), r, 0); lay_par.addWidget(self.spin_move, r, 1); lay_par.addWidget(self.unit_move, r, 2); r += 1
        lay_par.addWidget(QLabel("MAX CYCLE"), r, 0); lay_par.addWidget(self.spin_max, r, 1); lay_par.addWidget(self.unit_max, r, 2); r += 1
        lay_par.addWidget(QLabel("PRESET"), r, 0); lay_par.addWidget(self.cmb_preset, r, 1, 1, 2); r += 1
        lay_par.addWidget(self.btn_apply_cycle, r, 0); lay_par.addWidget(self.btn_apply_all, r, 1); lay_par.addWidget(self.lbl_par, r, 2); r += 1

        row = QHBoxLayout(); row.addWidget(card_net); row.addWidget(card_par)
        root.addLayout(row)

        self.btn_apply.clicked.connect(self._apply_net)
        self.btn_connect.clicked.connect(self._connect_opta)
        self.btn_apply_cycle.clicked.connect(lambda: self._apply_params(False))
        self.btn_apply_all.clicked.connect(lambda: self._apply_params(True))

        self._load_settings()

    def _to_ms(self, value: float, unit_cb: QComboBox) -> int:
        u = unit_cb.currentText()
        if u == "seg":
            return int(round(value * 1000))
        if u == "min":
            return int(round(value * 60000))
        return int(round(value))

    def _load_settings(self):
        s = _api("/api/settings")
        if not s:
            return
        self.cmb_mode.setCurrentText(s.get("mode", "sim"))
        self.ed_base.setText(s.get("remote_base", ""))
        p = s.get("params", {})
        # convert ms -> seg por padrão
        self.spin_step.setValue(max(0.1, (p.get("STEP_MS", 5000))/1000))
        self.spin_sac.setValue(max(0.1, (p.get("SACODE_MS", 5000))/1000))
        self.spin_move.setValue(max(0.05, (p.get("MOVE_TIMEOUT_MS", 900))/1000))
        self.spin_max.setValue(max(1.0, (p.get("MAX_CYCLE_MS", 25000))/1000))
        self.unit_step.setCurrentText("seg"); self.unit_sac.setCurrentText("seg"); self.unit_move.setCurrentText("seg"); self.unit_max.setCurrentText("seg")

    def _apply_net(self):
        mode = self.cmb_mode.currentText()
        base = self.ed_base.text().strip()
        res = _api("/api/settings", {"mode": mode, "remote_base": base})
        self.lbl_net.setText("Salvo" if res and res.get("ok") else "Erro")

    def _connect_opta(self):
        base = self.ed_base.text().strip()
        pr = _api("/api/probe", {"base": base})
        if not pr or not pr.get("ok"):
            self.lbl_net.setText("Falha")
            return
        mode = pr.get("mode"); rb = pr.get("base")
        s1 = _api("/api/settings", {"mode": mode, "remote_base": rb})
        self.cmb_mode.setCurrentText(mode)
        self.ed_base.setText(rb)
        self.lbl_net.setText("Conectado via HTTP" if mode == "proxy" else "Conectado via Modbus")

    def _apply_params(self, apply_all: bool):
        body = {
            "STEP_MS": self._to_ms(self.spin_step.value(), self.unit_step),
            "SACODE_MS": self._to_ms(self.spin_sac.value(), self.unit_sac),
            "MOVE_TIMEOUT_MS": self._to_ms(self.spin_move.value(), self.unit_move),
            "MAX_CYCLE_MS": self._to_ms(self.spin_max.value(), self.unit_max),
        }
        if apply_all:
            body["PRESET"] = int(self.cmb_preset.currentText().split(" ")[0])
        r = _api("/api/params", body)
        self.lbl_par.setText("Aplicado" if r and r.get("ok") else "Erro")

