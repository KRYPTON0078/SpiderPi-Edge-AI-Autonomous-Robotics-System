#!/usr/bin/python3
# coding=utf8
"""
Phone control bridge for SpiderPi.

Serves a mobile web UI and forwards simple command intents to the built-in
SpiderPi JSON-RPC server (default: 127.0.0.1:9030).
"""

import json
import logging
import os
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = os.environ.get("PHONE_CONTROL_HOST", "0.0.0.0")
PORT = int(os.environ.get("PHONE_CONTROL_PORT", "5000"))
RPC_URL = os.environ.get("SPIDERPI_RPC_URL", "http://127.0.0.1:9030")
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
CAMERA_SNAPSHOT_URL = os.environ.get("SPIDERPI_CAMERA_URL", "http://127.0.0.1:8080/?action=snapshot")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")

LOG = logging.getLogger("phone_control")


def rpc_call(method, params=None, timeout=2.0):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params if params is not None else [],
        "id": int(time.time() * 1000),
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(RPC_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


class CommandRouter:
    def __init__(self):
        self.lock = Lock()
        self.last_command_time = 0.0
        self.last_command_name = "none"
        self.mission_lock = Lock()
        self.mission_running = False

    def run_command(self, command, speed_label="low"):
        command = (command or "").strip().lower()
        speed_label = (speed_label or "low").strip().lower()

        # Guard against accidental command floods from touch events.
        now = time.time()
        with self.lock:
            if now - self.last_command_time < 0.15 and command != "stop":
                return {"ok": True, "skipped": True, "reason": "throttled"}
            self.last_command_time = now
            self.last_command_name = command

        if command in ("forward", "back", "left", "right"):
            action_id = {
                "forward": "1",  # go_forward_low
                "back": "2",     # back_low
                "left": "3",     # turn_left_low
                "right": "4",    # turn_right_low
            }[command]
            times = {"low": 1, "medium": 2, "high": 3}.get(speed_label, 1)
            return self._rpc_ok("RunAction", [action_id, times], command)

        if command == "stop":
            return self._rpc_ok("RunAction", ["0", 1], command)

        if command == "stand":
            # Height/mode/time values follow existing Stand(height, mode, t).
            return self._rpc_ok("Stand", [160, 2, 500], command)

        if command == "wave":
            return self._rpc_ok("RunAction", ["11", 1], command)

        if command == "dance":
            return self._rpc_ok("RunAction", ["10", 1], command)

        if command == "kick":
            return self._rpc_ok("RunAction", ["12", 1], command)

        if command == "patrol":
            Thread(target=self._run_patrol_macro, daemon=True).start()
            return {"ok": True, "command": command, "macro": "started"}

        if command == "autoavoid":
            started = self._start_autoavoid_mission(duration_sec=30)
            if started:
                return {"ok": True, "command": command, "mission": "auto_avoid_30s_started"}
            return {"ok": False, "command": command, "error": "mission_already_running"}

        return {"ok": False, "error": "unknown_command", "command": command}

    def _run_patrol_macro(self):
        sequence = [
            ("RunAction", ["1", 1], 0.9),
            ("RunAction", ["4", 1], 0.9),
            ("RunAction", ["1", 1], 0.9),
            ("RunAction", ["3", 1], 0.9),
            ("RunAction", ["11", 1], 0.2),
        ]
        for method, params, delay in sequence:
            try:
                rpc_call(method, params=params, timeout=2.0)
            except Exception as exc:  # pragma: no cover - runtime visibility
                LOG.error("patrol macro error: %s", exc)
                break
            time.sleep(delay)
        try:
            rpc_call("RunAction", params=["0", 1], timeout=2.0)
        except Exception:
            pass

    def _rpc_ok(self, method, params, command_name):
        try:
            result = rpc_call(method, params=params, timeout=2.0)
            return {"ok": True, "command": command_name, "rpc": result}
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            return {"ok": False, "command": command_name, "error": str(exc)}
        except Exception as exc:  # pragma: no cover - runtime visibility
            return {"ok": False, "command": command_name, "error": str(exc)}

    def _start_autoavoid_mission(self, duration_sec=30):
        with self.mission_lock:
            if self.mission_running:
                return False
            self.mission_running = True
        Thread(target=self._run_autoavoid_mission, args=(duration_sec,), daemon=True).start()
        return True

    def _run_autoavoid_mission(self, duration_sec):
        start_ts = time.time()
        try:
            # Switch to Avoidance mode and start it.
            rpc_call("LoadFunc", [8], timeout=2.0)
            rpc_call("StartFunc", [], timeout=2.0)
            LOG.info("autoavoid mission started for %ss", duration_sec)

            # Keep behavior alive; Running heartbeat timeout is 7s.
            while time.time() - start_ts < duration_sec:
                try:
                    rpc_call("Heartbeat", [], timeout=2.0)
                except Exception as exc:
                    LOG.warning("autoavoid heartbeat failed: %s", exc)
                time.sleep(2.0)
        except Exception as exc:
            LOG.error("autoavoid mission failed: %s", exc)
        finally:
            # Stop and return to remote-control mode so manual control resumes.
            try:
                rpc_call("StopFunc", [], timeout=2.0)
            except Exception:
                pass
            try:
                rpc_call("UnloadFunc", [], timeout=2.0)
            except Exception:
                pass
            try:
                rpc_call("LoadFunc", [1], timeout=2.0)
                rpc_call("StartFunc", [], timeout=2.0)
            except Exception:
                pass
            with self.mission_lock:
                self.mission_running = False
            LOG.info("autoavoid mission completed")


ROUTER = CommandRouter()
KEEPALIVE_RUNNING = True


def call_openai_json(system_prompt, user_prompt, timeout=10.0):
    if not OPENAI_API_KEY:
        raise RuntimeError("missing OPENAI_API_KEY")
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    req = Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + OPENAI_API_KEY,
        },
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    return json.loads(content)


