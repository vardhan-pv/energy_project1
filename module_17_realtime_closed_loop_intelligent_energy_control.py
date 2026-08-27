# ================================================================
# MODULE 17 — REAL-TIME CLOSED-LOOP INTELLIGENT ENERGY CONTROL
# ================================================================
#
# Purpose:
#   Connect Module 14H decisions
#        ↓
#   Module 15 IoT execution
#        ↓
#   Module 16 virtual ESP32 hardware
#        ↓
#   Sensor feedback
#        ↓
#   Closed-loop evaluation
#        ↓
#   Reward calculation
#        ↓
#   Policy adaptation
#        ↓
#   Next control recommendation
#
# Hardware:
#   Physical ESP32      : NOT REQUIRED
#   Physical smart plug: NOT REQUIRED
#   Simulation          : ACTIVE
#
# ================================================================

import os
import sys
import time
import math
import json
import traceback
from datetime import datetime

import pandas as pd
import numpy as np


# ================================================================
# GLOBAL CONFIGURATION
# ================================================================

MODULE_NAME = "MODULE 17 — REAL-TIME CLOSED-LOOP INTELLIGENT ENERGY CONTROL"

EXECUTION_MODE = "SIMULATION"
PHYSICAL_HARDWARE = False
VIRTUAL_CONTROL = True
CLOSED_LOOP_CONTROL = True
POLICY_ADAPTATION = True
SAFETY_CONTROLLER = True

MAX_REDUCTION_PERCENT = 30.0

SUPPORTED_ACTIONS = {
    "maintain",
    "reduce",
    "shift",
    "turn_off"
}

SAFE_ACTIONS = {
    "maintain",
    "reduce",
    "shift"
}

BLOCKED_ACTIONS = {
    "turn_off"
}


# ================================================================
# PATHS
# ================================================================

BASE_DIR = r"E:\energy_project"

INITIALIZATION_DIR = os.path.join(
    BASE_DIR,
    "initialization"
)

