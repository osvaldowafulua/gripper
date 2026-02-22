from domain.models import ProjectConfig


def build_ascii_diagram(cfg: ProjectConfig) -> str:
    x1 = [i for i in cfg.io_map if i.terminal.startswith("X1:")]
    x2 = [i for i in cfg.io_map if i.terminal.startswith("X2:")]
    lines = []
    lines.append("UNIFILAR – OPTA WiFi + A0602")
    lines.append("A0602 LEDs = indicadores (não alimentam 24V)")
    lines.append("")
    lines.append("X1 (Entradas)")
    for i in x1:
        lines.append(f"{i.terminal:<6} {i.pin:<6} {i.tag:<8} {i.descricao}")
    lines.append("")
    lines.append("X2 (Saídas – Relés)")
    for o in x2:
        lines.append(f"{o.terminal:<6} {o.pin:<6} {o.tag:<8} {o.descricao}")
    return "\n".join(lines)