def heuristic_plan_from_text(prompt_text):
    text = (prompt_text or "").strip().lower()
    duration = 30
    duration_match = re.search(r"(\d+)\s*(s|sec|secs|second|seconds)", text)
    if duration_match:
        duration = max(10, min(120, int(duration_match.group(1))))
    elif "1 minute" in text or "60" in text:
        duration = 60

    steps = []
    if "avoid" in text or "obstacle" in text or "patrol" in text:
        steps.append({"type": "autoavoid", "duration": duration})
    if "forward" in text:
        steps.append({"type": "move", "direction": "forward", "speed": "low", "repeats": 2})
    if "left" in text:
        steps.append({"type": "move", "direction": "left", "speed": "low", "repeats": 1})
    if "right" in text:
        steps.append({"type": "move", "direction": "right", "speed": "low", "repeats": 1})
    if "wave" in text or "greet" in text or "hello" in text:
        steps.append({"type": "action", "name": "wave", "times": 1})
    if "dance" in text or "celebrate" in text:
        steps.append({"type": "action", "name": "dance", "times": 1})
    if "kick" in text:
        steps.append({"type": "action", "name": "kick", "times": 1})
    if not steps:
        steps = [
            {"type": "autoavoid", "duration": 25},
            {"type": "action", "name": "wave", "times": 1},
            {"type": "stand"},
        ]
    if steps[-1].get("type") != "stand":
        steps.append({"type": "stand"})
    return {"name": "planned_mission", "steps": steps}


