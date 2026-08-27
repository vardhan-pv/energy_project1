import os
import json
import uuid
import pandas as pd
from datetime import datetime


# ============================================================
# MODULE 14A — HOUSE & APPLIANCE INITIALIZATION
# ============================================================

BASE_DIR = r"E:\energy_project"
OUTPUT_DIR = os.path.join(BASE_DIR, "initialization")

HOUSE_CONFIG_FILE = os.path.join(
    OUTPUT_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG_FILE = os.path.join(
    OUTPUT_DIR,
    "appliance_config.csv"
)

SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "initialization_summary.csv"
)


# ============================================================
# DISPLAY
# ============================================================

print("=" * 70)
print("MODULE 14A — HOUSE & APPLIANCE INITIALIZATION")
print("=" * 70)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

print()
print("Initialization directory:")
print(OUTPUT_DIR)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_name(value):
    """
    Convert user input into a safe readable name.
    """

    value = str(value).strip()

    if not value:
        return ""

    value = value.replace(" ", "_")
    value = value.replace("-", "_")

    return value.lower()


def get_positive_float(prompt):
    """
    Read a positive floating-point number.
    """

    while True:

        value = input(prompt).strip()

        try:

            number = float(value)

            if number <= 0:
                print("Please enter a value greater than 0.")
                continue

            return number

        except ValueError:

            print("Invalid number. Please try again.")


def get_positive_integer(prompt):
    """
    Read a positive integer.
    """

    while True:

        value = input(prompt).strip()

        try:

            number = int(value)

            if number <= 0:
                print("Please enter an integer greater than 0.")
                continue

            return number

        except ValueError:

            print("Invalid integer. Please try again.")


def get_non_empty(prompt):
    """
    Read non-empty text.
    """

    while True:

        value = input(prompt).strip()

        if value:

            return value

        print("This field cannot be empty.")


# ============================================================
# HOUSE INFORMATION
# ============================================================

print()
print("-" * 70)
print("HOUSE INFORMATION")
print("-" * 70)

house_name = get_non_empty(
    "Enter house name: "
)

house_location = input(
    "Enter location (optional): "
).strip()

owner_name = input(
    "Enter owner/user name (optional): "
).strip()


# ============================================================
# GENERATE HOUSE ID
# ============================================================

house_id = "HOUSE_" + uuid.uuid4().hex[:8].upper()

created_at = datetime.now().isoformat(timespec="seconds")


# ============================================================
# APPLIANCE INFORMATION
# ============================================================

print()
print("-" * 70)
print("APPLIANCE CONFIGURATION")
print("-" * 70)

number_of_appliances = get_positive_integer(
    "How many appliances are present in this house? "
)


appliances = []

used_sensor_ids = set()


# ============================================================
# COLLECT APPLIANCES
# ============================================================

for i in range(number_of_appliances):

    print()
    print("-" * 70)
    print(f"APPLIANCE {i + 1} OF {number_of_appliances}")
    print("-" * 70)

    appliance_name = get_non_empty(
        "Appliance name: "
    )

    appliance_type = get_non_empty(
        "Appliance type/category: "
    )

    sensor_id = get_non_empty(
        "Sensor / Smart Plug ID: "
    ).upper()

    # --------------------------------------------------------
    # SENSOR ID VALIDATION
    # --------------------------------------------------------

    while sensor_id in used_sensor_ids:

        print(
            "This sensor ID is already assigned."
        )

        sensor_id = get_non_empty(
            "Enter a different Sensor / Smart Plug ID: "
        ).upper()

    used_sensor_ids.add(sensor_id)

    # --------------------------------------------------------
    # RATED POWER
    # --------------------------------------------------------

    rated_power = get_positive_float(
        "Rated power (W): "
    )

    # --------------------------------------------------------
    # GENERATE APPLIANCE ID
    # --------------------------------------------------------

    appliance_id = (
        "APP_"
        + str(i + 1).zfill(3)
        + "_"
        + uuid.uuid4().hex[:6].upper()
    )

    # --------------------------------------------------------
    # CREATE RECORD
    # --------------------------------------------------------

    appliance_record = {

        "appliance_id": appliance_id,

        "house_id": house_id,

        "appliance_name": appliance_name.strip(),

        "appliance_type": appliance_type.strip(),

        "sensor_id": sensor_id,

        "rated_power_w": rated_power,

        "status": "active",

        "created_at": created_at
    }

    appliances.append(appliance_record)


