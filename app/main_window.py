from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
import urllib.request, json
from app.style import industrial_dark_stylesheet
from app.views.map_view import MapView
from app.views.simulator_view import SimulatorView
from app.views.export_view import ExportView
from app.views.protections_view import ProtectionsView
from app.views.config_view import ConfigView
from domain.models import default_project


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Opta WiFi + A0602 – Simulador/Documentador")
        self.resize(1100, 720)
        self.project = default_project()

        self.setStyleSheet(industrial_dark_stylesheet())

        container = QWidget()
        vbox = QVBoxLayout(container)

        # Header
        self.header = QFrame(); self.header.setObjectName("panel")
        h = QHBoxLayout(self.header)
        left = QVBoxLayout()
        self.lbl_title = QLabel("Opta WiFi + A0602"); left.addWidget(self.lbl_title)
        self.lbl_sub = QLabel("Painel Industrial de Simulação"); left.addWidget(self.lbl_sub)
        h.addLayout(left)
        self.lbl_mode = QLabel("Simulação Local"); h.addWidget(self.lbl_mode)
        self.lbl_conn = QLabel("Conexão: OFFLINE"); h.addWidget(self.lbl_conn)
        self.lbl_wifi_opta = QLabel("WiFi OPTA — ---- / N/D"); h.addWidget(self.lbl_wifi_opta)
        self.lbl_wifi_app = QLabel("WiFi APP — ---- / N/D"); h.addWidget(self.lbl_wifi_app)
        vbox.addWidget(self.header)

        self.tabs = QTabWidget()
        vbox.addWidget(self.tabs)
        self.setCentralWidget(container)

        self.map_view = MapView(self.project)
        self.sim_view = SimulatorView(self.project)
        self.export_view = ExportView(self.project)
        self.prot_view = ProtectionsView(self.project)

        self.config_view = ConfigView()
        self.tabs.addTab(self.config_view, "Configurações")
        self.tabs.addTab(self.map_view, "Mapa de Ligações")
        self.tabs.addTab(self.sim_view, "Simulador")
        self.tabs.addTab(self.export_view, "Exportar Manual (PDF)")
        self.tabs.addTab(self.prot_view, "Proteções")

        self.map_view.projectChanged.connect(self._on_project_changed)
        self.prot_view.projectChanged.connect(self._on_project_changed)

        # Timer para atualizar header com estado do servidor local (HTTP)
        self._timer = QTimer(self); self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_header)
        self._timer.start()

    def _on_project_changed(self, p):
        self.project = p
        self.sim_view.set_project(p)
        self.export_view.set_project(p)
        self.prot_view.set_project(p)

    def _refresh_header(self):
        try:
            with urllib.request.urlopen("http://localhost:8000/api/state", timeout=1.0) as r:
                s = json.loads(r.read().decode("utf-8"))
        except Exception:
            self.lbl_conn.setText("Conexão: OFFLINE")
            self.lbl_mode.setText("Simulação Local")
            self.lbl_wifi_opta.setText("WiFi OPTA — ---- / N/D")
            self.lbl_wifi_app.setText("WiFi APP — ---- / N/D")
            return
        mode = s.get("mode","sim"); base = s.get("remote_base","")
        self.lbl_conn.setText("Conexão: ONLINE")
        self.lbl_mode.setText("Opta via IP" if mode=="proxy" else ("Modbus TCP" if mode=="modbus" else "Simulação Local"))
        wifi = s.get("wifi",{})
        def bars(q):
            m={0:'----',1:'▂---',2:'▂▄--',3:'▂▄▆-',4:'▂▄▆█'}; return m.get(int(q) if isinstance(q,int) else 0,'----')
        opta_bar = bars(wifi.get("opta_quality"))
        app_bar = bars(wifi.get("app_quality"))
        opta_val = f"{wifi.get('opta_rssi')} dBm" if wifi.get('opta_rssi') is not None else (f"{wifi.get('opta_latency_ms')} ms" if wifi.get('opta_latency_ms') is not None else 'N/D')
        app_val = f"{wifi.get('app_rssi')} dBm" if wifi.get('app_rssi') is not None else 'N/D'
        self.lbl_wifi_opta.setText(f"WiFi OPTA — {opta_bar} / {opta_val}")
        self.lbl_wifi_app.setText(f"WiFi APP — {app_bar} / {app_val}")
