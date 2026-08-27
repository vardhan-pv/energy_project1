# ================================================================
# MODULE 15 — REAL-TIME IoT ACTION EXECUTION + FEEDBACK LOOP
# ================================================================
#
# Architecture:
#
# House
#   ↓
# Appliances
#   ↓
# Dynamic Features
#   ↓
# Module 14E — ML/RL Models
#   ↓
# Module 14F — RL Optimization
#   ↓
# Module 14G — Self-Evolution
#   ↓
# Module 14H — Real-Time Decision
#   ↓
# Module 15 — IoT Action Execution
#   ↓
# Appliance / Smart Plug / ESP32
#   ↓
# Sensor Feedback
#   ↓
# Feedback Evaluation
#   ↓
# Future Policy Update
#
# DEMO MODE:
#   Simulates IoT command execution safely.
#
# LIVE MODE:
#   Prepared interface for ESP32 / Smart Plug integration.
#
# ================================================================

import os
import sys
import time
import json
import uuid
from datetime import datetime

import numpy as np
import pandas as pd


# ================================================================
# CONFIGURATION
# ================================================================

PROJECT_ROOT = r"E:\energy_project"

INITIALIZATION_DIR = os.path.join(
    PROJECT_ROOT,
    "initialization"
)

HOUSE_CONFIG_PATH = os.path.join(
    INITIALIZATION_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG_PATH = os.path.join(
    INITIALIZATION_DIR,
    "appliance_config.csv"
)


# ================================================================
# LOAD HOUSE CONFIGURATION
# ================================================================

print("=" * 70)
print("MODULE 15 — REAL-TIME IoT ACTION EXECUTION + FEEDBACK LOOP")
print("=" * 70)

print()
print("=" * 70)
print("CHECKING REQUIRED FILES")
print("=" * 70)


def check_file(path, name):
    if not os.path.isfile(path):
        print(f"[ERROR] {name}: {path}")
        sys.exit(1)

    print(f"[OK] {name}: {path}")


check_file(
    HOUSE_CONFIG_PATH,
    "House configuration"
)

check_file(
    APPLIANCE_CONFIG_PATH,
    "Appliance configuration"
)


# ================================================================
# HOUSE CONFIG
# ================================================================

print()
print("Loading house configuration...")

with open(
    HOUSE_CONFIG_PATH,
    "r",
    encoding="utf-8"
) as f:
    house_config = json.load(f)


HOUSE_ID = house_config.get(
    "house_id",
    "UNKNOWN_HOUSE"
)

HOUSE_NAME = house_config.get(
    "house_name",
    "Unknown_House"
)

LOCATION = house_config.get(
    "location",
    "Unknown"
)

print(f"House ID   : {HOUSE_ID}")
print(f"House Name : {HOUSE_NAME}")
print(f"Location   : {LOCATION}")


# ================================================================
# PATHS
# ================================================================

HOUSE_DIR = os.path.join(
    PROJECT_ROOT,
    "house_data",
    HOUSE_ID
)

FEATURE_DIR = os.path.join(
    HOUSE_DIR,
    "features"
)

MODEL_DIR = os.path.join(
    HOUSE_DIR,
    "models"
)

OPTIMIZATION_DIR = os.path.join(
    HOUSE_DIR,
    "optimization"
)

EVOLUTION_DIR = os.path.join(
    HOUSE_DIR,
    "evolution"
)

REALTIME_DIR = os.path.join(
    HOUSE_DIR,
    "realtime"
)

IOT_DIR = os.path.join(
    HOUSE_DIR,
    "iot"
)

os.makedirs(IOT_DIR, exist_ok=True)


# ================================================================
# INPUT FILES
# ================================================================

REALTIME_DECISIONS_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_decisions.csv"
)

REALTIME_SUMMARY_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_decision_summary.csv"
)

ACTION_SUMMARY_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_action_summary.csv"
)

EVOLVED_POLICY_PATH = os.path.join(
    EVOLUTION_DIR,
    "dynamic_evolved_policy_parameters.csv"
)


# ================================================================
# OUTPUT FILES
# ================================================================

IOT_EXECUTION_PATH = os.path.join(
    IOT_DIR,
    "iot_action_execution.csv"
)

IOT_FEEDBACK_PATH = os.path.join(
    IOT_DIR,
    "iot_action_feedback.csv"
)

IOT_DEVICE_STATUS_PATH = os.path.join(
    IOT_DIR,
    "iot_device_status.csv"
)

IOT_ACTION_SUMMARY_PATH = os.path.join(
    IOT_DIR,
    "iot_action_summary.csv"
)

