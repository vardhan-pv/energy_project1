#!/usr/bin/env python3
"""
=============================================================================
SIMULATED ESP32 TELEMETRY TRANSMITTER — COGNITIVE ENERGY SYSTEM (PHASE 17A)
=============================================================================
Simulates a physical ESP32 microcontroller with sensors (voltage, current,
temperature, humidity) sending hardware-ready telemetry over HTTP POST.

Command Line Options:
  --backend          Base API URL (default: http://127.0.0.1:5000)
  --device-id        Device ID (DEV-XXXXXXXX)
  --device-secret    Device Secret token (SEC-XXXXXXXX)
  --appliance-id     Target Appliance ID (APP-XXXXXXXX)
  --appliance-type   Appliance type (fridge, laptop, fan, ac, generic)
  --interval         Transmission interval in seconds (default: 5)
  --rated-power      Rated wattage for realistic physics simulation (default: 150)
=============================================================================
"""

import sys
import time
import math
import random
import argparse
import urllib.request
import urllib.error
import json


def parse_args():
    parser = argparse.ArgumentParser(description="Simulated ESP32 Hardware Telemetry Generator")
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:5000", help="Base API URL")
    parser.add_argument("--device-id", type=str, required=True, help="Device ID (DEV-XXXXXXXX)")
    parser.add_argument("--device-secret", type=str, required=True, help="Device Secret Token (SEC-XXXXXXXX)")
    parser.add_argument("--appliance-id", type=str, required=True, help="Appliance ID (APP-XXXXXXXX)")
    parser.add_argument("--appliance-type", type=str, default="fridge", help="Appliance category (fridge, laptop, fan, ac, generic)")
    parser.add_argument("--interval", type=float, default=5.0, help="Transmission interval in seconds")
    parser.add_argument("--rated-power", type=float, default=150.0, help="Rated appliance wattage")
    return parser.parse_args()


def generate_telemetry(step_count: int, appliance_type: str, rated_power: float, cumulative_kwh: float, interval_sec: float):
    """Generate realistic physics-based simulated ESP32 sensor readings."""
    # Voltage simulation: nominal 230V with minor grid fluctuations (222V - 238V)
    voltage = round(230.0 + 4.0 * math.sin(step_count / 10.0) + random.uniform(-1.5, 1.5), 1)

    # Status & Power draw simulation based on appliance type
    atype = appliance_type.lower()
    if atype in ["fridge", "refrigerator"]:
        # Compressor duty cycle (cooling cycle ON for 60%, idling for 40%)
        is_on = (step_count % 30) < 18
        base_power = rated_power * (0.85 + 0.15 * math.sin(step_count / 5.0)) if is_on else 8.0
    elif atype in ["laptop", "computer"]:
        is_on = True
        base_power = rated_power * (0.3 + 0.5 * (math.sin(step_count / 4.0) ** 2))
    elif atype in ["fan", "office_fan"]:
        is_on = True
        base_power = rated_power * (0.7 + 0.3 * random.uniform(0.9, 1.1))
    elif atype in ["ac", "air_conditioner"]:
        is_on = (step_count % 40) < 32
        base_power = rated_power * (0.8 + 0.2 * math.sin(step_count / 8.0)) if is_on else 25.0
    else:
        is_on = True
        base_power = rated_power * random.uniform(0.6, 0.9)

    power_w = round(max(0.0, base_power + random.uniform(-2.0, 2.0)), 1)
    status_str = "ON" if is_on and power_w > 5.0 else "OFF"
    if status_str == "OFF":
        power_w = round(random.uniform(0.5, 3.0), 1)

    # Current (A) = Power (W) / Voltage (V)
    current_a = round(power_w / max(voltage, 1.0), 2)

    # Accumulate energy (kWh) = power_w * time_hours / 1000
    added_kwh = (power_w * (interval_sec / 3600.0)) / 1000.0
    new_cumulative_kwh = round(cumulative_kwh + added_kwh, 4)

    # Environmental sensor readings (DHT22 sensor simulation)
    temp_c = round(24.0 + 3.0 * math.sin(step_count / 15.0) + (power_w / rated_power) * 4.0 + random.uniform(-0.3, 0.3), 1)
    humidity_pct = round(52.0 - 2.0 * math.sin(step_count / 15.0) + random.uniform(-1.0, 1.0), 1)

    return {
        "appliance_id": appetite_clean := appliance_id_clean(appliance_type),
        "voltage": voltage,
        "current": current_a,
        "power_w": power_w,
        "energy_kwh": new_cumulative_kwh,
        "temperature": temp_c,
        "humidity": humidity_pct,
        "status": status_str,
    }, new_cumulative_kwh


def appliance_id_clean(appliance_type: str) -> str:
    return appliance_type


def main():
    args = parse_args()
    backend_url = args.backend.rstrip("/") + "/api/telemetry"

    print("=============================================================================")
    print("      [SIMULATED ESP32 TELEMETRY TRANSMITTER — HARDWARE-READY PIPELINE]")
    print("=============================================================================")
    print(f"  Target Backend  : {backend_url}")
    print(f"  Device ID       : {args.device_id}")
    print(f"  Device Secret   : [SECURED]")
    print(f"  Appliance ID    : {args.appliance_id}")
    print(f"  Appliance Type  : {args.appliance_type}")
    print(f"  Transmission Int: {args.interval}s")
    print("=============================================================================")
    print("Press Ctrl+C to stop simulation.\n")

    cumulative_kwh = 0.05
    step_count = 0

    while True:
        step_count += 1
        telemetry, cumulative_kwh = generate_telemetry(
            step_count, args.appliance_type, args.rated_power, cumulative_kwh, args.interval
        )
        telemetry["appliance_id"] = args.appliance_id

        # Print simulator output clearly labeled as SIMULATED ESP32 TELEMETRY
        print(f"[SIMULATED ESP32 TELEMETRY] Step #{step_count} -> Appliance: {args.appliance_id} | Status: {telemetry['status']} | Power: {telemetry['power_w']}W | Voltage: {telemetry['voltage']}V | Current: {telemetry['current']}A | Temp: {telemetry['temperature']}°C")

        # Send HTTP POST to API
        body_bytes = json.dumps(telemetry).encode("utf-8")
        req = urllib.request.Request(
            backend_url,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "X-Device-Id": args.device_id,
                "X-Device-Secret": args.device_secret,
                "User-Agent": "ESP32-Hardware-Simulator/v1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as res:
                resp_data = json.loads(res.read().decode("utf-8"))
                print(f"  └─ HTTP {res.status} OK -> Server Status: {resp_data.get('status')} | Anomaly Score: {resp_data.get('anomaly_score', 0.05):.4f}")
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            print(f"  └─ HTTP ERROR {e.code}: {err_msg}")
        except urllib.error.URLError as e:
            print(f"  └─ CONNECTION FAILED: {e.reason}")
        except Exception as e:
            print(f"  └─ ERROR: {e}")

        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SIMULATED ESP32 TELEMETRY] Simulator stopped by user.")
        sys.exit(0)
