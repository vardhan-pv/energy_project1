# ================================================================
# MODULE 14H — DYNAMIC REAL-TIME DECISION ENGINE
# ================================================================
#
# Architecture:
#
#   House
#      ↓
#   Appliances
#      ↓
#   Dynamic Features
#      ↓
#   Verified JOBLIB Models
#      ↓
#   RL Policy Optimization
#      ↓
#   Self-Evolved Policy
#      ↓
#   REAL-TIME DECISION
#
# ================================================================

import os
import time
import json
import joblib
import numpy as np
import pandas as pd


# ================================================================
# CONFIGURATION
# ================================================================

START_TIME = time.time()

PROJECT_ROOT = r"E:\energy_project"

HOUSE_CONFIG_PATH = os.path.join(
    PROJECT_ROOT,
    "initialization",
    "house_config.json"
)

APPLIANCE_CONFIG_PATH = os.path.join(
    PROJECT_ROOT,
    "initialization",
    "appliance_config.csv"
)


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def print_line(char="=", length=70):
    print(char * length)


def require_file(path, description):
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{description} not found:\n{path}"
        )

    print(f"[OK] {description}: {path}")


def require_directory(path):
    os.makedirs(path, exist_ok=True)


def clean_numeric_features(df, feature_columns):
    """
    Convert required model features to numeric and remove
    rows containing invalid values.
    """

    result = df.copy()

    for column in feature_columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        )

    before = len(result)

    result = result.replace(
        [np.inf, -np.inf],
        np.nan
    )

    result = result.dropna(
        subset=feature_columns
    ).reset_index(drop=True)

    after = len(result)

    return result, before, after


def safe_float(value, default=0.0):
    try:
        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except Exception:
        return default


# ================================================================
# HEADER
# ================================================================

print_line()
print("MODULE 14H — DYNAMIC REAL-TIME DECISION ENGINE")
print_line()

print()
print("Architecture:")
print("  House → Appliances → Dynamic Features")
print("                         ↓")
print("                 Verified JOBLIB Models")
print("                         ↓")
print("                 RL Policy Optimization")
print("                         ↓")
print("                 Self-Evolved Policy")
print("                         ↓")
print("                 REAL-TIME DECISION")
print()


# ================================================================
# CHECK BASIC FILES
# ================================================================

print_line()
print("CHECKING REQUIRED FILES")
print_line()

require_file(
    HOUSE_CONFIG_PATH,
    "House configuration"
)

require_file(
    APPLIANCE_CONFIG_PATH,
    "Appliance configuration"
)


# ================================================================
# LOAD HOUSE CONFIGURATION
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


if not HOUSE_ID:
    raise ValueError(
        "house_id missing from house_config.json"
    )


print(f"House ID   : {HOUSE_ID}")
print(f"House Name : {HOUSE_NAME}")
print(f"Location   : {LOCATION}")


# ================================================================
# HOUSE DATA PATHS
# ================================================================

HOUSE_DIR = os.path.join(
    PROJECT_ROOT,
    "house_data",
    HOUSE_ID
)

FEATURES_DIR = os.path.join(
    HOUSE_DIR,
    "features"
)

MODELS_DIR = os.path.join(
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


DYNAMIC_FEATURES_PATH = os.path.join(
    FEATURES_DIR,
    "dynamic_features.csv"
)

TRAINING_SUMMARY_PATH = os.path.join(
    MODELS_DIR,
    "dynamic_training_summary.csv"
)

MODEL_REGISTRY_PATH = os.path.join(
    MODELS_DIR,
    "model_registry.csv"
)

RL_OPTIMIZATION_PATH = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization.csv"
)

OPTIMIZATION_SUMMARY_PATH = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization_summary.csv"
)

SELF_EVOLUTION_SUMMARY_PATH = os.path.join(
    EVOLUTION_DIR,
    "dynamic_self_evolution_summary.csv"
)

EVOLVED_POLICY_PATH = os.path.join(
    EVOLUTION_DIR,
    "dynamic_evolved_policy_parameters.csv"
)


# Output files

REALTIME_DECISION_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_decisions.csv"
)

REALTIME_SUMMARY_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_decision_summary.csv"
)

