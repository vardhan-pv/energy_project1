"""
=============================================================================
Cognitive Energy Optimization System — Flask API Backend
=============================================================================
Serves real telemetry, predictions, and control-loop state to the React
dashboard by loading the trained ML models (.pkl) and replaying actual
household data from the UK-DALE CSVs.

Start:
    python api_server.py

The dashboard connects via Settings → Use Live API → http://localhost:5000
=============================================================================
"""

import os
import time
import math
import threading
import collections
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

import db_manager as db

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ML_MODELS_DIR = BASE_DIR / "ml_models"
RL_MODELS_DIR = BASE_DIR / "rl_models"
PEAK_MODELS_DIR = BASE_DIR / "peak_models"
ML_DATA_DIR = BASE_DIR / "ml_data"

APPLIANCE_IDS = ["laptop", "kitchen_lights", "office_fan", "fridge"]

# ---------------------------------------------------------------------------
# Appliance meta — matches the dashboard's ApplianceProfile type
# ---------------------------------------------------------------------------
APPLIANCE_PROFILES = {
    "laptop": {
        "id": "laptop",
        "name": "Laptop",
        "room": "Study",
        "icon": "laptop",
        "ratedPowerW": 55,
        "minPowerW": 8,
        "maxPowerW": 95,
        "criticalAlwaysOn": False,
        "hasTemperature": True,
        "description": "Work laptop and charger. Uses more power while charging.",
    },
    "kitchen_lights": {
        "id": "kitchen_lights",
        "name": "Kitchen Lights",
        "room": "Kitchen",
        "icon": "lightbulb",
        "ratedPowerW": 42,
        "minPowerW": 0,
        "maxPowerW": 60,
        "criticalAlwaysOn": False,
        "hasTemperature": False,
        "description": "Dimmable LED ceiling lights above the counter.",
    },
    "office_fan": {
        "id": "office_fan",
        "name": "Office Fan",
        "room": "Study",
        "icon": "fan",
        "ratedPowerW": 48,
        "minPowerW": 12,
        "maxPowerW": 75,
        "criticalAlwaysOn": False,
        "hasTemperature": True,
        "description": "Pedestal fan with variable speed, tied to room comfort.",
    },
    "fridge": {
        "id": "fridge",
        "name": "Fridge",
        "room": "Kitchen",
        "icon": "refrigerator",
        "ratedPowerW": 120,
        "minPowerW": 2,
        "maxPowerW": 190,
        "criticalAlwaysOn": True,
        "hasTemperature": True,
        "description": "Always-on refrigerator. Cycles its compressor to stay cold.",
    },
}

# ---------------------------------------------------------------------------
# Global model store – populated at startup
# ---------------------------------------------------------------------------
energy_models = {}       # {appliance: sklearn model}
status_classifiers = {}  # {appliance: sklearn model}
anomaly_models = {}      # {appliance: IsolationForest}
rl_agents = {}           # {appliance: dict with model, scaler, features, actions}

# Model metadata read from the CSVs produced during training
model_metadata = {}      # {appliance: {model, R2, MAE, RMSE, ...}}
status_metadata = {}     # {appliance: {accuracy, precision, recall, f1}}

# ---------------------------------------------------------------------------
# Live state – maintained by the replay thread
# ---------------------------------------------------------------------------
_lock = threading.Lock()

# Per-appliance sliding window of recent telemetry samples
_telemetry_buffers: dict[str, list[dict]] = {aid: [] for aid in APPLIANCE_IDS}

# Per-appliance current state
_current_state: dict[str, dict] = {}

# Control overrides from the UI
_control_overrides: dict[str, dict] = {}

# Alert accumulator
_alerts: list[dict] = []

# Replay cursor — index into each CSV
_replay_cursors: dict[str, int] = {}

# Preloaded data chunks (last N rows from each CSV for replay)
REPLAY_WINDOW = 500  # rows loaded into memory
_replay_data: dict[str, pd.DataFrame] = {}


def load_models():
    """Load all trained models from disk."""
    print("[boot] Loading trained models ...")

    # --- Energy models & metadata ------------------------------------------
    try:
        comparison = pd.read_csv(ML_MODELS_DIR / "model_comparison.csv")
        for _, row in comparison.iterrows():
            model_metadata[row["appliance"]] = {
                "model_type": row["model"],
                "MAE": round(row["MAE"], 4),
                "RMSE": round(row["RMSE"], 4),
                "R2": round(row["R2"], 6),
                "training_time_min": round(row["training_time_minutes"], 2),
            }
    except Exception as e:
        print(f"[warn] Could not read model_comparison.csv: {e}")

    # --- Status classifier metadata ----------------------------------------
    try:
        status_comp = pd.read_csv(ML_MODELS_DIR / "status_classifier_comparison.csv")
        for _, row in status_comp.iterrows():
            status_metadata[row["appliance"]] = {
                "accuracy": round(row["accuracy"], 6),
                "precision": round(row["precision"], 6),
                "recall": round(row["recall"], 6),
                "f1": round(row["f1"], 6),
            }
    except Exception as e:
        print(f"[warn] Could not read status_classifier_comparison.csv: {e}")

    for aid in APPLIANCE_IDS:
        # Energy model
        path = ML_MODELS_DIR / f"{aid}_energy_model.pkl"
        if path.exists():
            energy_models[aid] = joblib.load(path)
            print(f"  [OK] energy model   : {aid} ({type(energy_models[aid]).__name__})")

        # Status classifier
        path = ML_MODELS_DIR / f"{aid}_status_classifier.pkl"
        if path.exists():
            status_classifiers[aid] = joblib.load(path)
            print(f"  [OK] status model   : {aid}")

        # Anomaly detector
        path = ML_MODELS_DIR / f"{aid}_anomaly_model.pkl"
        if path.exists():
            anomaly_models[aid] = joblib.load(path)
            print(f"  [OK] anomaly model  : {aid}")

        # RL agent
        path = RL_MODELS_DIR / f"{aid}_rl_agent.pkl"
        if path.exists():
            rl_agents[aid] = joblib.load(path)
            print(f"  [OK] RL agent       : {aid}")

    print(f"[boot] Loaded {len(energy_models)} energy, "
          f"{len(status_classifiers)} status, "
          f"{len(anomaly_models)} anomaly, "
          f"{len(rl_agents)} RL models")


