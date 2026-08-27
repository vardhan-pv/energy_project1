# ================================================================
# MODULE 14E — DYNAMIC ML/RL MODEL TRAINING
# ================================================================
#
# Architecture:
#   House
#      ↓
#   Appliances
#      ↓
#   Dynamic Features
#      ↓
#   ML/RL Model Training
#      ↓
#   Verified Model Artifacts
#
# IMPORTANT:
# Every saved .pkl model is immediately reloaded and tested.
# A model is NOT considered successfully trained unless:
#   1. pickle.dump() succeeds
#   2. pickle.load() succeeds
#   3. prediction succeeds
#
# ================================================================

import os
import sys
import time
import json
import pickle
import warnings
import traceback

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")


# ================================================================
# CONFIGURATION
# ================================================================

BASE_DIR = r"E:\energy_project"

HOUSE_CONFIG_PATH = os.path.join(
    BASE_DIR,
    "initialization",
    "house_config.json"
)

APPLIANCE_CONFIG_PATH = os.path.join(
    BASE_DIR,
    "initialization",
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


def print_section(title):
    print()
    print("-" * 70)
    print(title)
    print("-" * 70)


def safe_float(value, default=0.0):
    try:
        value = float(value)
        if np.isfinite(value):
            return value
        return default
    except Exception:
        return default


def clean_numeric(series, default=0.0):
    return pd.to_numeric(series, errors="coerce").replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(default)


def normalize_columns(df):
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_")
        for c in df.columns
    ]
    return df


# ================================================================
# MODEL SAVE / LOAD / VALIDATION
# ================================================================

def save_verified_model(model_bundle, model_path, X_test):
    """
    Save model using standard pickle.dump(), then immediately
    reload it and perform a prediction.

    This prevents corrupted/incompatible model files from being
    silently accepted.
    """

    # ------------------------------------------------------------
    # Remove old file
    # ------------------------------------------------------------

    if os.path.exists(model_path):
        try:
            os.remove(model_path)
        except Exception as exc:
            raise RuntimeError(
                f"Could not remove old model file: {exc}"
            )

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------

    try:
        with open(model_path, "wb") as f:
            pickle.dump(
                model_bundle,
                f,
                protocol=pickle.HIGHEST_PROTOCOL
            )

    except Exception as exc:
        raise RuntimeError(
            f"pickle.dump failed: {exc}"
        )

    # ------------------------------------------------------------
    # FILE VALIDATION
    # ------------------------------------------------------------

    if not os.path.exists(model_path):
        raise RuntimeError(
            "Model file was not created."
        )

    file_size = os.path.getsize(model_path)

    if file_size <= 100:
        raise RuntimeError(
            f"Model file is suspiciously small: {file_size} bytes"
        )

    # ------------------------------------------------------------
    # RELOAD
    # ------------------------------------------------------------

    try:
        with open(model_path, "rb") as f:
            loaded_bundle = pickle.load(f)

    except Exception as exc:
        raise RuntimeError(
            f"Model reload failed: {exc}"
        )

    # ------------------------------------------------------------
    # STRUCTURE VALIDATION
    # ------------------------------------------------------------

    if not isinstance(loaded_bundle, dict):
        raise RuntimeError(
            "Reloaded model bundle is not a dictionary."
        )

    required_keys = [
        "model",
        "scaler",
        "feature_names",
        "appliance_id",
        "house_id",
        "model_type"
    ]

    missing_keys = [
        key for key in required_keys
        if key not in loaded_bundle
    ]

    if missing_keys:
        raise RuntimeError(
            f"Reloaded model missing keys: {missing_keys}"
        )

    # ------------------------------------------------------------
    # PREDICTION VALIDATION
    # ------------------------------------------------------------

    try:
        loaded_model = loaded_bundle["model"]
        loaded_scaler = loaded_bundle["scaler"]

        X_scaled = loaded_scaler.transform(X_test)

        prediction = loaded_model.predict(X_scaled)

        if len(prediction) == 0:
            raise RuntimeError(
                "Reloaded model produced zero predictions."
            )

        prediction = np.asarray(prediction, dtype=float)

        if not np.all(np.isfinite(prediction)):
            raise RuntimeError(
                "Reloaded model produced invalid predictions."
            )

    except Exception as exc:
        raise RuntimeError(
            f"Reloaded model prediction failed: {exc}"
        )

    return loaded_bundle, prediction, file_size


