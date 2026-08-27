import os
import json
import sqlite3
import time
import subprocess
import sys
import pandas as pd
from datetime import datetime

# ============================================================
# MODULE 14C — AUTOMATIC PIPELINE ORCHESTRATOR
# ============================================================

print("=" * 70)
print("MODULE 14C — AUTOMATIC PIPELINE ORCHESTRATOR")
print("=" * 70)

BASE_DIR = r"E:\energy_project"

INIT_DIR = os.path.join(BASE_DIR, "initialization")
HOUSE_CONFIG = os.path.join(INIT_DIR, "house_config.json")
APPLIANCE_CONFIG = os.path.join(INIT_DIR, "appliance_config.csv")

PIPELINE_LOG_DIR = os.path.join(BASE_DIR, "pipeline_logs")
PIPELINE_OUTPUT_DIR = os.path.join(BASE_DIR, "pipeline_output")

os.makedirs(PIPELINE_LOG_DIR, exist_ok=True)
os.makedirs(PIPELINE_OUTPUT_DIR, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def print_ok(message):
    print(f"[OK] {message}")


def print_warn(message):
    print(f"[WARNING] {message}")


def print_error(message):
    print(f"[ERROR] {message}")


def find_house_database(house_id):
    house_dir = os.path.join(BASE_DIR, "house_data", house_id)

    candidates = [
        os.path.join(house_dir, f"{house_id}.db"),
        os.path.join(house_dir, "house.db"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def run_python_module(module_name, working_dir=BASE_DIR):
    """
    Execute another Python module and return True/False.
    """

    script_path = os.path.join(working_dir, module_name)

    if not os.path.exists(script_path):
        print_warn(f"{module_name} not found")
        return False

    print()
    print("-" * 70)
    print(f"RUNNING: {module_name}")
    print("-" * 70)

    start = time.time()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=working_dir,
            capture_output=False,
            text=True
        )

        elapsed = (time.time() - start) / 60

        if result.returncode == 0:
            print_ok(
                f"{module_name} completed in {elapsed:.2f} minutes"
            )
            return True

        print_error(
            f"{module_name} failed with exit code {result.returncode}"
        )
        return False

    except Exception as e:
        print_error(f"{module_name}: {e}")
        return False


def validate_database(db_path):
    print()
    print("=" * 70)
    print("HOUSE DATABASE VALIDATION")
    print("=" * 70)

    if not os.path.exists(db_path):
        print_error("House database not found")
        return False

    try:
        conn = sqlite3.connect(db_path)

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            ORDER BY name
            """,
            conn
        )

        print("Tables:")
        for table in tables["name"]:
            print(f"  - {table}")

        if "house" in tables["name"]:
            count = pd.read_sql_query(
                "SELECT COUNT(*) AS n FROM house",
                conn
            ).iloc[0]["n"]
            print(f"House records: {count}")

        if "appliance" in tables["name"]:
            count = pd.read_sql_query(
                "SELECT COUNT(*) AS n FROM appliance",
                conn
            ).iloc[0]["n"]
            print(f"Appliance records: {count}")

        if "raw_energy" in tables["name"]:
            count = pd.read_sql_query(
                "SELECT COUNT(*) AS n FROM raw_energy",
                conn
            ).iloc[0]["n"]
            print(f"Energy records: {count}")

        conn.close()

        print_ok("Database validation completed")
        return True

    except Exception as e:
        print_error(f"Database validation failed: {e}")
        return False


# ============================================================
# STEP 1 — CHECK INITIALIZATION
# ============================================================

print()
print("-" * 70)
print("CHECKING INITIALIZATION")
print("-" * 70)

if not os.path.exists(HOUSE_CONFIG):
    print_error(f"Missing: {HOUSE_CONFIG}")
    sys.exit(1)

if not os.path.exists(APPLIANCE_CONFIG):
    print_error(f"Missing: {APPLIANCE_CONFIG}")
    sys.exit(1)

print_ok("House configuration")
print_ok("Appliance configuration")


# ============================================================
# STEP 2 — LOAD HOUSE
# ============================================================

print()
print("Loading house configuration...")

try:
    with open(HOUSE_CONFIG, "r", encoding="utf-8") as f:
        house = json.load(f)
except Exception as e:
    print_error(f"Cannot read house_config.json: {e}")
    sys.exit(1)

house_id = house.get("house_id")

if not house_id:
    print_error("house_id missing from house_config.json")
    sys.exit(1)

house_name = house.get("house_name", "Unknown House")
location = house.get("location", "")

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")
print(f"Location   : {location}")


# ============================================================
# STEP 3 — LOAD APPLIANCES
# ============================================================

print()
print("Loading appliance configuration...")

try:
    appliances = pd.read_csv(APPLIANCE_CONFIG)
except Exception as e:
    print_error(f"Cannot read appliance_config.csv: {e}")
    sys.exit(1)

if appliances.empty:
    print_error("No appliances registered")
    sys.exit(1)

required_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]

missing = [
    c for c in required_columns
    if c not in appliances.columns
]

if missing:
    print_error(f"Missing appliance columns: {missing}")
    sys.exit(1)

print(f"Registered appliances: {len(appliances)}")

print()
print(appliances[required_columns].to_string(index=False))


# ============================================================
# STEP 4 — FIND DATABASE
# ============================================================

print()
print("Finding house database...")

db_path = find_house_database(house_id)

if db_path is None:
    print_error("House database not found")
    print(
        f"Expected location: "
        f"E:\\energy_project\\house_data\\{house_id}\\"
    )
    sys.exit(1)

print_ok(f"Database found: {db_path}")


# ============================================================
# STEP 5 — VALIDATE DATABASE
# ============================================================

if not validate_database(db_path):
    sys.exit(1)


# ============================================================
# STEP 6 — CREATE HOUSE PIPELINE DIRECTORIES
# ============================================================

house_root = os.path.join(
    BASE_DIR,
    "house_data",
    house_id
)

directories = {
    "processed": os.path.join(house_root, "processed"),
    "features": os.path.join(house_root, "features"),
    "models": os.path.join(house_root, "models"),
    "optimization": os.path.join(house_root, "optimization"),
    "evolution": os.path.join(house_root, "evolution"),
    "integration": os.path.join(house_root, "integration"),
    "realtime": os.path.join(house_root, "realtime"),
}

for path in directories.values():
    os.makedirs(path, exist_ok=True)

print()
print_ok("House pipeline directories ready")


# ============================================================
# STEP 7 — CREATE PIPELINE STATE
# ============================================================

pipeline_start = time.time()

results = []

def record(module, status, elapsed=0, message=""):
    results.append({
        "house_id": house_id,
        "house_name": house_name,
        "module": module,
        "status": status,
        "time_minutes": round(elapsed, 4),
        "message": message,
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })


# ============================================================
# IMPORTANT ARCHITECTURE NOTE
# ============================================================

print()
print("=" * 70)
print("PIPELINE MODE")
print("=" * 70)

print("House-specific mode enabled.")
print(f"House: {house_id}")
print(f"Appliances: {len(appliances)}")

print()
print(
    "The existing Modules 10–13 were developed for the "
    "UK-DALE dataset."
)

print(
    "Therefore they are NOT blindly executed against the new "
    "house database."
)

print(
    "14C first verifies the dynamic house data and then runs "
    "compatible processing stages."
)


# ============================================================
# STEP 8 — DYNAMIC DATA VALIDATION
# ============================================================

print()
print("=" * 70)
print("DYNAMIC HOUSE DATA VALIDATION")
print("=" * 70)

try:
    conn = sqlite3.connect(db_path)

    energy = pd.read_sql_query(
        "SELECT * FROM raw_energy",
        conn
    )

    conn.close()

    print(f"Raw energy rows: {len(energy)}")

    if energy.empty:
        print_error("No raw energy data available")
        record(
            "Dynamic Data Validation",
            "FAILED",
            0,
            "No raw energy rows"
        )
        sys.exit(1)

    print_ok("Raw energy data available")

    record(
        "Dynamic Data Validation",
        "SUCCESS",
        0,
        f"{len(energy)} raw rows"
    )

except Exception as e:
    print_error(f"Dynamic validation failed: {e}")

    record(
        "Dynamic Data Validation",
        "FAILED",
        0,
        str(e)
    )

    sys.exit(1)


# ============================================================
# STEP 9 — DYNAMIC FEATURE GENERATION
# ============================================================

print()
print("=" * 70)
print("DYNAMIC FEATURE GENERATION")
print("=" * 70)

feature_start = time.time()

try:

    df = energy.copy()

    # Timestamp detection
    timestamp_column = None

    for col in [
        "timestamp",
        "datetime",
        "recorded_at",
        "time"
    ]:
        if col in df.columns:
            timestamp_column = col
            break

    if timestamp_column:

        df[timestamp_column] = pd.to_datetime(
            df[timestamp_column],
            errors="coerce"
        )

        df["hour"] = df[timestamp_column].dt.hour
        df["day_of_week"] = df[timestamp_column].dt.dayofweek
        df["is_weekend"] = (
            df["day_of_week"] >= 5
        ).astype(int)

    else:

        df["hour"] = 0
        df["day_of_week"] = 0
        df["is_weekend"] = 0

    # Power column
    power_column = None

    for col in [
        "power_w",
        "power",
        "active_power_w"
    ]:
        if col in df.columns:
            power_column = col
            break

    if power_column is None:
        print_error("No power column found")
        raise ValueError("Missing power column")

    df["power_w"] = pd.to_numeric(
        df[power_column],
        errors="coerce"
    ).fillna(0)

    # Energy
    if "energy_kwh" in df.columns:

        df["energy_kwh"] = pd.to_numeric(
            df["energy_kwh"],
            errors="coerce"
        ).fillna(0)

    else:

        df["energy_kwh"] = (
            df["power_w"] * 5 / 3600000
        )

    # Group by appliance
    if "appliance_id" in df.columns:

        df["power_lag_1"] = (
            df.groupby("appliance_id")["power_w"]
            .shift(1)
            .fillna(0)
        )

        df["power_lag_5"] = (
            df.groupby("appliance_id")["power_w"]
            .shift(5)
            .fillna(0)
        )

        df["power_rolling_mean"] = (
            df.groupby("appliance_id")["power_w"]
            .transform(
                lambda x:
                x.rolling(5, min_periods=1).mean()
            )
        )

        df["power_rolling_max"] = (
            df.groupby("appliance_id")["power_w"]
            .transform(
                lambda x:
                x.rolling(5, min_periods=1).max()
            )
        )

    else:

        df["power_lag_1"] = (
            df["power_w"].shift(1).fillna(0)
        )

        df["power_lag_5"] = (
            df["power_w"].shift(5).fillna(0)
        )

        df["power_rolling_mean"] = (
            df["power_w"]
            .rolling(5, min_periods=1)
            .mean()
        )

        df["power_rolling_max"] = (
            df["power_w"]
            .rolling(5, min_periods=1)
            .max()
        )

    # Basic anomaly score
    mean_power = df["power_w"].mean()
    std_power = df["power_w"].std()

    if std_power and std_power > 0:
        df["anomaly_score"] = (
            (df["power_w"] - mean_power)
            .abs() / std_power
        ).clip(0, 5) / 5
    else:
        df["anomaly_score"] = 0.0

    # Peak risk
    peak_limit = df["power_w"].quantile(0.95)

    if peak_limit > 0:
        df["peak_risk"] = (
            df["power_w"] / peak_limit
        ).clip(0, 1)
    else:
        df["peak_risk"] = 0.0

    # Behaviour features
    df["user_behavior_score"] = 50.0

    df["energy_routine_index"] = (
        1.0 - df["anomaly_score"]
    )

    df["dsc_score"] = (
        1.0 - df["peak_risk"]
    )

    df["stability_score"] = (
        1.0 -
        (
            df["power_w"]
            .diff()
            .abs()
            .fillna(0)
            /
            max(
                df["power_w"].max(),
                1
            )
        ).clip(0, 1)
    )

    df["change_score"] = (
        df["power_w"]
        .diff()
        .abs()
        .fillna(0)
    )

    df["cdi_score"] = (
        (
            df["anomaly_score"]
            + df["peak_risk"]
        ) / 2
    )

    feature_path = os.path.join(
        directories["features"],
        "dynamic_features.csv"
    )

    df.to_csv(
        feature_path,
        index=False
    )

    elapsed = (time.time() - feature_start) / 60

    print_ok(
        f"Dynamic features generated: {feature_path}"
    )

    print(f"Feature rows: {len(df)}")
    print(f"Feature columns: {len(df.columns)}")

    record(
        "Dynamic Feature Generation",
        "SUCCESS",
        elapsed,
        f"{len(df)} rows"
    )

except Exception as e:

    elapsed = (time.time() - feature_start) / 60

    print_error(
        f"Dynamic feature generation failed: {e}"
    )

    record(
        "Dynamic Feature Generation",
        "FAILED",
        elapsed,
        str(e)
    )


# ============================================================
# STEP 10 — DYNAMIC HOUSE SUMMARY
# ============================================================

print()
print("=" * 70)
print("GENERATING HOUSE PIPELINE SUMMARY")
print("=" * 70)

summary_rows = []

for _, appliance in appliances.iterrows():

    aid = appliance["appliance_id"]

    if "appliance_id" in df.columns:

        subset = df[
            df["appliance_id"] == aid
        ].copy()

    else:

        subset = df.iloc[0:0]

    if len(subset) > 0:

        summary_rows.append({
            "house_id": house_id,
            "appliance_id": aid,
            "appliance_name":
                appliance["appliance_name"],
            "appliance_type":
                appliance["appliance_type"],
            "sensor_id":
                appliance["sensor_id"],
            "rated_power_w":
                appliance["rated_power_w"],
            "rows":
                len(subset),
            "average_power_w":
                subset["power_w"].mean(),
            "maximum_power_w":
                subset["power_w"].max(),
            "total_energy_kwh":
                subset["energy_kwh"].sum()
        })

    else:

        summary_rows.append({
            "house_id": house_id,
            "appliance_id": aid,
            "appliance_name":
                appliance["appliance_name"],
            "appliance_type":
                appliance["appliance_type"],
            "sensor_id":
                appliance["sensor_id"],
            "rated_power_w":
                appliance["rated_power_w"],
            "rows": 0,
            "average_power_w": 0,
            "maximum_power_w": 0,
            "total_energy_kwh": 0
        })


house_summary = pd.DataFrame(summary_rows)

summary_path = os.path.join(
    house_root,
    f"{house_id}_pipeline_summary.csv"
)

house_summary.to_csv(
    summary_path,
    index=False
)

print_ok(
    f"House pipeline summary: {summary_path}"
)

record(
    "House Pipeline Summary",
    "SUCCESS",
    0,
    f"{len(house_summary)} appliances"
)


# ============================================================
# STEP 11 — SAVE PIPELINE STATE
# ============================================================

total_time = (time.time() - pipeline_start) / 60

success_count = sum(
    1 for r in results
    if r["status"] == "SUCCESS"
)

failed_count = sum(
    1 for r in results
    if r["status"] == "FAILED"
)

skipped_count = sum(
    1 for r in results
    if r["status"] == "SKIPPED"
)


if failed_count == 0:
    system_status = "HOUSE_PIPELINE_READY"
else:
    system_status = "PARTIAL_PIPELINE"


log_path = os.path.join(
    PIPELINE_LOG_DIR,
    f"{house_id}_pipeline_execution.csv"
)

state_path = os.path.join(
    PIPELINE_OUTPUT_DIR,
    f"{house_id}_pipeline_state.csv"
)

log_df = pd.DataFrame(results)

log_df.to_csv(
    log_path,
    index=False
)

state_df = pd.DataFrame([{
    "house_id": house_id,
    "house_name": house_name,
    "appliance_count": len(appliances),
    "successful_modules": success_count,
    "failed_modules": failed_count,
    "skipped_modules": skipped_count,
    "total_time_minutes": round(total_time, 4),
    "system_status": system_status,
    "timestamp": datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
}])

state_df.to_csv(
    state_path,
    index=False
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 70)
print("MODULE STATUS")
print("=" * 70)

for r in results:

    print(
        f"{r['module']:<35}"
        f"{r['status']:<12}"
        f"{r['time_minutes']:.3f} min"
    )


print()
print("=" * 70)
print("MODULE 14C COMPLETE")
print("=" * 70)

print()
print("PIPELINE SUMMARY")
print("-" * 70)

print(f"House ID            : {house_id}")
print(f"House Name          : {house_name}")
print(f"Appliances          : {len(appliances)}")
print(f"Successful modules  : {success_count}")
print(f"Failed modules      : {failed_count}")
print(f"Skipped modules     : {skipped_count}")
print(f"Total time          : {total_time:.2f} minutes")
print(f"System status       : {system_status}")

print()
print("OUTPUT FILES")
print("-" * 70)

print(f"Pipeline log:")
print(log_path)

print()
print(f"Pipeline state:")
print(state_path)

print()
print(f"House summary:")
print(summary_path)

print()
print("=" * 70)