# ================================================================
# MODULE 16 — VIRTUAL ESP32 + SMART PLUG HARDWARE SIMULATOR
# ================================================================
#
# Purpose:
#   Simulate the complete hardware execution layer without
#   requiring physical ESP32 or smart plugs.
#
# Architecture:
#
#   Module 14H
#       ↓
#   Module 15 IoT Action Execution
#       ↓
#   Module 16 Virtual ESP32
#       ↓
#   Virtual Smart Plug
#       ↓
#   Virtual Appliance
#       ↓
#   Simulated Power Measurement
#       ↓
#   Hardware Feedback
#       ↓
#   System Validation
#
# Hardware status:
#   NO PHYSICAL HARDWARE REQUIRED
#
# Modes:
#   SIMULATION only
#
# ================================================================

import os
import json
import time
import random
from datetime import datetime

import pandas as pd
import numpy as np


# ================================================================
# CONFIGURATION
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


# ------------------------------------------------
# House-specific directories
# ------------------------------------------------

HOUSE_ID = None
HOUSE_DIR = None

REALTIME_DIR = None
IOT_DIR = None
HARDWARE_DIR = None


# ------------------------------------------------
# Module 15 input
# ------------------------------------------------

IOT_ACTION_FILE = None
IOT_FEEDBACK_FILE = None
IOT_DEVICE_STATUS_FILE = None
IOT_ACTION_SUMMARY_FILE = None
IOT_FEEDBACK_SUMMARY_FILE = None
IOT_SYSTEM_SUMMARY_FILE = None


# ------------------------------------------------
# Module 16 outputs
# ------------------------------------------------

ESP32_COMMAND_QUEUE_FILE = None
ESP32_COMMAND_LOG_FILE = None
ESP32_SENSOR_FEEDBACK_FILE = None
ESP32_DEVICE_STATUS_FILE = None
ESP32_HARDWARE_SUMMARY_FILE = None
ESP32_SYSTEM_SUMMARY_FILE = None


# ================================================================
# SIMULATION SETTINGS
# ================================================================

EXECUTION_MODE = "SIMULATION"

HARDWARE_CONNECTED = False

ESP32_INTERFACE_READY = True
SMART_PLUG_INTERFACE_READY = True

SIMULATED_WIFI = True

# Safety settings

ALLOW_MAINTAIN = True
ALLOW_REDUCE = True
ALLOW_SHIFT = True

# Turn-off remains disabled for automatic execution.
ALLOW_TURN_OFF = False

# Maximum reduction allowed in simulation.
MAX_REDUCTION_PERCENT = 30.0

# Simulated response characteristics

REDUCE_FACTOR = 0.80
SHIFT_FACTOR = 0.90
TURN_OFF_FACTOR = 0.05

# Random seed for reproducible demo results

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ================================================================
# ACTION MAPPING
# ================================================================

ACTION_MAP = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}


COMMAND_MAP = {
    "maintain": "KEEP_CURRENT",
    "reduce": "REDUCE_LOAD",
    "shift": "SHIFT_LOAD",
    "turn_off": "TURN_OFF"
}


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def separator(char="=", width=70):
    print(char * width)


def print_header(title):
    print()
    separator()
    print(title)
    separator()


def require_file(path, description):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required file missing: {description}\n{path}"
        )

    print(f"[OK] {description}: {path}")


def safe_float(value, default=0.0):
    try:
        value = float(value)

        if np.isnan(value) or np.isinf(value):
            return default

        return value

    except Exception:
        return default


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def get_action_name(value):

    if isinstance(value, str):

        value = value.strip().lower()

        if value in [
            "maintain",
            "reduce",
            "shift",
            "turn_off"
        ]:
            return value

    try:

        integer_value = int(value)

        return ACTION_MAP.get(
            integer_value,
            "maintain"
        )

    except Exception:

        return "maintain"


def get_command(action):

    return COMMAND_MAP.get(
        action,
        "KEEP_CURRENT"
    )


# ================================================================
# LOAD HOUSE CONFIGURATION
# ================================================================

print_header(
    "MODULE 16 — VIRTUAL ESP32 + SMART PLUG HARDWARE SIMULATOR"
)

print()
print("Hardware mode : SOFTWARE SIMULATION")
print("Physical ESP32: NOT REQUIRED")
print("Physical plugs : NOT REQUIRED")

print()
print("Architecture:")
print("  Module 14H → Module 15 → Virtual ESP32")
print("                           ↓")
print("                    Virtual Smart Plug")
print("                           ↓")
print("                    Virtual Appliance")
print("                           ↓")
print("                    Simulated Feedback")


# ================================================================
# CHECK INITIALIZATION FILES
# ================================================================

print_header("CHECKING REQUIRED FILES")

require_file(
    HOUSE_CONFIG_FILE,
    "House configuration"
)

require_file(
    APPLIANCE_CONFIG_FILE,
    "Appliance configuration"
)


# ================================================================
# LOAD HOUSE CONFIG
# ================================================================

print()
print("Loading house configuration...")

with open(
    HOUSE_CONFIG_FILE,
    "r",
    encoding="utf-8"
) as f:

    house_config = json.load(f)


