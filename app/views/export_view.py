from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog
from domain.models import ProjectConfig
from export.ascii_diagram import build_ascii_diagram
from export.pdf_generator import generate_pdf


class ExportView(QWidget):
    def __init__(self, project: ProjectConfig):
        super().__init__()
        self.project = project
        lay = QVBoxLayout(self)
        self.lbl = QLabel("Gerar PDF profissional do manual técnico")
        self.btn = QPushButton("Gerar PDF")
        self.out = QLabel("")
        lay.addWidget(self.lbl)
        lay.addWidget(self.btn)
        lay.addWidget(self.out)
        self.btn.clicked.connect(self._make)

    def set_project(self, p: ProjectConfig):
        self.project = p

    def _make(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", "manual.pdf", "PDF (*.pdf)")
        if not path:
            return
        ascii_d = build_ascii_diagram(self.project)
        generate_pdf(path, self.project, ascii_d)
        self.out.setText(f"PDF salvo em: {path}")
