import os
import json
import time
import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error


# ============================================================
# MODULE 14F — DYNAMIC RL POLICY OPTIMIZATION
# ============================================================

START_TIME = time.time()

BASE_DIR = r"E:\energy_project"

INIT_DIR = os.path.join(BASE_DIR, "initialization")
HOUSE_DATA_DIR = os.path.join(BASE_DIR, "house_data")

HOUSE_CONFIG_FILE = os.path.join(
    INIT_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG_FILE = os.path.join(
    INIT_DIR,
    "appliance_config.csv"
)


# ============================================================
# LOAD HOUSE CONFIGURATION
# ============================================================

print("=" * 70)
print("MODULE 14F — DYNAMIC RL POLICY OPTIMIZATION")
print("=" * 70)

print()
print("=" * 70)
print("CHECKING REQUIRED FILES")
print("=" * 70)

if not os.path.exists(HOUSE_CONFIG_FILE):
    raise FileNotFoundError(
        f"House configuration not found:\n{HOUSE_CONFIG_FILE}"
    )

if not os.path.exists(APPLIANCE_CONFIG_FILE):
    raise FileNotFoundError(
        f"Appliance configuration not found:\n{APPLIANCE_CONFIG_FILE}"
    )

print(f"[OK] House configuration: {HOUSE_CONFIG_FILE}")
print(f"[OK] Appliance configuration: {APPLIANCE_CONFIG_FILE}")


# ============================================================
# READ HOUSE CONFIG
# ============================================================

print()
print("Loading house configuration...")

with open(HOUSE_CONFIG_FILE, "r", encoding="utf-8") as f:
    house_config = json.load(f)

house_id = house_config.get("house_id")
house_name = house_config.get("house_name", "Unknown House")
location = house_config.get("location", "")

if not house_id:
    raise ValueError("house_id missing from house_config.json")

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")
print(f"Location   : {location}")


# ============================================================
# LOAD APPLIANCE CONFIG
# ============================================================

print()
print("Loading appliance configuration...")

appliances = pd.read_csv(APPLIANCE_CONFIG_FILE)

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
        f"Missing appliance columns: {missing}"
    )

print(f"Registered appliances: {len(appliances)}")

print()
print(
    appliances[
        required_appliance_columns
    ].to_string(index=False)
)


# ============================================================
# HOUSE PATHS
# ============================================================

HOUSE_DIR = os.path.join(
    HOUSE_DATA_DIR,
    house_id
)

FEATURE_FILE = os.path.join(
    HOUSE_DIR,
    "features",
    "dynamic_features.csv"
)

MODEL_DIR = os.path.join(
    HOUSE_DIR,
    "models"
)

OPTIMIZATION_DIR = os.path.join(
    HOUSE_DIR,
    "optimization"
)

os.makedirs(OPTIMIZATION_DIR, exist_ok=True)

print()
print("=" * 70)
print("HOUSE DATA PATHS")
print("=" * 70)

print(f"House directory : {HOUSE_DIR}")
print(f"Features        : {FEATURE_FILE}")
print(f"Models          : {MODEL_DIR}")
print(f"Optimization    : {OPTIMIZATION_DIR}")


# ============================================================
# CHECK FEATURES
# ============================================================

if not os.path.exists(FEATURE_FILE):
    raise FileNotFoundError(
        f"Dynamic feature file not found:\n{FEATURE_FILE}"
    )

if not os.path.exists(MODEL_DIR):
    raise FileNotFoundError(
        f"Model directory not found:\n{MODEL_DIR}"
    )


# ============================================================
# LOAD DYNAMIC FEATURES
# ============================================================

print()
print("=" * 70)
print("LOADING DYNAMIC FEATURES")
print("=" * 70)

features_df = pd.read_csv(FEATURE_FILE)

print(f"Rows loaded    : {len(features_df)}")
print(f"Columns loaded : {len(features_df.columns)}")


# ============================================================
# MODEL FEATURES
# ============================================================

MODEL_FEATURES = [
    "power_w",
    "voltage_v",
    "current_a",
    "energy_kwh",
    "temperature_c",
    "humidity_pct",
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
    "energy_routine_index"
]