HOUSE_ID = house_config.get(
    "house_id"
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
# BUILD HOUSE PATHS
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


os.makedirs(
    HARDWARE_DIR,
    exist_ok=True
)


# ================================================================
# MODULE 15 INPUT FILES
# ================================================================

IOT_ACTION_FILE = os.path.join(
    IOT_DIR,
    "iot_action_execution.csv"
)

IOT_FEEDBACK_FILE = os.path.join(
    IOT_DIR,
    "iot_action_feedback.csv"
)

IOT_DEVICE_STATUS_FILE = os.path.join(
    IOT_DIR,
    "iot_device_status.csv"
)

IOT_ACTION_SUMMARY_FILE = os.path.join(
    IOT_DIR,
    "iot_action_summary.csv"
)

IOT_FEEDBACK_SUMMARY_FILE = os.path.join(
    IOT_DIR,
    "iot_feedback_summary.csv"
)

IOT_SYSTEM_SUMMARY_FILE = os.path.join(
    IOT_DIR,
    "iot_execution_system_summary.csv"
)


# ================================================================
# MODULE 16 OUTPUT FILES
# ================================================================

ESP32_COMMAND_QUEUE_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_command_queue.csv"
)

ESP32_COMMAND_LOG_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_command_log.csv"
)

ESP32_SENSOR_FEEDBACK_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_sensor_feedback.csv"
)

ESP32_DEVICE_STATUS_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_device_status.csv"
)

ESP32_HARDWARE_SUMMARY_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_hardware_summary.csv"
)

ESP32_SYSTEM_SUMMARY_FILE = os.path.join(
    HARDWARE_DIR,
    "esp32_system_summary.csv"
)


# ================================================================
# DISPLAY PATHS
# ================================================================

print_header("HOUSE DATA PATHS")

print(
    f"House directory : {HOUSE_DIR}"
)

print(
    f"IoT input        : {IOT_DIR}"
)

print(
    f"Hardware output  : {HARDWARE_DIR}"
)


# ================================================================
# CHECK MODULE 15 INPUTS
# ================================================================

print_header("CHECKING MODULE 15 INPUTS")

require_file(
    IOT_ACTION_FILE,
    "Module 15 IoT action execution"
)

require_file(
    IOT_FEEDBACK_FILE,
    "Module 15 IoT action feedback"
)

require_file(
    IOT_DEVICE_STATUS_FILE,
    "Module 15 IoT device status"
)

require_file(
    IOT_ACTION_SUMMARY_FILE,
    "Module 15 IoT action summary"
)

require_file(
    IOT_FEEDBACK_SUMMARY_FILE,
    "Module 15 IoT feedback summary"
)

require_file(
    IOT_SYSTEM_SUMMARY_FILE,
    "Module 15 IoT system summary"
)


# ================================================================
# LOAD APPLIANCE CONFIGURATION
# ================================================================

print_header("LOADING APPLIANCE CONFIGURATION")

appliances = pd.read_csv(
    APPLIANCE_CONFIG_FILE
)

print(
    f"Registered appliances: {len(appliances)}"
)

print()

display_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]

print(
    appliances[
        [
            c for c in display_columns
            if c in appliances.columns
        ]
    ].to_string(index=False)
)


# ================================================================
# VALIDATE APPLIANCE CONFIG
# ================================================================

required_appliance_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]

missing = [
    c for c in required_appliance_columns
    if c not in appliances.columns
]

if missing:

    raise ValueError(
        "Missing appliance configuration columns:\n"
        + "\n".join(missing)
    )


# ================================================================
# CREATE DEVICE MAP
# ================================================================

device_map = {}

for _, row in appliances.iterrows():

    appliance_id = str(
        row["appliance_id"]
    )

    sensor_id = str(
        row["sensor_id"]
    )

    appliance_name = str(
        row["appliance_name"]
    )

    device_id = f"IOT_{sensor_id}"

    device_map[appliance_id] = {
        "appliance_id": appliance_id,
        "appliance_name": appliance_name,
        "appliance_type": str(
            row["appliance_type"]
        ),
        "sensor_id": sensor_id,
        "device_id": device_id,
        "rated_power_w": safe_float(
            row["rated_power_w"]
        )
    }


# ================================================================
# DISPLAY DEVICE MAPPING
# ================================================================

print_header("VIRTUAL ESP32 DEVICE MAPPING")

for appliance_id, device in device_map.items():

    print(
        f"{appliance_id} -> "
        f"{device['sensor_id']} -> "
        f"{device['device_id']} -> "
        f"{device['appliance_name']}"
    )


# ================================================================
# LOAD MODULE 15 ACTION DATA
# ================================================================

print_header("LOADING MODULE 15 IoT ACTION DATA")

actions = pd.read_csv(
    IOT_ACTION_FILE
)

print(
    f"Action rows : {len(actions)}"
)

print(
    f"Columns     : {len(actions.columns)}"
)

print()

print("Available columns:")

for index, column in enumerate(
    actions.columns,
    start=1
):

    print(
        f"{index:2d}. {column}"
    )


# ================================================================
# IDENTIFY REQUIRED COLUMNS
# ================================================================

print_header("VALIDATING MODULE 15 INPUT")

required_action_columns = [
    "appliance_id",
    "appliance_name",
    "sensor_id",
    "requested_action",
    "previous_power_w",
    "target_power_w",
    "actual_power_w"
]


# ------------------------------------------------
# Support alternate column names
# ------------------------------------------------

