# energy_project1

Cognitive Energy Optimization System. Built with a React + Vite dashboard and a Python Flask backend serving real machine learning telemetry.

## Local Windows setup

Run these commands from **Command Prompt** in the extracted repository folder:

```bat
cd /d "<project-folder>"
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python api_server.py
```

The backend binds to `0.0.0.0` on port `5000` by default. If occupied, it prints and uses port `5001`; set `IREOS_PORT` before starting to choose a port explicitly. Verify locally at `http://127.0.0.1:5000/api/health` (substitute the printed port). Allow Python/Flask through **Windows Defender Firewall on Private networks**. From another LAN device, verify `http://<backend-laptop-IPv4>:5000/api/health`. The ESP32 URL and dashboard URL must use the same port.

In a second Command Prompt:

```bat
cd /d "<project-folder>\dashboard"
npm install
npm run dev
```

The dashboard's local Live API default is `http://127.0.0.1:5000`. Use Settings → Backend URL to change it when needed. The dashboard's package script is `dev` (Vite); the root package has no `dev` script.

## Register and configure physical ESP32

1. Start Flask and create/sign in to an account using the dashboard. Copy its House ID from Settings.
2. In another Command Prompt at the repository root run `python register_physical_esp32.py --house-id HSE-...`. This uses the existing `houses`, `devices`, and `appliances` tables. It prints the generated IDs and one-time device secret; keep that secret private.
3. Edit the clearly marked constants near the top of `hardware/esp32/firmware/ireos_esp32.ino`: `BACKEND_BASE_URL`, `DEVICE_ID`, `DEVICE_SECRET`, `APPLIANCE_ID`, and `HOUSE_ID`. The current network example is `http://10.106.86.45:5000`; change the address when the backend laptop/network changes. Do not commit real credentials.
4. In Arduino IDE install the libraries **WiFiManager** (tzapu), **ArduinoJson**, **PZEM004T v3**, **DHT sensor library** (Adafruit), and **hd44780** (Bill Perry). Select ESP32 Dev Module, compile/upload, then open Serial Monitor at 115200 baud.

The firmware defaults the active-low relay to OFF, reads actual PZEM/DHT values, keeps sensor sampling/LCD/local overload protection working while the backend is unavailable, and retries authenticated uploads. GPIO 27 held LOW for about five seconds clears WiFiManager credentials; the device restarts and opens `IREOS_SETUP` (password `ireos1234`). The configuration portal is nonblocking.

## Telemetry and control behavior

Physical telemetry uses `device_id`, `house_id`, `appliance_id`, `appliance`, `voltage`, `current`, `power_w`, `energy_kwh`, `frequency`, `pf`, `temperature`, `humidity`, `relay_state`, `status`, and optional `latest_rl_action_code` / `latest_rl_action`. Missing sensor readings are JSON `null`; missing PZEM power prevents an upload rather than being replaced with a fake value. Authentication is sent only in `X-Device-Id` and `X-Device-Secret` headers. Unknown/incorrect credentials receive HTTP 401; telemetry no longer silently registers devices or rotates secrets.

The ESP32 polls the existing authenticated `GET /api/control-loop` and consumes its array row for the configured appliance: `rlActionCode` 0–3, `rlAction`, `decisionSource`, `nextAction`, and `safetyStatus`. Semantics remain 0 Maintain, 1 Reduce Load, 2 Shift Usage, 3 Turn OFF. A single relay physically supports OFF; 1 and 2 are reported but not claimed/executed. Only action 3 from a loaded RL model, when not safety-blocked, turns the relay off. Action 0 leaves the safe current state unchanged. The local configurable 500 W overload trip independently switches OFF. Boot state is OFF.

Dashboard live hardware status is based on fresh (30-second) telemetry identified as ESP32; simulator telemetry is labeled separately, and readings are not substituted with simulator/default sensor values. `/api/health` reports DB status/count, loaded model counts, expected/missing model artifacts, replay-data artifacts, and most recent live hardware telemetry.

## Tests and evidence limits

With Flask running, verify both `http://127.0.0.1:5000/api/health` and the laptop LAN URL. Existing automated API suites can be run from the root with `python -m unittest test_phase15_multiuser test_phase16_production_db test_phase17a_simulator`. They validate registration, telemetry persistence, bad-secret rejection, ownership checks, and simulator compatibility. They do **not** prove physical sensor readings, Wi-Fi portal behavior, LCD rendering, relay switching, or end-to-end dashboard hardware display; those require the connected ESP32, router, and dashboard browser.

Model artifacts are read relative to the repository root from `ml_models/` (`*_energy_model.pkl`, `*_status_classifier.pkl`, `*_anomaly_model.pkl`, plus two comparison CSVs), `rl_models/` (`*_rl_agent.pkl`), and replay CSVs from `ml_data/`. The artifact directories are not present in this repository snapshot, so no models or replay data can be reported as loaded until these files are supplied. Model absence is exposed in `/api/health`, not hidden.
"# IRESO-PROJECT" 