# ================================================================
# START
# ================================================================

start_time = time.time()

print_header(
    "MODULE 14E — DYNAMIC ML/RL MODEL TRAINING"
)

print()
print("Architecture:")
print("  House → Appliances → Dynamic Features → Model Training")
print("                         ↓")
print("                 Verified ML/RL Models")


# ================================================================
# CHECK REQUIRED CONFIGURATION
# ================================================================

print_header("CHECKING REQUIRED FILES")

if not os.path.exists(HOUSE_CONFIG_PATH):
    print(
        f"[ERROR] House configuration not found:\n"
        f"{HOUSE_CONFIG_PATH}"
    )
    sys.exit(1)

print(
    f"[OK] House configuration: "
    f"{HOUSE_CONFIG_PATH}"
)

if not os.path.exists(APPLIANCE_CONFIG_PATH):
    print(
        f"[ERROR] Appliance configuration not found:\n"
        f"{APPLIANCE_CONFIG_PATH}"
    )
    sys.exit(1)

print(
    f"[OK] Appliance configuration: "
    f"{APPLIANCE_CONFIG_PATH}"
)


# ================================================================
# LOAD HOUSE CONFIGURATION
# ================================================================

print()
print("Loading house configuration...")

try:
    with open(
        HOUSE_CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        house_config = json.load(f)

except Exception as exc:
    print(f"[ERROR] Could not load house configuration: {exc}")
    sys.exit(1)


# Support several possible configuration structures
house_id = (
    house_config.get("house_id")
    or house_config.get("id")
    or "UNKNOWN_HOUSE"
)

house_name = (
    house_config.get("house_name")
    or house_config.get("name")
    or "Unknown House"
)

location = (
    house_config.get("location")
    or "Unknown"
)

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")
print(f"Location   : {location}")


# ================================================================
# LOAD APPLIANCE CONFIGURATION
# ================================================================

print()
print("Loading appliance configuration...")

try:
    appliances = pd.read_csv(
        APPLIANCE_CONFIG_PATH
    )

except Exception as exc:
    print(
        f"[ERROR] Could not load appliance configuration: {exc}"
    )
    sys.exit(1)

appliances = normalize_columns(appliances)

required_appliance_columns = [
    "appliance_id",
    "appliance_name"
]

for col in required_appliance_columns:
    if col not in appliances.columns:
        print(
            f"[ERROR] Missing appliance configuration column: {col}"
        )
        sys.exit(1)

print(
    f"Registered appliances: {len(appliances)}"
)

display_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]

display_columns = [
    c for c in display_columns
    if c in appliances.columns
]

print()
print(appliances[display_columns].to_string(index=False))


# ================================================================
# HOUSE PATHS
# ================================================================

HOUSE_DIR = os.path.join(
    BASE_DIR,
    "house_data",
    str(house_id)
)

FEATURES_PATH = os.path.join(
    HOUSE_DIR,
    "features",
    "dynamic_features.csv"
)

MODELS_DIR = os.path.join(
    HOUSE_DIR,
    "models"
)

os.makedirs(MODELS_DIR, exist_ok=True)


print_header("HOUSE DATA PATHS")

print(f"House directory : {HOUSE_DIR}")
print(f"Features        : {FEATURES_PATH}")
print(f"Models          : {MODELS_DIR}")


# ================================================================
# CHECK FEATURES
# ================================================================

if not os.path.exists(FEATURES_PATH):
    print(
        f"[ERROR] Dynamic features not found:\n"
        f"{FEATURES_PATH}"
    )
    sys.exit(1)


# ================================================================
# LOAD DYNAMIC FEATURES
# ================================================================