# ============================================================
# HOUSE CONFIGURATION
# ============================================================

house_config = {

    "module": "14A",

    "module_name":
        "House & Appliance Initialization",

    "house_id": house_id,

    "house_name": house_name,

    "location": house_location,

    "owner_name": owner_name,

    "created_at": created_at,

    "number_of_appliances":
        len(appliances),

    "appliances": appliances
}


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("INITIALIZATION VALIDATION")
print("=" * 70)

validation_errors = []


# ------------------------------------------------------------
# HOUSE ID
# ------------------------------------------------------------

if not house_id:

    validation_errors.append(
        "House ID is missing."
    )


# ------------------------------------------------------------
# HOUSE NAME
# ------------------------------------------------------------

if not house_name:

    validation_errors.append(
        "House name is missing."
    )


# ------------------------------------------------------------
# APPLIANCE COUNT
# ------------------------------------------------------------

if len(appliances) == 0:

    validation_errors.append(
        "No appliances configured."
    )


# ------------------------------------------------------------
# APPLIANCE VALIDATION
# ------------------------------------------------------------

for appliance in appliances:

    if not appliance["appliance_name"]:

        validation_errors.append(
            "Appliance name is missing."
        )

    if not appliance["sensor_id"]:

        validation_errors.append(
            f"Sensor ID missing for "
            f"{appliance['appliance_name']}."
        )

    if appliance["rated_power_w"] <= 0:

        validation_errors.append(
            f"Invalid rated power for "
            f"{appliance['appliance_name']}."
        )


# ============================================================
# STOP IF INVALID
# ============================================================

if validation_errors:

    print()
    print("VALIDATION FAILED")
    print("-" * 70)

    for error in validation_errors:

        print("[ERROR]", error)

    print()
    print("Initialization was not completed.")

    raise SystemExit(1)


print("[OK] House ID")
print("[OK] House name")
print("[OK] Appliance count")
print("[OK] Appliance configuration")
print("[OK] Sensor IDs")
print("[OK] Rated power values")


# ============================================================
# SAVE HOUSE CONFIGURATION
# ============================================================

with open(
    HOUSE_CONFIG_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        house_config,
        file,
        indent=4
    )


# ============================================================
# SAVE APPLIANCE CONFIGURATION
# ============================================================

appliance_df = pd.DataFrame(appliances)

appliance_df.to_csv(
    APPLIANCE_CONFIG_FILE,
    index=False
)


# ============================================================
# CREATE SUMMARY
# ============================================================

summary_rows = []

for appliance in appliances:

    summary_rows.append({

        "house_id":
            house_id,

        "house_name":
            house_name,

        "appliance_id":
            appliance["appliance_id"],

        "appliance_name":
            appliance["appliance_name"],

        "appliance_type":
            appliance["appliance_type"],

        "sensor_id":
            appliance["sensor_id"],

        "rated_power_w":
            appliance["rated_power_w"],

        "status":
            appliance["status"],

        "initialization_status":
            "SUCCESS",

        "created_at":
            created_at
    })


summary_df = pd.DataFrame(summary_rows)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================
# DISPLAY FINAL CONFIGURATION
# ============================================================

print()
print("=" * 70)
print("HOUSE INITIALIZATION COMPLETE")
print("=" * 70)

print()
print("HOUSE")
print("-" * 70)

print(
    f"House ID       : {house_id}"
)

print(
    f"House Name     : {house_name}"
)

print(
    f"Location       : "
    f"{house_location if house_location else 'Not specified'}"
)

print(
    f"Appliances     : "
    f"{len(appliances)}"
)

print()
print("REGISTERED APPLIANCES")
print("-" * 70)

display_columns = [

    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w",
    "status"
]

print(
    appliance_df[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# OUTPUT FILES
# ============================================================

print()
print("=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print()
print(
    "House configuration:"
)

print(
    HOUSE_CONFIG_FILE
)

print()
print(
    "Appliance configuration:"
)

print(
    APPLIANCE_CONFIG_FILE
)

print()
print(
    "Initialization summary:"
)

print(
    SUMMARY_FILE
)

print()
print("=" * 70)
print("MODULE 14A COMPLETE")
print("=" * 70)