def validate_plan(plan):
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("plan.steps must be a non-empty array")

    safe_steps = []
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError("each step must be an object")
        step_type = str(step.get("type", "")).strip().lower()
        if step_type == "autoavoid":
            duration = int(step.get("duration", 20))
            duration = max(5, min(120, duration))
            safe_steps.append({"type": "autoavoid", "duration": duration})
        elif step_type == "move":
            direction = str(step.get("direction", "forward")).strip().lower()
            if direction not in ("forward", "back", "left", "right"):
                raise ValueError("invalid move direction")
            speed = str(step.get("speed", "low")).strip().lower()
            if speed not in ("low", "medium", "high"):
                speed = "low"
            repeats = int(step.get("repeats", 1))
            repeats = max(1, min(8, repeats))
            safe_steps.append({"type": "move", "direction": direction, "speed": speed, "repeats": repeats})
        elif step_type == "action":
            name = str(step.get("name", "wave")).strip().lower()
            if name not in ("wave", "dance", "kick", "stand"):
                raise ValueError("invalid action name")
            times = int(step.get("times", 1))
            times = max(1, min(3, times))
            safe_steps.append({"type": "action", "name": name, "times": times})
        elif step_type == "wait":
            duration = int(step.get("duration", 2))
            duration = max(1, min(15, duration))
            safe_steps.append({"type": "wait", "duration": duration})
        elif step_type == "stand":
            safe_steps.append({"type": "stand"})
        else:
            raise ValueError("unsupported step type: " + step_type)

    return {"name": str(plan.get("name", "mission"))[:60], "steps": safe_steps}


class MissionEngine:
    def __init__(self, router):
        self.router = router
        self.lock = Lock()
        self.stop_requested = False
        self.running = False
        self.current_step = -1
        self.current_step_name = "idle"
        self.plan = None
        self.last_result = "idle"
        self.logs = []

    def status(self):
        with self.lock:
            return {
                "running": self.running,
                "current_step": self.current_step,
                "current_step_name": self.current_step_name,
                "last_result": self.last_result,
                "plan": self.plan,
                "logs": self.logs[-15:],
            }

    def append_log(self, msg):
        ts = time.strftime("%H:%M:%S")
        with self.lock:
            self.logs.append("[" + ts + "] " + msg)
            self.logs = self.logs[-100:]

    def request_stop(self):
        with self.lock:
            self.stop_requested = True
        self.append_log("stop requested")

    def start(self, plan):
        with self.lock:
            if self.running:
                return False
            self.running = True
            self.stop_requested = False
            self.plan = plan
            self.current_step = -1
            self.current_step_name = "starting"
            self.last_result = "running"
        Thread(target=self._run_plan, daemon=True).start()
        return True

    def _is_stop_requested(self):
        with self.lock:
            return self.stop_requested

    def _run_plan(self):
        try:
            plan = self.status()["plan"] or {"steps": []}
            steps = plan.get("steps", [])
            self.append_log("mission started: " + plan.get("name", "mission"))
            for idx, step in enumerate(steps):
                if self._is_stop_requested():
                    self.append_log("mission interrupted by operator")
                    break
                step_name = step.get("type", "step")
                with self.lock:
                    self.current_step = idx
                    self.current_step_name = step_name
                self.append_log("step " + str(idx + 1) + "/" + str(len(steps)) + ": " + json.dumps(step))
                self._execute_step(step)
            self.append_log("mission finished")
            self.last_result = "completed"
        except Exception as exc:
            self.append_log("mission error: " + str(exc))
            self.last_result = "error"
        finally:
            try:
                # Always return to safe manual state.
                rpc_call("RunAction", ["0", 1], timeout=2.0)
            except Exception:
                pass
            try:
                rpc_call("StopFunc", [], timeout=2.0)
            except Exception:
                pass
            try:
                rpc_call("UnloadFunc", [], timeout=2.0)
            except Exception:
                pass
            try:
                rpc_call("LoadFunc", [1], timeout=2.0)
                rpc_call("StartFunc", [], timeout=2.0)
            except Exception:
                pass
            with self.lock:
                self.running = False
                self.stop_requested = False
                self.current_step_name = "idle"
                self.current_step = -1

    def _execute_step(self, step):
        step_type = step["type"]
        if step_type == "autoavoid":
            duration = step["duration"]
            rpc_call("LoadFunc", [8], timeout=2.0)
            rpc_call("StartFunc", [], timeout=2.0)
            t_end = time.time() + duration
            while time.time() < t_end:
                if self._is_stop_requested():
                    break
                try:
                    rpc_call("Heartbeat", [], timeout=2.0)
                except Exception:
                    pass
                time.sleep(1.5)
            rpc_call("StopFunc", [], timeout=2.0)
            rpc_call("UnloadFunc", [], timeout=2.0)
            rpc_call("LoadFunc", [1], timeout=2.0)
            rpc_call("StartFunc", [], timeout=2.0)
            return

        if step_type == "move":
            action_id = {
                "forward": "1",
                "back": "2",
                "left": "3",
                "right": "4",
            }[step["direction"]]
            times = {"low": 1, "medium": 2, "high": 3}.get(step["speed"], 1)
            for _ in range(step["repeats"]):
                if self._is_stop_requested():
                    break
                rpc_call("RunAction", [action_id, times], timeout=2.0)
                time.sleep(0.8)
            rpc_call("RunAction", ["0", 1], timeout=2.0)
            return

        if step_type == "action":
            action_name = step["name"]
            if action_name == "stand":
                rpc_call("Stand", [160, 2, 500], timeout=2.0)
                return
            action_id = {"wave": "11", "dance": "10", "kick": "12"}[action_name]
            rpc_call("RunAction", [action_id, step["times"]], timeout=2.0)
            time.sleep(1.0)
            rpc_call("RunAction", ["0", 1], timeout=2.0)
            return

        if step_type == "wait":
            t_end = time.time() + step["duration"]
            while time.time() < t_end:
                if self._is_stop_requested():
                    break
                time.sleep(0.2)
            return

        if step_type == "stand":
            rpc_call("Stand", [160, 2, 500], timeout=2.0)
            return


