import json
import os
import sys
import urllib.request
import socket
from urllib.error import URLError, HTTPError
import threading
import time
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from domain.models import default_project
from sim.state_machine import StateMachine

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(root))
static_dir = os.path.join(root, "static")
proj = default_project()
sm = StateMachine(proj.params)

# settings for web server behavior
SETTINGS = {
    "mode": "sim",
    "remote_base": "http://192.168.0.10/",
}

DEFAULT_MODBUS_MAP = {
    # lemos 0..63 continuamente
    "hr_base": 0,
    "hr_count": 64,

    # feedback
    "hr_state": 0,
    "hr_cycles_lo": 1,
    "hr_cycles_hi": 2,
    "hr_emg": 3,
    "hr_latched": 4,
    "hr_step_ms": 5,
    "hr_sacode_ms": 6,
    "hr_toggle_ms": 7,
    "hr_max_ms": 8,
    "hr_inmask": 9,
    "hr_outmask": 10,
    "hr_est_ms": 30,

    # setpoints (escrita)
    "hr_set_step": 20,
    "hr_set_sacode": 21,
    "hr_set_move": 22,
    "hr_set_max": 23,
    "hr_preset": 24,

    # coils comandos (pulso)
    "coil_start": 0,
    "coil_stop": 1,
    "coil_reset": 2,
    "coil_apply_cycle": 4,
    "coil_apply_all": 5,
}

MODBUS = {
    "host": "",
    "port": 502,
    "map": DEFAULT_MODBUS_MAP.copy(),
    "snapshot": None,
    "lock": threading.Lock(),
    "running": False,
}

def _parse_host_port(base):
    b = base or ""
    if b.startswith("http://") or b.startswith("https://"):
        b = b.split("://",1)[1]
    if "/" in b:
        b = b.split("/",1)[0]
    if ":" in b:
        h, p = b.split(":",1)
        try:
            return h, int(p)
        except Exception:
            return h, 502
    return b, 502

def _ensure_modbus_thread():
    if MODBUS["running"]:
        return
    MODBUS["running"] = True
    t = threading.Thread(target=_modbus_loop, daemon=True)
    t.start()

def _modbus_client():
    try:
        from pymodbus.client import ModbusTcpClient
    except Exception:
        return None
    host, port = MODBUS["host"], MODBUS["port"]
    if not host:
        return None
    c = ModbusTcpClient(host=host, port=port)
    return c

def _modbus_write_register(addr: int, value: int) -> bool:
    c = _modbus_client()
    if not c:
        return False
    try:
        if not c.connect():
            return False
        r = c.write_register(addr, int(value))
        ok = hasattr(r, 'isError') and not r.isError()
        c.close()
        return ok
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        return False

def _modbus_pulse_coil(idx: int) -> bool:
    c = _modbus_client()
    if not c:
        return False
    try:
        if not c.connect():
            return False
        r1 = c.write_coil(idx, True)
        r2 = c.write_coil(idx, False)
        ok = all((hasattr(r1,'isError') and not r1.isError(), hasattr(r2,'isError') and not r2.isError()))
        c.close()
        return ok
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        return False

