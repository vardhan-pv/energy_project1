import os
import sys
import json
import sqlite3
import subprocess
import time
from datetime import datetime

# ============================================================
# MODULE 14C — AUTOMATIC PIPELINE ORCHESTRATION
# ============================================================

BASE_DIR = r"E:\energy_project"

INITIALIZATION_DIR = os.path.join(
    BASE_DIR,
    "initialization"
)

HOUSE_DATA_DIR = os.path.join(
    BASE_DIR,
    "house_data"
)

HOUSE_CONFIG = os.path.join(
    INITIALIZATION_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG = os.path.join(
    INITIALIZATION_DIR,
    "appliance_config.csv"
)

PIPELINE_LOG_DIR = os.path.join(
    BASE_DIR,
    "pipeline_logs"
)

PIPELINE_OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "pipeline_output"
)

os.makedirs(PIPELINE_LOG_DIR, exist_ok=True)
os.makedirs(PIPELINE_OUTPUT_DIR, exist_ok=True)

# ============================================================
# PIPELINE MODULES
# ============================================================

PIPELINE_MODULES = [

    # Existing ML / data pipeline
    ("Module 10", "module_10_anomaly_detection.py"),

    # RL
    ("Module 11A", "module_11a_rl_environment.py"),
    ("Module 11B", "module_11b_rl_training.py"),
    ("Module 11C", "module_11c_rl_policy_evaluation.py"),
    ("Module 11D", "module_11d_rl_optimization.py"),

    # Self evolution
    ("Module 12A", "module_12a_feedback.py"),
    ("Module 12B", "module_12b_adaptive_policy.py"),
    ("Module 12C", "module_12c_policy_evolution.py"),
    ("Module 12D", "module_12d_self_evolution_validation.py"),

    # Integration
    ("Module 13A", "module_13a_system_integration.py"),
    ("Module 13B", "module_13b_unified_prediction_rl_pipeline.py"),
    ("Module 13C", "module_13c_realtime_processing.py"),
]

# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 14C — AUTOMATIC PIPELINE ORCHESTRATION")
print("=" * 70)

pipeline_start = time.time()

# ============================================================
# STEP 1 — CHECK PYTHON
# ============================================================

print()
print("Checking Python environment...")
print("-" * 70)

print("Python executable:")
print(sys.executable)

print("Python version:")
print(sys.version.split()[0])

# ============================================================
# STEP 2 — CHECK INITIALIZATION
# ============================================================

print()
print("Checking house initialization...")
print("-" * 70)

if not os.path.exists(HOUSE_CONFIG):
    print("[ERROR] house_config.json not found")
    print("Run Module 14A first.")
    sys.exit(1)

print(f"[OK] House configuration: {HOUSE_CONFIG}")

if not os.path.exists(APPLIANCE_CONFIG):
    print("[ERROR] appliance_config.csv not found")
    print("Run Module 14A first.")
    sys.exit(1)

print(f"[OK] Appliance configuration: {APPLIANCE_CONFIG}")

# ============================================================
# LOAD HOUSE
# ============================================================

with open(
    HOUSE_CONFIG,
    "r",
    encoding="utf-8"
) as f:

    house = json.load(f)

house_id = house["house_id"]
house_name = house["house_name"]

print()
print("HOUSE")
print("-" * 70)

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")

# ============================================================
# HOUSE DATABASE
# ============================================================

house_dir = os.path.join(
    HOUSE_DATA_DIR,
    house_id
)

database_file = os.path.join(
    house_dir,
    f"{house_id}.db"
)

print()
print("Checking house database...")

if not os.path.exists(database_file):

    print(
        f"[ERROR] Database not found:\n"
        f"{database_file}"
    )

    print("Run Module 14B first.")
    sys.exit(1)

print(f"[OK] Database: {database_file}")

# ============================================================
# DATABASE VALIDATION
# ============================================================

print()
print("Validating raw energy database...")
print("-" * 70)