MISSION_ENGINE = MissionEngine(ROUTER)

def ensure_remote_control_mode():
    """
    Try to enable SpiderPi remote-control function mode on startup so MJPEG
    stream and remote control behave consistently for demo usage.
    """
    attempts = 5
    for idx in range(attempts):
        try:
            load_ret = rpc_call("LoadFunc", [1], timeout=2.0)
            start_ret = rpc_call("StartFunc", [], timeout=2.0)
            LOG.info("startup mode init ok: LoadFunc=%s StartFunc=%s", load_ret, start_ret)
            return
        except Exception as exc:  # pragma: no cover - runtime visibility
            LOG.warning("startup mode init retry %d/%d failed: %s", idx + 1, attempts, exc)
            time.sleep(1.0)
    LOG.warning("startup mode init failed after retries; continue serving UI/API")


def heartbeat_keepalive():
    """
    Keep SpiderPi function mode alive so camera/mode is not auto-unloaded by the
    7-second heartbeat timeout in Functions/Running.py.
    """
    while KEEPALIVE_RUNNING:
        try:
            rpc_call("Heartbeat", [], timeout=2.0)
        except Exception as exc:
            LOG.debug("heartbeat keepalive failed: %s", exc)
        time.sleep(2.0)


class PhoneControlHandler(BaseHTTPRequestHandler):
    server_version = "SpiderPiPhoneControl/1.0"

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            mission_status = MISSION_ENGINE.status()
            self._write_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "rpc_url": RPC_URL,
                    "last_command": ROUTER.last_command_name,
                    "mission_running": mission_status["running"],
                    "mission_step": mission_status["current_step_name"],
                    "timestamp": int(time.time()),
                },
            )
            return
        if self.path == "/api/ensure_mode":
            try:
                ensure_remote_control_mode()
                self._write_json(HTTPStatus.OK, {"ok": True, "message": "mode ensured"})
            except Exception as exc:
                self._write_json(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return
        if self.path.startswith("/api/camera.jpg"):
            self._serve_camera_snapshot()
            return
        if self.path == "/api/mission/status":
            self._write_json(HTTPStatus.OK, {"ok": True, "mission": MISSION_ENGINE.status()})
            return

        if self.path in ("/", "/index.html"):
            self._serve_static("index.html", "text/html; charset=utf-8")
            return
        if self.path == "/app.js":
            self._serve_static("app.js", "application/javascript; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._serve_static("styles.css", "text/css; charset=utf-8")
            return

        self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if self.path not in ("/api/command", "/api/mission/plan", "/api/mission/start", "/api/mission/stop"):
            self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not_found"})
            return

        body = self._read_json_body()
        if body is None:
            self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid_json"})
            return

        if self.path == "/api/mission/plan":
            prompt = str(body.get("prompt", "")).strip()
            if not prompt:
                self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "missing prompt"})
                return
            plan = None
            planner = "heuristic"
            try:
                ai_output = call_openai_json(
                    "You convert robot requests into safe mission JSON. Output only JSON with keys: name, steps. "
                    "Allowed steps: autoavoid(duration), move(direction,speed,repeats), action(name,times), wait(duration), stand.",
                    prompt,
                    timeout=12.0,
                )
                plan = validate_plan(ai_output)
                planner = "ai"
            except Exception as exc:
                LOG.info("AI planner unavailable, using heuristic planner: %s", exc)
                try:
                    plan = validate_plan(heuristic_plan_from_text(prompt))
                except Exception as inner_exc:
                    self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(inner_exc)})
                    return
            self._write_json(HTTPStatus.OK, {"ok": True, "planner": planner, "plan": plan})
            return

        if self.path == "/api/mission/start":
            plan = body.get("plan")
            try:
                safe_plan = validate_plan(plan)
            except Exception as exc:
                self._write_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
                return
            if not MISSION_ENGINE.start(safe_plan):
                self._write_json(HTTPStatus.CONFLICT, {"ok": False, "error": "mission already running"})
                return
            self._write_json(HTTPStatus.OK, {"ok": True, "mission": MISSION_ENGINE.status()})
            return

        if self.path == "/api/mission/stop":
            MISSION_ENGINE.request_stop()
            self._write_json(HTTPStatus.OK, {"ok": True, "mission": MISSION_ENGINE.status()})
            return

        command = body.get("command")
        speed = body.get("speed", "low")
        mission_status = MISSION_ENGINE.status()
        if mission_status["running"] and command != "stop":
            self._write_json(HTTPStatus.CONFLICT, {"ok": False, "error": "mission running; use stop or mission stop"})
            return
        response = ROUTER.run_command(command, speed_label=speed)
        status = HTTPStatus.OK if response.get("ok") else HTTPStatus.BAD_GATEWAY
        self._write_json(status, response)

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw) if raw else {}
        except Exception:
            return None

    def _serve_static(self, filename, content_type):
        path = os.path.join(WEB_DIR, filename)
        if not os.path.isfile(path):
            self._write_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "missing_static_file"})
            return
        with open(path, "rb") as fh:
            payload = fh.read()
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_camera_snapshot(self):
        try:
            req = Request(CAMERA_SNAPSHOT_URL, method="GET")
            with urlopen(req, timeout=2.0) as resp:
                payload = resp.read()
            if not payload:
                raise RuntimeError("empty camera snapshot")
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            LOG.warning("camera snapshot failed: %s", exc)
            self._write_json(HTTPStatus.SERVICE_UNAVAILABLE, {"ok": False, "error": "camera_unavailable"})

    def _write_json(self, status, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format_, *args):  # pragma: no cover
        LOG.info("%s - %s", self.address_string(), format_ % args)


def main():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    ensure_remote_control_mode()
    Thread(target=heartbeat_keepalive, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), PhoneControlHandler)
    LOG.info("phone control server listening on %s:%s (rpc: %s)", HOST, PORT, RPC_URL)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
