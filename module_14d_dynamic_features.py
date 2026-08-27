import os
import json
import sqlite3
import time
import numpy as np
import pandas as pd


# ============================================================
# MODULE 14D — DYNAMIC DATA CLEANING & FEATURE ENGINEERING
# ============================================================

START_TIME = time.time()

BASE_DIR = r"E:\energy_project"

INIT_DIR = os.path.join(BASE_DIR, "initialization")
HOUSE_DATA_DIR = os.path.join(BASE_DIR, "house_data")

HOUSE_CONFIG = os.path.join(INIT_DIR, "house_config.json")
APPLIANCE_CONFIG = os.path.join(INIT_DIR, "appliance_config.csv")


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 14D — DYNAMIC DATA CLEANING & FEATURE ENGINEERING")
print("=" * 70)


# ============================================================
# CHECK INPUT FILES
# ============================================================

print("\nChecking required files...")
print("-" * 70)

if not os.path.exists(HOUSE_CONFIG):
    raise FileNotFoundError(
        f"House configuration not found:\n{HOUSE_CONFIG}"
    )

if not os.path.exists(APPLIANCE_CONFIG):
    raise FileNotFoundError(
        f"Appliance configuration not found:\n{APPLIANCE_CONFIG}"
    )

print(f"[OK] House configuration: {HOUSE_CONFIG}")
print(f"[OK] Appliance configuration: {APPLIANCE_CONFIG}")


# ============================================================
# LOAD HOUSE CONFIGURATION
# ============================================================

print("\nLoading house configuration...")

with open(HOUSE_CONFIG, "r", encoding="utf-8") as f:
    house = json.load(f)

house_id = house["house_id"]
house_name = house.get("house_name", "")
location = house.get("location", "")

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")
print(f"Location   : {location}")


# ============================================================
# LOAD APPLIANCE CONFIGURATION
# ============================================================

print("\nLoading appliance configuration...")

appliances = pd.read_csv(APPLIANCE_CONFIG)

required_appliance_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w",
]

missing = [
    c for c in required_appliance_columns
    if c not in appliances.columns
]

if missing:
    raise ValueError(
        f"Missing appliance configuration columns: {missing}"
    )

print(f"Registered appliances: {len(appliances)}")

print("\nREGISTERED APPLIANCES")
print("-" * 70)

print(
    appliances[
        required_appliance_columns
    ].to_string(index=False)
)


# ============================================================
# HOUSE DIRECTORIES
# ============================================================

HOUSE_DIR = os.path.join(HOUSE_DATA_DIR, house_id)

RAW_DIR = os.path.join(HOUSE_DIR, "raw")
PROCESSED_DIR = os.path.join(HOUSE_DIR, "processed")
FEATURE_DIR = os.path.join(HOUSE_DIR, "features")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FEATURE_DIR, exist_ok=True)

DATABASE = os.path.join(
    HOUSE_DIR,
    f"{house_id}.db"
)

RAW_CSV = os.path.join(
    RAW_DIR,
    "raw_energy_data.csv"
)

CLEAN_CSV = os.path.join(
    PROCESSED_DIR,
    "clean_energy_data.csv"
)

FEATURE_CSV = os.path.join(
    FEATURE_DIR,
    "dynamic_features.csv"
)

SUMMARY_CSV = os.path.join(
    FEATURE_DIR,
    "feature_engineering_summary.csv"
)


print("\nHOUSE DATA PATHS")
print("-" * 70)
print(f"House directory : {HOUSE_DIR}")
print(f"Database        : {DATABASE}")
print(f"Raw CSV         : {RAW_CSV}")
print(f"Clean CSV       : {CLEAN_CSV}")
print(f"Features        : {FEATURE_CSV}")


# ============================================================
# LOAD RAW DATA
# ============================================================

print("\nLoading raw energy data...")
print("-" * 70)

if os.path.exists(RAW_CSV):

    print("Using raw CSV...")
    raw = pd.read_csv(RAW_CSV)

elif os.path.exists(DATABASE):

    print("Raw CSV not found.")
    print("Reading raw data from SQLite database...")

    conn = sqlite3.connect(DATABASE)

    raw = pd.read_sql_query(
        "SELECT * FROM raw_energy",
        conn
    )

    conn.close()

else:

    raise FileNotFoundError(
        "Neither raw CSV nor house database was found."
    )


print(f"Raw rows loaded: {len(raw):,}")
print(f"Raw columns: {len(raw.columns)}")

print("\nRAW COLUMNS")
print("-" * 70)
print(raw.columns.tolist())


# ============================================================
# STANDARDIZE COLUMN NAMES
# ============================================================

raw.columns = [
    str(c).strip().lower()
    for c in raw.columns
]


# ============================================================
# COLUMN MAPPING
# ============================================================

