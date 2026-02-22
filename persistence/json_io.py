import json
from dataclasses import asdict
from typing import Any
from domain.models import ProjectConfig, IOItem, ColorsWiring, SafetyItem, SimulationParams


def project_to_dict(p: ProjectConfig) -> dict:
    d = asdict(p)
    d["io_map"] = [asdict(i) for i in p.io_map]
    d["colors"] = [asdict(c) for c in p.colors]
    d["protecoes"] = [asdict(s) for s in p.protecoes]
    d["params"] = asdict(p.params)
    return d


def dict_to_project(d: dict) -> ProjectConfig:
    io = [IOItem(**i) for i in d["io_map"]]
    colors = [ColorsWiring(**c) for c in d["colors"]]
    prot = [SafetyItem(**s) for s in d["protecoes"]]
    params = SimulationParams(**d.get("params", {}))
    return ProjectConfig(
        controlador=d["controlador"],
        expansao=d["expansao"],
        io_map=io,
        colors=colors,
        protecoes=prot,
        params=params,
        versao=d.get("versao", "1.0.0"),
    )


def export_json(p: ProjectConfig, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(project_to_dict(p), f, ensure_ascii=False, indent=2)


def import_json(path: str) -> ProjectConfig:
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return dict_to_project(d)