def _modbus_loop():
    client = None
    ModbusTcpClient = None
    while MODBUS["running"]:
        try:
            if ModbusTcpClient is None:
                try:
                    from pymodbus.client import ModbusTcpClient as _C
                    ModbusTcpClient = _C
                except Exception:
                    time.sleep(1.0)
                    continue
            host = MODBUS["host"]
            port = MODBUS["port"]
            mp = MODBUS["map"]
            if not host:
                time.sleep(0.5)
                continue
            if client is None or not client.connected:
                client = ModbusTcpClient(host=host, port=port, timeout=1.5)
                client.connect()
            t0 = time.monotonic()
            base_hr = mp["hr_base"]
            count = mp["hr_count"]
            hrs = []
            if client:
                try:
                    resp = client.read_holding_registers(base_hr, count)
                    hrs = getattr(resp, 'registers', []) or []
                    if len(hrs) < count:
                        # fallback: ler em blocos (p.ex. 2x32)
                        hrs = []
                        off = 0
                        while off < count:
                            n = min(32, count - off)
                            r = client.read_holding_registers(base_hr + off, n)
                            part = getattr(r, 'registers', []) or []
                            if len(part) != n:
                                hrs = []
                                break
                            hrs.extend(part)
                            off += n
                except Exception:
                    hrs = []
            t1 = time.monotonic()
            def h(addr):
                try:
                    return int(hrs[addr - base_hr])
                except Exception:
                    return 0
            inmask = h(mp["hr_inmask"]) if mp.get("hr_inmask") is not None else 0
            outmask = h(mp["hr_outmask"]) if mp.get("hr_outmask") is not None else 0
            ins = {f"I{i}": bool(inmask & (1 << (i-1))) for i in range(1,9)}
            outs = {
                "Q1": bool(outmask & (1<<0)),
                "Q2": bool(outmask & (1<<1)),
                "Q3": bool(outmask & (1<<2)),
                "Q4": bool(outmask & (1<<3)),
                "Q5": bool(outmask & (1<<4)),
                "Q6": bool(outmask & (1<<5)),
                "Q7": bool(outmask & (1<<6)),
            }
            state = str(h(mp["hr_state"])) if mp.get("hr_state") is not None else "?"
            cyc = (h(mp["hr_cycles_hi"]) << 16) | h(mp["hr_cycles_lo"]) if mp.get("hr_cycles_hi") is not None else h(mp.get("hr_cycles_lo", 0))
            payload = {
                "state": state,
                "tStep": 0,
                "tCycle": 0,
                "emergency": int(h(mp["hr_emg"])),
                "latched": bool(h(mp["hr_latched"])),
                "cycles": int(cyc),
                "inputs": ins,
                "outputs": outs,
                "diag": f"STATE={state} EMG={int(h(mp['hr_emg']))} LATCH={int(bool(h(mp['hr_latched'])))} est={h(mp['hr_est_ms'])}",
                "panel": {
                    "READY": state == "0" or state == "IDLE",
                    "RUN": any(outs.get(k, False) for k in ("Q1","Q2","Q3")),
                    "STOP": state in {"STOPPED","EMG_LOCK"} or bool(h(mp["hr_emg"])),
                    "EMERGENCY_LOCKED": state in {"EMG_LOCK","EMERGENCY_LOCKED"} or bool(h(mp["hr_latched"])),
                },
                "params": {
                    "STEP_MS": h(mp["hr_step_ms"]),
                    "SACODE_MS": h(mp["hr_sacode_ms"]),
                    "MOVE_TIMEOUT_MS": h(mp.get("hr_set_move", 22)),
                    "MAX_CYCLE_MS": h(mp["hr_max_ms"]),
                },
                "rt_ms": int((t1 - t0)*1000)
            }
            with MODBUS["lock"]:
                MODBUS["snapshot"] = payload
            time.sleep(0.2)
        except Exception:
            with MODBUS["lock"]:
                MODBUS["snapshot"] = None
            if client:
                try:
                    client.close()
                except Exception:
                    pass
                client = None
            time.sleep(0.8)


def _bg_loop():
    while True:
        sm.tick(100)
        time.sleep(0.1)