print()
print("Validating model features...")

missing_features = [
    c for c in MODEL_FEATURES
    if c not in features_df.columns
]

if missing_features:
    raise ValueError(
        f"Missing model features: {missing_features}"
    )

print(
    f"[OK] All {len(MODEL_FEATURES)} dynamic RL features available."
)


# ============================================================
# CLEAN FEATURES
# ============================================================

print()
print("Cleaning optimization features...")

before_rows = len(features_df)

features_df = features_df.replace(
    [np.inf, -np.inf],
    np.nan
)

features_df[MODEL_FEATURES] = (
    features_df[MODEL_FEATURES]
    .apply(pd.to_numeric, errors="coerce")
)

features_df = features_df.dropna(
    subset=MODEL_FEATURES
).copy()

after_rows = len(features_df)

print(f"Rows before cleaning : {before_rows}")
print(f"Rows after cleaning  : {after_rows}")
print(f"Rows removed         : {before_rows - after_rows}")


# ============================================================
# ACTION DEFINITIONS
# ============================================================

ACTION_NAMES = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}


# ============================================================
# OPTIMIZATION FUNCTIONS
# ============================================================

def calculate_action_value(
    model,
    feature_vector,
    current_power,
    rated_power,
    peak_risk,
    anomaly_score
):
    """
    Generate a policy value from the trained RandomForest model.

    The existing 14E models predict a policy-value style target.
    The value is combined with energy-saving heuristics so that
    the optimizer can make a dynamic action recommendation.
    """

    try:
        prediction = model.predict(
            feature_vector.reshape(1, -1)
        )[0]

        prediction = float(prediction)

    except Exception:
        prediction = 0.0

    # Normalize loading relative to appliance rated power
    if rated_power and rated_power > 0:
        load_ratio = current_power / rated_power
    else:
        load_ratio = 0.0

    load_ratio = float(
        np.clip(load_ratio, 0.0, 2.0)
    )

    peak_risk = float(
        np.clip(peak_risk, 0.0, 1.0)
    )

    anomaly_score = float(
        np.clip(anomaly_score, 0.0, 1.0)
    )

    # --------------------------------------------------------
    # Dynamic action scoring
    # --------------------------------------------------------

    scores = {
        0: prediction,
        1: prediction,
        2: prediction,
        3: prediction
    }

    # Maintain
    scores[0] += 0.10

    # Reduce becomes attractive when load is significant
    scores[1] += (
        0.35 * load_ratio
        + 0.25 * peak_risk
    )

    # Shift becomes attractive when peak risk is high
    scores[2] += (
        0.30 * peak_risk
        + 0.10 * anomaly_score
    )

    # Turn off becomes attractive for high load + anomaly
    scores[3] += (
        0.35 * load_ratio
        + 0.25 * anomaly_score
    )

    # --------------------------------------------------------
    # Safety rules
    # --------------------------------------------------------

    # If appliance is effectively off, maintain.
    if current_power <= 0.01:
        scores[0] += 2.0

    # Do not recommend turn-off for very small loads.
    if load_ratio < 0.10:
        scores[3] -= 1.0

    # Avoid aggressive action for very low peak risk.
    if peak_risk < 0.10:
        scores[2] -= 0.5

    best_action = max(
        scores,
        key=scores.get
    )

    return int(best_action), prediction, scores


# ============================================================
# PROCESS APPLIANCES
# ============================================================

print()
print("=" * 70)
print("DYNAMIC RL POLICY OPTIMIZATION")
print("=" * 70)

all_results = []
summary_results = []