print_header("LOADING DYNAMIC FEATURES")

try:
    features_df = pd.read_csv(
        FEATURES_PATH
    )

except Exception as exc:
    print(
        f"[ERROR] Could not load dynamic features: {exc}"
    )
    sys.exit(1)

features_df = normalize_columns(features_df)

print(
    f"Rows loaded    : {len(features_df)}"
)

print(
    f"Columns loaded : {len(features_df.columns)}"
)


# ================================================================
# MODEL FEATURES
# ================================================================

MODEL_FEATURES = [
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
    "cdi_score"
]


# ================================================================
# VALIDATE MODEL FEATURES
# ================================================================

print()
print("Validating model features...")

missing_features = [
    feature
    for feature in MODEL_FEATURES
    if feature not in features_df.columns
]

if missing_features:
    print(
        "[ERROR] Missing model features:"
    )

    for feature in missing_features:
        print(f"  - {feature}")

    sys.exit(1)

print(
    f"[OK] All {len(MODEL_FEATURES)} model features available."
)


# ================================================================
# CLEAN TRAINING FEATURES
# ================================================================

print()
print("Cleaning training features...")

rows_before_cleaning = len(features_df)

# Ensure appliance ID exists
if "appliance_id" not in features_df.columns:
    print(
        "[ERROR] dynamic_features.csv does not contain "
        "'appliance_id'."
    )
    sys.exit(1)


# Convert model features to numeric
for feature in MODEL_FEATURES:
    features_df[feature] = clean_numeric(
        features_df[feature]
    )


# Remove rows with missing appliance ID
features_df = features_df[
    features_df["appliance_id"].notna()
].copy()


# Remove duplicate rows
features_df = features_df.drop_duplicates().reset_index(
    drop=True
)

rows_after_cleaning = len(features_df)

print(
    f"Rows before cleaning : {rows_before_cleaning}"
)

print(
    f"Rows after cleaning  : {rows_after_cleaning}"
)

print(
    f"Rows removed         : "
    f"{rows_before_cleaning - rows_after_cleaning}"
)


# ================================================================
# VALIDATE DATA
# ================================================================

if len(features_df) == 0:
    print(
        "[ERROR] No training data available after cleaning."
    )
    sys.exit(1)


# ================================================================
# DYNAMIC APPLIANCE MODEL TRAINING
# ================================================================

print_header(
    "DYNAMIC APPLIANCE MODEL TRAINING"
)

training_results = []
registry_results = []

successful_models = 0
failed_models = 0


# ================================================================
# PROCESS EACH REGISTERED APPLIANCE
# ================================================================

