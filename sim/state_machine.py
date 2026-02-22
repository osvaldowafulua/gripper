import logging
from dataclasses import dataclass
from typing import Dict
from domain.models import CycleState, SimulationParams, SimulationState


@dataclass
class Edge:
    pass


class StateMachine:
    def __init__(self, params: SimulationParams):
        self.params = params
        self.s = SimulationState()
        self._ts_state = 0
        self._ts_cycle = 0
        self._ts_move = 0
        self._c3_cmd_down = True
        self._start_pulse = False
        self._auto = True
        self._auto_ts = 0
        self.log = logging.getLogger("sim")
        # TUNE button semantics
        self._tune_pressing = False
        self._tune_press_ms = 0
        self._tune_clicks = 0
        self._tune_group_ms = 0
        self._tune_idx = 0  # 0: STEP, 1: SACODE, 2: MOVE_TIMEOUT, 3: MAX_CYCLE
        self._defaults = SimulationParams(
            STEP_MS=params.STEP_MS,
            SACODE_MS=params.SACODE_MS,
            MOVE_TIMEOUT_MS=params.MOVE_TIMEOUT_MS,
            MAX_CYCLE_MS=params.MAX_CYCLE_MS,
        )
        self.reset_inputs_outputs()

    def reset_inputs_outputs(self):
        self.s.inputs = {f"I{i}": False for i in range(1, 9)}
        self.s.outputs = {f"Q{i}": False for i in range(1, 8)}

    def press_start(self):
        self._start_pulse = True
        self.s.inputs["I6"] = False

    def release_start(self):
        self.s.inputs["I6"] = False

    def set_emergency(self, active: bool):
        self.s.inputs["I7"] = active

    def reset_lock(self):
        if not self.s.inputs.get("I7", False) and self.s.state == CycleState.EMERGENCY_LOCKED:
            self.s.emergency_latched = False
            self._goto(CycleState.IDLE)

    def stop(self):
        self._all_off()
        self._goto(CycleState.STOPPED)

    def set_sensor(self, name: str, active: bool):
        mapping = {
            "S1.1": "I1",      # Gripper fechado
            "S2.0": "I2",      # Braço cima
            "S2.1": "I3",      # Braço baixo
            "START": "I6",     # Pedal start
            "STOP": "I5",      # Botão stop
            "EMERGENCIA": "I7",# Botão emergência
            "TUNE": "I8",      # Botão de ajuste
        }
        if name in mapping:
            self.s.inputs[mapping[name]] = active

    def tick(self, dt_ms: int):
        self.s.t_step_ms += dt_ms
        if self.s.state != CycleState.IDLE:
            self.s.t_cycle_ms += dt_ms

        # Process TUNE button (I8)
        self._tune_process(dt_ms)

        if self.s.inputs.get("I7", False):
            if not self.s.emergency_latched:
                self.log.info("[FAULT] EMERGENCY")
            self.s.emergency_latched = True
            self._all_off()
            self._goto(CycleState.EMERGENCY_LOCKED)
            return

        if self.s.state == CycleState.EMERGENCY_LOCKED:
            self._all_off()
            return

        if self.s.state == CycleState.STOPPED:
            self._all_off()
            return

        if self.s.inputs.get("I5", False):
            self._all_off()
            self._goto(CycleState.STOPPED)
            return

        if self.s.state == CycleState.IDLE:
            self._all_off()
            if (self._start_pulse or self.s.inputs.get("I6", False)) and not self.s.emergency_latched:
                self._goto(CycleState.C1_FECHAR)
                self._ts_move = 0
                # consome pulso de START e solta I6
                self._start_pulse = False
                self.s.inputs["I6"] = False
            return

        if self.s.t_cycle_ms > self.params.MAX_CYCLE_MS:
            self.log.info("[FAULT] TIMEOUT_CYCLE %d", self.s.t_cycle_ms)
            self._all_off()
            self._goto(CycleState.STOPPED)
            return

        if self.s.state == CycleState.C1_FECHAR:
            self._air(True)
            self._q("Q1", True)
            if self._auto:
                # gripper fechado (ex.: S1.0=1, S1.1=0)
                self.s.inputs["I1"], self.s.inputs["I2"] = True, False
            if self.s.t_step_ms >= self.params.STEP_MS:
                self._goto(CycleState.C2_DESCER)
                self._ts_move = 0

        elif self.s.state == CycleState.C2_DESCER:
            self._air(True)
            self._q("Q2", True)
            if self._auto:
                # descendo: BAIXO
                self.s.inputs["I3"], self.s.inputs["I4"] = True, False
            if self.s.t_step_ms >= self.params.STEP_MS:
                self._goto(CycleState.SACODE)
                self._ts_move = 0
                self._c3_cmd_down = True

        elif self.s.state == CycleState.SACODE:
            self._air(True)
            # Agitador por tempo (sem sensores dedicados)
            if self._auto:
                self._auto_ts += dt_ms
                if self._auto_ts >= 150:
                    self._auto_ts = 0
                    self._c3_cmd_down = not self._c3_cmd_down
            self._q("Q3", self._c3_cmd_down)
            if self.s.t_step_ms >= self.params.SACODE_MS:
                self._goto(CycleState.C2_SUBIR)

        elif self.s.state == CycleState.C2_SUBIR:
            self._air(True)
            self._q("Q2", False)
            if self._auto:
                # subindo: CIMA
                self.s.inputs["I3"], self.s.inputs["I4"] = False, True
            if self.s.t_step_ms >= self.params.STEP_MS:
                self._goto(CycleState.C1_ABRIR)

        elif self.s.state == CycleState.C1_ABRIR:
            self._air(True)
            self._q("Q1", False)
            if self._auto:
                # gripper aberto (ex.: S1.0=0, S1.1=1)
                self.s.inputs["I1"], self.s.inputs["I2"] = False, True
            if self.s.t_step_ms >= self.params.STEP_MS:
                self._all_off()
                self.s.cycles += 1
                self._goto(CycleState.IDLE)

    def diag_line(self) -> str:
        s = self.s
        s1 = f"{int(self.s.inputs.get('I1', False))}"  # S1.1 FECHADO
        s2 = f"{int(self.s.inputs.get('I2', False))}/{int(self.s.inputs.get('I3', False))}"  # CIMA/BAIXO
        s3 = "-/-"  # sem sensores dedicados
        q = "".join(str(int(self.s.outputs.get(f"Q{i}", False))) for i in range(1, 8))
        return (
            f"STATE={s.state.value} EMG={int(self.s.inputs.get('I7', False))} LATCH={int(s.emergency_latched)} "
            f"tStep={s.t_step_ms} tCycle={s.t_cycle_ms} S1={s1} S2={s2} S3={s3} Q={q}"
        )

    def panel_flags(self) -> Dict[str, bool]:
        ready = self.s.state == CycleState.IDLE
        run = self.s.state in {
            CycleState.C1_FECHAR,
            CycleState.C2_DESCER,
            CycleState.SACODE,
            CycleState.C2_SUBIR,
            CycleState.C1_ABRIR,
        }
        stop = self.s.state in {CycleState.STOPPED, CycleState.EMERGENCY_LOCKED}
        return {"READY": ready, "RUN": run, "STOP": stop, "EMERGENCY_LOCKED": self.s.state == CycleState.EMERGENCY_LOCKED}

    def _goto(self, st: CycleState):
        self.s.state = st
        self.s.t_step_ms = 0
        if st == CycleState.IDLE:
            self.s.t_cycle_ms = 0

    def _q(self, name: str, on: bool):
        self.s.outputs[name] = on

    def _air(self, on: bool):
        self.s.outputs["Q4"] = on

    def _all_off(self):
        for k in list(self.s.outputs.keys()):
            self.s.outputs[k] = False
        if self._auto:
            # sensores repouso
            for k in ("I1","I2","I3"):
                self.s.inputs[k] = False

    # --- TUNE helpers ----------------------------------------------------
    def _tune_process(self, dt_ms: int):
        i8 = bool(self.s.inputs.get("I8", False))
        LONG_MS = 1500
        GROUP_MS = 600
        # Pressing/long-press tracking
        if i8:
            if not self._tune_pressing:
                self._tune_pressing = True
                self._tune_press_ms = 0
            self._tune_press_ms += dt_ms
            if self._tune_press_ms >= LONG_MS:
                self.tune_reset()
                self._tune_clicks = 0
                self._tune_group_ms = 0
                # auto-release to simulate button release
                self.s.inputs["I8"] = False
                self._tune_pressing = False
                self._tune_press_ms = 0
                return
        else:
            if self._tune_pressing:
                # rising->falling edge registered as a click
                self._tune_clicks += 1
                self._tune_group_ms = GROUP_MS
                self._tune_pressing = False
                self._tune_press_ms = 0
        # Grouping window for multi-click
        if self._tune_group_ms > 0:
            self._tune_group_ms -= dt_ms
            if self._tune_group_ms <= 0:
                # interpret clicks
                if self._tune_clicks == 1:
                    self.tune_dec()
                elif self._tune_clicks == 2:
                    self.tune_inc()
                elif self._tune_clicks == 3:
                    self.tune_next()
                elif self._tune_clicks >= 4:
                    self.tune_prev()
                self._tune_clicks = 0
                self._tune_group_ms = 0

    def _current_key(self) -> str:
        order = ["STEP_MS","SACODE_MS","MOVE_TIMEOUT_MS","MAX_CYCLE_MS"]
        return order[self._tune_idx % len(order)]

    def _step_for(self, key: str) -> int:
        return {"STEP_MS":100, "SACODE_MS":100, "MOVE_TIMEOUT_MS":50, "MAX_CYCLE_MS":1000}.get(key, 100)

    def _limits_for(self, key: str):
        mins = {"STEP_MS":100, "SACODE_MS":100, "MOVE_TIMEOUT_MS":50, "MAX_CYCLE_MS":2000}
        maxs = {"STEP_MS":60000, "SACODE_MS":60000, "MOVE_TIMEOUT_MS":5000, "MAX_CYCLE_MS":600000}
        return mins.get(key,0), maxs.get(key,10**9)

    def _apply_delta(self, key: str, delta: int):
        cur = getattr(self.params, key)
        lo, hi = self._limits_for(key)
        new = max(lo, min(hi, cur + delta))
        setattr(self.params, key, int(new))

    # actions exposed for API/UI
    def tune_inc(self):
        k = self._current_key(); self._apply_delta(k, +self._step_for(k))

    def tune_dec(self):
        k = self._current_key(); self._apply_delta(k, -self._step_for(k))

    def tune_next(self):
        self._tune_idx = (self._tune_idx + 1) % 4

    def tune_prev(self):
        self._tune_idx = (self._tune_idx - 1) % 4

    def tune_reset(self):
        self.params.STEP_MS = self._defaults.STEP_MS
        self.params.SACODE_MS = self._defaults.SACODE_MS
        self.params.MOVE_TIMEOUT_MS = self._defaults.MOVE_TIMEOUT_MS
        self.params.MAX_CYCLE_MS = self._defaults.MAX_CYCLE_MS