REALTIME_ACTION_SUMMARY_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_action_summary.csv"
)

REALTIME_SYSTEM_SUMMARY_PATH = os.path.join(
    REALTIME_DIR,
    "dynamic_realtime_system_summary.csv"
)


require_directory(
    REALTIME_DIR
)


print()
print_line()
print("HOUSE DATA PATHS")
print_line()

print(f"House directory : {HOUSE_DIR}")
print(f"Features        : {DYNAMIC_FEATURES_PATH}")
print(f"Models          : {MODELS_DIR}")
print(f"Optimization    : {OPTIMIZATION_DIR}")
print(f"Evolution       : {EVOLUTION_DIR}")
print(f"Realtime        : {REALTIME_DIR}")


# ================================================================
# CHECK MODULE INPUTS
# ================================================================

print()
print_line()
print("CHECKING MODULE INPUTS")
print_line()

require_file(
    DYNAMIC_FEATURES_PATH,
    "Dynamic features"
)

require_file(
    TRAINING_SUMMARY_PATH,
    "Training summary"
)

require_file(
    MODEL_REGISTRY_PATH,
    "Model registry"
)

require_file(
    RL_OPTIMIZATION_PATH,
    "Dynamic RL optimization"
)

require_file(
    OPTIMIZATION_SUMMARY_PATH,
    "Optimization summary"
)

require_file(
    SELF_EVOLUTION_SUMMARY_PATH,
    "Self-evolution summary"
)

require_file(
    EVOLVED_POLICY_PATH,
    "Evolved policy parameters"
)


# ================================================================
# LOAD APPLIANCE CONFIGURATION
# ================================================================

print()
print("Loading appliance configuration...")

appliances = pd.read_csv(
    APPLIANCE_CONFIG_PATH
)

if appliances.empty:
    raise ValueError(
        "Appliance configuration is empty."
    )


required_appliance_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w"
]


missing_appliance_columns = [
    column
    for column in required_appliance_columns
    if column not in appliances.columns
]


if missing_appliance_columns:

    raise ValueError(
        "Missing appliance configuration columns:\n"
        + "\n".join(missing_appliance_columns)
    )


print(
    f"Registered appliances: {len(appliances)}"
)

print()

print(
    appliances[
        required_appliance_columns
    ].to_string(index=False)
)


# ================================================================
# LOAD DYNAMIC FEATURES
# ================================================================

print()
print_line()
print("LOADING DYNAMIC FEATURES")
print_line()

features_df = pd.read_csv(
    DYNAMIC_FEATURES_PATH
)

print(
    f"Rows loaded    : {len(features_df)}"
)

print(
    f"Columns loaded : {len(features_df.columns)}"
)


# ================================================================
# MODEL FEATURE DEFINITION
# ================================================================
#
# These are the exact 17 features discovered from the
# trained JOBLIB model:
#
# 1  power_w
# 2  energy_kwh
# 3  hour
# 4  day_of_week
# 5  is_weekend
# 6  power_lag_1
# 7  power_lag_5
# 8  power_rolling_mean
# 9  power_rolling_max
# 10 anomaly_score
# 11 peak_risk
# 12 user_behavior_score
# 13 energy_routine_index
# 14 dsc_score
# 15 stability_score
# 16 change_score
# 17 cdi_score
#
# IMPORTANT:
# During prediction we still use model.feature_names_in_
# as the final source of truth.
# ================================================================