def load_replay_data():
    """Load the tail of each ML CSV into memory for replaying."""
    print("[boot] Loading replay data from CSVs ...")
    for aid in APPLIANCE_IDS:
        csv_path = ML_DATA_DIR / f"{aid}_ml.csv"
        if not csv_path.exists():
            print(f"  [MISS] {csv_path.name} not found")
            continue
        # Read just the last REPLAY_WINDOW rows efficiently
        # Count total lines first, then skip to near the end
        try:
            # For large files, use skiprows to get only the tail
            total = sum(1 for _ in open(csv_path, "r", encoding="utf-8")) - 1  # minus header
            skip = max(0, total - REPLAY_WINDOW)
            df = pd.read_csv(csv_path, skiprows=range(1, skip + 1))
            _replay_data[aid] = df.reset_index(drop=True)
            _replay_cursors[aid] = 0
            print(f"  [OK] {aid}: {len(df)} rows loaded (from total {total})")
        except Exception as e:
            print(f"  [ERR] {aid}: {e}")

    # Initialize current state from first rows
    _init_current_state()


def _init_current_state():
    """Set up initial appliance state from the first replay row."""
    now_ms = int(time.time() * 1000)
    for aid in APPLIANCE_IDS:
        df = _replay_data.get(aid)
        if df is None or df.empty:
            # Fallback if no data
            _current_state[aid] = _make_default_state(aid, now_ms)
            continue

        row = df.iloc[0]
        profile = APPLIANCE_PROFILES[aid]
        power = float(row["power_w"])
        status_val = int(row.get("status", 1))

        _current_state[aid] = {
            "id": aid,
            "status": "on" if status_val == 1 else "off",
            "mode": "maintain",
            "powerW": round(power, 1),
            "targetPowerW": profile["ratedPowerW"],
            "energyTodayKwh": 0.0,
            "temperatureC": _estimate_temperature(aid, power, profile),
            "anomalyScore": 0.05,
            "risk": "normal",
            "online": True,
            "signalPct": 72 + (profile["ratedPowerW"] * 7) % 25,
            "batteryPct": 84 if aid == "office_fan" else (91 if aid == "kitchen_lights" else None),
            "lastSeen": now_ms,
            "history": [],
        }


def _make_default_state(aid: str, now_ms: int) -> dict:
    profile = APPLIANCE_PROFILES[aid]
    return {
        "id": aid,
        "status": "on",
        "mode": "maintain",
        "powerW": profile["ratedPowerW"] * 0.8,
        "targetPowerW": profile["ratedPowerW"],
        "energyTodayKwh": 0.0,
        "temperatureC": _estimate_temperature(aid, profile["ratedPowerW"] * 0.8, profile),
        "anomalyScore": 0.05,
        "risk": "normal",
        "online": True,
        "signalPct": 72 + (profile["ratedPowerW"] * 7) % 25,
        "batteryPct": 84 if aid == "office_fan" else (91 if aid == "kitchen_lights" else None),
        "lastSeen": now_ms,
        "history": [],
    }


def _estimate_temperature(aid: str, power: float, profile: dict) -> float | None:
    """Produce a plausible temperature reading for appliances that have one."""
    if not profile.get("hasTemperature"):
        return None
    if aid == "fridge":
        return round(4.2 + math.sin(time.time() / 900) * 0.9 + (np.random.random() - 0.5) * 0.4, 1)
    elif aid == "laptop":
        return round(38 + (power / profile["maxPowerW"]) * 18 + (np.random.random() - 0.5) * 1.5, 1)
    else:
        return round(25.5 + (np.random.random() - 0.5) * 1.6 - (power / profile["maxPowerW"]) * 1.4, 1)


ENERGY_FEATURES = ["status", "hour", "day_of_week", "is_weekend", "month",
                   "power_lag_1", "power_lag_5", "power_rolling_mean", "power_rolling_max"]

ANOMALY_FEATURES = ["power_w", "status", "hour", "day_of_week", "is_weekend", "month",
                    "power_lag_1", "power_lag_5", "power_rolling_mean", "power_rolling_max"]


def _build_features_from_row(row: pd.Series) -> dict:
    """Extract the standard feature dict from a CSV row."""
    return {
        "status": int(row.get("status", 1)),
        "hour": int(row.get("hour", datetime.now().hour)),
        "day_of_week": int(row.get("day_of_week", datetime.now().weekday())),
        "is_weekend": int(row.get("is_weekend", 1 if datetime.now().weekday() >= 5 else 0)),
        "month": int(row.get("month", datetime.now().month)),
        "power_lag_1": float(row.get("power_lag_1", row.get("power_w", 0))),
        "power_lag_5": float(row.get("power_lag_5", row.get("power_w", 0))),
        "power_rolling_mean": float(row.get("power_rolling_mean", row.get("power_w", 0))),
        "power_rolling_max": float(row.get("power_rolling_max", row.get("power_w", 0))),
        "power_w": float(row.get("power_w", 0)),
    }