for _, appliance in appliances.iterrows():

    appliance_start = time.time()

    appliance_id = str(
        appliance["appliance_id"]
    ).strip()

    appliance_name = str(
        appliance["appliance_name"]
    ).strip()

    appliance_type = str(
        appliance.get(
            "appliance_type",
            "Unknown"
        )
    )

    sensor_id = str(
        appliance.get(
            "sensor_id",
            "Unknown"
        )
    )

    rated_power = safe_float(
        appliance.get(
            "rated_power_w",
            0
        )
    )

    print_header(
        f"PROCESSING: {appliance_name}"
    )

    print(
        f"Appliance ID : {appliance_id}"
    )

    print(
        f"Type         : {appliance_type}"
    )

    print(
        f"Sensor       : {sensor_id}"
    )

    print(
        f"Rated power  : {rated_power:.2f} W"
    )


    # ------------------------------------------------------------
    # SELECT APPLIANCE DATA
    # ------------------------------------------------------------

    appliance_data = features_df[
        features_df["appliance_id"].astype(str).str.strip()
        == appliance_id
    ].copy()

    available_rows = len(appliance_data)

    print(
        f"Available rows: {available_rows}"
    )


    # ------------------------------------------------------------
    # DATA QUALITY
    # ------------------------------------------------------------

    if available_rows < 20:
        data_quality = "DEMO_LOW_DATA"

    elif available_rows < 100:
        data_quality = "LIMITED_DATA"

    else:
        data_quality = "PRODUCTION_READY_DATA"

    print(
        f"Data quality: {data_quality}"
    )


    # ------------------------------------------------------------
    # MINIMUM DATA CHECK
    # ------------------------------------------------------------

    if available_rows < 2:

        print(
            "[ERROR] Not enough rows for model training."
        )

        failed_models += 1

        training_results.append({
            "house_id": house_id,
            "appliance_id": appliance_id,
            "appliance_name": appliance_name,
            "appliance_type": appliance_type,
            "sensor_id": sensor_id,
            "rated_power_w": rated_power,
            "training_samples": available_rows,
            "features": len(MODEL_FEATURES),
            "mae": np.nan,
            "rmse": np.nan,
            "target_mean": np.nan,
            "target_min": np.nan,
            "target_max": np.nan,
            "maintain_actions": 0,
            "reduce_actions": 0,
            "shift_actions": 0,
            "turn_off_actions": 0,
            "data_quality": data_quality,
            "model_status": "FAILED_INSUFFICIENT_DATA"
        })

        continue


    # ------------------------------------------------------------
    # TRAINING MATRIX
    # ------------------------------------------------------------

    X = appliance_data[
        MODEL_FEATURES
    ].copy()

    # ------------------------------------------------------------
    # POLICY-VALUE TARGET
    # ------------------------------------------------------------
    #
    # The target represents an energy-efficiency / policy value.
    # This is a DEMO policy target because the current dataset
    # contains only 10 samples per appliance.
    #
    # Higher power and higher peak risk increase the optimization
    # pressure, while stability and routine behaviour reduce it.
    # ------------------------------------------------------------

    print(
        "Generating policy-value target..."
    )

    power_norm = (
        appliance_data["power_w"]
        /
        max(rated_power, 1.0)
    )

    power_norm = np.clip(
        power_norm,
        0,
        2
    )

    peak_risk = np.clip(
        appliance_data["peak_risk"],
        0,
        1
    )

    anomaly = np.clip(
        appliance_data["anomaly_score"],
        0,
        1
    )

    behavior = np.clip(
        appliance_data["user_behavior_score"],
        0,
        1
    )

    routine = np.clip(
        appliance_data["energy_routine_index"],
        0,
        1
    )

    stability = np.clip(
        appliance_data["stability_score"],
        0,
        1
    )

    change = np.clip(
        appliance_data["change_score"],
        0,
        1
    )

    cdi = np.clip(
        appliance_data["cdi_score"],
        0,
        1
    )

    target = (
        0.30 * power_norm
        + 0.20 * peak_risk
        + 0.10 * anomaly
        + 0.10 * (1.0 - behavior)
        + 0.10 * (1.0 - routine)
        + 0.05 * (1.0 - stability)
        + 0.05 * change
        + 0.10 * cdi
    )

    target = np.asarray(
        target,
        dtype=float
    )

    target = np.nan_to_num(
        target,
        nan=0.0,
        posinf=1.0,
        neginf=0.0
    )

    target = np.clip(
        target,
        0,
        1
    )


    # ------------------------------------------------------------
    # SCALE FEATURES
    # ------------------------------------------------------------

    print(
        "Fitting StandardScaler..."
    )

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(
        X
    )


    # ------------------------------------------------------------
    # RANDOM FOREST
    # ------------------------------------------------------------

    print(
        "Training Random Forest..."
    )

    random_state = 42

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=1,
        random_state=random_state,
        n_jobs=-1
    )

    model.fit(
        X_scaled,
        target
    )


    # ------------------------------------------------------------
    # TRAINING PREDICTIONS
    # ------------------------------------------------------------

    predictions = model.predict(
        X_scaled
    )

    predictions = np.asarray(
        predictions,
        dtype=float
    )

    predictions = np.nan_to_num(
        predictions,
        nan=0.0,
        posinf=1.0,
        neginf=0.0
    )

    predictions = np.clip(
        predictions,
        0,
        1
    )


    # ------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------

    mae = mean_absolute_error(
        target,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            target,
            predictions
        )
    )


    # ------------------------------------------------------------
    # ACTION GENERATION
    # ------------------------------------------------------------

    # 0 = maintain
    # 1 = reduce
    # 2 = shift
    # 3 = turn_off

    actions = []

    for value in target:

        if value < 0.25:
            action = 0

        elif value < 0.50:
            action = 1

        elif value < 0.75:
            action = 2

        else:
            action = 3

        actions.append(action)

    actions = np.asarray(
        actions,
        dtype=int
    )


    maintain_count = int(
        np.sum(actions == 0)
    )

    reduce_count = int(
        np.sum(actions == 1)
    )

    shift_count = int(
        np.sum(actions == 2)
    )

    turn_off_count = int(
        np.sum(actions == 3)
    )


    # ------------------------------------------------------------
    # MODEL BUNDLE
    # ------------------------------------------------------------

    model_bundle = {
        "model": model,
        "scaler": scaler,
        "feature_names": MODEL_FEATURES.copy(),
        "appliance_id": appliance_id,
        "appliance_name": appliance_name,
        "appliance_type": appliance_type,
        "sensor_id": sensor_id,
        "rated_power_w": rated_power,
        "house_id": house_id,
        "house_name": house_name,
        "location": location,
        "model_type": "RandomForestRegressor",
        "model_role": "Dynamic RL Policy Value Estimator",
        "target_type": "Policy Value",
        "action_mapping": {
            0: "maintain",
            1: "reduce",
            2: "shift",
            3: "turn_off"
        },
        "training_samples": int(
            available_rows
        ),
        "data_quality": data_quality,
        "random_state": random_state,
        "module": "14E",
        "policy_version": "v1.0"
    }


    # ------------------------------------------------------------
    # MODEL PATH
    # ------------------------------------------------------------

    model_filename = (
        f"{appliance_id}_rl_agent.pkl"
    )

    model_path = os.path.join(
        MODELS_DIR,
        model_filename
    )


    # ------------------------------------------------------------
    # SAVE + RELOAD + PREDICT VALIDATION
    # ------------------------------------------------------------

    print()
    print(
        "Saving and validating model..."
    )

    try:

        (
            loaded_bundle,
            reload_predictions,
            file_size
        ) = save_verified_model(
            model_bundle,
            model_path,
            X.iloc[:1]
        )

        print(
            f"[OK] Model saved: {model_path}"
        )

        print(
            f"[OK] Model size: {file_size:,} bytes"
        )

        print(
            "[OK] Pickle reload validation passed"
        )

        print(
            "[OK] Prediction validation passed"
        )

        model_status = (
            "TRAINED_VERIFIED_"
            + data_quality
        )

        successful_models += 1

    except Exception as exc:

        print(
            f"[ERROR] Model validation failed: {exc}"
        )

        print(
            "[ERROR] This model will NOT be marked as trained."
        )

        model_status = (
            "FAILED_MODEL_VALIDATION"
        )

        failed_models += 1

        # Remove invalid artifact
        if os.path.exists(model_path):
            try:
                os.remove(model_path)
                print(
                    "[OK] Invalid model artifact removed."
                )
            except Exception:
                pass


    # ------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------

    print()
    print("-" * 70)
    print(
        f"RESULT: {appliance_name}"
    )
    print("-" * 70)

    print(
        f"Training samples: {available_rows}"
    )

    print(
        f"Features: {len(MODEL_FEATURES)}"
    )

    print(
        f"MAE: {mae:.6f}"
    )

    print(
        f"RMSE: {rmse:.6f}"
    )

    print(
        f"Target mean: {np.mean(target):.6f}"
    )

    print(
        f"Target min: {np.min(target):.6f}"
    )

    print(
        f"Target max: {np.max(target):.6f}"
    )

    print(
        f"Action 0 maintain: {maintain_count}"
    )

    print(
        f"Action 1 reduce: {reduce_count}"
    )

    print(
        f"Action 2 shift: {shift_count}"
    )

    print(
        f"Action 3 turn_off: {turn_off_count}"
    )

    print(
        f"Model status: {model_status}"
    )

    print(
        f"Model: {model_path}"
    )

    elapsed = (
        time.time()
        - appliance_start
    ) / 60.0

    print(
        f"Time: {elapsed:.2f} minutes"
    )


    # ------------------------------------------------------------
    # TRAINING SUMMARY RECORD
    # ------------------------------------------------------------

    training_results.append({
        "house_id": house_id,
        "appliance_id": appliance_id,
        "appliance_name": appliance_name,
        "appliance_type": appliance_type,
        "sensor_id": sensor_id,
        "rated_power_w": rated_power,
        "training_samples": available_rows,
        "features": len(MODEL_FEATURES),
        "mae": float(mae),
        "rmse": float(rmse),
        "target_mean": float(np.mean(target)),
        "target_min": float(np.min(target)),
        "target_max": float(np.max(target)),
        "maintain_actions": maintain_count,
        "reduce_actions": reduce_count,
        "shift_actions": shift_count,
        "turn_off_actions": turn_off_count,
        "data_quality": data_quality,
        "model_status": model_status,
        "model_path": model_path,
        "model_file_size_bytes": (
            int(file_size)
            if "file_size" in locals()
            and os.path.exists(model_path)
            else 0
        )
    })


    # ------------------------------------------------------------
    # REGISTRY
    # ------------------------------------------------------------

    registry_results.append({
        "house_id": house_id,
        "appliance_id": appliance_id,
        "appliance_name": appliance_name,
        "appliance_type": appliance_type,
        "sensor_id": sensor_id,
        "rated_power_w": rated_power,
        "model_type": "RandomForestRegressor",
        "model_role": "Dynamic RL Policy Value Estimator",
        "feature_count": len(MODEL_FEATURES),
        "feature_names": "|".join(
            MODEL_FEATURES
        ),
        "model_filename": model_filename,
        "model_path": model_path,
        "training_samples": available_rows,
        "data_quality": data_quality,
        "model_status": model_status,
        "verified": (
            "YES"
            if model_status.startswith(
                "TRAINED_VERIFIED"
            )
            else "NO"
        ),
        "policy_version": "v1.0"
    })