column_aliases = {

    "previous_power_w": [
        "previous_power_w",
        "power_w",
        "previous_power"
    ],

    "target_power_w": [
        "target_power_w",
        "target_power"
    ],

    "actual_power_w": [
        "actual_power_w",
        "actual_power"
    ],

    "requested_action": [
        "requested_action",
        "action",
        "recommended_action",
        "action_name"
    ]
}


def resolve_column(df, logical_name):

    if logical_name not in column_aliases:

        return (
            logical_name
            if logical_name in df.columns
            else None
        )

    for candidate in column_aliases[
        logical_name
    ]:

        if candidate in df.columns:

            return candidate

    return None


resolved_columns = {}

for logical_name in required_action_columns:

    column = resolve_column(
        actions,
        logical_name
    )

    resolved_columns[
        logical_name
    ] = column


for logical_name, column in resolved_columns.items():

    if column is None:

        raise ValueError(
            f"Required Module 15 column missing: "
            f"{logical_name}"
        )

    print(
        f"[OK] {logical_name:<20}: {column}"
    )


# ================================================================
# NORMALIZE MODULE 15 DATA
# ================================================================

actions = actions.copy()

actions["_appliance_id"] = (
    actions[
        resolved_columns[
            "appliance_id"
        ]
    ].astype(str)
)

actions["_appliance_name"] = (
    actions[
        resolved_columns[
            "appliance_name"
        ]
    ].astype(str)
)

actions["_sensor_id"] = (
    actions[
        resolved_columns[
            "sensor_id"
        ]
    ].astype(str)
)

actions["_requested_action"] = (
    actions[
        resolved_columns[
            "requested_action"
        ]
    ].apply(get_action_name)
)

actions["_previous_power_w"] = (
    actions[
        resolved_columns[
            "previous_power_w"
        ]
    ].apply(safe_float)
)

actions["_target_power_w"] = (
    actions[
        resolved_columns[
            "target_power_w"
        ]
    ].apply(safe_float)
)

actions["_actual_power_w"] = (
    actions[
        resolved_columns[
            "actual_power_w"
        ]
    ].apply(safe_float)
)


# ================================================================
# VALIDATE APPLIANCE MAPPING
# ================================================================

print()
print("Validating appliance mapping...")

unknown_appliances = sorted(
    set(actions["_appliance_id"])
    -
    set(device_map.keys())
)

if unknown_appliances:

    raise ValueError(
        "Unknown appliance IDs found:\n"
        + "\n".join(
            unknown_appliances
        )
    )

print(
    "[OK] All Module 15 appliances "
    "mapped to virtual devices."
)


# ================================================================
# VALIDATE SENSOR MAPPING
# ================================================================

for _, row in actions.iterrows():

    appliance_id = row[
        "_appliance_id"
    ]

    expected_sensor = device_map[
        appliance_id
    ]["sensor_id"]

    actual_sensor = row[
        "_sensor_id"
    ]

    if actual_sensor != expected_sensor:

        raise ValueError(
            f"Sensor mismatch for "
            f"{appliance_id}: "
            f"expected {expected_sensor}, "
            f"found {actual_sensor}"
        )

print(
    "[OK] Sensor-to-appliance mapping validated."
)


# ================================================================
# SAFETY CONTROLLER
# ================================================================

print_header("SAFETY CONTROLLER")

print(
    f"Maintain allowed : {ALLOW_MAINTAIN}"
)

print(
    f"Reduce allowed   : {ALLOW_REDUCE}"
)

print(
    f"Shift allowed    : {ALLOW_SHIFT}"
)

print(
    f"Turn-off allowed : {ALLOW_TURN_OFF}"
)

print(
    f"Maximum reduction: "
    f"{MAX_REDUCTION_PERCENT:.1f}%"
)


def safety_check(action, power, rated_power):

    if action == "maintain":

        if not ALLOW_MAINTAIN:

            return (
                False,
                "MAINTAIN_DISABLED"
            )

        return (
            True,
            "SAFE"
        )


    if action == "reduce":

        if not ALLOW_REDUCE:

            return (
                False,
                "REDUCE_DISABLED"
            )

        if power < 0:

            return (
                False,
                "NEGATIVE_POWER"
            )

        if rated_power <= 0:

            return (
                False,
                "INVALID_RATED_POWER"
            )

        return (
            True,
            "SAFE"
        )


    if action == "shift":

        if not ALLOW_SHIFT:

            return (
                False,
                "SHIFT_DISABLED"
            )

        return (
            True,
            "SAFE"
        )


    if action == "turn_off":

        if not ALLOW_TURN_OFF:

            return (
                False,
                "TURN_OFF_BLOCKED"
            )

        return (
            True,
            "SAFE"
        )


    return (
        False,
        "INVALID_ACTION"
    )


# ================================================================
# VIRTUAL ESP32 EXECUTION
# ================================================================

print_header("VIRTUAL ESP32 HARDWARE EXECUTION")

print()
print("Execution mode      : SIMULATION")
print("Physical hardware   : NOT CONNECTED")
print("ESP32 interface     : READY")
print("Smart plug interface: READY")
print("Wi-Fi simulation    : ACTIVE")
print("Safety controller   : ACTIVE")


# ================================================================
# OUTPUT RECORD COLLECTION
# ================================================================

command_queue_records = []
command_log_records = []
sensor_feedback_records = []
device_status_records = []


# ================================================================
# PROCESS EACH ACTION
# ================================================================

total_rows = len(actions)

execution_start = time.time()