EXPECTED_MODEL_FEATURES = [
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
# VALIDATE BASE FEATURES
# ================================================================

print()
print("Validating dynamic model features...")


missing_expected = [
    feature
    for feature in EXPECTED_MODEL_FEATURES
    if feature not in features_df.columns
]


if missing_expected:

    raise ValueError(
        "Missing dynamic model features:\n"
        + "\n".join(missing_expected)
    )


print(
    f"[OK] All {len(EXPECTED_MODEL_FEATURES)} model features available."
)


# ================================================================
# CLEAN FEATURES
# ================================================================

print()
print("Cleaning realtime features...")

features_df, rows_before, rows_after = clean_numeric_features(
    features_df,
    EXPECTED_MODEL_FEATURES
)


print(
    f"Rows before cleaning : {rows_before}"
)

print(
    f"Rows after cleaning  : {rows_after}"
)

print(
    f"Rows removed         : {rows_before - rows_after}"
)


if features_df.empty:

    raise ValueError(
        "No valid dynamic feature rows remain after cleaning."
    )


# ================================================================
# LOAD TRAINING SUMMARY
# ================================================================

print()
print("Loading training summary...")

training_summary = pd.read_csv(
    TRAINING_SUMMARY_PATH
)

print(
    f"Training records: {len(training_summary)}"
)


# ================================================================
# LOAD MODEL REGISTRY
# ================================================================

print()
print("Loading model registry...")

model_registry = pd.read_csv(
    MODEL_REGISTRY_PATH
)

print(
    f"Registered models: {len(model_registry)}"
)


# ================================================================
# LOAD RL OPTIMIZATION
# ================================================================

print()
print("Loading RL optimization...")

optimization_df = pd.read_csv(
    RL_OPTIMIZATION_PATH
)

print(
    f"Optimization rows: {len(optimization_df)}"
)


# ================================================================
# LOAD EVOLVED POLICY
# ================================================================

print()
print("Loading evolved policy parameters...")

evolved_policy_df = pd.read_csv(
    EVOLVED_POLICY_PATH
)

print(
    f"Evolved policy records: {len(evolved_policy_df)}"
)


# ================================================================
# DISPLAY DYNAMIC REAL-TIME ENGINE
# ================================================================

print()
print_line()
print("DYNAMIC REAL-TIME DECISION ENGINE")
print_line()


# ================================================================
# ACTION DEFINITIONS
# ================================================================

ACTION_NAMES = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}


# ================================================================
# STORAGE
# ================================================================

all_decisions = []
summary_records = []
action_summary_records = []

models_loaded = 0
models_failed = 0


# ================================================================
# PROCESS EACH APPLIANCE
# ================================================================