for _, appliance in appliances.iterrows():

    appliance_id = str(
        appliance["appliance_id"]
    )

    appliance_name = str(
        appliance["appliance_name"]
    )

    appliance_type = str(
        appliance["appliance_type"]
    )

    sensor_id = str(
        appliance["sensor_id"]
    )

    rated_power = float(
        appliance["rated_power_w"]
    )

    print()
    print("=" * 70)
    print(
        f"PROCESSING: {appliance_name}"
    )
    print("=" * 70)

    print(f"Appliance ID : {appliance_id}")
    print(f"Type         : {appliance_type}")
    print(f"Sensor       : {sensor_id}")
    print(f"Rated power  : {rated_power:.2f} W")

    # --------------------------------------------------------
    # Select appliance data
    # --------------------------------------------------------

    if "appliance_id" in features_df.columns:

        appliance_data = features_df[
            features_df["appliance_id"].astype(str)
            == appliance_id
        ].copy()

    elif "appliance_name" in features_df.columns:

        appliance_data = features_df[
            features_df["appliance_name"].astype(str)
            == appliance_name
        ].copy()

    else:
        raise ValueError(
            "dynamic_features.csv must contain appliance_id "
            "or appliance_name."
        )

    print(
        f"Available rows: {len(appliance_data)}"
    )

    if len(appliance_data) == 0:

        print(
            "[WARNING] No feature data available. Skipping."
        )

        continue

    # --------------------------------------------------------
    # Locate model
    # --------------------------------------------------------

    model_file = os.path.join(
        MODEL_DIR,
        f"{appliance_id}_rl_agent.pkl"
    )

    if not os.path.exists(model_file):

        print(
            f"[WARNING] Model not found: {model_file}"
        )

        continue

    print(
        f"Model: {model_file}"
    )

    package = joblib.load(model_file)

    if isinstance(package, dict):

        model = package.get("model")

        stored_features = package.get(
            "features",
            MODEL_FEATURES
        )

    else:

        model = package
        stored_features = MODEL_FEATURES

    if model is None:
        raise ValueError(
            f"Invalid model package: {model_file}"
        )

    print(
        f"Model type: {type(model).__name__}"
    )

    print(
        f"Stored feature count: {len(stored_features)}"
    )

    # --------------------------------------------------------
    # Handle models trained with the same 17 features
    # --------------------------------------------------------

    usable_features = []

    for feature in stored_features:

        if feature in appliance_data.columns:
            usable_features.append(feature)

    # Some 14E model packages may contain action.
    # Action is NOT an input for dynamic optimization.
    usable_features = [
        f for f in usable_features
        if f != "action"
    ]

    if len(usable_features) != len(MODEL_FEATURES):

        missing_model_features = [
            f for f in MODEL_FEATURES
            if f not in appliance_data.columns
        ]

        if missing_model_features:
            raise ValueError(
                f"Missing features for {appliance_name}: "
                f"{missing_model_features}"
            )

        usable_features = MODEL_FEATURES

    # --------------------------------------------------------
    # DEMO DATA FLAG
    # --------------------------------------------------------

    if len(appliance_data) < 1000:
        data_quality = "DEMO_LOW_DATA"
    else:
        data_quality = "PRODUCTION_DATA"

    # --------------------------------------------------------
    # Create optimization records
    # --------------------------------------------------------

    appliance_results = []

    for index, row in appliance_data.iterrows():

        x = row[
            usable_features
        ].astype(float).values

        current_power = float(
            row.get("power_w", 0.0)
        )

        peak_risk = float(
            row.get("peak_risk", 0.0)
        )

        anomaly_score = float(
            row.get("anomaly_score", 0.0)
        )

        action, prediction, action_scores = (
            calculate_action_value(
                model=model,
                feature_vector=x,
                current_power=current_power,
                rated_power=rated_power,
                peak_risk=peak_risk,
                anomaly_score=anomaly_score
            )
        )

        # ----------------------------------------------------
        # Energy optimization factors
        # ----------------------------------------------------

        reduction_factor = {
            0: 1.00,
            1: 0.85,
            2: 0.90,
            3: 0.00
        }[action]

        original_energy = float(
            row.get("energy_kwh", 0.0)
        )

        optimized_energy = (
            original_energy
            * reduction_factor
        )

        estimated_saving = (
            original_energy
            - optimized_energy
        )

        result = row.to_dict()

        result.update({
            "house_id": house_id,
            "appliance_name": appliance_name,
            "appliance_type": appliance_type,
            "sensor_id": sensor_id,
            "rated_power_w": rated_power,

            "rl_prediction": prediction,

            "maintain_score":
                float(action_scores[0]),

            "reduce_score":
                float(action_scores[1]),

            "shift_score":
                float(action_scores[2]),

            "turn_off_score":
                float(action_scores[3]),

            "recommended_action":
                action,

            "recommended_action_name":
                ACTION_NAMES[action],

            "original_energy_kwh":
                original_energy,

            "optimized_energy_kwh":
                optimized_energy,

            "estimated_savings_kwh":
                estimated_saving,

            "data_quality":
                data_quality
        })

        appliance_results.append(result)

    # --------------------------------------------------------
    # Convert to DataFrame
    # --------------------------------------------------------

    appliance_results_df = pd.DataFrame(
        appliance_results
    )

    all_results.extend(
        appliance_results
    )

    # --------------------------------------------------------
    # Action counts
    # --------------------------------------------------------

    action_counts = {
        action: int(
            (
                appliance_results_df[
                    "recommended_action"
                ] == action
            ).sum()
        )
        for action in range(4)
    }

    # --------------------------------------------------------
    # Energy summary
    # --------------------------------------------------------

    original_energy_total = float(
        appliance_results_df[
            "original_energy_kwh"
        ].sum()
    )

    optimized_energy_total = float(
        appliance_results_df[
            "optimized_energy_kwh"
        ].sum()
    )

    savings_total = (
        original_energy_total
        - optimized_energy_total
    )

    if original_energy_total > 0:

        savings_percentage = (
            savings_total
            / original_energy_total
            * 100
        )

    else:

        savings_percentage = 0.0

    # --------------------------------------------------------
    # Prediction metrics
    # --------------------------------------------------------

    predictions = appliance_results_df[
        "rl_prediction"
    ].values

    target_values = appliance_data[
        "power_w"
    ].astype(float).values

    # Scale power to a stable policy target
    if rated_power > 0:

        target_policy = np.clip(
            target_values / rated_power,
            0,
            2
        )

    else:

        target_policy = np.zeros(
            len(target_values)
        )

    try:

        mae = mean_absolute_error(
            target_policy,
            predictions
        )

        rmse = np.sqrt(
            mean_squared_error(
                target_policy,
                predictions
            )
        )

    except Exception:

        mae = np.nan
        rmse = np.nan

    # --------------------------------------------------------
    # Optimization confidence
    # --------------------------------------------------------

    action_score_matrix = (
        appliance_results_df[
            [
                "maintain_score",
                "reduce_score",
                "shift_score",
                "turn_off_score"
            ]
        ].values
    )

    score_sorted = np.sort(
        action_score_matrix,
        axis=1
    )

    if len(score_sorted) > 0:

        margin = (
            score_sorted[:, -1]
            - score_sorted[:, -2]
        )

        confidence = (
            50
            + 50
            * np.tanh(
                np.mean(margin)
            )
        )

    else:

        confidence = 0.0

    confidence = float(
        np.clip(
            confidence,
            0,
            100
        )
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print(
        f"RESULT: {appliance_name}"
    )
    print("-" * 70)

    print(
        f"Optimization samples: "
        f"{len(appliance_results_df)}"
    )

    print(
        f"Features: {len(usable_features)}"
    )

    print(
        f"Data quality: {data_quality}"
    )

    print(
        f"MAE: {mae:.6f}"
    )

    print(
        f"RMSE: {rmse:.6f}"
    )

    print(
        f"Original energy: "
        f"{original_energy_total:.6f} kWh"
    )

    print(
        f"Optimized energy: "
        f"{optimized_energy_total:.6f} kWh"
    )

    print(
        f"Estimated savings: "
        f"{savings_total:.6f} kWh"
    )

    print(
        f"Estimated savings %: "
        f"{savings_percentage:.4f}%"
    )

    print()
    print("ACTION DISTRIBUTION")

    for action in range(4):

        print(
            f"{action} ({ACTION_NAMES[action]}): "
            f"{action_counts[action]}"
        )

    print(
        f"Policy confidence: "
        f"{confidence:.2f}%"
    )

    # --------------------------------------------------------
    # Appliance summary
    # --------------------------------------------------------

    summary_results.append({
        "house_id":
            house_id,

        "appliance_id":
            appliance_id,

        "appliance_name":
            appliance_name,

        "appliance_type":
            appliance_type,

        "sensor_id":
            sensor_id,

        "rated_power_w":
            rated_power,

        "optimization_rows":
            len(appliance_results_df),

        "features":
            len(usable_features),

        "data_quality":
            data_quality,

        "mae":
            float(mae),

        "rmse":
            float(rmse),

        "original_energy_kwh":
            original_energy_total,

        "optimized_energy_kwh":
            optimized_energy_total,

        "estimated_savings_kwh":
            savings_total,

        "estimated_savings_percentage":
            savings_percentage,

        "maintain_actions":
            action_counts[0],

        "reduce_actions":
            action_counts[1],

        "shift_actions":
            action_counts[2],

        "turn_off_actions":
            action_counts[3],

        "policy_confidence":
            confidence
    })


# ============================================================
# SAVE RESULTS
# ============================================================

print()
print("=" * 70)
print("GENERATING OPTIMIZATION OUTPUTS")
print("=" * 70)

if len(all_results) == 0:

    raise RuntimeError(
        "No appliances were successfully optimized."
    )

optimization_df = pd.DataFrame(
    all_results
)

summary_df = pd.DataFrame(
    summary_results
)


# ============================================================
# SAVE FULL OPTIMIZATION DATA
# ============================================================

FULL_OUTPUT = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization.csv"
)