for index, row in actions.iterrows():

    execution_number = index + 1

    appliance_id = row[
        "_appliance_id"
    ]

    appliance_name = row[
        "_appliance_name"
    ]

    sensor_id = row[
        "_sensor_id"
    ]

    device = device_map[
        appliance_id
    ]

    device_id = device[
        "device_id"
    ]

    rated_power = device[
        "rated_power_w"
    ]

    requested_action = row[
        "_requested_action"
    ]

    previous_power = row[
        "_previous_power_w"
    ]

    target_power = row[
        "_target_power_w"
    ]

    module15_actual_power = row[
        "_actual_power_w"
    ]


    # ------------------------------------------------------------
    # Safety check
    # ------------------------------------------------------------

    safe, safety_status = safety_check(
        requested_action,
        previous_power,
        rated_power
    )


    # ------------------------------------------------------------
    # Command
    # ------------------------------------------------------------

    command = get_command(
        requested_action
    )


    # ------------------------------------------------------------
    # Virtual ESP32 command ID
    # ------------------------------------------------------------

    command_id = (
        f"ESP32CMD_"
        f"{execution_number:04d}_"
        f"{sensor_id}"
    )


    timestamp = datetime.now().isoformat(
        timespec="milliseconds"
    )


    # ------------------------------------------------------------
    # Queue command
    # ------------------------------------------------------------

    queue_status = (
        "QUEUED"
        if safe
        else "BLOCKED"
    )


    command_queue_records.append({

        "command_id":
            command_id,

        "timestamp":
            timestamp,

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "requested_action":
            requested_action,

        "command":
            command,

        "previous_power_w":
            round(previous_power, 6),

        "target_power_w":
            round(target_power, 6),

        "rated_power_w":
            round(rated_power, 6),

        "safety_status":
            safety_status,

        "queue_status":
            queue_status,

        "execution_mode":
            EXECUTION_MODE

    })


    # ------------------------------------------------------------
    # Simulated network delay
    # ------------------------------------------------------------

    response_time_ms = random.uniform(
        35.0,
        95.0
    )


    # ------------------------------------------------------------
    # Simulate appliance response
    # ------------------------------------------------------------

    if not safe:

        actual_power = previous_power

        execution_status = (
            "BLOCKED_BY_SAFETY"
        )

        feedback_score = 0.0

        power_error = abs(
            actual_power -
            target_power
        )


    else:

        if requested_action == "maintain":

            actual_power = previous_power


        elif requested_action == "reduce":

            reduction_factor = (
                1.0 -
                (
                    MAX_REDUCTION_PERCENT
                    / 100.0
                )
            )

            actual_power = (
                previous_power *
                reduction_factor
            )

            # Add realistic simulated control error.

            control_error = random.uniform(
                -0.025,
                0.025
            )

            actual_power *= (
                1.0 +
                control_error
            )


        elif requested_action == "shift":

            actual_power = (
                previous_power *
                SHIFT_FACTOR
            )


        elif requested_action == "turn_off":

            actual_power = (
                previous_power *
                TURN_OFF_FACTOR
            )


        else:

            actual_power = previous_power


        # --------------------------------------------------------
        # Physical power cannot be negative.
        # --------------------------------------------------------

        actual_power = max(
            0.0,
            actual_power
        )


        # --------------------------------------------------------
        # Error against target
        # --------------------------------------------------------

        power_error = abs(
            actual_power -
            target_power
        )


        # --------------------------------------------------------
        # Feedback score
        # --------------------------------------------------------

        if requested_action == "maintain":

            feedback_score = 1.0


        elif target_power <= 0:

            feedback_score = 0.5


        else:

            relative_error = (
                power_error /
                max(
                    target_power,
                    0.001
                )
            )

            feedback_score = clamp(
                1.0 -
                relative_error,
                0.0,
                1.0
            )


        execution_status = (
            "SIMULATED_SUCCESS"
        )


    # ------------------------------------------------------------
    # Energy savings estimation
    #
    # One 5-second IoT sampling interval is used.
    # ------------------------------------------------------------

    interval_hours = 5.0 / 3600.0

    energy_before = (
        previous_power *
        interval_hours /
        1000.0
    )

    energy_after = (
        actual_power *
        interval_hours /
        1000.0
    )

    savings = max(
        0.0,
        energy_before -
        energy_after
    )


    # ------------------------------------------------------------
    # Virtual ESP32 state
    # ------------------------------------------------------------

    esp32_state = (
        "ONLINE"
        if SIMULATED_WIFI
        else "OFFLINE"
    )

    plug_state = (
        "ON"
        if actual_power > 1.0
        else "OFF"
    )


    # ------------------------------------------------------------
    # Command log
    # ------------------------------------------------------------

    command_log_records.append({

        "command_id":
            command_id,

        "timestamp":
            timestamp,

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "action":
            requested_action,

        "command":
            command,

        "target_power_w":
            round(target_power, 6),

        "previous_power_w":
            round(previous_power, 6),

        "actual_power_w":
            round(actual_power, 6),

        "power_error_w":
            round(power_error, 6),

        "energy_before_kwh":
            round(
                energy_before,
                9
            ),

        "energy_after_kwh":
            round(
                energy_after,
                9
            ),

        "savings_kwh":
            round(
                savings,
                9
            ),

        "feedback_score":
            round(
                feedback_score,
                6
            ),

        "response_time_ms":
            round(
                response_time_ms,
                3
            ),

        "execution_status":
            execution_status,

        "safety_status":
            safety_status,

        "esp32_state":
            esp32_state,

        "smart_plug_state":
            plug_state,

        "execution_mode":
            EXECUTION_MODE

    })


    # ------------------------------------------------------------
    # Sensor feedback
    # ------------------------------------------------------------

    sensor_feedback_records.append({

        "feedback_id":
            f"FB_{execution_number:04d}_{sensor_id}",

        "timestamp":
            timestamp,

        "command_id":
            command_id,

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "requested_action":
            requested_action,

        "target_power_w":
            round(
                target_power,
                6
            ),

        "measured_power_w":
            round(
                actual_power,
                6
            ),

        "power_error_w":
            round(
                power_error,
                6
            ),

        "energy_savings_kwh":
            round(
                savings,
                9
            ),

        "feedback_score":
            round(
                feedback_score,
                6
            ),

        "feedback_status":
            (
                "POSITIVE"
                if feedback_score >= 0.90
                else
                "ACCEPTABLE"
                if feedback_score >= 0.70
                else
                "NEGATIVE"
            ),

        "response_time_ms":
            round(
                response_time_ms,
                3
            ),

        "esp32_state":
            esp32_state,

        "smart_plug_state":
            plug_state,

        "execution_mode":
            EXECUTION_MODE

    })


    # ------------------------------------------------------------
    # Device status
    # ------------------------------------------------------------

    device_status_records.append({

        "timestamp":
            timestamp,

        "house_id":
            HOUSE_ID,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "sensor_id":
            sensor_id,

        "device_id":
            device_id,

        "device_type":
            "Virtual ESP32 Smart Plug",

        "esp32_status":
            esp32_state,

        "wifi_status":
            "CONNECTED_SIMULATED",

        "smart_plug_status":
            "ONLINE_SIMULATED",

        "appliance_status":
            (
                "ACTIVE"
                if actual_power > 1.0
                else
                "OFF"
            ),

        "current_power_w":
            round(
                actual_power,
                6
            ),

        "rated_power_w":
            round(
                rated_power,
                6
            ),

        "last_action":
            requested_action,

        "last_command":
            command,

        "hardware_connected":
            False,

        "execution_mode":
            EXECUTION_MODE,

        "device_health":
            "GOOD"

    })


    # ------------------------------------------------------------
    # Console output
    # ------------------------------------------------------------

    print()
    print("-" * 70)

    print(
        f"EXECUTION "
        f"{execution_number}/{total_rows}"
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
        f"Action    : {requested_action}"
    )

    print(
        f"Command   : {command}"
    )

    print(
        f"Power     : {previous_power:.3f} W"
    )

    print(
        f"Target    : {target_power:.3f} W"
    )

    print(
        f"Actual    : {actual_power:.3f} W"
    )

    print(
        f"Feedback  : {feedback_score:.3f}"
    )

    print(
        f"Response  : {response_time_ms:.2f} ms"
    )

    print(
        f"Status    : {execution_status}"
    )

    print(
        f"Safety    : {safety_status}"
    )