for _, appliance in appliances.iterrows():

    appliance_start = time.time()

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

    rated_power = safe_float(
        appliance["rated_power_w"]
    )


    print()
    print_line()
    print(f"PROCESSING: {appliance_name}")
    print_line()

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
    # FILTER APPLIANCE DATA
    # ------------------------------------------------------------

    appliance_rows = features_df[
        features_df["appliance_id"].astype(str)
        == appliance_id
    ].copy()


    print(
        f"Available rows: {len(appliance_rows)}"
    )


    if appliance_rows.empty:

        print(
            f"[WARNING] No feature rows for {appliance_name}"
        )

        models_failed += 1

        continue


    # ------------------------------------------------------------
    # FIND MODEL
    # ------------------------------------------------------------

    model_path = os.path.join(
        MODELS_DIR,
        f"{appliance_id}_rl_agent.joblib"
    )


    if not os.path.isfile(model_path):

        print(
            f"[ERROR] Model not found: {model_path}"
        )

        models_failed += 1

        continue


    print(
        f"Model: {model_path}"
    )


    # ------------------------------------------------------------
    # LOAD MODEL
    # ------------------------------------------------------------

    try:

        model = joblib.load(
            model_path
        )

    except Exception as exc:

        print(
            f"[ERROR] Model loading failed: {exc}"
        )

        models_failed += 1

        continue


    models_loaded += 1


    print(
        f"Model type: {type(model).__name__}"
    )


    # ------------------------------------------------------------
    # READ EXACT MODEL FEATURES
    # ------------------------------------------------------------
    #
    # This is the critical fix.
    #
    # Instead of assuming Module 14H knows the feature order,
    # the trained model tells us exactly what it expects.
    # ------------------------------------------------------------

    if not hasattr(
        model,
        "feature_names_in_"
    ):

        print(
            "[ERROR] Model does not contain feature_names_in_."
        )

        models_failed += 1

        continue


    model_features = list(
        model.feature_names_in_
    )


    print(
        f"Stored feature count: {len(model_features)}"
    )


    # ------------------------------------------------------------
    # VALIDATE FEATURE COUNT
    # ------------------------------------------------------------

    if len(model_features) != 17:

        raise ValueError(
            f"Unexpected model feature count for "
            f"{appliance_name}: "
            f"{len(model_features)}. Expected 17."
        )


    # ------------------------------------------------------------
    # VALIDATE EXACT FEATURES
    # ------------------------------------------------------------

    missing_model_features = [
        feature
        for feature in model_features
        if feature not in appliance_rows.columns
    ]


    if missing_model_features:

        raise ValueError(
            f"Missing model features for "
            f"{appliance_name}:\n"
            + "\n".join(missing_model_features)
        )


    # ------------------------------------------------------------
    # FEATURE ORDER VALIDATION
    # ------------------------------------------------------------

    print()
    print("MODEL FEATURE ORDER")
    print("-" * 70)

    for index, feature in enumerate(
        model_features,
        start=1
    ):

        print(
            f"{index:2d}. {feature}"
        )


    # ------------------------------------------------------------
    # BUILD MODEL INPUT
    # ------------------------------------------------------------

    X = appliance_rows[
        model_features
    ].copy()


    # Ensure numeric values

    for feature in model_features:

        X[feature] = pd.to_numeric(
            X[feature],
            errors="coerce"
        )


    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )


    valid_mask = ~X.isna().any(
        axis=1
    )


    X = X.loc[
        valid_mask
    ].reset_index(drop=True)


    appliance_rows = appliance_rows.loc[
        valid_mask
    ].reset_index(drop=True)


    if X.empty:

        print(
            f"[ERROR] No valid model input rows for "
            f"{appliance_name}"
        )

        models_failed += 1

        continue


    # ------------------------------------------------------------
    # PREDICTION
    # ------------------------------------------------------------

    try:

        predictions = model.predict(
            X
        )

    except Exception as exc:

        raise RuntimeError(
            f"Prediction failed for {appliance_name}: "
            f"{exc}"
        )


    predictions = np.asarray(
        predictions,
        dtype=float
    )


    # ------------------------------------------------------------
    # LOAD EVOLVED POLICY
    # ------------------------------------------------------------

    policy_row = evolved_policy_df[
        evolved_policy_df[
            "appliance_id"
        ].astype(str)
        == appliance_id
    ]


    if policy_row.empty:

        print(
            "[WARNING] No evolved policy found. "
            "Using default policy weights."
        )

        maintain_weight = 1.0
        reduce_weight = 1.0
        shift_weight = 1.0
        turn_off_weight = 1.0

        learning_rate = 0.01
        adaptation_factor = 1.0

    else:

        policy = policy_row.iloc[0]

        maintain_weight = safe_float(
            policy.get(
                "evolved_maintain_weight",
                1.0
            ),
            1.0
        )

        reduce_weight = safe_float(
            policy.get(
                "evolved_reduce_weight",
                1.0
            ),
            1.0
        )

        shift_weight = safe_float(
            policy.get(
                "evolved_shift_weight",
                1.0
            ),
            1.0
        )

        turn_off_weight = safe_float(
            policy.get(
                "evolved_turn_off_weight",
                1.0
            ),
            1.0
        )

        learning_rate = safe_float(
            policy.get(
                "recommended_learning_rate",
                0.01
            ),
            0.01
        )

        adaptation_factor = safe_float(
            policy.get(
                "adaptation_factor",
                1.0
            ),
            1.0
        )


    # ------------------------------------------------------------
    # POLICY DECISION
    # ------------------------------------------------------------
    #
    # The trained model predicts a policy/value score.
    #
    # We transform that score into a dynamic action score.
    #
    # Policy weights come from Module 14G.
    #
    # This keeps Module 14H connected to:
    #
    # 14E → trained model
    # 14F → optimization
    # 14G → evolved policy
    # 14H → realtime decision
    # ------------------------------------------------------------

    decisions = []

    confidence_values = []


    for prediction in predictions:

        prediction = float(
            np.clip(
                prediction,
                0.0,
                1.0
            )
        )


        # --------------------------------------------------------
        # BASE ACTION SCORES
        # --------------------------------------------------------

        maintain_score = (
            (1.0 - prediction)
            * maintain_weight
        )

        reduce_score = (
            prediction
            * reduce_weight
        )

        shift_score = (
            prediction
            * 0.90
            * shift_weight
        )

        turn_off_score = (
            prediction
            * 0.35
            * turn_off_weight
        )


        action_scores = {
            0: maintain_score,
            1: reduce_score,
            2: shift_score,
            3: turn_off_score
        }


        # --------------------------------------------------------
        # APPLIANCE SAFETY RULES
        # --------------------------------------------------------
        #
        # Avoid aggressive turn-off behavior for this project.
        # Refrigerator should never be automatically turned off.
        # --------------------------------------------------------

        if appliance_type.lower() == "cooling":
            turn_off_score = 0.0
            action_scores[3] = 0.0


        if appliance_name.lower() == "refrigerator":
            turn_off_score = 0.0
            action_scores[3] = 0.0


        # --------------------------------------------------------
        # SELECT ACTION
        # --------------------------------------------------------

        selected_action = max(
            action_scores,
            key=action_scores.get
        )


        sorted_scores = sorted(
            action_scores.values(),
            reverse=True
        )


        highest_score = sorted_scores[0]

        second_score = (
            sorted_scores[1]
            if len(sorted_scores) > 1
            else 0.0
        )


        total_score = sum(
            max(value, 0.0)
            for value in action_scores.values()
        )


        if total_score > 0:

            confidence = (
                highest_score
                / total_score
            ) * 100.0

        else:

            confidence = 0.0


        # Keep confidence within bounds

        confidence = float(
            np.clip(
                confidence,
                0.0,
                100.0
            )
        )


        decisions.append(
            selected_action
        )

        confidence_values.append(
            confidence
        )


    # ============================================================
    # REAL-TIME RESULTS
    # ============================================================

    appliance_rows["predicted_value"] = predictions

    appliance_rows["recommended_action"] = decisions

    appliance_rows["action_name"] = [
        ACTION_NAMES[action]
        for action in decisions
    ]

    appliance_rows["policy_confidence"] = (
        confidence_values
    )

    appliance_rows[
        "learning_rate"
    ] = learning_rate

    appliance_rows[
        "adaptation_factor"
    ] = adaptation_factor

    appliance_rows[
        "policy_version"
    ] = "v2.0"


    appliance_rows[
        "appliance_name"
    ] = appliance_name


    appliance_rows[
        "appliance_type"
    ] = appliance_type


    appliance_rows[
        "sensor_id"
    ] = sensor_id


    # ------------------------------------------------------------
    # ENERGY CALCULATION
    # ------------------------------------------------------------

    original_energy = pd.to_numeric(
        appliance_rows["energy_kwh"],
        errors="coerce"
    ).fillna(0.0)


    # Action reduction assumptions
    #
    # maintain = 0%
    # reduce   = 15%
    # shift    = 10%
    # turn_off = 100%
    #
    # Refrigerator turn-off is already disabled above.

    reduction_factor = []

    for action in decisions:

        if action == 0:
            factor = 1.00

        elif action == 1:
            factor = 0.85

        elif action == 2:
            factor = 0.90

        elif action == 3:
            factor = 0.00

        else:
            factor = 1.00

        reduction_factor.append(
            factor
        )


    appliance_rows[
        "estimated_energy_factor"
    ] = reduction_factor


    appliance_rows[
        "estimated_optimized_energy_kwh"
    ] = (
        original_energy
        * appliance_rows[
            "estimated_energy_factor"
        ]
    )


    appliance_rows[
        "estimated_savings_kwh"
    ] = (
        original_energy
        - appliance_rows[
            "estimated_optimized_energy_kwh"
        ]
    )


    # ------------------------------------------------------------
    # ACTION COUNTS
    # ------------------------------------------------------------

    action_counts = {
        0: int(
            sum(
                action == 0
                for action in decisions
            )
        ),

        1: int(
            sum(
                action == 1
                for action in decisions
            )
        ),

        2: int(
            sum(
                action == 2
                for action in decisions
            )
        ),

        3: int(
            sum(
                action == 3
                for action in decisions
            )
        )
    }


    # ------------------------------------------------------------
    # ENERGY SUMMARY
    # ------------------------------------------------------------

    original_total = safe_float(
        appliance_rows[
            "energy_kwh"
        ].sum()
    )

    optimized_total = safe_float(
        appliance_rows[
            "estimated_optimized_energy_kwh"
        ].sum()
    )

    savings_total = safe_float(
        appliance_rows[
            "estimated_savings_kwh"
        ].sum()
    )


    if original_total > 0:

        savings_percentage = (
            savings_total
            / original_total
        ) * 100.0

    else:

        savings_percentage = 0.0


    average_confidence = safe_float(
        np.mean(confidence_values)
    )


    # ------------------------------------------------------------
    # DATA QUALITY
    # ------------------------------------------------------------

    if len(appliance_rows) < 50:

        data_quality = "DEMO_LOW_DATA"

    else:

        data_quality = "PRODUCTION_READY"


    # ------------------------------------------------------------
    # SAVE TO MEMORY
    # ------------------------------------------------------------

    all_decisions.append(
        appliance_rows
    )


    summary_records.append(
        {
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

            "decision_rows":
                len(appliance_rows),

            "original_energy_kwh":
                original_total,

            "optimized_energy_kwh":
                optimized_total,

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

            "average_policy_confidence":
                average_confidence,

            "learning_rate":
                learning_rate,

            "adaptation_factor":
                adaptation_factor,

            "policy_version":
                "v2.0",

            "data_quality":
                data_quality,

            "model_feature_count":
                len(model_features),

            "model_format":
                "JOBLIB",

            "model_validation":
                "PASSED"
        }
    )


    action_summary_records.append(
        {
            "appliance_id":
                appliance_id,

            "appliance_name":
                appliance_name,

            "maintain":
                action_counts[0],

            "reduce":
                action_counts[1],

            "shift":
                action_counts[2],

            "turn_off":
                action_counts[3],

            "total":
                len(decisions)
        }
    )


    # ------------------------------------------------------------
    # PRINT RESULTS
    # ------------------------------------------------------------

    print()
    print_line("-")
    print(
        f"RESULT: {appliance_name}"
    )
    print_line("-")

    print(
        f"Decision samples: {len(appliance_rows)}"
    )

    print(
        f"Features: {len(model_features)}"
    )

    print(
        f"Data quality: {data_quality}"
    )

    print(
        f"Original energy: {original_total:.6f} kWh"
    )

    print(
        f"Optimized energy: {optimized_total:.6f} kWh"
    )

    print(
        f"Estimated savings: {savings_total:.6f} kWh"
    )

    print(
        f"Estimated savings %: "
        f"{savings_percentage:.4f}%"
    )

    print()
    print("ACTION DISTRIBUTION")
    print("-" * 70)

    print(
        f"0 (maintain): {action_counts[0]}"
    )

    print(
        f"1 (reduce):   {action_counts[1]}"
    )

    print(
        f"2 (shift):    {action_counts[2]}"
    )

    print(
        f"3 (turn_off): {action_counts[3]}"
    )

    print()
    print(
        f"Average policy confidence: "
        f"{average_confidence:.2f}%"
    )

    print(
        f"Policy version: v2.0"
    )

    print(
        f"Processing time: "
        f"{(time.time() - appliance_start):.2f} seconds"
    )