class Handler(SimpleHTTPRequestHandler):
    def _wifi_app_info(self):
        try:
            # macOS airport utility for RSSI and SSID
            cmd = [
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I",
            ]
            out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=1.0)
            rssi = None
            ssid = None
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("agrCtlRSSI:"):
                    try:
                        rssi = int(line.split(":",1)[1].strip())
                    except Exception:
                        pass
                elif line.startswith("SSID:"):
                    ssid = line.split(":",1)[1].strip()
            return {"rssi": rssi, "ssid": ssid}
        except Exception:
            return {"rssi": None, "ssid": None}

    def _quality_from_rssi(self, rssi):
        try:
            if rssi is None:
                return 0
            # Typical RSSI thresholds
            if rssi >= -55:
                return 4
            if rssi >= -65:
                return 3
            if rssi >= -75:
                return 2
            if rssi >= -85:
                return 1
            return 0
        except Exception:
            return 0
    def _json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/api/state":
            if SETTINGS["mode"] == "sim":
                s = sm.s
                app_wifi = self._wifi_app_info()
                payload = {
                    "state": s.state.value,
                    "tStep": s.t_step_ms,
                    "tCycle": s.t_cycle_ms,
                    "emergency": int(s.inputs.get("I7", False)),
                    "latched": s.emergency_latched,
                    "cycles": s.cycles,
                    "inputs": s.inputs,
                    "outputs": s.outputs,
                    "diag": sm.diag_line(),
                    "panel": sm.panel_flags(),
                    "mode": SETTINGS["mode"],
                    "remote_base": SETTINGS["remote_base"],
                    "params": {
                        "STEP_MS": sm.params.STEP_MS,
                        "SACODE_MS": sm.params.SACODE_MS,
                        "MOVE_TIMEOUT_MS": sm.params.MOVE_TIMEOUT_MS,
                        "MAX_CYCLE_MS": sm.params.MAX_CYCLE_MS,
                    },
                    "wifi": {
                        "opta_rssi": None,
                        "app_rssi": app_wifi.get("rssi"),
                        "app_ssid": app_wifi.get("ssid"),
                        "opta_latency_ms": None,
                        "opta_quality": None,
                        "app_quality": self._quality_from_rssi(app_wifi.get("rssi")),
                    }
                }
                return self._json(200, payload)
            elif SETTINGS["mode"] == "modbus":
                with MODBUS["lock"]:
                    snap = MODBUS["snapshot"]
                if not snap:
                    return self._json(502, {"error": "remote_unreachable"})
                snap = dict(snap)
                app_wifi = self._wifi_app_info()
                snap["wifi"] = {
                    "opta_rssi": None,  # not available via Modbus by default
                    "opta_latency_ms": snap.pop("rt_ms", None),
                    "app_rssi": app_wifi.get("rssi"),
                    "app_ssid": app_wifi.get("ssid"),
                    "opta_quality": None,
                    "app_quality": self._quality_from_rssi(app_wifi.get("rssi")),
                }
                snap.update({"mode": SETTINGS["mode"], "remote_base": f"{MODBUS['host']}:{MODBUS['port']}"})
                return self._json(200, snap)
            else:
                # proxy read-only: pull JSON from Opta and adapt
                base = SETTINGS.get("remote_base") or ""
                try:
                    t0 = time.monotonic()
                    with urllib.request.urlopen(base, timeout=2) as r:
                        data = r.read().decode("utf-8")
                        remote = json.loads(data)
                    t1 = time.monotonic()
                except Exception as e:
                    return self._json(502, {"error": "remote_unreachable", "detail": str(e)})
                # Arduino sketch exposes: ip, state, cycles, emg, latched, step, sacode, toggle, max
                state = str(remote.get("state", "?"))
                # tStep/tCycle não são publicados pelo Opta HTTP -> mantemos 0
                tStep = int(remote.get("tStep", 0) or 0)
                tCycle = int(remote.get("tCycle", 0) or 0)
                emergency = int(remote.get("emg", remote.get("emergency", 0)) or 0)
                latched = bool(remote.get("latched", False))
                cycles = int(remote.get("cycles", 0) or 0)
                # infer outputs a partir do estado (Opta: GRIP_CLOSE/ARM_DOWN/SACODE/ARM_UP/GRIP_OPEN)
                outs = {k: False for k in ("Q1","Q2","Q3","Q4","Q5","Q6","Q7")}
                if state in {"GRIP_CLOSE", "C1_FECHAR"}: outs.update({"Q1": True, "Q4": True})
                elif state in {"GRIP_OPEN", "C1_ABRIR"}: outs.update({"Q1": False, "Q4": True})
                elif state in {"ARM_DOWN", "C2_DESCER"}: outs.update({"Q2": True, "Q4": True})
                elif state in {"ARM_UP", "C2_SUBIR"}: outs.update({"Q2": False, "Q4": True})
                elif state in {"SACODE", "SACODE_C3"}: outs.update({"Q3": True, "Q4": True})
                ins = {f"I{i}": False for i in range(1,9)}
                # build panel flags for both naming schemes
                panel = {
                    "READY": state == "IDLE",
                    "RUN": state in {"GRIP_CLOSE","ARM_DOWN","SACODE","ARM_UP","GRIP_OPEN","C1_FECHAR","C2_DESCER","C2_SUBIR","C1_ABRIR"},
                    "STOP": state in {"STOPPED","EMG_LOCK","EMERGENCY_LOCKED"},
                    "EMERGENCY_LOCKED": state in {"EMG_LOCK","EMERGENCY_LOCKED"},
                }
                app_wifi = self._wifi_app_info()
                opta_rssi = remote.get("rssi") if isinstance(remote.get("rssi"), int) else None
                opta_latency_ms = int((t1 - t0)*1000) if 't1' in locals() else None
                opta_quality = self._quality_from_rssi(opta_rssi) if opta_rssi is not None else None
                payload = {
                    "state": state,
                    "tStep": tStep,
                    "tCycle": tCycle,
                    "emergency": emergency,
                    "latched": latched,
                    "cycles": cycles,
                    "inputs": ins,
                    "outputs": outs,
                    "diag": f"STATE={state} EMG={emergency} LATCH={int(latched)} tStep={tStep} tCycle={tCycle}",
                    "panel": panel,
                    "mode": SETTINGS["mode"],
                    "remote_base": base,
                    "params": {
                        "STEP_MS": int(remote.get("step", 0) or 0),
                        "SACODE_MS": int(remote.get("sacode", 0) or 0),
                        "MOVE_TIMEOUT_MS": 0,
                        "MAX_CYCLE_MS": int(remote.get("max", 0) or 0),
                        # toggle é período do agitador; mantemos separado no diag
                    },
                    "toggle_ms": int(remote.get("toggle", 0) or 0),
                    "wifi": {
                        "opta_rssi": opta_rssi,
                        "opta_latency_ms": opta_latency_ms,
                        "app_rssi": app_wifi.get("rssi"),
                        "app_ssid": app_wifi.get("ssid"),
                        "opta_quality": opta_quality,
                        "app_quality": self._quality_from_rssi(app_wifi.get("rssi")),
                    }
                }
                return self._json(200, payload)
        if p == "/api/settings":
            return self._json(200, {
                "mode": SETTINGS["mode"],
                "remote_base": SETTINGS["remote_base"],
                "params": {
                    "STEP_MS": sm.params.STEP_MS,
                    "SACODE_MS": sm.params.SACODE_MS,
                    "MOVE_TIMEOUT_MS": sm.params.MOVE_TIMEOUT_MS,
                    "MAX_CYCLE_MS": sm.params.MAX_CYCLE_MS,
                }
            })
        if p == "/" or p == "/index.html":
            path = os.path.join(static_dir, "index.html")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        if p.startswith("/static/"):
            fp = os.path.join(static_dir, p[len("/static/"):])
            if os.path.exists(fp):
                ctype = "text/plain"
                if fp.endswith(".css"): ctype = "text/css"
                if fp.endswith(".js"): ctype = "application/javascript"
                with open(fp, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        p = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}
        if p == "/api/command":
            mode = SETTINGS["mode"]
            cmd = data.get("cmd")
            val = data.get("value")
            if mode == "sim":
                if cmd == "start":
                    sm.press_start()
                elif cmd == "stop":
                    sm.stop()
                elif cmd == "reset":
                    sm.reset_lock()
                elif cmd == "emergency":
                    sm.set_emergency(bool(val))
                return self._json(200, {"ok": True})
            elif mode == "modbus":
                mp = MODBUS["map"]
                if cmd == "start":
                    ok = _modbus_pulse_coil(mp["coil_start"])
                elif cmd == "stop":
                    ok = _modbus_pulse_coil(mp["coil_stop"])
                elif cmd == "reset":
                    ok = _modbus_pulse_coil(mp["coil_reset"])
                elif cmd == "emergency":
                    return self._json(501, {"ok": False, "error": "emergency_not_writable_modbus"})
                else:
                    return self._json(400, {"ok": False, "error": "unknown_command"})
                return self._json(200, {"ok": bool(ok)})
            else:
                return self._json(501, {"ok": False, "error": "commands_not_supported_in_proxy"})
        if p == "/api/params":
            params = data or {}
            if SETTINGS["mode"] == "sim":
                for k in ("STEP_MS","SACODE_MS","MOVE_TIMEOUT_MS","MAX_CYCLE_MS"):
                    if k in params:
                        setattr(sm.params, k, int(params[k]))
                return self._json(200, {"ok": True, "params": {
                    "STEP_MS": sm.params.STEP_MS,
                    "SACODE_MS": sm.params.SACODE_MS,
                    "MOVE_TIMEOUT_MS": sm.params.MOVE_TIMEOUT_MS,
                    "MAX_CYCLE_MS": sm.params.MAX_CYCLE_MS,
                }})
            elif SETTINGS["mode"] == "modbus":
                mp = MODBUS["map"]
                # escreve setpoints e/ou preset
                oks = []
                wrote_any = False
                if "STEP_MS" in params:
                    oks.append(_modbus_write_register(mp["hr_set_step"], int(params["STEP_MS"])))
                    wrote_any = True
                if "SACODE_MS" in params:
                    oks.append(_modbus_write_register(mp["hr_set_sacode"], int(params["SACODE_MS"])))
                    wrote_any = True
                if "MOVE_TIMEOUT_MS" in params:
                    oks.append(_modbus_write_register(mp["hr_set_move"], int(params["MOVE_TIMEOUT_MS"])))
                    wrote_any = True
                if "MAX_CYCLE_MS" in params:
                    oks.append(_modbus_write_register(mp["hr_set_max"], int(params["MAX_CYCLE_MS"])))
                    wrote_any = True
                if wrote_any:
                    oks.append(_modbus_pulse_coil(mp["coil_apply_cycle"]))
                if "PRESET" in params:
                    oks.append(_modbus_write_register(mp["hr_preset"], int(params["PRESET"])))
                    oks.append(_modbus_pulse_coil(mp["coil_apply_all"]))
                return self._json(200, {"ok": all(oks) if oks else True})
            else:
                return self._json(501, {"ok": False, "error": "params_not_supported_in_proxy"})
        if p == "/api/tune":
            if SETTINGS["mode"] != "sim":
                return self._json(501, {"ok": False, "error": "tune_not_supported_in_proxy"})
            action = (data.get("action") or "").lower()
            if action == "inc": sm.tune_inc()
            elif action == "dec": sm.tune_dec()
            elif action == "next": sm.tune_next()
            elif action == "prev": sm.tune_prev()
            elif action == "reset": sm.tune_reset()
            else: return self._json(400, {"ok": False, "error": "unknown_action"})
            return self._json(200, {"ok": True, "params": {
                "STEP_MS": sm.params.STEP_MS,
                "SACODE_MS": sm.params.SACODE_MS,
                "MOVE_TIMEOUT_MS": sm.params.MOVE_TIMEOUT_MS,
                "MAX_CYCLE_MS": sm.params.MAX_CYCLE_MS,
            }})
        if p == "/api/probe":
            base = str(data.get("base") or "").strip()
            if not base:
                return self._json(400, {"ok": False, "error": "missing_base"})
            url = base
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"http://{url}/"
            try:
                t0 = time.monotonic()
                with urllib.request.urlopen(url, timeout=1.5) as r:
                    raw = r.read().decode("utf-8")
                    _ = json.loads(raw)
                t1 = time.monotonic()
                return self._json(200, {"ok": True, "mode": "proxy", "base": url, "latency_ms": int((t1-t0)*1000)})
            except Exception:
                pass
            h, prt = _parse_host_port(base)
            if not prt:
                prt = 502
            try:
                t0 = time.monotonic()
                with socket.create_connection((h, prt), timeout=1.5):
                    pass
                t1 = time.monotonic()
                return self._json(200, {"ok": True, "mode": "modbus", "base": f"{h}:{prt}", "latency_ms": int((t1-t0)*1000)})
            except Exception as e:
                return self._json(502, {"ok": False, "error": "unreachable", "detail": str(e)})
        if p == "/api/settings":
            mode = data.get("mode")
            base = data.get("remote_base")
            if mode in ("sim","proxy","modbus"):
                SETTINGS["mode"] = mode
            if isinstance(base, str):
                SETTINGS["remote_base"] = base
                if SETTINGS["mode"] == "modbus":
                    h, prt = _parse_host_port(base)
                    MODBUS["host"], MODBUS["port"] = h, prt
                    _ensure_modbus_thread()
            return self._json(200, {"ok": True, "mode": SETTINGS["mode"], "remote_base": SETTINGS["remote_base"]})
        if p == "/api/sensor":
            if SETTINGS["mode"] != "sim":
                return self._json(501, {"ok": False, "error": "sensors_not_supported_in_proxy"})
            name = data.get("name")
            val = bool(data.get("value"))
            sm.set_sensor(name, val)
            return self._json(200, {"ok": True})
        self._json(404, {"error": "not found"})


if __name__ == "__main__":
    t = threading.Thread(target=_bg_loop, daemon=True)
    t.start()
    srv = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Server running at http://localhost:8000/")
    srv.serve_forever()