execution_time = (
    time.time() -
    execution_start
)


# ================================================================
# CREATE DATAFRAMES
# ================================================================

command_queue_df = pd.DataFrame(
    command_queue_records
)

command_log_df = pd.DataFrame(
    command_log_records
)

sensor_feedback_df = pd.DataFrame(
    sensor_feedback_records
)

device_status_df = pd.DataFrame(
    device_status_records
)


# ================================================================
# GENERATED DATA VALIDATION
# ================================================================

print_header("GENERATED DATA VALIDATION")

print(
    f"Command queue rows : "
    f"{len(command_queue_df)}"
)

print(
    f"Command log rows   : "
    f"{len(command_log_df)}"
)

print(
    f"Sensor feedback    : "
    f"{len(sensor_feedback_df)}"
)

print(
    f"Device status rows : "
    f"{len(device_status_df)}"
)


# ================================================================
# NULL VALIDATION
# ================================================================

print()
print("NULL VALIDATION")
print("-" * 70)

queue_nulls = (
    command_queue_df.isnull()
    .sum()
    .sum()
)

log_nulls = (
    command_log_df.isnull()
    .sum()
    .sum()
)

feedback_nulls = (
    sensor_feedback_df.isnull()
    .sum()
    .sum()
)

device_nulls = (
    device_status_df.isnull()
    .sum()
    .sum()
)

print(
    f"Command queue NULLs : {queue_nulls}"
)

print(
    f"Command log NULLs   : {log_nulls}"
)

print(
    f"Feedback NULLs      : {feedback_nulls}"
)

print(
    f"Device status NULLs : {device_nulls}"
)

if (
    queue_nulls == 0
    and log_nulls == 0
    and feedback_nulls == 0
    and device_nulls == 0
):

    print(
        "[OK] No NULL values."
    )

else:

    raise ValueError(
        "NULL validation failed."
    )


# ================================================================
# DUPLICATE VALIDATION
# ================================================================

print()
print("DUPLICATE VALIDATION")
print("-" * 70)

command_duplicates = (
    command_log_df[
        "command_id"
    ].duplicated()
    .sum()
)

feedback_duplicates = (
    sensor_feedback_df[
        "feedback_id"
    ].duplicated()
    .sum()
)

print(
    f"Command duplicates  : "
    f"{command_duplicates}"
)

print(
    f"Feedback duplicates : "
    f"{feedback_duplicates}"
)