# ================================================================
# CHECK RESULTS
# ================================================================

if not all_decisions:

    raise RuntimeError(
        "No appliance decisions were generated."
    )


# ================================================================
# COMBINE REALTIME DECISIONS
# ================================================================

realtime_df = pd.concat(
    all_decisions,
    ignore_index=True
)


summary_df = pd.DataFrame(
    summary_records
)


action_summary_df = pd.DataFrame(
    action_summary_records
)


# ================================================================
# CLEAN OUTPUT
# ================================================================

realtime_df = realtime_df.replace(
    [np.inf, -np.inf],
    np.nan
)


# Do not silently leave NULLs in critical decision columns

critical_columns = [
    "appliance_id",
    "appliance_name",
    "timestamp",
    "predicted_value",
    "recommended_action",
    "action_name",
    "policy_confidence"
]


for column in critical_columns:

    if column in realtime_df.columns:

        if realtime_df[column].isna().any():

            raise ValueError(
                f"NULL values found in critical "
                f"column: {column}"
            )


# ================================================================
# GENERATING OUTPUTS
# ================================================================

print()
print_line()
print("GENERATING REAL-TIME OUTPUTS")
print_line()


realtime_df.to_csv(
    REALTIME_DECISION_PATH,
    index=False
)

print(
    f"[OK] Full realtime decisions:\n"
    f"{REALTIME_DECISION_PATH}"
)