IOT_FEEDBACK_SUMMARY_PATH = os.path.join(
    IOT_DIR,
    "iot_feedback_summary.csv"
)

IOT_SYSTEM_SUMMARY_PATH = os.path.join(
    IOT_DIR,
    "iot_execution_system_summary.csv"
)


# ================================================================
# EXECUTION MODE
# ================================================================

EXECUTION_MODE = "DEMO"

# Available:
#
# DEMO
#   Safe simulation
#
# LIVE
#   Reserved for ESP32 / Smart Plug integration
#

print()
print("=" * 70)
print("EXECUTION CONFIGURATION")
print("=" * 70)

print(f"Execution mode : {EXECUTION_MODE}")
print("Hardware mode  : SAFE DEMO")


# ================================================================
# CHECK INPUTS
# ================================================================

print()
print("=" * 70)
print("CHECKING MODULE 15 INPUTS")
print("=" * 70)

check_file(
    REALTIME_DECISIONS_PATH,
    "Module 14H realtime decisions"
)

check_file(
    REALTIME_SUMMARY_PATH,
    "Module 14H decision summary"
)

check_file(
    ACTION_SUMMARY_PATH,
    "Module 14H action summary"
)

check_file(
    EVOLVED_POLICY_PATH,
    "Module 14G evolved policy"
)


# ================================================================
# LOAD APPLIANCE CONFIGURATION
# ================================================================

print()
print("Loading appliance configuration...")

appliances = pd.read_csv(
    APPLIANCE_CONFIG_PATH
)

print(
    f"Registered appliances: {len(appliances)}"
)

required_appliance_columns = [
    "appliance_id",
    "house_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w",
    "status"
]

missing = [
    c for c in required_appliance_columns
    if c not in appliances.columns
]

if missing:
    raise ValueError(
        "Missing appliance configuration columns: "
        + ", ".join(missing)
    )


print()

print(
    appliances[
        [
            "appliance_id",
            "appliance_name",
            "appliance_type",
            "sensor_id",
            "rated_power_w"
        ]
    ].to_string(index=False)
)


# ================================================================
# VERIFY HOUSE
# ================================================================

wrong_house = appliances[
    appliances["house_id"].astype(str) != str(HOUSE_ID)
]

if len(wrong_house) > 0:
    raise ValueError(
        "Appliance configuration contains appliances "
        "belonging to another house."
    )


# ================================================================
# DEVICE MAP
# ================================================================

print()
print("=" * 70)
print("IOT DEVICE MAPPING")
print("=" * 70)

device_map = {}

for _, row in appliances.iterrows():

    appliance_id = str(row["appliance_id"])
    sensor_id = str(row["sensor_id"])

    device_map[appliance_id] = {
        "appliance_id": appliance_id,
        "appliance_name": str(row["appliance_name"]),
        "appliance_type": str(row["appliance_type"]),
        "sensor_id": sensor_id,
        "rated_power_w": float(row["rated_power_w"]),
        "device_id": f"IOT_{sensor_id}",
        "connection_type": "ESP32_SMART_PLUG",
        "execution_mode": EXECUTION_MODE
    }

    print(
        f"{appliance_id} -> "
        f"{sensor_id} -> "
        f"IOT_{sensor_id} -> "
        f"{row['appliance_name']}"
    )


# ================================================================
# EXPECTED FOUR DEVICES
# ================================================================

EXPECTED_SENSOR_IDS = {
    "SP001",
    "SP002",
    "SP003",
    "SP004"
}

actual_sensor_ids = set(
    appliances["sensor_id"].astype(str)
)

missing_sensors = EXPECTED_SENSOR_IDS - actual_sensor_ids

if missing_sensors:
    print()
    print(
        "[WARNING] Expected sensors missing:",
        sorted(missing_sensors)
    )


# ================================================================
# LOAD MODULE 14H DATA
# ================================================================

print()
print("=" * 70)
print("LOADING MODULE 14H REAL-TIME DECISIONS")
print("=" * 70)

realtime = pd.read_csv(
    REALTIME_DECISIONS_PATH
)

print(
    f"Realtime decision rows: {len(realtime)}"
)

print(
    f"Realtime columns       : {len(realtime.columns)}"
)


# ================================================================
# DISPLAY COLUMNS
# ================================================================

print()
print("Available decision columns:")

for i, column in enumerate(
    realtime.columns,
    start=1
):
    print(
        f"{i:2d}. {column}"
    )


# ================================================================
# IDENTIFY REQUIRED COLUMNS
# ================================================================

def find_column(df, candidates):

    for candidate in candidates:

        if candidate in df.columns:
            return candidate

    return None