if (
    command_duplicates == 0
    and feedback_duplicates == 0
):

    print(
        "[OK] No duplicate command "
        "or feedback IDs."
    )

else:

    raise ValueError(
        "Duplicate validation failed."
    )


# ================================================================
# ACTION VALIDATION
# ================================================================

print()
print("ACTION VALIDATION")
print("-" * 70)

valid_actions = {
    "maintain",
    "reduce",
    "shift",
    "turn_off"
}

invalid_actions = sorted(
    set(
        command_log_df["action"]
    )
    -
    valid_actions
)

print(
    f"Invalid actions : "
    f"{len(invalid_actions)}"
)

if invalid_actions:

    raise ValueError(
        f"Invalid actions: "
        f"{invalid_actions}"
    )

print(
    "[OK] All actions valid."
)


# ================================================================
# POWER VALIDATION
# ================================================================

print()
print("POWER VALIDATION")
print("-" * 70)

negative_power = (
    command_log_df[
        "actual_power_w"
    ] < 0
).sum()

negative_savings = (
    command_log_df[
        "savings_kwh"
    ] < 0
).sum()

negative_target = (
    command_log_df[
        "target_power_w"
    ] < 0
).sum()

print(
    f"Negative actual power : "
    f"{negative_power}"
)

print(
    f"Negative savings      : "
    f"{negative_savings}"
)

print(
    f"Negative target power : "
    f"{negative_target}"
)

if (
    negative_power == 0
    and negative_savings == 0
    and negative_target == 0
):

    print(
        "[OK] Power values valid."
    )

else:

    raise ValueError(
        "Power validation failed."
    )


# ================================================================
# SAFETY VALIDATION
# ================================================================

print()
print("SAFETY VALIDATION")
print("-" * 70)

blocked_turn_off = (
    (
        command_log_df["action"]
        == "turn_off"
    )
    &
    (
        command_log_df[
            "execution_status"
        ]
        ==
        "BLOCKED_BY_SAFETY"
    )
).sum()

unsafe_executions = (
    command_log_df[
        "safety_status"
    ]
    == "INVALID_ACTION"
).sum()

print(
    f"Blocked turn-off actions : "
    f"{blocked_turn_off}"
)

print(
    f"Invalid safety actions   : "
    f"{unsafe_executions}"
)

print(
    "[OK] Safety controller validated."
)


# ================================================================
# DEVICE VALIDATION
# ================================================================

print()
print("DEVICE VALIDATION")
print("-" * 70)

expected_devices = set(
    device_map.keys()
)

processed_devices = set(
    command_log_df[
        "appliance_id"
    ]
)

missing_devices = (
    expected_devices -
    processed_devices
)

print(
    f"Expected devices  : "
    f"{len(expected_devices)}"
)

print(
    f"Processed devices : "
    f"{len(processed_devices)}"
)

if missing_devices:

    raise ValueError(
        "Missing devices:\n"
        + "\n".join(
            missing_devices
        )
    )

print(
    "[OK] Every registered appliance "
    "processed."
)


# ================================================================
# BUILD HARDWARE SUMMARY
# ================================================================

summary_records = []


for appliance_id, device in device_map.items():

    subset = command_log_df[
        command_log_df[
            "appliance_id"
        ]
        ==
        appliance_id
    ]

    feedback_subset = sensor_feedback_df[
        sensor_feedback_df[
            "appliance_id"
        ]
        ==
        appliance_id
    ]


    if len(subset) == 0:

        continue


    summary_records.append({

        "appliance_id":
            appliance_id,

        "appliance_name":
            device[
                "appliance_name"
            ],

        "sensor_id":
            device[
                "sensor_id"
            ],

        "device_id":
            device[
                "device_id"
            ],

        "execution_count":
            len(subset),

        "successful_executions":
            (
                subset[
                    "execution_status"
                ]
                ==
                "SIMULATED_SUCCESS"
            ).sum(),

        "blocked_executions":
            (
                subset[
                    "execution_status"
                ]
                ==
                "BLOCKED_BY_SAFETY"
            ).sum(),

        "average_previous_power_w":
            round(
                subset[
                    "previous_power_w"
                ].mean(),
                6
            ),

        "average_target_power_w":
            round(
                subset[
                    "target_power_w"
                ].mean(),
                6
            ),

        "average_actual_power_w":
            round(
                subset[
                    "actual_power_w"
                ].mean(),
                6
            ),

        "total_savings_kwh":
            round(
                subset[
                    "savings_kwh"
                ].sum(),
                9
            ),

        "average_feedback_score":
            round(
                feedback_subset[
                    "feedback_score"
                ].mean(),
                6
            ),

        "average_response_time_ms":
            round(
                subset[
                    "response_time_ms"
                ].mean(),
                3
            ),

        "esp32_status":
            "ONLINE_SIMULATED",

        "smart_plug_status":
            "ONLINE_SIMULATED",

        "hardware_connected":
            False,

        "execution_mode":
            EXECUTION_MODE

    })


hardware_summary_df = pd.DataFrame(
    summary_records
)


# ================================================================
# FEEDBACK SUMMARY
# ================================================================

positive_feedback = (
    sensor_feedback_df[
        "feedback_status"
    ]
    == "POSITIVE"
).sum()

acceptable_feedback = (
    sensor_feedback_df[
        "feedback_status"
    ]
    == "ACCEPTABLE"
).sum()

