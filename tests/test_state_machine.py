from sim.state_machine import StateMachine
from domain.models import SimulationParams, CycleState


def test_simple_cycle():
    params = SimulationParams(STEP_MS=100, SACODE_MS=100, MOVE_TIMEOUT_MS=500, MAX_CYCLE_MS=3000)
    sm = StateMachine(params)
    sm.press_start()
    total = 0
    while total < 1200 and sm.s.state != CycleState.SACODE:
        sm.tick(50)
        total += 50
    sm.set_sensor("S3.0", True)
    sm.tick(100)
    sm.set_sensor("S3.0", False)
    sm.set_sensor("S3.1", True)
    sm.tick(100)
    while total < 2500 and sm.s.state != CycleState.IDLE:
        sm.tick(50)
        total += 50
    assert sm.s.state == CycleState.IDLE
    assert sm.s.cycles >= 1


def test_emergency_latch():
    sm = StateMachine(SimulationParams(STEP_MS=100, SACODE_MS=100, MOVE_TIMEOUT_MS=500, MAX_CYCLE_MS=2000))
    sm.press_start()
    sm.tick(100)
    sm.set_emergency(True)
    sm.tick(10)
    assert sm.s.state == CycleState.EMERGENCY_LOCKED
    sm.set_emergency(False)
    sm.reset_lock()
    assert sm.s.state == CycleState.IDLE