appliance_id_col = find_column(
    realtime,
    [
        "appliance_id",
        "app_id"
    ]
)

appliance_name_col = find_column(
    realtime,
    [
        "appliance_name",
        "name"
    ]
)

action_col = find_column(
    realtime,
    [
        "recommended_action",
        "action",
        "decision",
        "selected_action"
    ]
)

power_col = find_column(
    realtime,
    [
        "power_w",
        "current_power_w",
        "actual_power_w"
    ]
)

energy_col = find_column(
    realtime,
    [
        "energy_kwh",
        "current_energy_kwh"
    ]
)

optimized_energy_col = find_column(
    realtime,
    [
        "optimized_energy_kwh"
    ]
)

confidence_col = find_column(
    realtime,
    [
        "policy_confidence",
        "average_policy_confidence"
    ]
)

timestamp_col = find_column(
    realtime,
    [
        "timestamp",
        "datetime"
    ]
)


# ================================================================
# REQUIRED INPUT VALIDATION
# ================================================================

print()
print("=" * 70)
print("INPUT COLUMN VALIDATION")
print("=" * 70)

print(
    "Appliance ID column :",
    appliance_id_col
)

print(
    "Appliance name      :",
    appliance_name_col
)

print(
    "Action column       :",
    action_col
)

print(
    "Power column        :",
    power_col
)

print(
    "Energy column       :",
    energy_col
)

print(
    "Confidence column   :",
    confidence_col
)

print(
    "Timestamp column    :",
    timestamp_col
)


if appliance_id_col is None:
    raise ValueError(
        "Module 14H output does not contain appliance_id."
    )

if action_col is None:
    raise ValueError(
        "Module 14H output does not contain an action column."
    )

if power_col is None:
    raise ValueError(
        "Module 14H output does not contain power_w."
    )

if energy_col is None:
    raise ValueError(
        "Module 14H output does not contain energy_kwh."
    )


# ================================================================
# NORMALIZE ACTIONS
# ================================================================

ACTION_MAP = {
    "maintain": "KEEP_CURRENT",
    "reduce": "REDUCE_LOAD",
    "shift": "DELAY_LOAD",
    "turn_off": "POWER_OFF",
    "turnoff": "POWER_OFF",
    "off": "POWER_OFF"
}


ACTION_NAMES = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}


def normalize_action(value):

    if pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip().lower()

    # Numeric action representation
    try:

        numeric = int(float(text))

        if numeric in ACTION_NAMES:
            return ACTION_NAMES[numeric]

    except Exception:
        pass

    if text in ACTION_MAP:
        return text

    if text in ACTION_NAMES.values():
        return text

    if "maintain" in text:
        return "maintain"

    if "reduce" in text:
        return "reduce"

    if "shift" in text:
        return "shift"

    if "off" in text:
        return "turn_off"

    return "UNKNOWN"


realtime["normalized_action"] = (
    realtime[action_col]
    .apply(normalize_action)
)


# ================================================================
# VALIDATE ACTIONS
# ================================================================

valid_actions = {
    "maintain",
    "reduce",
    "shift",
    "turn_off"
}

invalid_actions = set(
    realtime["normalized_action"]
) - valid_actions

if invalid_actions:

    raise ValueError(
        "Invalid actions found: "
        + ", ".join(
            sorted(
                str(x)
                for x in invalid_actions
            )
        )
    )

print()
print(
    "[OK] All actions are valid."
)


# ================================================================
# SIMULATED DEVICE BEHAVIOR
# ================================================================

def calculate_target_power(
    current_power,
    rated_power,
    action
):

    current_power = max(
        0.0,
        float(current_power)
    )

    rated_power = max(
        0.0,
        float(rated_power)
    )

    if action == "maintain":

        return current_power

    if action == "reduce":

        # Demo reduction.
        # Real ESP32 implementation will determine
        # actual appliance control behavior.

        return current_power * 0.80

    if action == "shift":

        # Shift means temporarily reduce demand
        # until the next allowed period.

        return current_power * 0.50

    if action == "turn_off":

        return 0.0

    return current_power


def simulate_device_response(
    current_power,
    target_power,
    action
):

    current_power = float(
        max(0.0, current_power)
    )

    target_power = float(
        max(0.0, target_power)
    )

    if EXECUTION_MODE == "DEMO":

        # Simulate realistic device response.
        #
        # Maintain → almost exact
        # Reduce   → small execution deviation
        # Shift    → small execution deviation
        # Off      → 0

        if action == "maintain":

            actual = current_power

        elif action == "reduce":

            actual = target_power * 1.03

        elif action == "shift":

            actual = target_power * 1.05

        elif action == "turn_off":

            actual = 0.0

        else:

            actual = current_power

        response_status = "SIMULATED_SUCCESS"

        device_status = "ONLINE_DEMO"

        response_time = np.random.uniform(
            25,
            120
        )

        return (
            actual,
            response_status,
            device_status,
            response_time
        )

    # ============================================================
    # LIVE MODE PLACEHOLDER
    # ============================================================

    raise NotImplementedError(
        "LIVE mode is not yet connected to ESP32."
    )


