from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QFileDialog, QLabel
from domain.models import ProjectConfig, IOItem, IOType, ColorsWiring
from persistence.json_io import export_json, import_json
from persistence.sqlite_repo import SQLiteRepo


class MapView(QWidget):
    projectChanged = Signal(object)

    def __init__(self, project: ProjectConfig):
        super().__init__()
        self.project = project
        self.repo = SQLiteRepo()
        self.tbl_x1x2 = QTableWidget()
        self.tbl_colors = QTableWidget()
        self.info = QLabel("A0602: LEDs são apenas indicadores (não alimentam 24V)")

        btns = QHBoxLayout()
        btn_export = QPushButton("Exportar JSON")
        btn_import = QPushButton("Importar JSON")
        btn_save = QPushButton("Salvar no SQLite")
        btn_load = QPushButton("Carregar do SQLite")
        btns.addWidget(btn_export)
        btns.addWidget(btn_import)
        btns.addWidget(btn_save)
        btns.addWidget(btn_load)

        lay = QVBoxLayout(self)
        lay.addLayout(btns)
        lay.addWidget(QLabel("Mapa X1/X2"))
        lay.addWidget(self.tbl_x1x2)
        lay.addWidget(QLabel("Cores e Cablagem"))
        lay.addWidget(self.tbl_colors)
        lay.addWidget(self.info)

        btn_export.clicked.connect(self._export_json)
        btn_import.clicked.connect(self._import_json)
        btn_save.clicked.connect(self._save_db)
        btn_load.clicked.connect(self._load_db)

        self._refresh_tables()

    def _refresh_tables(self):
        cols = ["Borne", "Pin Opta", "Tag", "Descrição", "Tipo", "Tensão", "Obs"]
        self.tbl_x1x2.setColumnCount(len(cols))
        self.tbl_x1x2.setHorizontalHeaderLabels(cols)
        data = self.project.io_map
        self.tbl_x1x2.setRowCount(len(data))
        for r, i in enumerate(data):
            vals = [i.terminal, i.pin, i.tag, i.descricao, i.tipo.value, i.tensao, i.obs]
            for c, v in enumerate(vals):
                self.tbl_x1x2.setItem(r, c, QTableWidgetItem(str(v)))

        ccols = ["Elemento", "Cor", "Função"]
        self.tbl_colors.setColumnCount(len(ccols))
        self.tbl_colors.setHorizontalHeaderLabels(ccols)
        self.tbl_colors.setRowCount(len(self.project.colors))
        for r, i in enumerate(self.project.colors):
            self.tbl_colors.setItem(r, 0, QTableWidgetItem(i.nome))
            self.tbl_colors.setItem(r, 1, QTableWidgetItem(i.cor))
            self.tbl_colors.setItem(r, 2, QTableWidgetItem(i.funcao))

    def _read_tables(self):
        new_items = []
        for r in range(self.tbl_x1x2.rowCount()):
            terminal = self.tbl_x1x2.item(r, 0).text()
            pin = self.tbl_x1x2.item(r, 1).text()
            tag = self.tbl_x1x2.item(r, 2).text()
            desc = self.tbl_x1x2.item(r, 3).text()
            tipo = IOType(self.tbl_x1x2.item(r, 4).text())
            tensao = self.tbl_x1x2.item(r, 5).text()
            obs = self.tbl_x1x2.item(r, 6).text() if self.tbl_x1x2.item(r, 6) else ""
            new_items.append(IOItem(terminal, pin, tag, desc, tipo, tensao, obs))
        colors = []
        for r in range(self.tbl_colors.rowCount()):
            nome = self.tbl_colors.item(r, 0).text()
            cor = self.tbl_colors.item(r, 1).text()
            func = self.tbl_colors.item(r, 2).text()
            colors.append(ColorsWiring(nome, cor, func))
        self.project.io_map = new_items
        self.project.colors = colors
        self.projectChanged.emit(self.project)

    def _export_json(self):
        self._read_tables()
        path, _ = QFileDialog.getSaveFileName(self, "Salvar JSON", "projeto.json", "JSON (*.json)")
        if path:
            export_json(self.project, path)

    def _import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir JSON", "", "JSON (*.json)")
        if path:
            self.project = import_json(path)
            self._refresh_tables()
            self.projectChanged.emit(self.project)

    def _save_db(self):
        self._read_tables()
        self.repo.save_project("projeto", self.project)

    def _load_db(self):
        p = self.repo.load_latest()
        if p:
            self.project = p
            self._refresh_tables()
            self.projectChanged.emit(self.project)