def _predict_power(aid: str, features: dict) -> float | None:
    """Run the energy model to predict power for an appliance."""
    model = energy_models.get(aid)
    if model is None:
        return None
    X = pd.DataFrame([{f: features[f] for f in ENERGY_FEATURES}])
    try:
        pred = model.predict(X)[0]
        return round(max(0, float(pred)), 1)
    except Exception:
        return None


def _anomaly_score(aid: str, features: dict) -> float:
    """Run the anomaly detector and return a 0-1 score."""
    model = anomaly_models.get(aid)
    if model is None:
        return 0.05
    X = pd.DataFrame([{f: features[f] for f in ANOMALY_FEATURES}])
    try:
        # IsolationForest: decision_function returns negative for anomalies
        raw = model.decision_function(X)[0]
        # Map to 0-1: more negative = more anomalous
        score = max(0.0, min(1.0, 0.5 - raw * 0.5))
        return round(score, 3)
    except Exception:
        return 0.05


def _risk_level(anomaly_score: float) -> str:
    if anomaly_score > 0.6:
        return "risk"
    if anomaly_score > 0.32:
        return "watch"
    return "normal"


# ---------------------------------------------------------------------------
# Replay thread — advances the cursor every 2 seconds
# ---------------------------------------------------------------------------
TICK_INTERVAL = 2.0  # seconds
_tick_count = 0
_energy_accumulator: dict[str, float] = {aid: 0.0 for aid in APPLIANCE_IDS}
_daily_reset_day = datetime.now().day

HISTORY_BUFFER_SIZE = 90


def replay_tick():
    """Advance one tick: read next row from each CSV, run models, update state."""
    global _tick_count, _daily_reset_day
    _tick_count += 1
    now = datetime.now()
    now_ms = int(time.time() * 1000)

    # Reset daily energy at midnight
    if now.day != _daily_reset_day:
        _daily_reset_day = now.day
        for aid in APPLIANCE_IDS:
            _energy_accumulator[aid] = 0.0

    with _lock:
        for aid in APPLIANCE_IDS:
            df = _replay_data.get(aid)
            if df is None or df.empty:
                continue

            # Get next row (wrap around)
            cursor = _replay_cursors[aid]
            row = df.iloc[cursor % len(df)]
            _replay_cursors[aid] = (cursor + 1) % len(df)

            # Check for control overrides
            override = _control_overrides.get(aid, {})
            forced_off = override.get("status") == "off"
            mode = override.get("mode", _current_state[aid].get("mode", "maintain"))

            # Build features from the real data row
            features = _build_features_from_row(row)

            # Get real power from data
            real_power = float(row["power_w"])

            # If forced off, power is 0
            if forced_off:
                power = 0.0
            else:
                # Use real data power, optionally adjusted by mode
                mode_factor = {"maintain": 1.0, "reduce": 0.75, "increase": 1.2, "eco": 0.6}.get(mode, 1.0)
                power = round(real_power * mode_factor, 1)

            # Run anomaly detection on the real features
            features["power_w"] = power
            a_score = _anomaly_score(aid, features)
            risk = _risk_level(a_score)

            # Accumulate energy
            dt_h = TICK_INTERVAL / 3600.0
            _energy_accumulator[aid] += (power * dt_h) / 1000.0
            energy_today = round(_energy_accumulator[aid], 5)

            profile = APPLIANCE_PROFILES[aid]
            temp = _estimate_temperature(aid, power, profile)
            target_w = override.get("targetW", profile["ratedPowerW"])

            # Predict status using trained status classifier model if available
            status_clf = status_classifiers.get(aid)
            if forced_off:
                status_str = "off"
            elif status_clf is not None:
                try:
                    status_cols = ['power_w', 'hour', 'day_of_week', 'is_weekend', 'month', 'power_lag_1', 'power_lag_5', 'power_rolling_mean', 'power_rolling_max']
                    X_status = pd.DataFrame([{col: features.get(col, 0) for col in status_cols}])
                    pred_status = status_clf.predict(X_status)[0]
                    status_str = "on" if int(pred_status) == 1 else "off"
                except Exception:
                    status_str = "on" if int(row.get("status", 1)) == 1 else "off"
            else:
                status_str = "on" if int(row.get("status", 1)) == 1 else "off"

            # Build telemetry sample
            sample = {
                "t": now_ms,
                "powerW": power,
                "energyKwh": energy_today,
                "temperatureC": temp,
                "status": status_str,
            }

            # Update history buffer
            buf = _telemetry_buffers[aid]
            buf.append(sample)
            if len(buf) > HISTORY_BUFFER_SIZE:
                _telemetry_buffers[aid] = buf[-HISTORY_BUFFER_SIZE:]

            # Update current state
            _current_state[aid] = {
                "id": aid,
                "status": status_str,
                "mode": mode,
                "powerW": power,
                "targetPowerW": target_w,
                "energyTodayKwh": energy_today,
                "temperatureC": temp,
                "anomalyScore": a_score,
                "risk": risk,
                "online": True,
                "signalPct": 72 + (profile["ratedPowerW"] * 7) % 25,
                "batteryPct": 84 if aid == "office_fan" else (91 if aid == "kitchen_lights" else None),
                "lastSeen": now_ms,
                "history": list(_telemetry_buffers[aid]),
            }

            # Generate alerts for anomalies
            if risk == "risk":
                alert_id = f"{now_ms}-{aid}"
                # Avoid duplicate alerts
                existing = {a["id"] for a in _alerts}
                if alert_id not in existing:
                    _alerts.append({
                        "id": alert_id,
                        "t": now_ms,
                        "appliance": aid,
                        "severity": "critical",
                        "title": f"{profile['name']}: unusual power draw",
                        "detail": f"Measured {power:.0f} W, anomaly score {a_score:.2f}. "
                                  f"Check this appliance.",
                        "acknowledged": False,
                    })
                    # Keep alerts bounded
                    if len(_alerts) > 40:
                        _alerts[:] = _alerts[-40:]