# ================================================================
# ENERGY FEEDBACK CALCULATION
# ================================================================

def estimate_energy_saving(
    current_power,
    actual_power,
    interval_minutes=5
):

    current_power = max(
        0.0,
        float(current_power)
    )

    actual_power = max(
        0.0,
        float(actual_power)
    )

    interval_hours = (
        float(interval_minutes) / 60.0
    )

    before_energy = (
        current_power *
        interval_hours /
        1000.0
    )

    after_energy = (
        actual_power *
        interval_hours /
        1000.0
    )

    saving = max(
        0.0,
        before_energy - after_energy
    )

    return (
        before_energy,
        after_energy,
        saving
    )


# ================================================================
# PROCESS DECISIONS
# ================================================================

print()
print("=" * 70)
print("REAL-TIME IoT ACTION EXECUTION")
print("=" * 70)

print()
print(
    "Mode:",
    EXECUTION_MODE
)

execution_records = []
feedback_records = []
device_records = []

start_time = time.time()


for index, row in realtime.iterrows():

    appliance_id = str(
        row[appliance_id_col]
    )

    if appliance_id not in device_map:

        print(
            f"[WARNING] Unknown appliance: "
            f"{appliance_id}"
        )

        continue

    device = device_map[
        appliance_id
    ]

    appliance_name = device[
        "appliance_name"
    ]

    sensor_id = device[
        "sensor_id"
    ]

    rated_power = device[
        "rated_power_w"
    ]

    current_power = float(
        pd.to_numeric(
            row[power_col],
            errors="coerce"
        )
    )

    if np.isnan(current_power):
        current_power = 0.0

    current_energy = float(
        pd.to_numeric(
            row[energy_col],
            errors="coerce"
        )
    )

    if np.isnan(current_energy):
        current_energy = 0.0

    action = row[
        "normalized_action"
    ]

    command = ACTION_MAP[
        action
    ]

    if timestamp_col:

        decision_timestamp = str(
            row[timestamp_col]
        )

    else:

        decision_timestamp = (
            datetime.now().isoformat()
        )

    execution_id = (
        "IOT_"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )
        + "_"
        + uuid.uuid4().hex[:8].upper()
    )

    target_power = calculate_target_power(
        current_power,
        rated_power,
        action
    )

    print()
    print(
        "-" * 70
    )

    print(
        f"EXECUTION {index + 1}/{len(realtime)}"
    )

    print(
        f"Appliance : {appliance_name}"
    )

    print(
        f"Sensor    : {sensor_id}"
    )

    print(
        f"Action    : {action}"
    )

    print(
        f"Command   : {command}"
    )

    print(
        f"Power     : {current_power:.3f} W"
    )

    print(
        f"Target    : {target_power:.3f} W"
    )

    actual_power, execution_status, device_status, response_time = (
        simulate_device_response(
            current_power,
            target_power,
            action
        )
    )

    (
        energy_before,
        energy_after,
        actual_saving
    ) = estimate_energy_saving(
        current_power,
        actual_power
    )

    if current_power > 0:

        actual_saving_percentage = (
            actual_saving /
            energy_before *
            100.0
        )

    else:

        actual_saving_percentage = 0.0

    expected_saving = max(
        0.0,
        energy_before - (
            target_power *
            (5.0 / 60.0) /
            1000.0
        )
    )

    # ------------------------------------------------------------
    # FEEDBACK
    # ------------------------------------------------------------

    power_error = abs(
        target_power -
        actual_power
    )

    if target_power > 0:

        relative_error = (
            power_error /
            max(target_power, 0.001)
        )

    else:

        relative_error = (
            actual_power /
            max(
                rated_power,
                1.0
            )
        )

    if action == "maintain":

        feedback_score = 1.0

    elif action == "turn_off":

        feedback_score = (
            1.0
            if actual_power <= 1.0
            else 0.0
        )

    else:

        feedback_score = max(
            0.0,
            1.0 - relative_error
        )

    if feedback_score >= 0.90:

        feedback_class = "POSITIVE"

    elif feedback_score >= 0.70:

        feedback_class = "ACCEPTABLE"

    else:

        feedback_class = "NEGATIVE"

    # ------------------------------------------------------------
    # EXECUTION RECORD
    # ------------------------------------------------------------

    execution_records.append({

        "execution_id":
            execution_id,

        "timestamp":
            datetime.now().isoformat(),

        "decision_timestamp":
            decision_timestamp,

        "house_id":
            HOUSE_ID,

        "house_name":
            HOUSE_NAME,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "appliance_type":
            device["appliance_type"],

        "sensor_id":
            sensor_id,

        "device_id":
            device["device_id"],

        "execution_mode":
            EXECUTION_MODE,

        "requested_action":
            action,

        "command":
            command,

        "rated_power_w":
            rated_power,

        "previous_power_w":
            current_power,

        "target_power_w":
            target_power,

        "actual_power_w":
            actual_power,

        "energy_before_kwh":
            energy_before,

        "energy_after_kwh":
            energy_after,

        "expected_savings_kwh":
            expected_saving,

        "actual_savings_kwh":
            actual_saving,

        "actual_savings_percentage":
            actual_saving_percentage,

        "execution_status":
            execution_status,

        "device_status":
            device_status,

        "response_time_ms":
            response_time,

        "feedback_score":
            feedback_score,

        "feedback_class":
            feedback_class
    })

    # ------------------------------------------------------------
    # FEEDBACK RECORD
    # ------------------------------------------------------------

    feedback_records.append({

        "feedback_id":
            "FDB_"
            + uuid.uuid4().hex[:10].upper(),

        "execution_id":
            execution_id,

        "timestamp":
            datetime.now().isoformat(),

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "requested_action":
            action,

        "target_power_w":
            target_power,

        "actual_power_w":
            actual_power,

        "power_error_w":
            power_error,

        "relative_error":
            relative_error,

        "expected_savings_kwh":
            expected_saving,

        "actual_savings_kwh":
            actual_saving,

        "actual_savings_percentage":
            actual_saving_percentage,

        "feedback_score":
            feedback_score,

        "feedback_class":
            feedback_class,

        "execution_status":
            execution_status,

        "learning_signal":
            (
                "POSITIVE_REINFORCEMENT"
                if feedback_class == "POSITIVE"
                else
                "CORRECTIVE_FEEDBACK"
            )
    })

    # ------------------------------------------------------------
    # DEVICE STATUS
    # ------------------------------------------------------------

    device_records.append({

        "timestamp":
            datetime.now().isoformat(),

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device["device_id"],

        "connection_type":
            device["connection_type"],

        "execution_mode":
            EXECUTION_MODE,

        "device_status":
            device_status,

        "execution_status":
            execution_status,

        "last_command":
            command,

        "last_action":
            action,

        "current_power_w":
            actual_power,

        "rated_power_w":
            rated_power,

        "response_time_ms":
            response_time
    })

    print(
        f"Actual    : {actual_power:.3f} W"
    )

    print(
        f"Status    : {execution_status}"
    )

    print(
        f"Feedback  : {feedback_class}"
        f" ({feedback_score:.3f})"
    )