try:

    conn = sqlite3.connect(database_file)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM appliances"
    )

    appliance_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM raw_energy"
    )

    raw_rows = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM raw_energy
        WHERE timestamp IS NULL
           OR appliance_id IS NULL
           OR power_w IS NULL
    """)

    invalid_rows = cursor.fetchone()[0]

    conn.close()

except Exception as e:

    print(f"[ERROR] Database validation failed: {e}")
    sys.exit(1)

print(f"Registered appliances : {appliance_count}")
print(f"Raw energy rows      : {raw_rows}")
print(f"Invalid rows         : {invalid_rows}")

if appliance_count == 0:

    print("[ERROR] No appliances registered.")
    sys.exit(1)

if raw_rows == 0:

    print("[ERROR] No raw energy data available.")
    sys.exit(1)

if invalid_rows > 0:

    print(
        f"[ERROR] {invalid_rows} invalid rows found."
    )

    sys.exit(1)

print("[OK] Raw database validation passed")

# ============================================================
# PIPELINE STATUS
# ============================================================

pipeline_results = []

# ============================================================
# RUN MODULE FUNCTION
# ============================================================

def run_module(module_name, script_name):

    script_path = os.path.join(
        BASE_DIR,
        script_name
    )

    print()
    print("=" * 70)
    print(f"RUNNING {module_name}")
    print("=" * 70)

    if not os.path.exists(script_path):

        print(
            f"[WARNING] Script not found:\n"
            f"{script_path}"
        )

        pipeline_results.append({
            "module": module_name,
            "script": script_name,
            "status": "SKIPPED",
            "return_code": -1,
            "time_minutes": 0
        })

        return False

    start = time.time()

    try:

        result = subprocess.run(
            [
                sys.executable,
                script_path
            ],
            cwd=BASE_DIR,
            capture_output=False,
            text=True
        )

        elapsed = (
            time.time() - start
        ) / 60

        if result.returncode == 0:

            status = "SUCCESS"

            print()
            print(
                f"[OK] {module_name} completed"
            )

        else:

            status = "FAILED"

            print()
            print(
                f"[ERROR] {module_name} failed"
            )

            print(
                f"Return code: {result.returncode}"
            )

        pipeline_results.append({
            "module": module_name,
            "script": script_name,
            "status": status,
            "return_code": result.returncode,
            "time_minutes": round(elapsed, 4)
        })

        return result.returncode == 0

    except Exception as e:

        elapsed = (
            time.time() - start
        ) / 60

        print()
        print(
            f"[ERROR] Exception in {module_name}"
        )

        print(str(e))

        pipeline_results.append({
            "module": module_name,
            "script": script_name,
            "status": "ERROR",
            "return_code": -2,
            "time_minutes": round(elapsed, 4)
        })

        return False

# ============================================================
# IMPORTANT:
# CURRENT DEVELOPMENT MODE
# ============================================================

print()
print("=" * 70)
print("PIPELINE EXECUTION MODE")
print("=" * 70)

print()
print("House-specific database is validated.")

print()
print(
    "NOTE:"
)

print(
    "The existing Modules 10–13 were developed around "
    "the UK-DALE dataset."
)

print(
    "Therefore this orchestrator first validates "
    "the house data and then checks module availability."
)

# ============================================================
# RUN EXISTING MODULES
# ============================================================

failed = False

for module_name, script_name in PIPELINE_MODULES:

    success = run_module(
        module_name,
        script_name
    )

    if not success:

        failed = True

        print()
        print(
            f"[WARNING] Pipeline stopped after {module_name}"
        )

        break

# ============================================================
# PIPELINE SUMMARY
# ============================================================

total_time = (
    time.time() - pipeline_start
) / 60

print()
print("=" * 70)
print("MODULE 14C — PIPELINE VALIDATION")
print("=" * 70)

print()
print(f"House ID           : {house_id}")
print(f"House Name         : {house_name}")
print(f"Appliances         : {appliance_count}")
print(f"Raw energy rows    : {raw_rows}")
print(f"Invalid rows       : {invalid_rows}")

print()
print("MODULE STATUS")
print("-" * 70)

for result in pipeline_results:

    print(
        f"{result['module']:12} "
        f"{result['status']:10} "
        f"{result['time_minutes']:.3f} min"
    )

# ============================================================
# COUNTS
# ============================================================

successful_modules = sum(
    1
    for r in pipeline_results
    if r["status"] == "SUCCESS"
)

failed_modules = sum(
    1
    for r in pipeline_results
    if r["status"] in ["FAILED", "ERROR"]
)

skipped_modules = sum(
    1
    for r in pipeline_results
    if r["status"] == "SKIPPED"
)

# ============================================================
# OVERALL STATUS
# ============================================================

if failed_modules > 0:

    system_status = "PIPELINE_FAILED"

elif successful_modules == len(PIPELINE_MODULES):

    system_status = "FULL_PIPELINE_COMPLETE"

else:

    system_status = "PARTIAL_PIPELINE"

# ============================================================
# SAVE PIPELINE LOG
# ============================================================

import pandas as pd

results_df = pd.DataFrame(
    pipeline_results
)

results_file = os.path.join(
    PIPELINE_LOG_DIR,
    f"{house_id}_pipeline_execution.csv"
)

results_df.to_csv(
    results_file,
    index=False
)

# ============================================================
# SAVE SYSTEM STATE
# ============================================================

system_state = pd.DataFrame([{

    "house_id": house_id,

    "house_name": house_name,

    "appliance_count":
        appliance_count,

    "raw_energy_rows":
        raw_rows,

    "invalid_rows":
        invalid_rows,

    "successful_modules":
        successful_modules,

    "failed_modules":
        failed_modules,

    "skipped_modules":
        skipped_modules,

    "pipeline_status":
        system_status,

    "pipeline_time_minutes":
        round(total_time, 4),

    "timestamp":
        datetime.now().isoformat()

}])

state_file = os.path.join(
    PIPELINE_OUTPUT_DIR,
    f"{house_id}_pipeline_state.csv"
)

system_state.to_csv(
    state_file,
    index=False
)

# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("MODULE 14C COMPLETE")
print("=" * 70)

print()
print("PIPELINE SUMMARY")
print("-" * 70)

print(
    f"Successful modules : {successful_modules}"
)

print(
    f"Failed modules     : {failed_modules}"
)

print(
    f"Skipped modules    : {skipped_modules}"
)

print(
    f"Total time         : {total_time:.2f} minutes"
)

print(
    f"System status      : {system_status}"
)

print()
print("OUTPUT FILES")
print("-" * 70)

print(
    f"Pipeline log:"
)

print(
    results_file
)

print()

print(
    f"Pipeline state:"
)

print(
    state_file
)

print()
print("=" * 70)