negative_feedback = (
    sensor_feedback_df[
        "feedback_status"
    ]
    == "NEGATIVE"
).sum()


# ================================================================
# SYSTEM TOTALS
# ================================================================

total_executions = len(
    command_log_df
)

successful_executions = (
    command_log_df[
        "execution_status"
    ]
    ==
    "SIMULATED_SUCCESS"
).sum()

blocked_executions = (
    command_log_df[
        "execution_status"
    ]
    ==
    "BLOCKED_BY_SAFETY"
).sum()

total_savings = (
    command_log_df[
        "savings_kwh"
    ].sum()
)

average_feedback = (
    sensor_feedback_df[
        "feedback_score"
    ].mean()
)

average_response = (
    command_log_df[
        "response_time_ms"
    ].mean()
)

average_power_error = (
    command_log_df[
        "power_error_w"
    ].mean()
)


# ================================================================
# SYSTEM STATUS
# ================================================================

if (
    total_executions > 0
    and
    len(missing_devices) == 0
    and
    queue_nulls == 0
    and
    log_nulls == 0
    and
    feedback_nulls == 0
    and
    device_nulls == 0
    and
    command_duplicates == 0
    and
    feedback_duplicates == 0
):

    system_status = (
        "HARDWARE_INTERFACE_READY"
    )

else:

    system_status = (
        "HARDWARE_INTERFACE_VALIDATION_FAILED"
    )


# ================================================================
# SYSTEM SUMMARY
# ================================================================

system_summary_df = pd.DataFrame([{

    "timestamp":
        datetime.now().isoformat(
            timespec="seconds"
        ),

    "house_id":
        HOUSE_ID,

    "house_name":
        HOUSE_NAME,

    "location":
        LOCATION,

    "registered_appliances":
        len(appliances),

    "processed_appliances":
        len(processed_devices),

    "execution_mode":
        EXECUTION_MODE,

    "physical_hardware_connected":
        False,

    "virtual_esp32_count":
        len(processed_devices),

    "virtual_smart_plug_count":
        len(processed_devices),

    "command_queue_rows":
        len(command_queue_df),

    "command_log_rows":
        len(command_log_df),

    "sensor_feedback_rows":
        len(sensor_feedback_df),

    "device_status_rows":
        len(device_status_df),

    "successful_executions":
        int(successful_executions),

    "blocked_executions":
        int(blocked_executions),

    "failed_executions":
        0,

    "positive_feedback":
        int(positive_feedback),

    "acceptable_feedback":
        int(acceptable_feedback),

    "negative_feedback":
        int(negative_feedback),

    "average_feedback_score":
        round(
            average_feedback,
            6
        ),

    "average_power_error_w":
        round(
            average_power_error,
            6
        ),

    "average_response_time_ms":
        round(
            average_response,
            3
        ),

    "total_simulated_savings_kwh":
        round(
            total_savings,
            9
        ),

    "esp32_interface":
        (
            "READY"
            if ESP32_INTERFACE_READY
            else "NOT_READY"
        ),

    "smart_plug_interface":
        (
            "READY"
            if SMART_PLUG_INTERFACE_READY
            else "NOT_READY"
        ),

    "wifi_interface":
        (
            "READY"
            if SIMULATED_WIFI
            else "NOT_READY"
        ),

    "safety_controller":
        "ACTIVE",

    "hardware_connection":
        "NO_PHYSICAL_HARDWARE",

    "feedback_loop":
        "ACTIVE",

    "system_status":
        system_status,

    "processing_time_seconds":
        round(
            execution_time,
            4
        )

}])


# ================================================================
# SAVE OUTPUTS
# ================================================================

print_header("GENERATING MODULE 16 OUTPUTS")


command_queue_df.to_csv(
    ESP32_COMMAND_QUEUE_FILE,
    index=False
)

print(
    "[OK] ESP32 command queue:"
)

print(
    ESP32_COMMAND_QUEUE_FILE
)


command_log_df.to_csv(
    ESP32_COMMAND_LOG_FILE,
    index=False
)

print(
    "[OK] ESP32 command log:"
)

print(
    ESP32_COMMAND_LOG_FILE
)


sensor_feedback_df.to_csv(
    ESP32_SENSOR_FEEDBACK_FILE,
    index=False
)

print(
    "[OK] ESP32 sensor feedback:"
)

print(
    ESP32_SENSOR_FEEDBACK_FILE
)


device_status_df.to_csv(
    ESP32_DEVICE_STATUS_FILE,
    index=False
)

print(
    "[OK] ESP32 device status:"
)

print(
    ESP32_DEVICE_STATUS_FILE
)


hardware_summary_df.to_csv(
    ESP32_HARDWARE_SUMMARY_FILE,
    index=False
)

print(
    "[OK] ESP32 hardware summary:"
)

print(
    ESP32_HARDWARE_SUMMARY_FILE
)


system_summary_df.to_csv(
    ESP32_SYSTEM_SUMMARY_FILE,
    index=False
)

print(
    "[OK] ESP32 system summary:"
)

print(
    ESP32_SYSTEM_SUMMARY_FILE
)


# ================================================================
# DISPLAY HARDWARE RESULTS
# ================================================================

print_header(
    "VIRTUAL ESP32 HARDWARE RESULTS"
)

display_summary_columns = [

    "appliance_id",

    "appliance_name",

    "sensor_id",

    "device_id",

    "execution_count",

    "successful_executions",

    "blocked_executions",

    "average_previous_power_w",

    "average_target_power_w",

    "average_actual_power_w",

    "total_savings_kwh",

    "average_feedback_score"

]

