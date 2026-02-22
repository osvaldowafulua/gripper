from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QGridLayout, QTextEdit, QFrame, QSpacerItem, QSizePolicy
)
from domain.models import ProjectConfig, SimulationParams
from sim.state_machine import StateMachine


class SimulatorView(QWidget):
    def __init__(self, project: ProjectConfig):
        super().__init__()
        self.project = project
        self.engine = StateMachine(project.params)

        root = QVBoxLayout(self)

        # Panel: Controls
        pnl_ctrl = QFrame(); pnl_ctrl.setObjectName("panel")
        lay_ctrl = QHBoxLayout(pnl_ctrl)
        lay_ctrl.addItem(QSpacerItem(10,10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        self.btn_start = QPushButton("S"); self.btn_start.setObjectName("btnStart"); self.btn_start.setProperty("round", True)
        self.btn_stop = QPushButton("P"); self.btn_stop.setObjectName("btnStop"); self.btn_stop.setProperty("round", True)
        self.btn_reset = QPushButton("R"); self.btn_reset.setObjectName("btnReset"); self.btn_reset.setProperty("round", True)
        self.btn_emg = QPushButton("E"); self.btn_emg.setObjectName("btnEmg"); self.btn_emg.setProperty("round", True)
        lay_ctrl.addWidget(self.btn_start)
        lay_ctrl.addWidget(self.btn_stop)
        lay_ctrl.addWidget(self.btn_reset)
        lay_ctrl.addWidget(self.btn_emg)
        lay_ctrl.addItem(QSpacerItem(10,10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        root.addWidget(pnl_ctrl)

        # Panel: Lamps + State
        pnl_status = QFrame(); pnl_status.setObjectName("panel")
        lay_status = QVBoxLayout(pnl_status)
        title = QLabel("ESTADO"); title.setProperty("class", "section")
        lay_status.addWidget(title)
        row = QHBoxLayout()
        self.lamp_ready = QLabel(); self._init_lamp(self.lamp_ready, "ready")
        self.lamp_run = QLabel(); self._init_lamp(self.lamp_run, "run")
        self.lamp_stop = QLabel(); self._init_lamp(self.lamp_stop, "stop")
        self.lamp_lock = QLabel(); self._init_lamp(self.lamp_lock, "lock")
        row.addWidget(self.lamp_ready); row.addWidget(QLabel("READY"))
        row.addWidget(self.lamp_run); row.addWidget(QLabel("RUN"))
        row.addWidget(self.lamp_stop); row.addWidget(QLabel("STOP"))
        row.addWidget(self.lamp_lock); row.addWidget(QLabel("LOCK"))
        lay_status.addLayout(row)
        self.lbl_state = QLabel("STATE=")
        lay_status.addWidget(self.lbl_state)
        root.addWidget(pnl_status)

        # Panel: Sensors
        pnl_sens = QFrame(); pnl_sens.setObjectName("panel")
        lay_sens = QVBoxLayout(pnl_sens)
        lay_sens.addWidget(self._section("SENSORES"))
        row_s = QHBoxLayout()
        self.cb_s11 = QCheckBox("S1.1 FECHADO")
        self.cb_s20 = QCheckBox("S2.0 CIMA")
        self.cb_s21 = QCheckBox("S2.1 BAIXO")
        self.cb_start = QCheckBox("START (I6)")
        self.cb_stop = QCheckBox("STOP (I5)")
        self.cb_emg = QCheckBox("EMERGÊNCIA (I7)")
        self.cb_tune = QCheckBox("TUNE (I8)")
        for w in [self.cb_s11,self.cb_s20,self.cb_s21,self.cb_stop,self.cb_start,self.cb_emg,self.cb_tune]:
            row_s.addWidget(w)
        lay_sens.addLayout(row_s)
        root.addWidget(pnl_sens)

        # Panel: IO tiles
        pnl_io = QFrame(); pnl_io.setObjectName("panel")
        lay_io = QVBoxLayout(pnl_io)
        lay_io.addWidget(self._section("SAÍDAS / ENTRADAS"))
        grid_io = QGridLayout(); grid_io.setHorizontalSpacing(8); grid_io.setVerticalSpacing(8)
        self.tiles_q = []
        for c in range(7):
            lbl = QLabel(f"Q{c+1}"); lbl.setObjectName("tile")
            grid_io.addWidget(lbl, 0, c)
            self.tiles_q.append(lbl)
        self.tiles_i = []
        for c in range(8):
            lbl = QLabel(f"I{c+1}"); lbl.setObjectName("tile")
            grid_io.addWidget(lbl, 1 + c // 4, c % 4)
            self.tiles_i.append(lbl)
        lay_io.addLayout(grid_io)
        root.addWidget(pnl_io)

        # Panel: Log
        pnl_log = QFrame(); pnl_log.setObjectName("panel")
        lay_log = QVBoxLayout(pnl_log)
        lay_log.addWidget(self._section("DIAGNÓSTICO"))
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True)
        lay_log.addWidget(self.txt_log)
        root.addWidget(pnl_log)

        self.btn_start.clicked.connect(self._start)
        self.btn_emg.clicked.connect(self._toggle_emg)
        self.btn_reset.clicked.connect(self._reset)
        self.btn_stop.clicked.connect(self._stop)

        for cb, name in [
            (self.cb_s11, "S1.1"), (self.cb_s20, "S2.0"), (self.cb_s21, "S2.1"),
            (self.cb_start, "START"), (self.cb_stop, "STOP"), (self.cb_emg, "EMERGENCIA"), (self.cb_tune, "TUNE")
        ]:
            cb.stateChanged.connect(lambda _=0, n=name, c=cb: self.engine.set_sensor(n, c.isChecked()))

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(lambda: self._tick(100))
        self.timer.start()

    def set_project(self, p: ProjectConfig):
        self.project = p
        self.engine = StateMachine(p.params)

    def _start(self):
        self.engine.press_start()

    def _toggle_emg(self):
        # alterna emergência (latching na lógica)
        cur = self.engine.s.inputs.get("I7", False)
        self.engine.set_emergency(not cur)

    def _reset(self):
        self.engine.reset_lock()

    def _stop(self):
        self.engine.stop()

    def _tick(self, dt):
        self.engine.tick(dt)
        self._refresh()

    def _refresh(self):
        s = self.engine.s
        diag = self.engine.diag_line()
        self.lbl_state.setText(diag)
        f = self.engine.panel_flags()
        self._set_lamp(self.lamp_ready, f["READY"]) 
        self._set_lamp(self.lamp_run, f["RUN"]) 
        self._set_lamp(self.lamp_stop, f["STOP"]) 
        self._set_lamp(self.lamp_lock, f["EMERGENCY_LOCKED"]) 
        # IO tiles
        for idx in range(7):
            on = bool(s.outputs[f"Q{idx+1}"])
            self.tiles_q[idx].setProperty("on", on)
            self.tiles_q[idx].style().unpolish(self.tiles_q[idx]); self.tiles_q[idx].style().polish(self.tiles_q[idx])
            self.tiles_q[idx].setText(f"Q{idx+1}: {int(on)}")
        for idx in range(8):
            on = bool(s.inputs[f"I{idx+1}"])
            self.tiles_i[idx].setProperty("on", on)
            self.tiles_i[idx].style().unpolish(self.tiles_i[idx]); self.tiles_i[idx].style().polish(self.tiles_i[idx])
            self.tiles_i[idx].setText(f"I{idx+1}: {int(on)}")
        if len(self.txt_log.toPlainText().splitlines()) > 200:
            self.txt_log.clear()
        self.txt_log.append(diag)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "section")
        return lbl

    def _init_lamp(self, lbl: QLabel, lamp_type: str):
        lbl.setProperty("lamp", True)
        lbl.setProperty("lampType", lamp_type)
        lbl.setProperty("on", False)
        lbl.setFixedSize(22, 22)

    def _set_lamp(self, lbl: QLabel, on: bool):
        lbl.setProperty("on", bool(on))
        lbl.style().unpolish(lbl); lbl.style().polish(lbl)