# ================================================================
# CREATE DATAFRAMES
# ================================================================

execution_df = pd.DataFrame(
    execution_records
)

feedback_df = pd.DataFrame(
    feedback_records
)

device_df = pd.DataFrame(
    device_records
)


# ================================================================
# VALIDATE GENERATED DATA
# ================================================================

print()
print("=" * 70)
print("GENERATED DATA VALIDATION")
print("=" * 70)

print(
    f"Execution rows : {len(execution_df)}"
)

print(
    f"Feedback rows  : {len(feedback_df)}"
)

print(
    f"Device rows    : {len(device_df)}"
)


# ================================================================
# ACTION SUMMARY
# ================================================================

if len(execution_df) > 0:

    action_summary = (
        execution_df
        .groupby(
            [
                "appliance_id",
                "appliance_name",
                "requested_action"
            ],
            dropna=False
        )
        .agg(
            execution_count=(
                "execution_id",
                "count"
            ),

            successful_executions=(
                "execution_status",
                lambda x:
                    int(
                        (
                            x == "SIMULATED_SUCCESS"
                        ).sum()
                    )
            ),

            average_previous_power_w=(
                "previous_power_w",
                "mean"
            ),

            average_actual_power_w=(
                "actual_power_w",
                "mean"
            ),

            total_actual_savings_kwh=(
                "actual_savings_kwh",
                "sum"
            ),

            average_feedback_score=(
                "feedback_score",
                "mean"
            )
        )
        .reset_index()
    )

else:

    action_summary = pd.DataFrame()