summary_df.to_csv(
    REALTIME_SUMMARY_PATH,
    index=False
)

print(
    f"[OK] Realtime decision summary:\n"
    f"{REALTIME_SUMMARY_PATH}"
)


action_summary_df.to_csv(
    REALTIME_ACTION_SUMMARY_PATH,
    index=False
)

print(
    f"[OK] Action summary:\n"
    f"{REALTIME_ACTION_SUMMARY_PATH}"
)


# ================================================================
# SYSTEM SUMMARY
# ================================================================

total_original_energy = safe_float(
    summary_df[
        "original_energy_kwh"
    ].sum()
)


total_optimized_energy = safe_float(
    summary_df[
        "optimized_energy_kwh"
    ].sum()
)


total_savings = safe_float(
    summary_df[
        "estimated_savings_kwh"
    ].sum()
)


if total_original_energy > 0:

    total_savings_percentage = (
        total_savings
        / total_original_energy
    ) * 100.0

else:

    total_savings_percentage = 0.0


average_confidence = safe_float(
    summary_df[
        "average_policy_confidence"
    ].mean()
)


average_learning_rate = safe_float(
    summary_df[
        "learning_rate"
    ].mean()
)


average_adaptation_factor = safe_float(
    summary_df[
        "adaptation_factor"
    ].mean()
)


