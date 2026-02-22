from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel
from domain.models import ProjectConfig, SafetyItem


class ProtectionsView(QWidget):
    projectChanged = Signal(object)

    def __init__(self, project: ProjectConfig):
        super().__init__()
        self.project = project
        lay = QVBoxLayout(self)
        self.tbl = QTableWidget()
        lay.addWidget(QLabel("Proteções recomendadas"))
        lay.addWidget(self.tbl)
        self._load()
        self.tbl.itemChanged.connect(self._save)

    def set_project(self, p: ProjectConfig):
        self.project = p
        self._load()

    def _load(self):
        cols = ["Item", "Tipo", "Valor", "Notas"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setRowCount(len(self.project.protecoes))
        for r, it in enumerate(self.project.protecoes):
            self.tbl.setItem(r, 0, QTableWidgetItem(it.item))
            self.tbl.setItem(r, 1, QTableWidgetItem(it.tipo))
            self.tbl.setItem(r, 2, QTableWidgetItem(it.valor))
            self.tbl.setItem(r, 3, QTableWidgetItem(it.notas))

    def _save(self):
        items = []
        for r in range(self.tbl.rowCount()):
            item = self.tbl.item(r, 0).text()
            tipo = self.tbl.item(r, 1).text()
            valor = self.tbl.item(r, 2).text()
            notas = self.tbl.item(r, 3).text() if self.tbl.item(r, 3) else ""
            items.append(SafetyItem(item, tipo, valor, notas))
        self.project.protecoes = items
        self.projectChanged.emit(self.project)