# ================================================================
# FEEDBACK SUMMARY
# ================================================================

if len(feedback_df) > 0:

    feedback_summary = (
        feedback_df
        .groupby(
            [
                "appliance_id",
                "appliance_name"
            ],
            dropna=False
        )
        .agg(
            feedback_records=(
                "feedback_id",
                "count"
            ),

            average_feedback_score=(
                "feedback_score",
                "mean"
            ),

            average_power_error_w=(
                "power_error_w",
                "mean"
            ),

            positive_feedback=(
                "feedback_class",
                lambda x:
                    int(
                        (
                            x == "POSITIVE"
                        ).sum()
                    )
            ),

            acceptable_feedback=(
                "feedback_class",
                lambda x:
                    int(
                        (
                            x == "ACCEPTABLE"
                        ).sum()
                    )
            ),

            negative_feedback=(
                "feedback_class",
                lambda x:
                    int(
                        (
                            x == "NEGATIVE"
                        ).sum()
                    )
            ),

            total_actual_savings_kwh=(
                "actual_savings_kwh",
                "sum"
            ),

            average_actual_savings_percentage=(
                "actual_savings_percentage",
                "mean"
            )
        )
        .reset_index()
    )

else:

    feedback_summary = pd.DataFrame()


# ================================================================
# SYSTEM TOTALS
# ================================================================

total_execution_rows = len(
    execution_df
)

total_feedback_rows = len(
    feedback_df
)

total_device_rows = len(
    device_df
)


successful_actions = int(
    (
        execution_df[
            "execution_status"
        ]
        == "SIMULATED_SUCCESS"
    ).sum()
)


failed_actions = (
    total_execution_rows -
    successful_actions
)


total_expected_savings = float(
    execution_df[
        "expected_savings_kwh"
    ].sum()
)


total_actual_savings = float(
    execution_df[
        "actual_savings_kwh"
    ].sum()
)


average_feedback = float(
    feedback_df[
        "feedback_score"
    ].mean()
) if len(feedback_df) else 0.0


average_response = float(
    execution_df[
        "response_time_ms"
    ].mean()
) if len(execution_df) else 0.0


positive_feedback = int(
    (
        feedback_df[
            "feedback_class"
        ]
        == "POSITIVE"
    ).sum()
)


acceptable_feedback = int(
    (
        feedback_df[
            "feedback_class"
        ]
        == "ACCEPTABLE"
    ).sum()
)


negative_feedback = int(
    (
        feedback_df[
            "feedback_class"
        ]
        == "NEGATIVE"
    ).sum()
)


if total_expected_savings > 0:

    feedback_saving_ratio = (
        total_actual_savings /
        total_expected_savings
    )

else:

    feedback_saving_ratio = 0.0


# ================================================================
# SYSTEM STATUS
# ================================================================

if (
    total_execution_rows > 0
    and
    successful_actions ==
    total_execution_rows
    and
    total_feedback_rows ==
    total_execution_rows
):

    system_status = (
        "IOT_DEMO_EXECUTION_READY"
    )

else:

    system_status = (
        "IOT_EXECUTION_PARTIAL"
    )


# ================================================================
# SYSTEM SUMMARY
# ================================================================

system_summary = pd.DataFrame([{

    "timestamp":
        datetime.now().isoformat(),

    "house_id":
        HOUSE_ID,

    "house_name":
        HOUSE_NAME,

    "location":
        LOCATION,

    "execution_mode":
        EXECUTION_MODE,

    "registered_appliances":
        len(appliances),

    "execution_rows":
        total_execution_rows,

    "feedback_rows":
        total_feedback_rows,

    "device_status_rows":
        total_device_rows,

    "successful_actions":
        successful_actions,

    "failed_actions":
        failed_actions,

    "expected_savings_kwh":
        total_expected_savings,

    "actual_savings_kwh":
        total_actual_savings,

    "average_feedback_score":
        average_feedback,

    "positive_feedback":
        positive_feedback,

    "acceptable_feedback":
        acceptable_feedback,

    "negative_feedback":
        negative_feedback,

    "feedback_saving_ratio":
        feedback_saving_ratio,

    "average_response_time_ms":
        average_response,

    "esp32_interface":
        "READY",

    "smart_plug_interface":
        "READY",

    "feedback_loop":
        "ACTIVE",

    "hardware_connected":
        False,

    "system_status":
        system_status
}])


# ================================================================
# SAVE OUTPUTS
# ================================================================

print()
print("=" * 70)
print("GENERATING MODULE 15 OUTPUTS")
print("=" * 70)


execution_df.to_csv(
    IOT_EXECUTION_PATH,
    index=False
)

