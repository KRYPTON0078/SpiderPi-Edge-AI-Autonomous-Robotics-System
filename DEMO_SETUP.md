# SpiderPi Phone + Voice Demo Setup

This setup keeps **robot-side control in Python** and uses your phone browser for UI + voice capture.

## 1) Files to copy to robot

Copy these into `/home/pi/SpiderPi` on the robot:

- `phone_control_server.py`
- `web/index.html`
- `web/app.js`
- `web/styles.css`
- `DEMO_SETUP.md` (optional for reference)

## 2) Dependency install (32-bit safe path)

Run on robot terminal:

```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv python3-numpy python3-yaml python3-serial python3-smbus i2c-tools pigpio python3-rpi.gpio
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install werkzeug json-rpc
```

Quick verify:

```bash
python3 -c "import cv2, numpy, yaml, werkzeug, jsonrpc, serial, pigpio; print('python deps ok')"
```

If any import fails, install that package first before demo.

## 3) Start SpiderPi core services

### Option A (recommended): use existing auto-start service

```bash
sudo systemctl status spiderpi
```

If not running:

```bash
sudo systemctl start spiderpi
```

### Option B: run manually

```bash
cd /home/pi/SpiderPi
python3 SpiderPi.py
```

Keep this running in one terminal.

## 4) Start phone control Python server

Open a second terminal:

```bash
cd /home/pi/SpiderPi
python3 phone_control_server.py
```

Default URL: `http://<robot-ip>:5000`

Get robot IP:

```bash
hostname -I
```

## 5) Demo from phone (same Wi-Fi)

1. Connect phone to same Wi-Fi as robot.
2. Open `http://<robot-ip>:5000` in phone browser.
3. Test buttons in this order:
   - `Stand`
   - `Forward`, `Left`, `Right`, `Back`
   - `STOP`
4. Test voice:
   - Tap `Start Voice`
   - Grant microphone permission
   - Say commands: `forward`, `left`, `right`, `back`, `stop`, `wave`, `dance`, `kick`, `patrol`

## 5.1) AI Mission Commander (new)

Open mission panel in the web UI:

- Enter prompt example: `Patrol with obstacle avoidance for 40 seconds, then wave and stand.`
- Tap `Plan Mission`
- Tap `Start Planned Mission`
- Monitor mission logs in the panel
- Use `Stop Mission` to interrupt safely

### Optional cloud AI planner

If you have internet and an API key, set on robot terminal before launch:

```bash
export OPENAI_API_KEY="your_key_here"
export OPENAI_MODEL="gpt-4o-mini"
python3 phone_control_server.py
```

If key is missing/unavailable, planner automatically falls back to a local heuristic planner.

## 6) Command mapping

These map to existing action groups in `ActionGroupDict.py`:

- `forward` -> `RunAction("1", times)` -> `go_forward_low`
- `back` -> `RunAction("2", times)` -> `back_low`
- `left` -> `RunAction("3", times)` -> `turn_left_low`
- `right` -> `RunAction("4", times)` -> `turn_right_low`
- `stop` -> `RunAction("0", 1)` -> stop current action
- `wave` -> `RunAction("11", 1)`
- `dance` -> `RunAction("10", 1)`
- `kick` -> `RunAction("12", 1)`
- `patrol` -> short macro sequence

## 7) Camera preview

UI automatically tries:

- `http://<robot-ip>:8080`

If camera does not appear:

- Confirm `SpiderPi.py` is running
- Open `http://<robot-ip>:8080` directly in phone browser

## 8) Demo fallback plan (very important)

If voice fails:

- Continue with touch buttons only (still valid and stable).

If phone UI fails:

- Verify server with `http://<robot-ip>:5000/api/health`
- Restart control server:
  ```bash
  pkill -f phone_control_server.py
  cd /home/pi/SpiderPi
  python3 phone_control_server.py
  ```

If robot does not move:

- Ensure no blocking mode is active in other scripts.
- Try `Stand` then `Forward` then `STOP`.

## 9) Optional auto-start for control server

For tomorrow, manual start is safer. After demo you can add a systemd service if needed.