optimization_df.to_csv(
    FULL_OUTPUT,
    index=False
)

print(
    f"[OK] Full optimization output:\n"
    f"{FULL_OUTPUT}"
)


# ============================================================
# SAVE SUMMARY
# ============================================================

SUMMARY_OUTPUT = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization_summary.csv"
)

summary_df.to_csv(
    SUMMARY_OUTPUT,
    index=False
)

print(
    f"[OK] Optimization summary:\n"
    f"{SUMMARY_OUTPUT}"
)


# ============================================================
# ACTION SUMMARY
# ============================================================

action_summary = (
    optimization_df[
        [
            "appliance_id",
            "appliance_name",
            "recommended_action",
            "recommended_action_name"
        ]
    ]
    .groupby(
        [
            "appliance_id",
            "appliance_name",
            "recommended_action",
            "recommended_action_name"
        ]
    )
    .size()
    .reset_index(
        name="action_count"
    )
)

ACTION_OUTPUT = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_action_summary.csv"
)

action_summary.to_csv(
    ACTION_OUTPUT,
    index=False
)

print(
    f"[OK] Action summary:\n"
    f"{ACTION_OUTPUT}"
)


# ============================================================
# SYSTEM SUMMARY
# ============================================================

total_original = float(
    summary_df[
        "original_energy_kwh"
    ].sum()
)