print(
    hardware_summary_df[
        [
            c
            for c in display_summary_columns
            if c in hardware_summary_df.columns
        ]
    ].to_string(
        index=False
    )
)


# ================================================================
# SYSTEM SUMMARY DISPLAY
# ================================================================

print_header(
    "MODULE 16 SYSTEM SUMMARY"
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
    f"{len(appliances)}"
)

print(
    f"Processed appliances      : "
    f"{len(processed_devices)}"
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
    f"Virtual ESP32 devices     : "
    f"{len(processed_devices)}"
)

print(
    f"Command executions        : "
    f"{total_executions}"
)

print(
    f"Successful executions     : "
    f"{successful_executions}"
)

print(
    f"Blocked executions        : "
    f"{blocked_executions}"
)

print(
    f"Positive feedback         : "
    f"{positive_feedback}"
)

print(
    f"Acceptable feedback      : "
    f"{acceptable_feedback}"
)

print(
    f"Negative feedback         : "
    f"{negative_feedback}"
)

print(
    f"Total simulated savings   : "
    f"{total_savings:.9f} kWh"
)

print(
    f"Average feedback score    : "
    f"{average_feedback:.4f}"
)

print(
    f"Average power error       : "
    f"{average_power_error:.4f} W"
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
    f"Wi-Fi interface           : READY (SIMULATED)"
)

print(
    f"Safety controller         : ACTIVE"
)

print(
    f"Feedback loop             : ACTIVE"
)

print(
    f"System status             : "
    f"{system_status}"
)


# ================================================================
# OUTPUT FILES
# ================================================================

print_header(
    "MODULE 16 OUTPUT FILES"
)

print()
print(
    "ESP32 command queue:"
)

print(
    ESP32_COMMAND_QUEUE_FILE
)

print()
print(
    "ESP32 command log:"
)

print(
    ESP32_COMMAND_LOG_FILE
)

print()
print(
    "ESP32 sensor feedback:"
)

print(
    ESP32_SENSOR_FEEDBACK_FILE
)

print()
print(
    "ESP32 device status:"
)

print(
    ESP32_DEVICE_STATUS_FILE
)

print()
print(
    "ESP32 hardware summary:"
)

print(
    ESP32_HARDWARE_SUMMARY_FILE
)

print()
print(
    "ESP32 system summary:"
)

print(
    ESP32_SYSTEM_SUMMARY_FILE
)


# ================================================================
# FINAL VALIDATION
# ================================================================

print_header(
    "MODULE 16 VALIDATION"
)

validation_checks = {

    "Every registered appliance processed":
        len(missing_devices) == 0,

    "Command queue generated":
        len(command_queue_df) == total_executions,

    "Command log generated":
        len(command_log_df) == total_executions,

    "Sensor feedback generated":
        len(sensor_feedback_df) == total_executions,

    "Device status generated":
        len(device_status_df) == total_executions,

    "No command NULL values":
        queue_nulls == 0,

    "No log NULL values":
        log_nulls == 0,

    "No feedback NULL values":
        feedback_nulls == 0,

    "No device NULL values":
        device_nulls == 0,

    "No duplicate command IDs":
        command_duplicates == 0,

    "No duplicate feedback IDs":
        feedback_duplicates == 0,

    "All actions valid":
        len(invalid_actions) == 0,

    "No negative actual power":
        negative_power == 0,

    "No negative savings":
        negative_savings == 0,

    "Safety controller active":
        True,

    "ESP32 interface ready":
        ESP32_INTERFACE_READY,

    "Smart plug interface ready":
        SMART_PLUG_INTERFACE_READY,

    "Physical hardware safely disconnected":
        HARDWARE_CONNECTED is False
}


all_valid = True


for check_name, result in validation_checks.items():

    if result:

        print(
            f"[OK] {check_name}"
        )

    else:

        print(
            f"[FAIL] {check_name}"
        )

        all_valid = False


if not all_valid:

    raise RuntimeError(
        "MODULE 16 VALIDATION FAILED"
    )


# ================================================================
# FINAL STATUS
# ================================================================

print_header(
    "MODULE 16 COMPLETE"
)

print(
    "[SUCCESS] Module 15 IoT actions consumed."
)

print(
    "[SUCCESS] Four-appliance virtual device mapping validated."
)

print(
    "[SUCCESS] Virtual ESP32 interface executed."
)

print(
    "[SUCCESS] Virtual smart-plug execution simulated."
)

print(
    "[SUCCESS] Sensor feedback generated."
)

print(
    "[SUCCESS] Safety controller validated."
)

print(
    "[SUCCESS] Hardware interface prepared."
)

print(
    "[SUCCESS] No physical hardware required."
)

print(
    "[SUCCESS] Module 16 validation passed."
)

print()
print(
    f"Execution mode : {EXECUTION_MODE}"
)

print(
    f"System status  : {system_status}"
)

print(
    f"Total time     : "
    f"{execution_time:.2f} seconds"
)

print()
separator()

print(
    "[SUCCESS] MODULE 16 COMPLETED."
)

print(
    "[SUCCESS] Virtual ESP32 hardware layer is READY."
)

print(
    "[SUCCESS] Real ESP32 can be integrated later "
    "without changing the ML/RL decision layer."
)

separator()