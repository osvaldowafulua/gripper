from typing import List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from domain.models import ProjectConfig


def _table(title: str, data: List[List[str]]):
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph(title, styles["Heading2"]))
    elems.append(Spacer(1, 6))
    t = Table(data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elems.append(t)
    return elems


def generate_pdf(path: str, cfg: ProjectConfig, ascii_diagram: str):
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Braço Pneumático – Manual Técnico", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Projeto: {cfg.controlador}", styles["Normal"]))
    story.append(Paragraph(f"Expansão: {cfg.expansao}", styles["Normal"]))
    story.append(Paragraph(f"Versão: {cfg.versao}", styles["Normal"]))
    story.append(PageBreak())

    head = ["Borne", "Pin Opta", "Tag", "Descrição", "Tipo", "Tensão"]
    rows_x1 = [head]
    rows_x2 = [head]
    for i in cfg.io_map:
        row = [i.terminal, i.pin, i.tag, i.descricao, i.tipo.value, i.tensao]
        if i.terminal.startswith("X1:"):
            rows_x1.append(row)
        else:
            rows_x2.append(row)

    story += _table("Mapa de Entradas X1", rows_x1)
    story.append(Spacer(1, 12))
    story += _table("Mapa de Saídas X2", rows_x2)
    story.append(PageBreak())

    rows_colors = [["Elemento", "Cor", "Função"]]
    for c in cfg.colors:
        rows_colors.append([c.nome, c.cor, c.funcao])
    story += _table("Cores e Cablagem", rows_colors)
    story.append(PageBreak())

    story.append(Paragraph("Diagrama Unifilar (ASCII)", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Preformatted(ascii_diagram, styles["Code"]))
    story.append(PageBreak())

    rows_prot = [["Item", "Tipo", "Valor", "Notas"]]
    for p in cfg.protecoes:
        rows_prot.append([p.item, p.tipo, p.valor, p.notas])
    story += _table("Proteções Recomendadas", rows_prot)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Operação e Segurança", styles["Heading2"]))
    story.append(Paragraph("Respeite normas de segurança. A expansão A0602 possui LEDs apenas indicadores.", styles["Normal"]))

    doc = SimpleDocTemplate(path, pagesize=A4, title="Manual Técnico – Braço Pneumático")
    doc.build(story)