# ================================================================
# GENERATE TRAINING SUMMARY
# ================================================================

print_header(
    "GENERATING TRAINING SUMMARY"
)

training_summary = pd.DataFrame(
    training_results
)

registry_df = pd.DataFrame(
    registry_results
)


TRAINING_SUMMARY_PATH = os.path.join(
    MODELS_DIR,
    "dynamic_training_summary.csv"
)

MODEL_REGISTRY_PATH = os.path.join(
    MODELS_DIR,
    "model_registry.csv"
)


training_summary.to_csv(
    TRAINING_SUMMARY_PATH,
    index=False
)

registry_df.to_csv(
    MODEL_REGISTRY_PATH,
    index=False
)


# ================================================================
# MODULE VALIDATION
# ================================================================

print_header(
    "MODULE 14E VALIDATION"
)

print(
    f"House ID             : {house_id}"
)

print(
    f"Registered appliances: {len(appliances)}"
)

print(
    f"Models trained       : {successful_models}"
)

print(
    f"Models failed        : {failed_models}"
)

print(
    f"Feature count        : {len(MODEL_FEATURES)}"
)


print()
print("MODEL VALIDATION")
print("-" * 70)


# ---------------------------------------------------------------
# Verify every registered appliance
# ---------------------------------------------------------------