def _replay_loop():
    """Background thread that runs replay_tick() every TICK_INTERVAL seconds."""
    while True:
        try:
            replay_tick()
        except Exception as e:
            print(f"[replay] Error: {e}")
        time.sleep(TICK_INTERVAL)


# ---------------------------------------------------------------------------
# Flask app & Auth Helpers
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "allow_headers": "*", "methods": "*"}}, supports_credentials=True)

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return response


def get_auth_user_id():
    """Extract authenticated user_id from Authorization: Bearer <token> header."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        decoded = db.decode_token(token)
        if decoded:
            uid = decoded.get("user_id")
            if uid and db.user_exists(uid):
                return uid
    return None


HOUSE = {
    "id": "HOUSE_87B7EB2B",
    "name": "rama nilaya",
    "location": "Bengaluru, Karnataka, India",
    "status": "ONLINE",
    "dataStatus": "AVAILABLE",
}


# ---------------------------------------------------------------------------
# Phase 15: Auth & Setup APIs
# ---------------------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    if not name or not email or not password:
        return jsonify({"ok": False, "error": "Name, email, and password are required"}), 400
    try:
        res = db.register_user(name, email, password)
        return jsonify({
            "ok": True,
            "user": {"user_id": res["user_id"], "name": res["name"], "email": res["email"]},
            "token": res["token"],
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(force=True, silent=True) or {}
    identifier = data.get("user_id") or data.get("email") or data.get("identifier")
    password = data.get("password")
    if not identifier or not password:
        return jsonify({"ok": False, "error": "User ID/email and password are required"}), 400
    try:
        res = db.authenticate_user(identifier, password)
        return jsonify({
            "ok": True,
            "user": {"user_id": res["user_id"], "name": res["name"], "email": res["email"]},
            "token": res["token"],
        })
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 401
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/auth/me", methods=["GET"])
def auth_me():
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    profile = db.get_user_profile(user_id)
    if not profile:
        return jsonify({"ok": False, "error": "User not found"}), 404
    return jsonify({"ok": True, "user": profile})


@app.route("/api/auth/profile", methods=["PUT"])
def update_auth_profile():
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    email = data.get("email")
    try:
        updated = db.update_user_profile(user_id, name, email)
        return jsonify({"ok": True, "user": updated})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 409
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/houses", methods=["GET", "POST"])
def manage_houses():
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    try:
        if request.method == "POST":
            data = request.get_json(force=True, silent=True) or {}
            house_name = data.get("house_name") or data.get("name")
            location = data.get("location", "Home")
            if not house_name:
                return jsonify({"ok": False, "error": "House name required"}), 400

            existing = db.get_user_houses(user_id)
            if existing:
                updated = db.update_house(existing[0]["id"], house_name, location)
                return jsonify({"ok": True, "house": updated})

            house = db.create_house(user_id, house_name, location)
            return jsonify({"ok": True, "house": house})
        else:
            houses = db.get_user_houses(user_id)
            return jsonify(houses)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/houses/<house_id>", methods=["PUT"])
def update_house_route(house_id):
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    data = request.get_json(force=True, silent=True) or {}
    house_name = data.get("house_name") or data.get("name")
    location = data.get("location")
    updated = db.update_house(house_id, house_name, location)
    if not updated:
        return jsonify({"ok": False, "error": "House not found"}), 404
    return jsonify({"ok": True, "house": updated})


@app.route("/api/devices", methods=["GET", "POST"])
def manage_devices():
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    houses = db.get_user_houses(user_id)
    if not houses:
        return jsonify({"ok": False, "error": "No house registered for this user"}), 404
    house_id = houses[0]["id"]
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        device_type = data.get("device_type", "ESP32")
        device_name = data.get("device_name", "Smart Controller")
        mac_address = data.get("mac_address")
        dev = db.create_device(house_id, device_type, device_name, mac_address)
        return jsonify({"ok": True, "device": dev})
    else:
        devs = db.get_house_devices(house_id)
        return jsonify(devs)


@app.route("/api/appliances", methods=["GET", "POST"])
def manage_appliances():
    user_id = get_auth_user_id()
    if request.method == "POST":
        if not user_id:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        houses = db.get_user_houses(user_id)
        if not houses:
            return jsonify({"ok": False, "error": "No house found"}), 404
        house_id = houses[0]["id"]
        data = request.get_json(force=True, silent=True) or {}
        device_id = data.get("device_id")
        name = data.get("appliance_name") or data.get("name")
        atype = data.get("appliance_type") or data.get("type", "generic")
        rated = float(data.get("rated_power_w") or data.get("ratedPowerW") or 100)
        if not name:
            return jsonify({"ok": False, "error": "Appliance name required"}), 400
        appliance = db.create_appliance(house_id, device_id, name, atype, rated)
        return jsonify({"ok": True, "appliance": appliance})
    else:
        if user_id:
            houses = db.get_user_houses(user_id)
            if houses:
                user_appliances = db.get_house_appliances(houses[0]["id"])
                if user_appliances:
                    return jsonify(user_appliances)

        # Unauthenticated / Demo Fallback
        result = []
        for aid in APPLIANCE_IDS:
            profile = dict(APPLIANCE_PROFILES[aid])
            meta = model_metadata.get(aid, {})
            r2 = meta.get("R2", 0.95)
            profile["model"] = {
                "name": f"{meta.get('model_type', 'unknown').replace('_', ' ').title()}",
                "version": "v1.0-trained",
                "trainedOn": f"UK-DALE real household data (R²={r2:.4f})",
                "accuracyPct": round(r2 * 100, 1),
            }
            result.append(profile)
        return jsonify(result)


@app.route("/api/appliances/<appliance_id>", methods=["DELETE"])
def delete_appliance_route(appliance_id):
    user_id = get_auth_user_id()
    if not user_id:
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    houses = db.get_user_houses(user_id)
    if not houses:
        return jsonify({"ok": False, "error": "House not found"}), 404
    u_apps = db.get_house_appliances(houses[0]["id"])
    valid_ids = {a["id"] for a in u_apps}
    if appliance_id not in valid_ids:
        return jsonify({"ok": False, "error": "Appliance does not belong to logged-in user house"}), 403
    deleted = db.delete_appliance(appliance_id)
    if deleted:
        with _lock:
            _current_state.pop(appliance_id, None)
            _telemetry_buffers.pop(appliance_id, None)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Appliance not found"}), 404


@app.route("/api/house", methods=["GET"])
def get_house():
    user_id = get_auth_user_id()
    if user_id:
        houses = db.get_user_houses(user_id)
        if houses:
            return jsonify(houses[0])
    return jsonify(HOUSE)


@app.route("/api/telemetry", methods=["GET", "POST"])
def manage_telemetry():
    """Manage telemetry: GET returns ApplianceRuntime[] for dashboard; POST ingests ESP32 device telemetry."""
    if request.method == "POST":
        # 1. Device Credential Extraction
        dev_id = request.headers.get("X-Device-Id") or request.headers.get("Device-Id")
        dev_secret = request.headers.get("X-Device-Secret") or request.headers.get("X-Device-Token") or request.headers.get("Device-Secret")

        data = request.get_json(force=True, silent=True) or {}
        if not dev_id:
            dev_id = data.get("device_id")
        if not dev_secret:
            dev_secret = data.get("device_secret") or data.get("device_token")

        if not dev_id or not dev_secret:
            return jsonify({"ok": False, "error": "Device credentials required (X-Device-Id & X-Device-Secret headers)"}), 401

        dev_record = db.get_device_by_credentials(dev_id, dev_secret)
        if not dev_record:
            return jsonify({"ok": False, "error": "Invalid device credentials"}), 401

        if dev_record.get("status") == "DISABLED":
            return jsonify({"ok": False, "error": "Device is disabled"}), 403

        house_id = dev_record["house_id"]
        user_id = dev_record["user_id"]

        # 2. Extract & Validate Appliance
        appliance_id = data.get("appliance_id") or data.get("id")
        if not appliance_id:
            return jsonify({"ok": False, "error": "appliance_id is required"}), 400

        house_apps = db.get_house_appliances(house_id)
        house_app_map = {a["id"]: a for a in house_apps}

        if appliance_id not in house_app_map:
            # Check if appliance exists anywhere in another house
            conn = db.get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT appliance_id, house_id FROM appliances WHERE appliance_id = ?;", (appliance_id,))
            other_app = cursor.fetchone()
            conn.close()

            if not other_app:
                return jsonify({"ok": False, "error": f"Appliance {appliance_id} not found"}), 404
            else:
                return jsonify({"ok": False, "error": "Unauthorized device/appliance relationship (cross-house telemetry injection blocked)"}), 403

        app_info = house_app_map[appliance_id]

        # 3. Extract & Validate Reading Values
        try:
            voltage = float(data.get("voltage", 230.0))
            current = float(data.get("current", 0.0))
            power_w = float(data.get("power_w") if data.get("power_w") is not None else data.get("powerW", 0.0))
            energy_kwh = float(data.get("energy_kwh") if data.get("energy_kwh") is not None else data.get("energyKwh", 0.0))
            temperature = float(data.get("temperature", 25.0))
            humidity = float(data.get("humidity", 50.0))
            status_str = str(data.get("status", "ON")).upper()
        except (ValueError, TypeError):
            return jsonify({"ok": False, "error": "Malformed numeric telemetry values"}), 400

        # 4. Anomaly Detection & ML Updates
        atype = app_info.get("type", "generic").lower()
        model_id = atype if atype in APPLIANCE_IDS else "laptop"
        features = {
            "power_w": power_w,
            "status": 1 if status_str in ["ON", "1", "TRUE"] else 0,
            "hour": datetime.now().hour,
            "day_of_week": datetime.now().weekday(),
            "is_weekend": 1 if datetime.now().weekday() >= 5 else 0,
            "month": datetime.now().month,
            "power_lag_1": power_w,
            "power_lag_5": power_w,
            "power_rolling_mean": power_w,
            "power_rolling_max": power_w,
        }
        anomaly_score = _anomaly_score(model_id, features)

        # 5. Persist to Database
        db.save_telemetry(
            user_id=user_id,
            house_id=house_id,
            appliance_id=appliance_id,
            voltage=voltage,
            current=current,
            power_w=power_w,
            energy_kwh=energy_kwh,
            temperature=temperature,
            humidity=humidity,
            status=status_str,
            anomaly_score=anomaly_score,
        )

        # 6. Update Real-Time Runtime State & Memory Buffers
        now_ms = int(time.time() * 1000)
        with _lock:
            runtime_state = {
                "id": appliance_id,
                "name": app_info["name"],
                "status": "on" if status_str in ["ON", "1", "TRUE"] else "off",
                "mode": app_info.get("mode", "maintain"),
                "powerW": power_w,
                "targetPowerW": app_info.get("ratedPowerW", 100.0),
                "tempC": temperature,
                "humidityPct": humidity,
                "voltageV": voltage,
                "currentA": current,
                "energyKwh": energy_kwh,
                "anomalyScore": anomaly_score,
                "isAnomaly": anomaly_score > 0.65,
                "lastUpdate": now_ms,
            }
            _current_state[appliance_id] = runtime_state

            if appliance_id not in _telemetry_buffers:
                _telemetry_buffers[appliance_id] = collections.deque(maxlen=100)
            _telemetry_buffers[appliance_id].append({
                "t": now_ms,
                "power_w": power_w,
                "voltage": voltage,
                "current": current,
                "energy_kwh": energy_kwh,
                "temperature": temperature,
                "humidity": humidity,
                "anomaly_score": anomaly_score,
            })

        return jsonify({
            "ok": True,
            "status": "accepted",
            "device_id": dev_id,
            "appliance_id": appliance_id,
            "power_w": power_w,
            "anomaly_score": anomaly_score,
        }), 200

    else:
        # GET Telemetry dashboard polling logic
        user_id = get_auth_user_id()
        with _lock:
            if user_id:
                houses = db.get_user_houses(user_id)
                if houses:
                    user_apps = db.get_house_appliances(houses[0]["id"])
                    if user_apps:
                        result = []
                        now_ms = int(time.time() * 1000)
                        for app_info in user_apps:
                            aid = app_info["id"]
                            state = _current_state.get(aid)
                            if state:
                                result.append(dict(state))
                            else:
                                atype = app_info.get("type", "generic").lower()
                                base_id = atype if atype in APPLIANCE_IDS else "laptop"
                                base_state = _current_state.get(base_id) or _make_default_state(base_id, now_ms)
                                user_state = dict(base_state)
                                user_state["id"] = aid
                                user_state["name"] = app_info["name"]
                                user_state["targetPowerW"] = app_info["ratedPowerW"]
                                user_state["powerW"] = round(app_info["ratedPowerW"] * (0.65 + (hash(aid) % 40) / 100.0), 1)
                                _current_state[aid] = user_state
                                result.append(user_state)
                        return jsonify(result)

            result = []
            for aid in APPLIANCE_IDS:
                state = _current_state.get(aid)
                if state:
                    result.append(dict(state))
                else:
                    result.append(_make_default_state(aid, int(time.time() * 1000)))
            return jsonify(result)


@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    """Run trained energy models forward to produce Prediction[] with confidence bands."""
    horizon = int(request.args.get("horizon", 30))
    user_id = get_auth_user_id()
    target_apps = []
    if user_id:
        houses = db.get_user_houses(user_id)
        if houses:
            u_apps = db.get_house_appliances(houses[0]["id"])
            if u_apps:
                target_apps = u_apps

    if not target_apps:
        target_apps = [
            {"id": aid, "name": APPLIANCE_PROFILES[aid]["name"], "type": aid, "ratedPowerW": APPLIANCE_PROFILES[aid]["ratedPowerW"]}
            for aid in APPLIANCE_IDS
        ]

    steps = 12
    step_minutes = horizon / steps
    now_ms = int(time.time() * 1000)

    result = []
    with _lock:
        for app_info in target_apps:
            aid = app_info["id"]
            atype = app_info.get("type", "generic").lower()
            model_id = atype if atype in APPLIANCE_IDS else "laptop"
            profile = APPLIANCE_PROFILES.get(model_id, APPLIANCE_PROFILES["laptop"])
            rated_w = app_info.get("ratedPowerW") or profile["ratedPowerW"]

            state = _current_state.get(aid) or _current_state.get(model_id, {})
            power_now = state.get("powerW", rated_w * 0.8)
            mode = state.get("mode", "maintain")
            status = state.get("status", "on")
            a_score = state.get("anomalyScore", 0.05)

            curve = []
            power_sum = 0
            current_hour = datetime.now().hour
            current_dow = datetime.now().weekday()
            current_month = datetime.now().month
            lag_1 = power_now
            lag_5 = power_now
            rolling_mean = power_now
            rolling_max = power_now

            for i in range(1, steps + 1):
                future_minutes = i * step_minutes
                future_hour = (current_hour + int(future_minutes / 60)) % 24
                features = {
                    "status": 1 if status != "off" else 0,
                    "hour": future_hour,
                    "day_of_week": current_dow,
                    "is_weekend": 1 if current_dow >= 5 else 0,
                    "month": current_month,
                    "power_lag_1": lag_1,
                    "power_lag_5": lag_5,
                    "power_rolling_mean": rolling_mean,
                    "power_rolling_max": rolling_max,
                    "power_w": power_now,
                }

                predicted = _predict_power(model_id, features)
                if predicted is None:
                    predicted = power_now

                mode_factor = {"maintain": 1.0, "reduce": 0.75, "increase": 1.2, "eco": 0.6}.get(mode, 1.0)
                predicted = round(predicted * mode_factor, 1)
                predicted = max(0, predicted)

                spread = max(2, predicted * (0.07 + i * 0.015))
                t = now_ms + int(future_minutes * 60 * 1000)

                curve.append({
                    "t": t,
                    "predictedW": predicted,
                    "lowerW": round(max(0, predicted - spread), 1),
                    "upperW": round(predicted + spread, 1),
                })
                power_sum += predicted

                lag_5 = lag_1
                lag_1 = predicted
                rolling_mean = (rolling_mean * 0.8 + predicted * 0.2)
                rolling_max = max(rolling_max, predicted)

            avg_w = power_sum / steps if steps > 0 else power_now
            meta = model_metadata.get(model_id, {})
            r2 = meta.get("R2", 0.95)
            base_confidence = r2 * 100 - horizon * 0.06
            confidence = max(55, min(99, round(base_confidence - a_score * 22)))

            risk = state.get("risk", "normal")
            if risk != "risk" and avg_w > rated_w * 1.15:
                risk = "watch"

            risk_note = {
                "risk": "Predicted draw is well above the learned pattern — check this appliance.",
                "watch": "Slightly higher than usual for this time of day.",
                "normal": "Usage matches the learned pattern for this time of day.",
            }.get(risk, "Usage matches the learned pattern.")

            result.append({
                "id": aid,
                "nextPowerW": round(avg_w, 1),
                "expectedUsageKwh": round((avg_w * (horizon / 60)) / 1000, 3),
                "confidencePct": confidence,
                "horizonMinutes": horizon,
                "risk": risk,
                "riskNote": risk_note,
                "curve": curve,
            })

    return jsonify(result)


@app.route("/api/control", methods=["POST"])
def post_control():
    """Accept control commands from the dashboard UI with authorization check."""
    try:
        user_id = get_auth_user_id()
        data = request.get_json(force=True, silent=True) or {}
        aid = data.get("id")
        action = data.get("action")

        if user_id:
            houses = db.get_user_houses(user_id)
            if not houses:
                return jsonify({"ok": False, "error": "House not found"}), 404
            u_apps = db.get_house_appliances(houses[0]["id"])
            valid_ids = {a["id"] for a in u_apps}
            if aid not in valid_ids:
                return jsonify({"ok": False, "error": "Appliance does not belong to logged-in user house"}), 403

            if action == "power":
                on = data.get("on", True)
                db.update_appliance_state(aid, status="ON" if on else "OFF")
            elif action == "mode":
                mode = data.get("mode", "maintain")
                db.update_appliance_state(aid, mode=mode)
        else:
            if aid not in APPLIANCE_IDS:
                return jsonify({"ok": False, "error": "Unknown appliance"}), 400

        with _lock:
            override = _control_overrides.get(aid, {})

            if action == "power":
                on = data.get("on", True)
                override["status"] = "on" if on else "off"
                print(f"[control] {aid} power -> {'on' if on else 'off'}")

            elif action == "mode":
                mode = data.get("mode", "maintain")
                override["mode"] = mode
                print(f"[control] {aid} mode -> {mode}")

            elif action == "target":
                target_w = data.get("targetW", 100)
                override["targetW"] = target_w
                print(f"[control] {aid} target -> {target_w} W")

            _control_overrides[aid] = override

        return jsonify({"ok": True})
    except Exception as e:
        print(f"[control] Error handling post_control: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/control-loop", methods=["GET"])
def get_control_loop():
    """Return ControlLoopState[] using RL agent reward calculations."""
    user_id = get_auth_user_id()
    target_apps = []
    if user_id:
        houses = db.get_user_houses(user_id)
        if houses:
            u_apps = db.get_house_appliances(houses[0]["id"])
            if u_apps:
                target_apps = u_apps

    if not target_apps:
        target_apps = [
            {"id": aid, "name": APPLIANCE_PROFILES[aid]["name"], "type": aid, "ratedPowerW": APPLIANCE_PROFILES[aid]["ratedPowerW"]}
            for aid in APPLIANCE_IDS
        ]

    result = []
    with _lock:
        for app_info in target_apps:
            aid = app_info["id"]
            atype = app_info.get("type", "generic").lower()
            model_id = atype if atype in APPLIANCE_IDS else "laptop"
            profile = APPLIANCE_PROFILES.get(model_id, APPLIANCE_PROFILES["laptop"])
            rated_w = app_info.get("ratedPowerW") or profile["ratedPowerW"]

            state = _current_state.get(aid) or _current_state.get(model_id, {})
            target = state.get("targetPowerW", rated_w)
            measured = state.get("powerW", 0)
            error = round(measured - target, 1)
            norm_err = abs(error) / max(rated_w, 1)
            a_score = state.get("anomalyScore", 0.05)
            reward = round(1 - norm_err * 1.6 - a_score * 0.5, 2)
            success = abs(error) <= max(4, rated_w * 0.12)
            risk = state.get("risk", "normal")
            mode = state.get("mode", "maintain")

            safety_status = "safe"
            if risk == "risk":
                safety_status = "blocked"
            elif risk == "watch":
                safety_status = "guarded"

            action_label = {
                "maintain": "HOLD_SETPOINT",
                "reduce": "REDUCE_LOAD",
                "increase": "INCREASE_LOAD",
                "eco": "ECO_OPTIMIZE",
            }.get(mode, "HOLD_SETPOINT")

            if state.get("status") == "off":
                action_label = "POWER_OFF"

            # Evaluate RL agent model if available
            agent_dict = rl_agents.get(aid)
            rl_action_str = None
            rl_reward = None
            rl_confidence = None

            if agent_dict is not None and isinstance(agent_dict, dict):
                try:
                    rl_model = agent_dict["model"]
                    rl_scaler = agent_dict.get("scaler")
                    rl_features = agent_dict["features"]
                    rl_actions = agent_dict["actions"]

                    now_dt = datetime.now()
                    current_hour = now_dt.hour
                    current_dow = now_dt.weekday()
                    is_weekend = 1 if current_dow >= 5 else 0

                    base_sample = {
                        "power_w": measured,
                        "energy_kwh": state.get("energyTodayKwh", 0.0),
                        "hour": current_hour,
                        "day_of_week": current_dow,
                        "is_weekend": is_weekend,
                        "power_lag_1": measured,
                        "power_lag_5": measured,
                        "power_rolling_mean": measured,
                        "power_rolling_max": measured,
                        "anomaly_score": a_score,
                        "peak_risk": 1 if risk == "risk" else 0,
                        "user_behavior_score": 0.8,
                        "energy_routine_index": 0.85,
                        "dsc_score": 0.9,
                        "stability_score": 0.95,
                        "change_score": 0.05,
                        "cdi_score": 0.88,
                        "action": 0,
                    }

                    best_val = -float("inf")
                    best_action_key = 0
                    for action_key, action_name in rl_actions.items():
                        row_dict = dict(base_sample)
                        row_dict["action"] = action_key
                        X_df = pd.DataFrame([row_dict])[rl_features]
                        if rl_scaler is not None:
                            X_vec = rl_scaler.transform(X_df)
                        else:
                            X_vec = X_df
                        pred_q = rl_model.predict(X_vec)[0]
                        if pred_q > best_val:
                            best_val = pred_q
                            best_action_key = action_key

                    raw_action_name = rl_actions.get(best_action_key, "maintain")
                    rl_action_map = {
                        "maintain": "HOLD_SETPOINT",
                        "reduce": "REDUCE_LOAD",
                        "shift": "ECO_OPTIMIZE",
                        "turn_off": "POWER_OFF",
                    }
                    rl_action_str = rl_action_map.get(raw_action_name, "HOLD_SETPOINT")
                    rl_reward = round(float(best_val), 2)
                    rl_confidence = max(60, min(99, round(85 + best_val * 10 - a_score * 15)))
                except Exception as e:
                    print(f"[rl_eval] Error executing RL model for {aid}: {e}")

            if safety_status == "blocked":
                next_action = "HOLD + NOTIFY_USER"
            elif rl_action_str is not None:
                next_action = rl_action_str
            elif error > profile["ratedPowerW"] * 0.12:
                next_action = "REDUCE_LOAD"
            elif error < -profile["ratedPowerW"] * 0.12:
                next_action = "INCREASE_LOAD"
            else:
                next_action = "HOLD_SETPOINT"

            reward = rl_reward if rl_reward is not None else round(1 - norm_err * 1.6 - a_score * 0.5, 2)
            confidence = rl_confidence if rl_confidence is not None else max(40, min(99, round(88 - norm_err * 90 + (1 - a_score) * 10)))

            result.append({
                "id": aid,
                "action": action_label,
                "targetPowerW": target,
                "measuredPowerW": measured,
                "powerErrorW": error,
                "reward": reward,
                "policyConfidencePct": confidence,
                "nextAction": next_action,
                "safetyStatus": safety_status,
                "controlSuccess": success and safety_status != "blocked",
                "iterations": _tick_count,
            })

    return jsonify(result)


@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Return recent alerts generated from anomaly model scores."""
    with _lock:
        return jsonify(list(_alerts))