COLUMN_ALIASES = {

    "timestamp": [
        "timestamp",
        "datetime",
        "time",
        "date_time",
        "recorded_at"
    ],

    "appliance_id": [
        "appliance_id",
        "appliance",
        "device_id"
    ],

    "power_w": [
        "power_w",
        "power",
        "watts",
        "watt",
        "active_power_w"
    ],

    "voltage_v": [
        "voltage_v",
        "voltage"
    ],

    "current_a": [
        "current_a",
        "current",
        "amps",
        "ampere"
    ],

    "energy_kwh": [
        "energy_kwh",
        "energy"
    ],

    "temperature_c": [
        "temperature_c",
        "temperature",
        "temp"
    ],

    "humidity_pct": [
        "humidity_pct",
        "humidity"
    ],

    "status": [
        "status",
        "state"
    ]
}


def find_column(df, aliases):

    for alias in aliases:

        if alias in df.columns:
            return alias

    return None


# ============================================================
# STANDARDIZE DATA COLUMNS
# ============================================================

print("\nMapping energy columns...")

mapping = {}

for standard_name, aliases in COLUMN_ALIASES.items():

    found = find_column(raw, aliases)

    if found:
        mapping[standard_name] = found
        print(f"[OK] {standard_name:<18} <- {found}")
    else:
        print(f"[INFO] {standard_name:<18} not available")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

if "timestamp" not in mapping:
    raise ValueError(
        "Timestamp column is required."
    )

if "appliance_id" not in mapping:
    raise ValueError(
        "Appliance ID column is required."
    )

if "power_w" not in mapping:
    raise ValueError(
        "Power column is required."
    )


# ============================================================
# CREATE STANDARDIZED DATAFRAME
# ============================================================

df = pd.DataFrame()

for standard_name, source_name in mapping.items():

    df[standard_name] = raw[source_name]


# ============================================================
# TIMESTAMP CONVERSION
# ============================================================

print("\nConverting timestamps...")

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

invalid_timestamp = df["timestamp"].isna().sum()