total_optimized = float(
    summary_df[
        "optimized_energy_kwh"
    ].sum()
)

total_savings = (
    total_original
    - total_optimized
)

if total_original > 0:

    overall_savings_percentage = (
        total_savings
        / total_original
        * 100
    )

else:

    overall_savings_percentage = 0.0


average_confidence = float(
    summary_df[
        "policy_confidence"
    ].mean()
)

system_summary = pd.DataFrame([
    {
        "house_id":
            house_id,

        "house_name":
            house_name,

        "registered_appliances":
            len(appliances),

        "optimized_appliances":
            len(summary_df),

        "total_optimization_rows":
            len(optimization_df),

        "total_original_energy_kwh":
            total_original,

        "total_optimized_energy_kwh":
            total_optimized,

        "total_estimated_savings_kwh":
            total_savings,

        "overall_savings_percentage":
            overall_savings_percentage,

        "average_policy_confidence":
            average_confidence,

        "system_status":
            (
                "DYNAMIC_OPTIMIZATION_READY"
                if len(summary_df) == len(appliances)
                else "PARTIAL_OPTIMIZATION"
            )
    }
])

SYSTEM_OUTPUT = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_optimization_system_summary.csv"
)

system_summary.to_csv(
    SYSTEM_OUTPUT,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("MODULE 14F VALIDATION")
print("=" * 70)

print(
    f"House ID             : {house_id}"
)

print(
    f"Registered appliances: {len(appliances)}"
)

print(
    f"Optimized appliances : {len(summary_df)}"
)

print(
    f"Optimization rows    : {len(optimization_df)}"
)

print(
    f"Feature count        : {len(MODEL_FEATURES)}"
)

print()
print("VALIDATION")
print("-" * 70)

# Required output validation

if len(summary_df) == len(appliances):

    print(
        "[OK] Every registered appliance was optimized."
    )

else:

    print(
        "[WARNING] Some appliances were not optimized."
    )


# Null validation

null_count = int(
    optimization_df.isnull().sum().sum()
)

if null_count == 0:

    print(
        "[OK] Optimization output contains no NULL values."
    )

else:

    print(
        f"[WARNING] Optimization output contains "
        f"{null_count} NULL values."
    )


# Duplicate validation

duplicate_count = int(
    optimization_df.duplicated().sum()
)

if duplicate_count == 0:

    print(
        "[OK] No duplicate optimization rows."
    )

else:

    print(
        f"[WARNING] Duplicate rows: "
        f"{duplicate_count}"
    )


# Model files

model_count = 0

for _, appliance in appliances.iterrows():

    appliance_id = str(
        appliance["appliance_id"]
    )

    model_file = os.path.join(
        MODEL_DIR,
        f"{appliance_id}_rl_agent.pkl"
    )

    if os.path.exists(model_file):
        model_count += 1

print(
    f"[OK] Model files found: "
    f"{model_count}/{len(appliances)}"
)


# ============================================================
# RESULTS TABLE
# ============================================================

print()
print("=" * 70)
print("DYNAMIC RL OPTIMIZATION RESULTS")
print("=" * 70)

display_columns = [
    "appliance_name",
    "optimization_rows",
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions",
    "policy_confidence",
    "data_quality"
]

print(
    summary_df[
        display_columns
    ].to_string(index=False)
)


# ============================================================
# SYSTEM SUMMARY
# ============================================================

print()
print("=" * 70)
print("SYSTEM OPTIMIZATION SUMMARY")
print("=" * 70)

print(
    f"Original energy      : "
    f"{total_original:.6f} kWh"
)

print(
    f"Optimized energy     : "
    f"{total_optimized:.6f} kWh"
)

print(
    f"Estimated savings    : "
    f"{total_savings:.6f} kWh"
)

print(
    f"Estimated savings %  : "
    f"{overall_savings_percentage:.4f}%"
)

print(
    f"Average confidence   : "
    f"{average_confidence:.2f}%"
)


# ============================================================
# FINAL STATUS
# ============================================================

elapsed_minutes = (
    time.time() - START_TIME
) / 60

print()
print("=" * 70)
print("MODULE 14F COMPLETE")
print("=" * 70)

print()
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
    f"Optimized           : {len(summary_df)}"
)

print(
    f"Total savings       : "
    f"{total_savings:.6f} kWh"
)

print(
    f"Savings percentage  : "
    f"{overall_savings_percentage:.4f}%"
)

print(
    f"Policy confidence   : "
    f"{average_confidence:.2f}%"
)

print(
    "System status       : "
    + (
        "DYNAMIC_OPTIMIZATION_READY"
        if len(summary_df) == len(appliances)
        else "PARTIAL_OPTIMIZATION"
    )
)

print()
print("OUTPUT FILES")
print("-" * 70)

print(
    f"Full optimization:\n"
    f"{FULL_OUTPUT}"
)

print(
    f"Optimization summary:\n"
    f"{SUMMARY_OUTPUT}"
)

print(
    f"Action summary:\n"
    f"{ACTION_OUTPUT}"
)

print(
    f"System summary:\n"
    f"{SYSTEM_OUTPUT}"
)

print()
print(
    f"Total time: {elapsed_minutes:.2f} minutes"
)

print("=" * 70)