system_status = (
    "REALTIME_DECISION_READY"
    if models_failed == 0
    else "PARTIAL_REALTIME_DECISION"
)


system_summary = pd.DataFrame(
    [
        {
            "house_id":
                HOUSE_ID,

            "house_name":
                HOUSE_NAME,

            "location":
                LOCATION,

            "registered_appliances":
                len(appliances),

            "appliances_processed":
                len(summary_df),

            "models_loaded":
                models_loaded,

            "models_failed":
                models_failed,

            "realtime_rows":
                len(realtime_df),

            "feature_count":
                17,

            "original_energy_kwh":
                total_original_energy,

            "optimized_energy_kwh":
                total_optimized_energy,

            "estimated_savings_kwh":
                total_savings,

            "estimated_savings_percentage":
                total_savings_percentage,

            "average_policy_confidence":
                average_confidence,

            "average_learning_rate":
                average_learning_rate,

            "average_adaptation_factor":
                average_adaptation_factor,

            "policy_version":
                "v2.0",

            "model_format":
                "JOBLIB",

            "system_status":
                system_status
        }
    ]
)


system_summary.to_csv(
    REALTIME_SYSTEM_SUMMARY_PATH,
    index=False
)


# ================================================================
# VALIDATION
# ================================================================

print()
print_line()
print("MODULE 14H VALIDATION")
print_line()

print(
    f"House ID             : {HOUSE_ID}"
)

print(
    f"Registered appliances: {len(appliances)}"
)

print(
    f"Processed appliances : {len(summary_df)}"
)

print(
    f"Realtime rows        : {len(realtime_df)}"
)

print(
    f"Feature count        : 17"
)


print()
print("VALIDATION")
print("-" * 70)


# ---------------------------------------------------------------
# Appliance validation
# ---------------------------------------------------------------

registered_ids = set(
    appliances[
        "appliance_id"
    ].astype(str)
)


processed_ids = set(
    summary_df[
        "appliance_id"
    ].astype(str)
)


if registered_ids == processed_ids:

    print(
        "[OK] Every registered appliance processed."
    )

else:

    missing_ids = (
        registered_ids
        - processed_ids
    )

    print(
        "[WARNING] Some appliances were not processed:"
    )

    for item in sorted(missing_ids):

        print(
            f"  - {item}"
        )


# ---------------------------------------------------------------
# NULL validation
# ---------------------------------------------------------------

final_nulls = int(
    realtime_df.isnull().sum().sum()
)


if final_nulls == 0:

    print(
        "[OK] Realtime output contains no NULL values."
    )

else:

    print(
        f"[WARNING] Realtime output contains "
        f"{final_nulls} NULL values."
    )


# ---------------------------------------------------------------
# Duplicate validation
# ---------------------------------------------------------------

duplicate_count = int(
    realtime_df.duplicated().sum()
)