all_models_valid = True

for _, appliance in appliances.iterrows():

    appliance_id = str(
        appliance["appliance_id"]
    ).strip()

    appliance_name = str(
        appliance["appliance_name"]
    ).strip()

    model_path = os.path.join(
        MODELS_DIR,
        f"{appliance_id}_rl_agent.pkl"
    )

    if not os.path.exists(model_path):

        print(
            f"[ERROR] Model missing: "
            f"{appliance_name}"
        )

        all_models_valid = False

        continue


    # -----------------------------------------------------------
    # Final independent pickle test
    # -----------------------------------------------------------

    try:

        with open(
            model_path,
            "rb"
        ) as f:

            bundle = pickle.load(f)

        if not isinstance(
            bundle,
            dict
        ):
            raise ValueError(
                "Model bundle is not a dictionary."
            )

        if "model" not in bundle:
            raise ValueError(
                "Missing model."
            )

        if "scaler" not in bundle:
            raise ValueError(
                "Missing scaler."
            )

        if "feature_names" not in bundle:
            raise ValueError(
                "Missing feature names."
            )

        if len(
            bundle["feature_names"]
        ) != len(MODEL_FEATURES):

            raise ValueError(
                "Feature count mismatch."
            )

        print(
            f"[OK] Model verified: "
            f"{appliance_name}"
        )

    except Exception as exc:

        print(
            f"[ERROR] Model verification failed: "
            f"{appliance_name}"
        )

        print(
            f"        {exc}"
        )

        all_models_valid = False