print(
    f"Invalid timestamps: {invalid_timestamp:,}"
)


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [
    "power_w",
    "voltage_v",
    "current_a",
    "energy_kwh",
    "temperature_c",
    "humidity_pct",
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# APPLIANCE VALIDATION
# ============================================================

print("\nValidating appliances...")

valid_appliance_ids = set(
    appliances["appliance_id"].astype(str)
)

df["appliance_id"] = (
    df["appliance_id"]
    .astype(str)
    .str.strip()
)

unknown_appliances = (
    ~df["appliance_id"].isin(valid_appliance_ids)
).sum()

print(
    f"Unknown appliance records: "
    f"{unknown_appliances:,}"
)


# ============================================================
# REMOVE INVALID RECORDS
# ============================================================

before_cleaning = len(df)

df = df[
    df["timestamp"].notna()
]

df = df[
    df["appliance_id"].isin(valid_appliance_ids)
]

df = df[
    df["power_w"].notna()
]

# Negative power is invalid for this pipeline.
df = df[
    df["power_w"] >= 0
]

after_cleaning = len(df)

removed_rows = (
    before_cleaning - after_cleaning
)


print("\nCLEANING RESULTS")
print("-" * 70)
print(f"Rows before cleaning : {before_cleaning:,}")
print(f"Rows after cleaning  : {after_cleaning:,}")
print(f"Rows removed         : {removed_rows:,}")


# ============================================================
# SORT DATA
# ============================================================

df = df.sort_values(
    ["appliance_id", "timestamp"]
).reset_index(drop=True)


# ============================================================
# ADD APPLIANCE INFORMATION
# ============================================================

print("\nJoining appliance metadata...")

metadata = appliances[
    [
        "appliance_id",
        "appliance_name",
        "appliance_type",
        "sensor_id",
        "rated_power_w",
    ]
].copy()

metadata["appliance_id"] = (
    metadata["appliance_id"]
    .astype(str)
)

df = df.merge(
    metadata,
    on="appliance_id",
    how="left"
)


# ============================================================
# ENERGY CALCULATION
# ============================================================

print("\nCalculating energy...")

if "energy_kwh" not in df.columns:

    print(
        "[INFO] Energy column not available."
    )

    # Calculate energy from elapsed time.
    df["time_diff_seconds"] = (
        df.groupby("appliance_id")["timestamp"]
        .diff()
        .dt.total_seconds()
    )

    # Prevent unreasonable time intervals.
    df["time_diff_seconds"] = (
        df["time_diff_seconds"]
        .fillna(0)
        .clip(lower=0, upper=3600)
    )

    df["energy_kwh"] = (
        df["power_w"]
        * df["time_diff_seconds"]
        / 3_600_000
    )

else:

    df["energy_kwh"] = (
        df["energy_kwh"]
        .fillna(0)
        .clip(lower=0)
    )


# ============================================================
# TIME FEATURES
# ============================================================

print("\nGenerating time features...")

df["hour"] = (
    df["timestamp"].dt.hour
)

df["minute"] = (
    df["timestamp"].dt.minute
)

df["day"] = (
    df["timestamp"].dt.day
)

df["day_of_week"] = (
    df["timestamp"].dt.dayofweek
)

df["is_weekend"] = (
    df["day_of_week"] >= 5
).astype(int)

df["month"] = (
    df["timestamp"].dt.month
)

df["day_of_year"] = (
    df["timestamp"].dt.dayofyear
)


# ============================================================
# POWER STATUS
# ============================================================

df["status"] = np.where(
    df["power_w"] > 0,
    "on",
    "off"
)


# ============================================================
# LAG FEATURES
# ============================================================

print("\nGenerating lag features...")

grouped = df.groupby(
    "appliance_id",
    group_keys=False
)

df["power_lag_1"] = grouped[
    "power_w"
].shift(1)

df["power_lag_5"] = grouped[
    "power_w"
].shift(5)

df["power_lag_10"] = grouped[
    "power_w"
].shift(10)


# ============================================================
# ROLLING FEATURES
# ============================================================

print("Generating rolling features...")

df["power_rolling_mean"] = (
    grouped["power_w"]
    .transform(
        lambda x:
        x.rolling(
            window=5,
            min_periods=1
        ).mean()
    )
)

df["power_rolling_std"] = (
    grouped["power_w"]
    .transform(
        lambda x:
        x.rolling(
            window=5,
            min_periods=1
        ).std()
    )
)

df["power_rolling_max"] = (
    grouped["power_w"]
    .transform(
        lambda x:
        x.rolling(
            window=5,
            min_periods=1
        ).max()
    )
)

df["power_rolling_min"] = (
    grouped["power_w"]
    .transform(
        lambda x:
        x.rolling(
            window=5,
            min_periods=1
        ).min()
    )
)


# ============================================================
# POWER CHANGE
# ============================================================

df["power_change"] = (
    grouped["power_w"]
    .diff()
    .fillna(0)
)

df["power_change_abs"] = (
    df["power_change"]
    .abs()
)


# ============================================================
# LOAD RATIO
# ============================================================

df["load_ratio"] = np.where(
    df["rated_power_w"] > 0,
    df["power_w"] /
    df["rated_power_w"],
    0
)

df["load_ratio"] = (
    df["load_ratio"]
    .clip(lower=0)
)


# ============================================================
# OVERLOAD INDICATOR
# ============================================================

df["overload_flag"] = (
    df["power_w"] >
    df["rated_power_w"]
).astype(int)


# ============================================================
# PEAK RISK
# ============================================================

df["peak_risk"] = (
    df["load_ratio"]
    .clip(0, 1)
)


# ============================================================
# ANOMALY SCORE
# ============================================================

print("Calculating anomaly scores...")

rolling_mean = (
    df["power_rolling_mean"]
    .replace(0, np.nan)
)

rolling_std = (
    df["power_rolling_std"]
    .fillna(0)
)

df["anomaly_score"] = (
    (
        df["power_w"] -
        rolling_mean
    ).abs()
    /
    (
        rolling_std + 1e-6
    )
)

df["anomaly_score"] = (
    df["anomaly_score"]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .fillna(0)
)

# Normalize to a practical range.
df["anomaly_score"] = (
    df["anomaly_score"]
    .clip(0, 10)
    / 10
)


# ============================================================
# BEHAVIOR FEATURES
# ============================================================

df["user_behavior_score"] = (
    100 *
    (
        1 -
        (
            df["power_change_abs"] /
            (
                df["power_rolling_mean"]
                + 1e-6
            )
        ).clip(0, 1)
    )
)

df["user_behavior_score"] = (
    df["user_behavior_score"]
    .clip(0, 100)
)


df["energy_routine_index"] = (
    df.groupby(
        ["appliance_id", "hour"]
    )["power_w"]
    .transform("mean")
)


# ============================================================
# STABILITY SCORE
# ============================================================

df["stability_score"] = (
    1 -
    (
        df["power_rolling_std"] /
        (
            df["power_rolling_mean"]
            + 1e-6
        )
    ).clip(0, 1)
)

df["stability_score"] = (
    df["stability_score"]
    .clip(0, 1)
)


# ============================================================
# CHANGE SCORE
# ============================================================

df["change_score"] = (
    df["power_change_abs"] /
    (
        df["power_rolling_mean"]
        + 1e-6
    )
)

df["change_score"] = (
    df["change_score"]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .fillna(0)
    .clip(0, 1)
)


# ============================================================
# DSC SCORE
# ============================================================

df["dsc_score"] = (
    (
        df["stability_score"]
        +
        (1 - df["change_score"])
    )
    / 2
)


# ============================================================
# CDI SCORE
# ============================================================

df["cdi_score"] = (
    (
        df["peak_risk"]
        +
        df["anomaly_score"]
        +
        df["change_score"]
    )
    / 3
)


# ============================================================
# FINAL CLEANUP
# ============================================================

print("\nFinalizing feature dataset...")

numeric_features = df.select_dtypes(
    include=[np.number]
).columns

df[numeric_features] = (
    df[numeric_features]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
)

df[numeric_features] = (
    df[numeric_features]
    .fillna(0)
)


# ============================================================
# FEATURE VALIDATION
# ============================================================

required_features = [
    "power_w",
    "energy_kwh",
    "hour",
    "day_of_week",
    "is_weekend",
    "power_lag_1",
    "power_lag_5",
    "power_rolling_mean",
    "power_rolling_max",
    "anomaly_score",
    "peak_risk",
    "user_behavior_score",
    "energy_routine_index",
    "dsc_score",
    "stability_score",
    "change_score",
    "cdi_score",
]


missing_features = [
    c for c in required_features
    if c not in df.columns
]

if missing_features:

    raise ValueError(
        f"Missing required features: "
        f"{missing_features}"
    )


# ============================================================
# SAVE CLEAN DATA
# ============================================================

print("\nSaving clean data...")

df.to_csv(
    CLEAN_CSV,
    index=False
)

print(
    f"[OK] Clean data saved:\n{CLEAN_CSV}"
)


# ============================================================
# SAVE FEATURE DATA
# ============================================================

df.to_csv(
    FEATURE_CSV,
    index=False
)

print(
    f"[OK] Dynamic features saved:\n{FEATURE_CSV}"
)


# ============================================================
# FEATURE SUMMARY
# ============================================================

print("\nGenerating feature summary...")

summary_rows = []

for appliance_id, group in df.groupby(
    "appliance_id"
):

    appliance_name = (
        group["appliance_name"]
        .iloc[0]
    )

    summary_rows.append({

        "house_id":
            house_id,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "rows":
            len(group),

        "total_energy_kwh":
            group["energy_kwh"].sum(),

        "average_power_w":
            group["power_w"].mean(),

        "maximum_power_w":
            group["power_w"].max(),

        "average_peak_risk":
            group["peak_risk"].mean(),

        "average_anomaly_score":
            group["anomaly_score"].mean(),

        "average_behavior_score":
            group["user_behavior_score"].mean(),

        "overload_rows":
            group["overload_flag"].sum(),

    })


summary = pd.DataFrame(
    summary_rows
)

summary.to_csv(
    SUMMARY_CSV,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("MODULE 14D VALIDATION")
print("=" * 70)

print(
    f"\nHouse ID              : {house_id}"
)

print(
    f"Appliances processed  : "
    f"{df['appliance_id'].nunique()}"
)

print(
    f"Rows processed        : "
    f"{len(df):,}"
)

print(
    f"Feature columns       : "
    f"{len(required_features)}"
)

print(
    f"Total columns         : "
    f"{len(df.columns)}"
)

print(
    f"Removed rows          : "
    f"{removed_rows:,}"
)

print(
    f"Final NULL values     : "
    f"{df.isna().sum().sum():,}"
)

print(
    f"Duplicate rows        : "
    f"{df.duplicated().sum():,}"
)


print("\nFEATURE VALIDATION")
print("-" * 70)

for feature in required_features:

    print(
        f"[OK] {feature}"
    )


print("\nENERGY SUMMARY")
print("-" * 70)

display_columns = [
    "appliance_id",
    "appliance_name",
    "rows",
    "total_energy_kwh",
    "average_power_w",
    "maximum_power_w",
    "average_peak_risk",
    "average_anomaly_score",
]

print(
    summary[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# FINAL VALIDATION
# ============================================================

assert len(df) > 0

assert df[
    "timestamp"
].notna().all()

assert df[
    "appliance_id"
].isin(
    valid_appliance_ids
).all()

assert df[
    "power_w"
].ge(0).all()

assert df[
    required_features
].isna().sum().sum() == 0


print("\n[OK] All final validations passed.")


# ============================================================
# COMPLETION
# ============================================================

elapsed = (
    time.time() -
    START_TIME
) / 60


print("\n" + "=" * 70)
print("MODULE 14D COMPLETE")
print("=" * 70)

print("\nOUTPUT FILES")
print("-" * 70)

print(
    f"Clean data:\n{CLEAN_CSV}"
)

print(
    f"\nDynamic features:\n{FEATURE_CSV}"
)

print(
    f"\nFeature summary:\n{SUMMARY_CSV}"
)

print(
    f"\nProcessing time: "
    f"{elapsed:.2f} minutes"
)

print("=" * 70)