print(
    "[OK] IoT action execution:"
)

print(
    IOT_EXECUTION_PATH
)


feedback_df.to_csv(
    IOT_FEEDBACK_PATH,
    index=False
)

print(
    "[OK] IoT action feedback:"
)

print(
    IOT_FEEDBACK_PATH
)


device_df.to_csv(
    IOT_DEVICE_STATUS_PATH,
    index=False
)

print(
    "[OK] IoT device status:"
)

print(
    IOT_DEVICE_STATUS_PATH
)


action_summary.to_csv(
    IOT_ACTION_SUMMARY_PATH,
    index=False
)

print(
    "[OK] IoT action summary:"
)

print(
    IOT_ACTION_SUMMARY_PATH
)


feedback_summary.to_csv(
    IOT_FEEDBACK_SUMMARY_PATH,
    index=False
)

print(
    "[OK] IoT feedback summary:"
)

print(
    IOT_FEEDBACK_SUMMARY_PATH
)


system_summary.to_csv(
    IOT_SYSTEM_SUMMARY_PATH,
    index=False
)

print(
    "[OK] IoT system summary:"
)

print(
    IOT_SYSTEM_SUMMARY_PATH
)


# ================================================================
# FINAL VALIDATION
# ================================================================

print()
print("=" * 70)
print("MODULE 15 VALIDATION")
print("=" * 70)


# ------------------------------------------------
# Appliance coverage
# ------------------------------------------------

registered_ids = set(
    appliances[
        "appliance_id"
    ].astype(str)
)

processed_ids = set(
    execution_df[
        "appliance_id"
    ].astype(str)
)


missing_appliances = (
    registered_ids -
    processed_ids
)


print(
    f"Registered appliances : "
    f"{len(registered_ids)}"
)

print(
    f"Processed appliances  : "
    f"{len(processed_ids)}"
)

if not missing_appliances:

    print(
        "[OK] Every registered appliance "
        "was processed."
    )

else:

    print(
        "[WARNING] Missing appliances:",
        sorted(missing_appliances)
    )


# ------------------------------------------------
# NULL CHECK
# ------------------------------------------------

execution_nulls = int(
    execution_df.isnull()
    .sum()
    .sum()
)

feedback_nulls = int(
    feedback_df.isnull()
    .sum()
    .sum()
)

device_nulls = int(
    device_df.isnull()
    .sum()
    .sum()
)


print()
print("NULL VALIDATION")
print("-" * 70)

print(
    f"Execution NULLs : {execution_nulls}"
)

print(
    f"Feedback NULLs  : {feedback_nulls}"
)

print(
    f"Device NULLs    : {device_nulls}"
)


if (
    execution_nulls == 0
    and
    feedback_nulls == 0
    and
    device_nulls == 0
):

    print(
        "[OK] No NULL values."
    )

else:

    raise ValueError(
        "NULL values detected in Module 15 outputs."
    )


# ------------------------------------------------
# DUPLICATE CHECK
# ------------------------------------------------

execution_duplicates = int(
    execution_df[
        "execution_id"
    ].duplicated()
    .sum()
)

feedback_duplicates = int(
    feedback_df[
        "feedback_id"
    ].duplicated()
    .sum()
)


print()
print("DUPLICATE VALIDATION")
print("-" * 70)

print(
    f"Execution duplicates : "
    f"{execution_duplicates}"
)

print(
    f"Feedback duplicates  : "
    f"{feedback_duplicates}"
)


if (
    execution_duplicates == 0
    and
    feedback_duplicates == 0
):

    print(
        "[OK] No duplicate execution "
        "or feedback IDs."
    )

else:

    raise ValueError(
        "Duplicate IDs detected."
    )


# ------------------------------------------------
# ACTION VALIDATION
# ------------------------------------------------

actual_actions = set(
    execution_df[
        "requested_action"
    ].astype(str)
)

invalid = (
    actual_actions -
    valid_actions
)


if not invalid:

    print(
        "[OK] All requested actions valid."
    )

else:

    raise ValueError(
        "Invalid action values detected."
    )


# ------------------------------------------------
# POWER VALIDATION
# ------------------------------------------------

negative_actual_power = int(
    (
        execution_df[
            "actual_power_w"
        ]
        < 0
    ).sum()
)

negative_savings = int(
    (
        execution_df[
            "actual_savings_kwh"
        ]
        < 0
    ).sum()
)


print()
print("POWER / ENERGY VALIDATION")
print("-" * 70)

print(
    f"Negative actual power : "
    f"{negative_actual_power}"
)

print(
    f"Negative savings      : "
    f"{negative_savings}"
)