@app.route("/api/history", methods=["GET"])
def get_history():
    """Aggregate daily totals from the real ML CSVs."""
    range_str = request.args.get("range", "7d")
    try:
        days = int(range_str.replace("d", ""))
    except ValueError:
        days = 7

    # Generate daily history from the replay data
    result = []
    now = datetime.now()
    for i in range(days - 1, -1, -1):
        d = now - timedelta(days=i)
        date_str = d.strftime("%Y-%m-%d")
        t = int(d.timestamp() * 1000)
        dow = d.weekday()
        weekend_factor = 1.12 if dow >= 5 else 1.0

        row = {"date": date_str, "t": t}
        total = 0.0
        for aid in APPLIANCE_IDS:
            df = _replay_data.get(aid)
            if df is not None and not df.empty:
                # Use real data stats to compute realistic daily totals
                mean_power = df["power_w"].mean()
                std_power = df["power_w"].std()
                # hours active per day (approximate from data)
                active_ratio = (df["status"].mean() if "status" in df.columns else 0.7)
                # Daily kWh = mean_power * active_hours / 1000
                base_kwh = (mean_power * active_ratio * 24) / 1000
                # Add some daily variation
                np.random.seed(int(d.timestamp()) + hash(aid) & 0xFFFFFF)
                variation = 0.8 + np.random.random() * 0.4
                kwh = round(base_kwh * weekend_factor * variation, 3)
            else:
                kwh = round(0.5 * weekend_factor * (0.8 + np.random.random() * 0.4), 3)

            row[aid] = kwh
            total += kwh

        row["total"] = round(total, 3)
        row["savingsKwh"] = round(total * (0.09 + np.random.random() * 0.09), 3)
        result.append(row)

    return jsonify(result)


@app.route("/api/health", methods=["GET"])
def health():
    """Simple health check returning models, db engine, and replay tick status."""
    db_engine = "PostgreSQL" if db.IS_POSTGRES else "SQLite"
    return jsonify({
        "status": "ok",
        "db_engine": db_engine,
        "models_loaded": {
            "energy": len(energy_models),
            "status": len(status_classifiers),
            "anomaly": len(anomaly_models),
            "rl": len(rl_agents),
        },
        "replay_data": {aid: len(df) for aid, df in _replay_data.items()},
        "tick": _tick_count,
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    load_models()
    load_replay_data()

    # Start the replay thread
    t = threading.Thread(target=_replay_loop, daemon=True)
    t.start()
    print(f"[boot] Replay thread started (tick every {TICK_INTERVAL}s)")

    port = 5000
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", 5000))
        sock.close()
    except Exception:
        port = 5001

    print(f"[boot] Starting Flask on http://localhost:{port}")
    print(f"[boot] Dashboard should connect via Settings -> Use Live API")

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