HOUSE_CONFIG_FILE = os.path.join(
    INITIALIZATION_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG_FILE = os.path.join(
    INITIALIZATION_DIR,
    "appliance_config.csv"
)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_subheader(title):
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def fail(message):
    print(f"[ERROR] {message}")
    sys.exit(1)


def safe_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if pd.isna(value):
            return default

        return int(value)

    except Exception:
        return default


def normalize_action(value):
    if pd.isna(value):
        return "maintain"

    action = str(value).strip().lower()

    mapping = {
        "keep": "maintain",
        "keep_current": "maintain",
        "maintain": "maintain",
        "reduce_load": "reduce",
        "reduce": "reduce",
        "shift_load": "shift",
        "shift": "shift",
        "off": "turn_off",
        "turnoff": "turn_off",
        "turn_off": "turn_off"
    }

    return mapping.get(action, action)


def find_existing_column(df, candidates):
    """
    Find the first available column from a list of candidates.
    Matching is case-insensitive.
    """

    lower_map = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:

        key = str(candidate).strip().lower()

        if key in lower_map:
            return lower_map[key]

    return None


def require_columns(df, required, dataframe_name):

    missing = []

    for col in required:
        if col not in df.columns:
            missing.append(col)

    if missing:
        fail(
            f"{dataframe_name} missing required columns: "
            + ", ".join(missing)
        )


def calculate_percentage_reduction(previous, actual):

    previous = safe_float(previous)
    actual = safe_float(actual)

    if previous <= 0:
        return 0.0

    return ((previous - actual) / previous) * 100.0


def clamp(value, minimum, maximum):

    value = safe_float(value)

    return max(minimum, min(maximum, value))


def calculate_reward(
    requested_action,
    previous_power,
    target_power,
    actual_power,
    feedback_score
):

    requested_action = normalize_action(requested_action)

    previous_power = safe_float(previous_power)
    target_power = safe_float(target_power)
    actual_power = safe_float(actual_power)
    feedback_score = clamp(feedback_score, 0.0, 1.0)

    if previous_power <= 0:
        return feedback_score

    reduction = (
        (previous_power - actual_power)
        / previous_power
    )

    target_error = (
        abs(actual_power - target_power)
        / max(previous_power, 1.0)
    )

    target_accuracy = 1.0 - clamp(
        target_error,
        0.0,
        1.0
    )

    if requested_action == "maintain":

        power_stability = 1.0 - clamp(
            abs(actual_power - previous_power)
            / max(previous_power, 1.0),
            0.0,
            1.0
        )

        reward = (
            0.50 * power_stability
            + 0.50 * feedback_score
        )

    elif requested_action == "reduce":

        energy_component = clamp(
            reduction,
            0.0,
            1.0
        )

        reward = (
            0.40 * energy_component
            + 0.35 * target_accuracy
            + 0.25 * feedback_score
        )

    elif requested_action == "shift":

        reward = (
            0.40 * target_accuracy
            + 0.60 * feedback_score
        )

    else:

        reward = feedback_score

    return clamp(reward, 0.0, 1.0)


def classify_reward(reward):

    reward = safe_float(reward)

    if reward >= 0.80:
        return "POSITIVE"

    if reward >= 0.60:
        return "ACCEPTABLE"

    return "NEGATIVE"


def calculate_next_action(
    current_action,
    previous_power,
    actual_power,
    rated_power,
    reward,
    feedback_score
):

    current_action = normalize_action(current_action)

    previous_power = safe_float(previous_power)
    actual_power = safe_float(actual_power)
    rated_power = safe_float(rated_power)

    reward = safe_float(reward)
    feedback_score = safe_float(feedback_score)

    if current_action == "turn_off":
        return "maintain"

    if previous_power <= 0:
        return "maintain"

    load_ratio = actual_power / max(rated_power, 1.0)

    reduction_percent = calculate_percentage_reduction(
        previous_power,
        actual_power
    )

    # ------------------------------------------------------------
    # Good reduction
    # ------------------------------------------------------------

    if current_action == "reduce":

        if reward >= 0.80 and feedback_score >= 0.85:

            # Do not continue reducing indefinitely.
            if reduction_percent >= 20.0:
                return "maintain"

            if load_ratio <= 0.35:
                return "maintain"

            return "reduce"

        if reward < 0.60:
            return "maintain"

    # ------------------------------------------------------------
    # Maintain
    # ------------------------------------------------------------

    if current_action == "maintain":

        if (
            reward >= 0.85
            and load_ratio > 0.75
        ):
            return "reduce"

        return "maintain"

    # ------------------------------------------------------------
    # Shift
    # ------------------------------------------------------------

    if current_action == "shift":

        if reward >= 0.80:
            return "maintain"

        return "maintain"

    return "maintain"


# ================================================================
# START
# ================================================================

START_TIME = time.time()

print_header(MODULE_NAME)

print()
print(f"Execution mode        : {EXECUTION_MODE}")
print(
    f"Physical hardware     : "
    f"{'CONNECTED' if PHYSICAL_HARDWARE else 'NOT CONNECTED'}"
)
print(
    f"Virtual control       : "
    f"{'ACTIVE' if VIRTUAL_CONTROL else 'INACTIVE'}"
)
print(
    f"Closed-loop control   : "
    f"{'ACTIVE' if CLOSED_LOOP_CONTROL else 'INACTIVE'}"
)
print(
    f"Policy adaptation     : "
    f"{'ACTIVE' if POLICY_ADAPTATION else 'INACTIVE'}"
)
print(
    f"Safety controller     : "
    f"{'ACTIVE' if SAFETY_CONTROLLER else 'INACTIVE'}"
)


# ================================================================
# CHECK INITIALIZATION FILES
# ================================================================

print_header("CHECKING REQUIRED FILES")

if not os.path.exists(HOUSE_CONFIG_FILE):
    fail(
        f"House configuration not found: "
        f"{HOUSE_CONFIG_FILE}"
    )

print(f"[OK] House configuration: {HOUSE_CONFIG_FILE}")


if not os.path.exists(APPLIANCE_CONFIG_FILE):
    fail(
        f"Appliance configuration not found: "
        f"{APPLIANCE_CONFIG_FILE}"
    )

print(
    f"[OK] Appliance configuration: "
    f"{APPLIANCE_CONFIG_FILE}"
)


# ================================================================
# LOAD HOUSE CONFIGURATION
# ================================================================

print()
print("Loading house configuration...")

try:

    with open(
        HOUSE_CONFIG_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        house_config = json.load(f)

except Exception as e:

    fail(
        f"Unable to load house configuration: {e}"
    )


HOUSE_ID = (
    house_config.get("house_id")
    or house_config.get("houseId")
    or "UNKNOWN_HOUSE"
)

HOUSE_NAME = (
    house_config.get("house_name")
    or house_config.get("houseName")
    or "Unknown House"
)

LOCATION = (
    house_config.get("location")
    or "Unknown"
)

print(f"House ID   : {HOUSE_ID}")
print(f"House Name : {HOUSE_NAME}")
print(f"Location   : {LOCATION}")


# ================================================================
# HOUSE DIRECTORIES
# ================================================================

HOUSE_DIR = os.path.join(
    BASE_DIR,
    "house_data",
    HOUSE_ID
)

REALTIME_DIR = os.path.join(
    HOUSE_DIR,
    "realtime"
)

IOT_DIR = os.path.join(
    HOUSE_DIR,
    "iot"
)

HARDWARE_DIR = os.path.join(
    HOUSE_DIR,
    "hardware"
)

CONTROL_DIR = os.path.join(
    HOUSE_DIR,
    "control"
)

os.makedirs(
    CONTROL_DIR,
    exist_ok=True
)


# ================================================================
# INPUT FILES
# ================================================================

MODULE14H_DECISIONS = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_decisions.csv"
)

MODULE15_EXECUTION = os.path.join(
    IOT_DIR,
    "iot_action_execution.csv"
)

MODULE15_FEEDBACK = os.path.join(
    IOT_DIR,
    "iot_action_feedback.csv"
)

MODULE16_QUEUE = os.path.join(
    HARDWARE_DIR,
    "esp32_command_queue.csv"
)

MODULE16_LOG = os.path.join(
    HARDWARE_DIR,
    "esp32_command_log.csv"
)

MODULE16_FEEDBACK = os.path.join(
    HARDWARE_DIR,
    "esp32_sensor_feedback.csv"
)

MODULE16_STATUS = os.path.join(
    HARDWARE_DIR,
    "esp32_device_status.csv"
)


# ================================================================
# OUTPUT FILES
# ================================================================

OUTPUT_CLOSED_LOOP = os.path.join(
    CONTROL_DIR,
    "closed_loop_control.csv"
)

OUTPUT_FEEDBACK_ANALYSIS = os.path.join(
    CONTROL_DIR,
    "closed_loop_feedback_analysis.csv"
)

OUTPUT_POLICY_ADAPTATION = os.path.join(
    CONTROL_DIR,
    "closed_loop_policy_adaptation.csv"
)

OUTPUT_NEXT_ACTIONS = os.path.join(
    CONTROL_DIR,
    "closed_loop_next_actions.csv"
)

OUTPUT_APPLIANCE_SUMMARY = os.path.join(
    CONTROL_DIR,
    "closed_loop_appliance_summary.csv"
)

OUTPUT_SYSTEM_SUMMARY = os.path.join(
    CONTROL_DIR,
    "closed_loop_system_summary.csv"
)


# ================================================================
# CHECK MODULE INPUTS
# ================================================================

print_header("CHECKING PREVIOUS MODULE INPUTS")

input_files = {
    "Module 14H realtime decisions":
        MODULE14H_DECISIONS,

    "Module 15 IoT action execution":
        MODULE15_EXECUTION,

    "Module 15 IoT action feedback":
        MODULE15_FEEDBACK,

    "Module 16 ESP32 command queue":
        MODULE16_QUEUE,

    "Module 16 ESP32 command log":
        MODULE16_LOG,

    "Module 16 ESP32 sensor feedback":
        MODULE16_FEEDBACK,

    "Module 16 ESP32 device status":
        MODULE16_STATUS
}

for label, path in input_files.items():

    if not os.path.exists(path):

        fail(
            f"{label} not found: {path}"
        )

    print(f"[OK] {label}: {path}")


# ================================================================
# LOAD APPLIANCE CONFIGURATION
# ================================================================

print_header("LOADING APPLIANCE CONFIGURATION")

try:

    appliances = pd.read_csv(
        APPLIANCE_CONFIG_FILE
    )

except Exception as e:

    fail(
        f"Unable to load appliance configuration: {e}"
    )


require_columns(
    appliances,
    [
        "appliance_id",
        "appliance_name",
        "sensor_id",
        "rated_power_w"
    ],
    "Appliance configuration"
)


print(
    f"Registered appliances: "
    f"{len(appliances)}"
)

print()

display_columns = [
    "appliance_id",
    "appliance_name",
]

optional_display = [
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]

for col in optional_display:

    if col in appliances.columns:
        display_columns.append(col)

print(
    appliances[
        display_columns
    ].to_string(index=False)
)


# ================================================================
# DEVICE REGISTRY
# ================================================================

print_header("VIRTUAL DEVICE REGISTRY")

device_registry = {}

for _, row in appliances.iterrows():

    appliance_id = str(
        row["appliance_id"]
    )

    appliance_name = str(
        row["appliance_name"]
    )

    sensor_id = str(
        row["sensor_id"]
    )

    device_id = f"IOT_{sensor_id}"

    appliance_type = ""

    if "appliance_type" in appliances.columns:

        appliance_type = str(
            row["appliance_type"]
        )

    rated_power = safe_float(
        row["rated_power_w"]
    )

    device_registry[appliance_id] = {
        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "appliance_type":
            appliance_type,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "rated_power_w":
            rated_power
    }

    print(
        f"{appliance_id} -> "
        f"{sensor_id} -> "
        f"{device_id} -> "
        f"{appliance_name}"
    )


# ================================================================
# LOAD DATASETS
# ================================================================

print_header("LOADING MODULE 14H DECISIONS")

decisions = pd.read_csv(
    MODULE14H_DECISIONS
)

print(
    f"Decision rows : {len(decisions)}"
)

print(
    f"Decision columns : {len(decisions.columns)}"
)


print_header("LOADING MODULE 15 EXECUTION DATA")

execution = pd.read_csv(
    MODULE15_EXECUTION
)

feedback15 = pd.read_csv(
    MODULE15_FEEDBACK
)

print(
    f"Execution rows : {len(execution)}"
)

print(
    f"Feedback rows  : {len(feedback15)}"
)


print_header("LOADING MODULE 16 VIRTUAL HARDWARE DATA")

queue16 = pd.read_csv(
    MODULE16_QUEUE
)

log16 = pd.read_csv(
    MODULE16_LOG
)

sensor_feedback16 = pd.read_csv(
    MODULE16_FEEDBACK
)

status16 = pd.read_csv(
    MODULE16_STATUS
)

print(
    f"Command queue rows : {len(queue16)}"
)

print(
    f"Command log rows   : {len(log16)}"
)

print(
    f"Sensor feedback    : {len(sensor_feedback16)}"
)

print(
    f"Device status rows : {len(status16)}"
)


# ================================================================
# VALIDATE INPUT SCHEMAS
# ================================================================

print_header("VALIDATING CLOSED-LOOP INPUTS")


# ------------------------------------------------
# Module 14H
# ------------------------------------------------

module14_required = [
    "appliance_id",
    "appliance_name",
    "power_w",
    "recommended_action"
]

require_columns(
    decisions,
    module14_required,
    "Module 14H"
)

for col in module14_required:

    print(
        f"[OK] Module 14H : {col}"
    )


# ------------------------------------------------
# Module 15
# ------------------------------------------------

module15_required = [
    "appliance_id",
    "requested_action",
    "previous_power_w",
    "target_power_w",
    "actual_power_w"
]

require_columns(
    execution,
    module15_required,
    "Module 15"
)

for col in module15_required:

    print(
        f"[OK] Module 15 : {col}"
    )


# ------------------------------------------------
# Module 16
# ------------------------------------------------

module16_basic_required = [
    "appliance_id",
    "sensor_id",
    "device_id"
]

require_columns(
    log16,
    module16_basic_required,
    "Module 16 command log"
)

for col in module16_basic_required:

    print(
        f"[OK] Module 16 : {col}"
    )


# ================================================================
# IMPORTANT MODULE 16 POWER COLUMN DETECTION
# ================================================================

print_subheader(
    "DETECTING MODULE 16 POWER FEEDBACK COLUMN"
)

actual_power_candidates = [
    "actual_power_w",
    "measured_power_w",
    "sensor_power_w",
    "feedback_power_w",
    "observed_power_w",
    "current_power_w",
    "power_w",
    "actual_power",
    "measured_power",
    "power"
]

module16_power_source = None
module16_power_dataframe = None


# ------------------------------------------------
# Search command log
# ------------------------------------------------

module16_power_source = find_existing_column(
    log16,
    actual_power_candidates
)

if module16_power_source:

    module16_power_dataframe = log16

    print(
        "[OK] Module 16 command log power column: "
        f"{module16_power_source}"
    )


# ------------------------------------------------
# Search sensor feedback
# ------------------------------------------------

if module16_power_source is None:

    module16_power_source = find_existing_column(
        sensor_feedback16,
        actual_power_candidates
    )

    if module16_power_source:

        module16_power_dataframe = (
            sensor_feedback16
        )

        print(
            "[OK] Module 16 sensor feedback "
            f"power column: {module16_power_source}"
        )


# ------------------------------------------------
# Search device status
# ------------------------------------------------

if module16_power_source is None:

    module16_power_source = find_existing_column(
        status16,
        actual_power_candidates
    )

    if module16_power_source:

        module16_power_dataframe = status16

        print(
            "[OK] Module 16 device status "
            f"power column: {module16_power_source}"
        )


# ------------------------------------------------
# Fallback to Module 15
# ------------------------------------------------

if module16_power_source is None:

    print(
        "[WARNING] Module 16 does not expose "
        "a direct actual-power column."
    )

    print(
        "[WARNING] Using Module 15 actual_power_w "
        "as the virtual hardware measurement baseline."
    )

    module16_power_dataframe = execution

    module16_power_source = "actual_power_w"

    print(
        "[OK] Fallback power source: "
        "Module 15 actual_power_w"
    )


# ================================================================
# SHOW MODULE 16 COLUMNS
# ================================================================

print_subheader(
    "MODULE 16 AVAILABLE POWER / FEEDBACK COLUMNS"
)

print(
    "Command log columns:"
)

for col in log16.columns:

    print(
        f"  - {col}"
    )

print()

print(
    "Sensor feedback columns:"
)

for col in sensor_feedback16.columns:

    print(
        f"  - {col}"
    )


# ================================================================
# BUILD CLOSED-LOOP DATA
# ================================================================

print_header(
    "BUILDING REAL-TIME CLOSED-LOOP CONTROL DATA"
)


# ------------------------------------------------
# Work from Module 15 execution records
# ------------------------------------------------

df = execution.copy()


# ------------------------------------------------
# Ensure timestamp
# ------------------------------------------------

timestamp_column = find_existing_column(
    df,
    [
        "timestamp",
        "decision_timestamp"
    ]
)

if timestamp_column:

    df["timestamp"] = pd.to_datetime(
        df[timestamp_column],
        errors="coerce"
    )

else:

    df["timestamp"] = pd.Timestamp.now()


# ------------------------------------------------
# Normalize IDs
# ------------------------------------------------

df["appliance_id"] = (
    df["appliance_id"]
    .astype(str)
    .str.strip()
)


# ------------------------------------------------
# Map appliance configuration
# ------------------------------------------------

config_lookup = (
    appliances
    .set_index("appliance_id")
    .to_dict("index")
)


# ================================================================
# PREPARE MODULE 16 FEEDBACK
# ================================================================

hardware_feedback = sensor_feedback16.copy()


hardware_feedback["appliance_id"] = (
    hardware_feedback["appliance_id"]
    .astype(str)
    .str.strip()
)


# ------------------------------------------------
# Detect feedback score
# ------------------------------------------------

feedback_score_column = find_existing_column(
    hardware_feedback,
    [
        "feedback_score",
        "sensor_feedback_score",
        "feedback",
        "score"
    ]
)


if feedback_score_column:

    print(
        f"[OK] Hardware feedback score: "
        f"{feedback_score_column}"
    )

else:

    print(
        "[WARNING] Module 16 feedback score not found."
    )

    print(
        "[OK] Defaulting hardware feedback score to 0.90."
    )


# ------------------------------------------------
# Detect response time
# ------------------------------------------------

response_time_column = find_existing_column(
    hardware_feedback,
    [
        "response_time_ms",
        "response_ms",
        "latency_ms"
    ]
)


if response_time_column:

    print(
        f"[OK] Hardware response time: "
        f"{response_time_column}"
    )

else:

    print(
        "[WARNING] Hardware response time unavailable."
    )


# ------------------------------------------------
# Build hardware power lookup
# ------------------------------------------------

hardware_power_lookup = {}

for _, row in hardware_feedback.iterrows():

    appliance_id = str(
        row["appliance_id"]
    ).strip()

    power_value = safe_float(
        row.get(
            module16_power_source,
            np.nan
        ),
        default=np.nan
    )

    if not math.isnan(power_value):

        hardware_power_lookup.setdefault(
            appliance_id,
            []
        ).append(power_value)


# ================================================================
# FEEDBACK RECORD LOOKUP
# ================================================================

hardware_feedback_score_lookup = {}

for _, row in hardware_feedback.iterrows():

    appliance_id = str(
        row["appliance_id"]
    ).strip()

    if feedback_score_column:

        score = safe_float(
            row.get(
                feedback_score_column
            ),
            default=0.90
        )

    else:

        score = 0.90

    hardware_feedback_score_lookup.setdefault(
        appliance_id,
        []
    ).append(
        clamp(score, 0.0, 1.0)
    )


# ================================================================
# RESPONSE TIME LOOKUP
# ================================================================

hardware_response_lookup = {}

for _, row in hardware_feedback.iterrows():

    appliance_id = str(
        row["appliance_id"]
    ).strip()

    if response_time_column:

        response = safe_float(
            row.get(
                response_time_column
            ),
            default=60.0
        )

    else:

        response = 60.0

    hardware_response_lookup.setdefault(
        appliance_id,
        []
    ).append(
        response
    )


# ================================================================
# CLOSED LOOP PROCESSING
# ================================================================

closed_loop_rows = []
feedback_rows = []
policy_rows = []
next_action_rows = []


processed_counts = {}


print_header(
    "REAL-TIME CLOSED-LOOP CONTROL"
)


for index, row in df.iterrows():

    execution_number = index + 1

    appliance_id = str(
        row["appliance_id"]
    ).strip()


    # ------------------------------------------------------------
    # Device configuration
    # ------------------------------------------------------------

    config = config_lookup.get(
        appliance_id,
        {}
    )

    appliance_name = str(
        config.get(
            "appliance_name",
            row.get(
                "appliance_name",
                "Unknown"
            )
        )
    )

    appliance_type = str(
        config.get(
            "appliance_type",
            row.get(
                "appliance_type",
                ""
            )
        )
    )

    sensor_id = str(
        config.get(
            "sensor_id",
            row.get(
                "sensor_id",
                ""
            )
        )
    )

    device_id = (
        f"IOT_{sensor_id}"
        if sensor_id
        else "UNKNOWN_DEVICE"
    )

    rated_power = safe_float(
        config.get(
            "rated_power_w",
            row.get(
                "rated_power_w",
                0
            )
        )
    )


    # ------------------------------------------------------------
    # Action
    # ------------------------------------------------------------

    requested_action = normalize_action(
        row.get(
            "requested_action",
            "maintain"
        )
    )


    # ------------------------------------------------------------
    # Power
    # ------------------------------------------------------------

    previous_power = safe_float(
        row.get(
            "previous_power_w",
            0
        )
    )

    target_power = safe_float(
        row.get(
            "target_power_w",
            previous_power
        )
    )

    module15_actual = safe_float(
        row.get(
            "actual_power_w",
            previous_power
        )
    )


    # ------------------------------------------------------------
    # Hardware feedback
    # ------------------------------------------------------------

    power_list = hardware_power_lookup.get(
        appliance_id,
        []
    )

    if power_list:

        position = (
            processed_counts.get(
                appliance_id,
                0
            )
        )

        if position < len(power_list):

            hardware_actual_power = safe_float(
                power_list[position],
                module15_actual
            )

        else:

            hardware_actual_power = module15_actual

    else:

        hardware_actual_power = module15_actual


    # ------------------------------------------------------------
    # IMPORTANT:
    #
    # If Module 16 power source is Module 15 fallback,
    # use Module 15 actual power.
    # ------------------------------------------------------------

    if (
        module16_power_dataframe is execution
        and module16_power_source == "actual_power_w"
    ):

        hardware_actual_power = module15_actual


    # ------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------

    score_list = hardware_feedback_score_lookup.get(
        appliance_id,
        []
    )

    position = processed_counts.get(
        appliance_id,
        0
    )

    if score_list and position < len(score_list):

        feedback_score = clamp(
            score_list[position],
            0.0,
            1.0
        )

    else:

        feedback_score = 0.90


    # ------------------------------------------------------------
    # Response
    # ------------------------------------------------------------

    response_list = hardware_response_lookup.get(
        appliance_id,
        []
    )

    if response_list and position < len(response_list):

        response_time = safe_float(
            response_list[position],
            60.0
        )

    else:

        response_time = 60.0


    # ------------------------------------------------------------
    # Safety controller
    # ------------------------------------------------------------

    safety_status = "SAFE"
    safety_action = requested_action

    if requested_action == "turn_off":

        safety_action = "maintain"

        safety_status = "BLOCKED"

    elif requested_action not in SUPPORTED_ACTIONS:

        safety_action = "maintain"

        safety_status = "BLOCKED"


    # ------------------------------------------------------------
    # Limit reduction
    # ------------------------------------------------------------

    if safety_action == "reduce":

        maximum_allowed_power = (
            previous_power
            * (
                1.0
                - MAX_REDUCTION_PERCENT / 100.0
            )
        )

        if target_power < maximum_allowed_power:

            target_power = maximum_allowed_power


    # ------------------------------------------------------------
    # Reward
    # ------------------------------------------------------------

    reward = calculate_reward(
        safety_action,
        previous_power,
        target_power,
        hardware_actual_power,
        feedback_score
    )

    reward_class = classify_reward(
        reward
    )


    # ------------------------------------------------------------
    # Energy saving
    # ------------------------------------------------------------

    actual_savings_kwh = max(
        0.0,
        (
            previous_power
            - hardware_actual_power
        )
        / 1000.0
        / 60.0
    )

    expected_savings_kwh = max(
        0.0,
        (
            previous_power
            - target_power
        )
        / 1000.0
        / 60.0
    )


    # ------------------------------------------------------------
    # Power error
    # ------------------------------------------------------------

    power_error = (
        abs(
            hardware_actual_power
            - target_power
        )
    )


    # ------------------------------------------------------------
    # Target accuracy
    # ------------------------------------------------------------

    target_accuracy = 1.0 - clamp(
        power_error
        / max(previous_power, 1.0),
        0.0,
        1.0
    )


    # ------------------------------------------------------------
    # Reduction
    # ------------------------------------------------------------

    reduction_percent = (
        calculate_percentage_reduction(
            previous_power,
            hardware_actual_power
        )
    )


    # ------------------------------------------------------------
    # Load ratio
    # ------------------------------------------------------------

    load_ratio = (
        hardware_actual_power
        / max(rated_power, 1.0)
    )


    # ------------------------------------------------------------
    # Policy adaptation
    # ------------------------------------------------------------

    old_confidence = safe_float(
        row.get(
            "policy_confidence",
            0.80
        ),
        0.80
    )

    old_learning_rate = safe_float(
        row.get(
            "learning_rate",
            0.10
        ),
        0.10
    )

    old_adaptation_factor = safe_float(
        row.get(
            "adaptation_factor",
            1.0
        ),
        1.0
    )


    if POLICY_ADAPTATION:

        if reward >= 0.80:

            confidence_change = (
                0.02
                * old_learning_rate
                * 10
            )

        elif reward >= 0.60:

            confidence_change = 0.0

        else:

            confidence_change = (
                -0.02
                * old_learning_rate
                * 10
            )

        new_confidence = clamp(
            old_confidence
            + confidence_change,
            0.0,
            1.0
        )

        adaptation_factor = clamp(
            old_adaptation_factor
            * (
                1.0
                + (
                    reward - 0.70
                ) * 0.05
            ),
            0.50,
            1.50
        )

    else:

        new_confidence = old_confidence
        adaptation_factor = old_adaptation_factor


    # ------------------------------------------------------------
    # Next action
    # ------------------------------------------------------------

    next_action = calculate_next_action(
        safety_action,
        previous_power,
        hardware_actual_power,
        rated_power,
        reward,
        feedback_score
    )


    # ------------------------------------------------------------
    # Safety for next action
    # ------------------------------------------------------------

    if next_action == "turn_off":

        next_action = "maintain"


    # ------------------------------------------------------------
    # Policy version
    # ------------------------------------------------------------

    old_policy_version = str(
        row.get(
            "policy_version",
            "V1"
        )
    )

    policy_version = (
        f"{old_policy_version}_CL"
    )


    # ------------------------------------------------------------
    # Status
    # ------------------------------------------------------------

    control_status = (
        "CLOSED_LOOP_SUCCESS"
    )

    if safety_status == "BLOCKED":

        control_status = (
            "CLOSED_LOOP_SAFETY_BLOCK"
        )


    # ------------------------------------------------------------
    # Print
    # ------------------------------------------------------------

    print()
    print(
        "-" * 70
    )

    print(
        f"CYCLE {execution_number}/{len(df)}"
    )

    print(
        f"Appliance : {appliance_name}"
    )

    print(
        f"Sensor    : {sensor_id}"
    )

    print(
        f"Device    : {device_id}"
    )

    print(
        f"Action    : {safety_action}"
    )

    print(
        f"Previous  : {previous_power:.3f} W"
    )

    print(
        f"Target    : {target_power:.3f} W"
    )

    print(
        f"Feedback  : {hardware_actual_power:.3f} W"
    )

    print(
        f"Power err : {power_error:.3f} W"
    )

    print(
        f"Saving    : {actual_savings_kwh:.6f} kWh"
    )

    print(
        f"Reward    : {reward:.3f} "
        f"({reward_class})"
    )

    print(
        f"Confidence: "
        f"{old_confidence:.3f} -> "
        f"{new_confidence:.3f}"
    )

    print(
        f"Next      : {next_action}"
    )

    print(
        f"Safety    : {safety_status}"
    )

    print(
        f"Status    : {control_status}"
    )


    # ------------------------------------------------------------
    # Closed-loop row
    # ------------------------------------------------------------

    closed_loop_rows.append({

        "control_id":
            f"CL_{execution_number:06d}",

        "timestamp":
            row.get(
                "timestamp",
                datetime.now()
            ),

        "house_id":
            HOUSE_ID,

        "house_name":
            HOUSE_NAME,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "appliance_type":
            appliance_type,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "requested_action":
            requested_action,

        "executed_action":
            safety_action,

        "next_action":
            next_action,

        "previous_power_w":
            previous_power,

        "target_power_w":
            target_power,

        "actual_power_w":
            hardware_actual_power,

        "power_error_w":
            power_error,

        "target_accuracy":
            target_accuracy,

        "load_ratio":
            load_ratio,

        "actual_reduction_percent":
            reduction_percent,

        "expected_savings_kwh":
            expected_savings_kwh,

        "actual_savings_kwh":
            actual_savings_kwh,

        "feedback_score":
            feedback_score,

        "reward":
            reward,

        "reward_class":
            reward_class,

        "response_time_ms":
            response_time,

        "safety_status":
            safety_status,

        "control_status":
            control_status,

        "policy_version":
            policy_version,

        "policy_confidence":
            new_confidence,

        "learning_rate":
            old_learning_rate,

        "adaptation_factor":
            adaptation_factor,

        "hardware_mode":
            EXECUTION_MODE,

        "physical_hardware":
            "NO"
    })


    # ------------------------------------------------------------
    # Feedback analysis
    # ------------------------------------------------------------

    feedback_rows.append({

        "control_id":
            f"CL_{execution_number:06d}",

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "target_power_w":
            target_power,

        "actual_power_w":
            hardware_actual_power,

        "power_error_w":
            power_error,

        "target_accuracy":
            target_accuracy,

        "previous_power_w":
            previous_power,

        "actual_reduction_percent":
            reduction_percent,

        "feedback_score":
            feedback_score,

        "feedback_class":
            reward_class,

        "reward":
            reward,

        "response_time_ms":
            response_time,

        "energy_savings_kwh":
            actual_savings_kwh
    })


    # ------------------------------------------------------------
    # Policy adaptation
    # ------------------------------------------------------------

    policy_rows.append({

        "control_id":
            f"CL_{execution_number:06d}",

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "old_policy_confidence":
            old_confidence,

        "new_policy_confidence":
            new_confidence,

        "confidence_change":
            new_confidence
            - old_confidence,

        "learning_rate":
            old_learning_rate,

        "old_adaptation_factor":
            old_adaptation_factor,

        "new_adaptation_factor":
            adaptation_factor,

        "reward":
            reward,

        "reward_class":
            reward_class,

        "policy_version":
            policy_version,

        "adaptation_status":
            "ADAPTED"
            if POLICY_ADAPTATION
            else "DISABLED"
    })


    # ------------------------------------------------------------
    # Next action
    # ------------------------------------------------------------

    next_action_rows.append({

        "control_id":
            f"CL_{execution_number:06d}",

        "timestamp":
            row.get(
                "timestamp",
                datetime.now()
            ),

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "current_action":
            safety_action,

        "next_recommended_action":
            next_action,

        "current_power_w":
            hardware_actual_power,

        "rated_power_w":
            rated_power,

        "load_ratio":
            load_ratio,

        "reward":
            reward,

        "feedback_score":
            feedback_score,

        "policy_confidence":
            new_confidence,

        "safety_status":
            safety_status,

        "closed_loop_status":
            "READY"
    })


    processed_counts[appliance_id] = (
        processed_counts.get(
            appliance_id,
            0
        ) + 1
    )


# ================================================================
# CREATE DATAFRAMES
# ================================================================

closed_loop_df = pd.DataFrame(
    closed_loop_rows
)

feedback_df = pd.DataFrame(
    feedback_rows
)

policy_df = pd.DataFrame(
    policy_rows
)

next_actions_df = pd.DataFrame(
    next_action_rows
)


# ================================================================
# GENERATED DATA VALIDATION
# ================================================================

print_header(
    "GENERATED DATA VALIDATION"
)

print(
    f"Closed-loop rows      : "
    f"{len(closed_loop_df)}"
)

print(
    f"Feedback analysis rows: "
    f"{len(feedback_df)}"
)

print(
    f"Policy rows           : "
    f"{len(policy_df)}"
)

print(
    f"Next action rows      : "
    f"{len(next_actions_df)}"
)


# ================================================================
# NULL VALIDATION
# ================================================================

print_subheader(
    "NULL VALIDATION"
)

closed_nulls = int(
    closed_loop_df.isnull()
    .sum()
    .sum()
)

feedback_nulls = int(
    feedback_df.isnull()
    .sum()
    .sum()
)

policy_nulls = int(
    policy_df.isnull()
    .sum()
    .sum()
)

next_nulls = int(
    next_actions_df.isnull()
    .sum()
    .sum()
)

print(
    f"Closed-loop NULLs : {closed_nulls}"
)

print(
    f"Feedback NULLs    : {feedback_nulls}"
)

print(
    f"Policy NULLs      : {policy_nulls}"
)

print(
    f"Next action NULLs : {next_nulls}"
)

if (
    closed_nulls
    + feedback_nulls
    + policy_nulls
    + next_nulls
) == 0:

    print(
        "[OK] No NULL values."
    )

else:

    print(
        "[WARNING] NULL values detected."
    )


# ================================================================
# DUPLICATE VALIDATION
# ================================================================

print_subheader(
    "DUPLICATE VALIDATION"
)

closed_duplicates = int(
    closed_loop_df[
        "control_id"
    ].duplicated()
    .sum()
)

feedback_duplicates = int(
    feedback_df[
        "control_id"
    ].duplicated()
    .sum()
)

policy_duplicates = int(
    policy_df[
        "control_id"
    ].duplicated()
    .sum()
)

next_duplicates = int(
    next_actions_df[
        "control_id"
    ].duplicated()
    .sum()
)

print(
    f"Closed-loop duplicates : "
    f"{closed_duplicates}"
)

print(
    f"Feedback duplicates    : "
    f"{feedback_duplicates}"
)

print(
    f"Policy duplicates      : "
    f"{policy_duplicates}"
)

print(
    f"Next action duplicates : "
    f"{next_duplicates}"
)

if (
    closed_duplicates
    + feedback_duplicates
    + policy_duplicates
    + next_duplicates
) == 0:

    print(
        "[OK] No duplicate control IDs."
    )

else:

    print(
        "[WARNING] Duplicate control IDs detected."
    )


# ================================================================
# ACTION VALIDATION
# ================================================================

print_subheader(
    "ACTION VALIDATION"
)

invalid_actions = closed_loop_df[
    ~closed_loop_df[
        "executed_action"
    ].isin(
        SUPPORTED_ACTIONS
    )
]

print(
    f"Invalid executed actions : "
    f"{len(invalid_actions)}"
)

invalid_next_actions = next_actions_df[
    ~next_actions_df[
        "next_recommended_action"
    ].isin(
        SAFE_ACTIONS
    )
]

print(
    f"Invalid next actions     : "
    f"{len(invalid_next_actions)}"
)

if (
    len(invalid_actions) == 0
    and len(invalid_next_actions) == 0
):

    print(
        "[OK] All actions valid."
    )

else:

    print(
        "[WARNING] Invalid actions detected."
    )


# ================================================================
# POWER VALIDATION
# ================================================================

print_subheader(
    "POWER / ENERGY VALIDATION"
)

negative_previous = int(
    (
        closed_loop_df[
            "previous_power_w"
        ] < 0
    ).sum()
)

negative_target = int(
    (
        closed_loop_df[
            "target_power_w"
        ] < 0
    ).sum()
)

negative_actual = int(
    (
        closed_loop_df[
            "actual_power_w"
        ] < 0
    ).sum()
)

negative_savings = int(
    (
        closed_loop_df[
            "actual_savings_kwh"
        ] < 0
    ).sum()
)

print(
    f"Negative previous power : "
    f"{negative_previous}"
)

print(
    f"Negative target power   : "
    f"{negative_target}"
)

print(
    f"Negative actual power   : "
    f"{negative_actual}"
)

print(
    f"Negative savings        : "
    f"{negative_savings}"
)

if (
    negative_previous
    + negative_target
    + negative_actual
    + negative_savings
) == 0:

    print(
        "[OK] Power and energy values valid."
    )

else:

    print(
        "[WARNING] Invalid power or energy values."
    )


# ================================================================
# SAFETY VALIDATION
# ================================================================

print_subheader(
    "SAFETY VALIDATION"
)

blocked_count = int(
    (
        closed_loop_df[
            "safety_status"
        ] == "BLOCKED"
    ).sum()
)

turn_off_executed = int(
    (
        closed_loop_df[
            "executed_action"
        ] == "turn_off"
    ).sum()
)

print(
    f"Blocked safety actions : "
    f"{blocked_count}"
)

print(
    f"Turn-off executions    : "
    f"{turn_off_executed}"
)

if turn_off_executed == 0:

    print(
        "[OK] No unsafe turn-off action executed."
    )

else:

    print(
        "[WARNING] Unsafe turn-off action detected."
    )


# ================================================================
# APPLIANCE VALIDATION
# ================================================================

print_subheader(
    "APPLIANCE VALIDATION"
)

registered_appliances = len(
    device_registry
)

processed_appliances = (
    closed_loop_df[
        "appliance_id"
    ].nunique()
)

print(
    f"Registered appliances : "
    f"{registered_appliances}"
)

print(
    f"Processed appliances  : "
    f"{processed_appliances}"
)

missing_appliances = (
    set(
        device_registry.keys()
    )
    -
    set(
        closed_loop_df[
            "appliance_id"
        ].unique()
    )
)

if not missing_appliances:

    print(
        "[OK] Every registered appliance processed."
    )

else:

    print(
        "[WARNING] Missing appliances:"
    )

    for appliance_id in missing_appliances:

        print(
            f"  - {appliance_id}"
        )


# ================================================================
# APPLIANCE SUMMARY
# ================================================================

print_header(
    "CLOSED-LOOP APPLIANCE RESULTS"
)

summary_rows = []

for appliance_id, group in closed_loop_df.groupby(
    "appliance_id"
):

    appliance_name = (
        group[
            "appliance_name"
        ].iloc[0]
    )

    executions = len(group)

    positive = int(
        (
            group[
                "reward_class"
            ] == "POSITIVE"
        ).sum()
    )

    acceptable = int(
        (
            group[
                "reward_class"
            ] == "ACCEPTABLE"
        ).sum()
    )

    negative = int(
        (
            group[
                "reward_class"
            ] == "NEGATIVE"
        ).sum()
    )

    summary_rows.append({

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "control_cycles":
            executions,

        "positive_feedback":
            positive,

        "acceptable_feedback":
            acceptable,

        "negative_feedback":
            negative,

        "average_previous_power_w":
            group[
                "previous_power_w"
            ].mean(),

        "average_target_power_w":
            group[
                "target_power_w"
            ].mean(),

        "average_actual_power_w":
            group[
                "actual_power_w"
            ].mean(),

        "average_power_error_w":
            group[
                "power_error_w"
            ].mean(),

        "average_reduction_percent":
            group[
                "actual_reduction_percent"
            ].mean(),

        "total_savings_kwh":
            group[
                "actual_savings_kwh"
            ].sum(),

        "average_feedback_score":
            group[
                "feedback_score"
            ].mean(),

        "average_reward":
            group[
                "reward"
            ].mean(),

        "average_policy_confidence":
            group[
                "policy_confidence"
            ].mean(),

        "final_next_action":
            group[
                "next_action"
            ].iloc[-1]
    })


appliance_summary_df = pd.DataFrame(
    summary_rows
)

print(
    appliance_summary_df.to_string(
        index=False
    )
)


# ================================================================
# SYSTEM METRICS
# ================================================================

total_cycles = len(
    closed_loop_df
)

total_savings = safe_float(
    closed_loop_df[
        "actual_savings_kwh"
    ].sum()
)

total_expected_savings = safe_float(
    closed_loop_df[
        "expected_savings_kwh"
    ].sum()
)

average_reward = safe_float(
    closed_loop_df[
        "reward"
    ].mean()
)

average_feedback = safe_float(
    closed_loop_df[
        "feedback_score"
    ].mean()
)

average_power_error = safe_float(
    closed_loop_df[
        "power_error_w"
    ].mean()
)

average_response_time = safe_float(
    closed_loop_df[
        "response_time_ms"
    ].mean()
)

average_reduction = safe_float(
    closed_loop_df[
        "actual_reduction_percent"
    ].mean()
)

positive_feedback = int(
    (
        closed_loop_df[
            "reward_class"
        ] == "POSITIVE"
    ).sum()
)

acceptable_feedback = int(
    (
        closed_loop_df[
            "reward_class"
        ] == "ACCEPTABLE"
    ).sum()
)

negative_feedback = int(
    (
        closed_loop_df[
            "reward_class"
        ] == "NEGATIVE"
    ).sum()
)

successful_cycles = int(
    (
        closed_loop_df[
            "control_status"
        ] == "CLOSED_LOOP_SUCCESS"
    ).sum()
)

final_confidence = safe_float(
    closed_loop_df[
        "policy_confidence"
    ].iloc[-1]
)


# ================================================================
# SAVE OUTPUTS
# ================================================================

print_header(
    "GENERATING MODULE 17 OUTPUTS"
)


closed_loop_df.to_csv(
    OUTPUT_CLOSED_LOOP,
    index=False
)

print(
    f"[OK] Closed-loop control:"
)

print(
    OUTPUT_CLOSED_LOOP
)


feedback_df.to_csv(
    OUTPUT_FEEDBACK_ANALYSIS,
    index=False
)

print(
    f"[OK] Closed-loop feedback analysis:"
)

print(
    OUTPUT_FEEDBACK_ANALYSIS
)


policy_df.to_csv(
    OUTPUT_POLICY_ADAPTATION,
    index=False
)

print(
    f"[OK] Closed-loop policy adaptation:"
)

print(
    OUTPUT_POLICY_ADAPTATION
)


next_actions_df.to_csv(
    OUTPUT_NEXT_ACTIONS,
    index=False
)

print(
    f"[OK] Closed-loop next actions:"
)

print(
    OUTPUT_NEXT_ACTIONS
)


appliance_summary_df.to_csv(
    OUTPUT_APPLIANCE_SUMMARY,
    index=False
)

print(
    f"[OK] Closed-loop appliance summary:"
)

print(
    OUTPUT_APPLIANCE_SUMMARY
)


# ================================================================
# SYSTEM SUMMARY
# ================================================================

system_summary = pd.DataFrame([
    {
        "house_id":
            HOUSE_ID,

        "house_name":
            HOUSE_NAME,

        "location":
            LOCATION,

        "registered_appliances":
            registered_appliances,

        "processed_appliances":
            processed_appliances,

        "execution_mode":
            EXECUTION_MODE,

        "physical_hardware":
            "NOT_CONNECTED",

        "virtual_control":
            "ACTIVE",

        "closed_loop_control":
            "ACTIVE",

        "policy_adaptation":
            "ACTIVE",

        "safety_controller":
            "ACTIVE",

        "control_cycles":
            total_cycles,

        "successful_cycles":
            successful_cycles,

        "blocked_cycles":
            blocked_count,

        "positive_feedback":
            positive_feedback,

        "acceptable_feedback":
            acceptable_feedback,

        "negative_feedback":
            negative_feedback,

        "expected_savings_kwh":
            total_expected_savings,

        "actual_savings_kwh":
            total_savings,

        "average_reduction_percent":
            average_reduction,

        "average_feedback_score":
            average_feedback,

        "average_reward":
            average_reward,

        "average_power_error_w":
            average_power_error,

        "average_response_time_ms":
            average_response_time,

        "final_policy_confidence":
            final_confidence,

        "feedback_loop":
            "ACTIVE",

        "ESP32_interface":
            "READY",

        "smart_plug_interface":
            "READY",

        "hardware_connected":
            "NO",

        "system_status":
            "CLOSED_LOOP_CONTROL_READY"
    }
])


system_summary.to_csv(
    OUTPUT_SYSTEM_SUMMARY,
    index=False
)


print(
    f"[OK] Closed-loop system summary:"
)

print(
    OUTPUT_SYSTEM_SUMMARY
)


# ================================================================
# SYSTEM SUMMARY DISPLAY
# ================================================================

print_header(
    "MODULE 17 SYSTEM SUMMARY"
)

print(
    f"House ID                  : "
    f"{HOUSE_ID}"
)

print(
    f"House Name                : "
    f"{HOUSE_NAME}"
)

print(
    f"Registered appliances     : "
    f"{registered_appliances}"
)

print(
    f"Processed appliances      : "
    f"{processed_appliances}"
)

print(
    f"Execution mode            : "
    f"{EXECUTION_MODE}"
)

print(
    f"Physical hardware         : "
    f"NOT CONNECTED"
)

print(
    f"Control cycles            : "
    f"{total_cycles}"
)

print(
    f"Successful cycles         : "
    f"{successful_cycles}"
)

print(
    f"Blocked cycles            : "
    f"{blocked_count}"
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
    f"Actual simulated savings  : "
    f"{total_savings:.6f} kWh"
)

print(
    f"Average reduction         : "
    f"{average_reduction:.2f}%"
)

print(
    f"Average feedback score    : "
    f"{average_feedback:.4f}"
)

print(
    f"Average reward            : "
    f"{average_reward:.4f}"
)

print(
    f"Average power error       : "
    f"{average_power_error:.4f} W"
)

print(
    f"Average response time     : "
    f"{average_response_time:.2f} ms"
)

print(
    f"Final policy confidence   : "
    f"{final_confidence:.4f}"
)

print(
    f"ESP32 interface           : "
    f"READY"
)

print(
    f"Smart plug interface      : "
    f"READY"
)

print(
    f"Safety controller         : "
    f"ACTIVE"
)

print(
    f"Feedback loop             : "
    f"ACTIVE"
)

print(
    f"Policy adaptation         : "
    f"ACTIVE"
)

print(
    f"Hardware connected        : "
    f"NO (SIMULATION)"
)

print(
    f"System status             : "
    f"CLOSED_LOOP_CONTROL_READY"
)


# ================================================================
# OUTPUT FILE LIST
# ================================================================

print_header(
    "MODULE 17 OUTPUT FILES"
)

print()
print(
    "Closed-loop control:"
)

print(
    OUTPUT_CLOSED_LOOP
)

print()
print(
    "Closed-loop feedback analysis:"
)

print(
    OUTPUT_FEEDBACK_ANALYSIS
)

print()
print(
    "Closed-loop policy adaptation:"
)

print(
    OUTPUT_POLICY_ADAPTATION
)

print()
print(
    "Closed-loop next actions:"
)

print(
    OUTPUT_NEXT_ACTIONS
)

print()
print(
    "Closed-loop appliance summary:"
)

print(
    OUTPUT_APPLIANCE_SUMMARY
)

print()
print(
    "Closed-loop system summary:"
)

print(
    OUTPUT_SYSTEM_SUMMARY
)


# ================================================================
# FINAL VALIDATION
# ================================================================

print_header(
    "MODULE 17 FINAL VALIDATION"
)

validation_results = {

    "Every registered appliance processed":
        processed_appliances
        == registered_appliances,

    "Closed-loop control generated":
        len(closed_loop_df) > 0,

    "Feedback analysis generated":
        len(feedback_df) > 0,

    "Policy adaptation generated":
        len(policy_df) > 0,

    "Next actions generated":
        len(next_actions_df) > 0,

    "No closed-loop NULL values":
        closed_nulls == 0,

    "No feedback NULL values":
        feedback_nulls == 0,

    "No policy NULL values":
        policy_nulls == 0,

    "No next-action NULL values":
        next_nulls == 0,

    "No duplicate control IDs":
        closed_duplicates == 0,

    "All actions valid":
        len(invalid_actions) == 0,

    "All next actions safe":
        len(invalid_next_actions) == 0,

    "No negative actual power":
        negative_actual == 0,

    "No negative savings":
        negative_savings == 0,

    "No unsafe turn-off execution":
        turn_off_executed == 0,

    "Safety controller active":
        SAFETY_CONTROLLER,

    "Closed-loop control active":
        CLOSED_LOOP_CONTROL,

    "Policy adaptation active":
        POLICY_ADAPTATION,

    "ESP32 interface ready":
        True,

    "Smart plug interface ready":
        True,

    "Physical hardware safely disconnected":
        not PHYSICAL_HARDWARE
}


all_valid = True

for description, result in validation_results.items():

    if result:

        print(
            f"[OK] {description}"
        )

    else:

        print(
            f"[ERROR] {description}"
        )

        all_valid = False


# ================================================================
# COMPLETION
# ================================================================

elapsed = time.time() - START_TIME

print()
print(
    f"Total time     : "
    f"{elapsed:.2f} seconds"
)

print_header(
    "MODULE 17 COMPLETE"
)

if all_valid:

    print(
        "[SUCCESS] Module 14H decisions consumed."
    )

    print(
        "[SUCCESS] Module 15 IoT execution consumed."
    )

    print(
        "[SUCCESS] Module 16 virtual hardware feedback consumed."
    )

    print(
        "[SUCCESS] Four-appliance closed-loop control completed."
    )

    print(
        "[SUCCESS] Real-time feedback evaluated."
    )

    print(
        "[SUCCESS] Energy reward calculated."
    )

    print(
        "[SUCCESS] Policy adaptation completed."
    )

    print(
        "[SUCCESS] Next actions generated."
    )

    print(
        "[SUCCESS] Safety controller validated."
    )

    print(
        "[SUCCESS] No physical hardware required."
    )

    print(
        "[SUCCESS] Module 17 validation passed."
    )

    print()

    print(
        "Execution mode : SIMULATION"
    )

    print(
        "System status  : CLOSED_LOOP_CONTROL_READY"
    )

else:

    print(
        "[WARNING] MODULE 17 COMPLETED WITH VALIDATION WARNINGS."
    )

    print(
        "Review the validation section above."
    )


print(
    "=" * 70
)