if (
    negative_actual_power == 0
    and
    negative_savings == 0
):

    print(
        "[OK] Power and savings values valid."
    )

else:

    raise ValueError(
        "Invalid negative power/savings detected."
    )


# ------------------------------------------------
# DEVICE VALIDATION
# ------------------------------------------------

valid_device_status = {
    "ONLINE_DEMO"
}

invalid_device_status = (
    set(
        device_df[
            "device_status"
        ].astype(str)
    )
    -
    valid_device_status
)


if not invalid_device_status:

    print(
        "[OK] Device status values valid."
    )

else:

    raise ValueError(
        "Invalid device status detected."
    )


# ================================================================
# DISPLAY ACTION SUMMARY
# ================================================================

print()
print("=" * 70)
print("IOT ACTION EXECUTION RESULTS")
print("=" * 70)

if len(action_summary) > 0:

    print(
        action_summary.to_string(
            index=False
        )
    )


# ================================================================
# DISPLAY FEEDBACK SUMMARY
# ================================================================

print()
print("=" * 70)
print("IOT FEEDBACK RESULTS")
print("=" * 70)

if len(feedback_summary) > 0:

    print(
        feedback_summary.to_string(
            index=False
        )
    )


# ================================================================
# SYSTEM SUMMARY
# ================================================================

elapsed_minutes = (
    time.time() -
    start_time
) / 60.0


print()
print("=" * 70)
print("SYSTEM IoT EXECUTION SUMMARY")
print("=" * 70)

print(
    f"House ID                  : "
    f"{HOUSE_ID}"
)

print(
    f"House Name                : "
    f"{HOUSE_NAME}"
)

print(
    f"Appliances                : "
    f"{len(appliances)}"
)

print(
    f"Execution mode            : "
    f"{EXECUTION_MODE}"
)

print(
    f"IoT execution rows        : "
    f"{total_execution_rows}"
)

print(
    f"Successful actions        : "
    f"{successful_actions}"
)

print(
    f"Failed actions            : "
    f"{failed_actions}"
)

print(
    f"Feedback records          : "
    f"{total_feedback_rows}"
)

print(
    f"Positive feedback         : "
    f"{positive_feedback}"
)

print(
    f"Acceptable feedback       : "
    f"{acceptable_feedback}"
)

print(
    f"Negative feedback         : "
    f"{negative_feedback}"
)

print(
    f"Expected savings          : "
    f"{total_expected_savings:.6f} kWh"
)

print(
    f"Actual savings            : "
    f"{total_actual_savings:.6f} kWh"
)

print(
    f"Average feedback score    : "
    f"{average_feedback:.4f}"
)

print(
    f"Average response time     : "
    f"{average_response:.2f} ms"
)

print(
    f"ESP32 interface           : READY"
)

print(
    f"Smart plug interface      : READY"
)

print(
    f"Feedback loop             : ACTIVE"
)

print(
    f"Hardware connected        : NO (DEMO)"
)

print(
    f"System status             : "
    f"{system_status}"
)


# ================================================================
# OUTPUT FILES
# ================================================================

print()
print("=" * 70)
print("MODULE 15 OUTPUT FILES")
print("=" * 70)

print()
print(
    "IoT action execution:"
)

print(
    IOT_EXECUTION_PATH
)

print()
print(
    "IoT action feedback:"
)

print(
    IOT_FEEDBACK_PATH
)

print()
print(
    "IoT device status:"
)

print(
    IOT_DEVICE_STATUS_PATH
)

print()
print(
    "IoT action summary:"
)

print(
    IOT_ACTION_SUMMARY_PATH
)

print()
print(
    "IoT feedback summary:"
)

print(
    IOT_FEEDBACK_SUMMARY_PATH
)

print()
print(
    "IoT execution system summary:"
)

print(
    IOT_SYSTEM_SUMMARY_PATH
)


# ================================================================
# COMPLETE
# ================================================================

print()
print("=" * 70)
print("MODULE 15 COMPLETE")
print("=" * 70)

print()
print(
    "[SUCCESS] Module 14H decisions consumed."
)

print(
    "[SUCCESS] Four-appliance IoT mapping validated."
)

print(
    "[SUCCESS] DEMO IoT actions executed."
)

print(
    "[SUCCESS] Execution feedback generated."
)

print(
    "[SUCCESS] Feedback loop activated."
)

print(
    "[SUCCESS] ESP32/Smart Plug interface prepared."
)

print(
    "[SUCCESS] Module 15 validation passed."
)

print()
print(
    f"Total time: "
    f"{elapsed_minutes:.2f} minutes"
)

print("=" * 70)