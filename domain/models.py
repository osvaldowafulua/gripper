from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class IOType(str, Enum):
    DI = "DI"
    DO = "DO"


@dataclass
class IOItem:
    terminal: str
    pin: str
    tag: str
    descricao: str
    tipo: IOType
    tensao: str
    obs: str = ""


@dataclass
class ColorsWiring:
    nome: str
    cor: str
    funcao: str


@dataclass
class SafetyItem:
    item: str
    tipo: str
    valor: str
    notas: str = ""


class CycleState(str, Enum):
    IDLE = "IDLE"
    C1_FECHAR = "C1_FECHAR"
    C2_DESCER = "C2_DESCER"
    SACODE = "SACODE"
    C2_SUBIR = "C2_SUBIR"
    C1_ABRIR = "C1_ABRIR"
    STOPPED = "STOPPED"
    EMERGENCY_LOCKED = "EMERGENCY_LOCKED"


@dataclass
class SimulationParams:
    STEP_MS: int = 5000
    SACODE_MS: int = 5000
    MOVE_TIMEOUT_MS: int = 900
    MAX_CYCLE_MS: int = 25000


@dataclass
class SimulationState:
    state: CycleState = CycleState.IDLE
    t_step_ms: int = 0
    t_cycle_ms: int = 0
    emergency_latched: bool = False
    cycles: int = 0
    inputs: Dict[str, bool] = field(default_factory=dict)
    outputs: Dict[str, bool] = field(default_factory=dict)


@dataclass
class ProjectConfig:
    controlador: str
    expansao: str
    io_map: List[IOItem]
    colors: List[ColorsWiring]
    protecoes: List[SafetyItem]
    params: SimulationParams = field(default_factory=SimulationParams)
    versao: str = "1.0.0"


def default_project() -> ProjectConfig:
    io_items: List[IOItem] = [
        IOItem("X1:01", "I1", "S1.1", "C1 Gripper – FECHADO", IOType.DI, "+24V"),
        IOItem("X1:02", "I2", "S2.0", "C2 Braço – CIMA", IOType.DI, "+24V"),
        IOItem("X1:03", "I3", "S2.1", "C2 Braço – BAIXO", IOType.DI, "+24V"),
        IOItem("X1:04", "I4", "RESERVA", "Entrada reserva", IOType.DI, "+24V"),
        IOItem("X1:05", "I5", "STOP", "Parada de ciclo", IOType.DI, "+24V"),
        IOItem("X1:06", "I6", "START", "Pedal NO", IOType.DI, "+24V"),
        IOItem("X1:07", "I7", "EMERGENCIA", "Botão de emergência", IOType.DI, "+24V"),
        IOItem("X1:08", "I8", "TUNE", "Ajuste fino (I8)", IOType.DI, "+24V"),
        IOItem("X2:01", "Q1(D0)", "C1", "Válvula do cilindro gripper", IOType.DO, "+24V"),
        IOItem("X2:02", "Q2(D1)", "C2", "Válvula sobe/desce do braço", IOType.DO, "+24V"),
        IOItem("X2:03", "Q3(D2)", "C3", "Válvula do cilindro agitador", IOType.DO, "+24V"),
        IOItem("X2:04", "Q4(D3)", "SINAL", "Sinalizador de trabalho", IOType.DO, "+24V"),
        IOItem("EXT:05", "Q5", "AR GERAL", "Válvula de corte do ar geral (extensor)", IOType.DO, "+24V"),
        IOItem("EXT:06", "Q6", "EMERG OUT", "Saída (ex.: sirene) ligada à emergência (extensor)", IOType.DO, "+24V"),
        IOItem("EXT:07", "Q7", "RESERVA", "Saída digital extra (extensor)", IOType.DO, "+24V"),
    ]

    colors = [
        ColorsWiring("Sensor PNP", "Castanho", "+24V"),
        ColorsWiring("Sensor PNP", "Azul", "0V"),
        ColorsWiring("Sensor PNP", "Preto", "Sinal -> Ix"),
        ColorsWiring("Carga 24V", "Vermelho", "+24V"),
        ColorsWiring("Carga 24V", "Azul", "0V"),
    ]

    protecoes = [
        SafetyItem("F1 Geral", "Fusível/Disjuntor", "2A"),
        SafetyItem("F2 C1", "Fusível", "1A"),
        SafetyItem("F3 C2", "Fusível", "1A"),
        SafetyItem("F4 C3", "Fusível", "1A"),
        SafetyItem("Relé Segurança", "Categoria", "PL d/Cat.3"),
        SafetyItem("Válvula Dump", "Segurança", "Despressurização"),
    ]

    return ProjectConfig(
        controlador="Arduino Opta WiFi",
        expansao="Arduino Pro Opta Ext A0602 (Analog Expansion) — LEDs apenas indicadores",
        io_map=io_items,
        colors=colors,
        protecoes=protecoes,
    )