# ---------------------------------------------------------------
# Feature validation
# ---------------------------------------------------------------

if len(MODEL_FEATURES) == 17:

    print(
        "[OK] 17 dynamic RL/ML features"
    )

else:

    print(
        "[ERROR] Unexpected feature count"
    )

    all_models_valid = False


# ---------------------------------------------------------------
# Training summary NULL validation
# ---------------------------------------------------------------

summary_nulls = int(
    training_summary.isnull().sum().sum()
)

if summary_nulls == 0:

    print(
        "[OK] Training summary contains no NULL values."
    )

else:

    print(
        f"[ERROR] Training summary contains "
        f"{summary_nulls} NULL values."
    )

    all_models_valid = False


# ================================================================
# TRAINING RESULTS
# ================================================================

print()
print("TRAINING RESULTS")
print("-" * 70)

result_columns = [
    "appliance_name",
    "training_samples",
    "features",
    "mae",
    "rmse",
    "data_quality",
    "model_status"
]

result_columns = [
    c
    for c in result_columns
    if c in training_summary.columns
]

if len(training_summary) > 0:

    print(
        training_summary[
            result_columns
        ].to_string(index=False)
    )


# ================================================================
# FINAL STATUS
# ================================================================

elapsed_total = (
    time.time()
    - start_time
) / 60.0


print_header(
    "MODULE 14E COMPLETE"
)

print(
    f"House ID            : {house_id}"
)

print(
    f"House Name          : {house_name}"
)

print(
    f"Appliances          : {len(appliances)}"
)

print(
    f"Models trained      : {successful_models}"
)

print(
    f"Models failed       : {failed_models}"
)

print(
    f"Features per model  : {len(MODEL_FEATURES)}"
)


if (
    successful_models == len(appliances)
    and failed_models == 0
    and all_models_valid
):

    system_status = "DYNAMIC_MODELS_READY"

else:

    system_status = "MODEL_VALIDATION_FAILED"


print(
    f"System status       : {system_status}"
)

print(
    f"Total time           : {elapsed_total:.2f} minutes"
)


print()
print("Training summary:")
print(
    TRAINING_SUMMARY_PATH
)

print()
print("Model registry:")
print(
    MODEL_REGISTRY_PATH
)

print()
print("Model directory:")
print(
    MODELS_DIR
)


# ================================================================
# FINAL HARD FAILURE IF MODELS ARE INVALID
# ================================================================

if system_status != "DYNAMIC_MODELS_READY":

    print()
    print(
        "=" * 70
    )

    print(
        "[ERROR] MODULE 14E FAILED FINAL MODEL VALIDATION."
    )

    print(
        "[ERROR] Do NOT run Module 14F yet."
    )

    print(
        "=" * 70
    )

    sys.exit(2)


print()
print(
    "=" * 70
)

print(
    "[SUCCESS] MODULE 14E COMPLETED."
)

print(
    "[SUCCESS] All model files were saved, reloaded and validated."
)

print(
    "[SUCCESS] Module 14F can now use the verified models."
)

print(
    "=" * 70
)