if duplicate_count == 0:

    print(
        "[OK] No duplicate realtime rows."
    )

else:

    print(
        f"[WARNING] Duplicate realtime rows: "
        f"{duplicate_count}"
    )


# ---------------------------------------------------------------
# Action validation
# ---------------------------------------------------------------

invalid_actions = realtime_df[
    ~realtime_df[
        "recommended_action"
    ].isin([0, 1, 2, 3])
]


if invalid_actions.empty:

    print(
        "[OK] All realtime actions are valid."
    )

else:

    raise ValueError(
        "Invalid action values detected."
    )


# ---------------------------------------------------------------
# Confidence validation
# ---------------------------------------------------------------

invalid_confidence = realtime_df[
    (
        realtime_df[
            "policy_confidence"
        ] < 0
    )
    |
    (
        realtime_df[
            "policy_confidence"
        ] > 100
    )
]


if invalid_confidence.empty:

    print(
        "[OK] Policy confidence values valid."
    )

else:

    raise ValueError(
        "Invalid policy confidence values detected."
    )


# ---------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------

if models_loaded == len(appliances):

    print(
        f"[OK] All {len(appliances)} JOBLIB models loaded."
    )

else:

    print(
        f"[WARNING] Models loaded: "
        f"{models_loaded}/{len(appliances)}"
    )


# ================================================================
# REAL-TIME RESULTS
# ================================================================

print()
print_line()
print("DYNAMIC REAL-TIME DECISION RESULTS")
print_line()


display_columns = [
    "appliance_name",
    "decision_rows",
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions",
    "average_policy_confidence",
    "data_quality"
]


print(
    summary_df[
        display_columns
    ].to_string(index=False)
)


# ================================================================
# SYSTEM SUMMARY
# ================================================================

print()
print_line()
print("SYSTEM REAL-TIME SUMMARY")
print_line()

print(
    f"Original energy      : "
    f"{total_original_energy:.6f} kWh"
)

print(
    f"Optimized energy     : "
    f"{total_optimized_energy:.6f} kWh"
)

print(
    f"Estimated savings    : "
    f"{total_savings:.6f} kWh"
)

print(
    f"Estimated savings %  : "
    f"{total_savings_percentage:.4f}%"
)

print(
    f"Average confidence   : "
    f"{average_confidence:.2f}%"
)

print(
    f"Average learning rate: "
    f"{average_learning_rate:.6f}"
)

print(
    f"Average adaptation   : "
    f"{average_adaptation_factor:.4f}"
)

print(
    f"Policy version       : v2.0"
)

print(
    f"System status        : {system_status}"
)


# ================================================================
# OUTPUT FILES
# ================================================================

print()
print_line()
print("MODULE 14H COMPLETE")
print_line()

print(
    f"House ID             : {HOUSE_ID}"
)

print(
    f"House Name           : {HOUSE_NAME}"
)

print(
    f"Appliances           : {len(appliances)}"
)

print(
    f"Processed            : {len(summary_df)}"
)

print(
    f"Realtime rows        : {len(realtime_df)}"
)

print(
    f"Features per model   : 17"
)

print(
    f"Model format         : JOBLIB"
)

print(
    f"Policy version       : v2.0"
)

print(
    f"System status        : {system_status}"
)


print()
print("OUTPUT FILES")
print("-" * 70)

print(
    f"Full realtime decisions:\n"
    f"{REALTIME_DECISION_PATH}"
)

print(
    f"Decision summary:\n"
    f"{REALTIME_SUMMARY_PATH}"
)

print(
    f"Action summary:\n"
    f"{REALTIME_ACTION_SUMMARY_PATH}"
)

print(
    f"System summary:\n"
    f"{REALTIME_SYSTEM_SUMMARY_PATH}"
)


elapsed_minutes = (
    time.time()
    - START_TIME
) / 60.0


print()
print(
    f"Total time: {elapsed_minutes:.2f} minutes"
)

print_line()

print(
    "[SUCCESS] MODULE 14H COMPLETED."
)

print(
    "[SUCCESS] All available JOBLIB models were loaded "
    "using their exact 17-feature schema."
)

print(
    "[SUCCESS] Real-time decision outputs generated."
)

print_line()