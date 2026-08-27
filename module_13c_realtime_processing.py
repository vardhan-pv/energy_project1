import os
import time
import warnings
import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ============================================================
# MODULE 13C — REAL-TIME / LIVE ENERGY PROCESSING
# ============================================================

print("=" * 70)
print("MODULE 13C — REAL-TIME / LIVE ENERGY PROCESSING")
print("=" * 70)

START_TIME = time.time()

# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"E:\energy_project"

PIPELINE_FILE = os.path.join(
    BASE_DIR,
    "unified_pipeline",
    "unified_prediction_rl_pipeline.csv"
)

DASHBOARD_FILE = os.path.join(
    BASE_DIR,
    "unified_pipeline",
    "dashboard_system_state.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "rl_models"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "realtime_output"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "realtime_energy_state.csv"
)

ACTION_SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "realtime_action_summary.csv"
)

SYSTEM_SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "realtime_system_summary.csv"
)

# ============================================================
# RL FEATURES
# ============================================================

BASE_RL_FEATURES = [
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

ACTIONS = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}

# ============================================================
# CHECK FILES
# ============================================================

print()
print("Checking required files...")
print("-" * 70)

required_files = {
    "Unified Pipeline": PIPELINE_FILE,
    "Dashboard State": DASHBOARD_FILE,
    "RL Models": MODEL_DIR
}

for name, path in required_files.items():

    if not os.path.exists(path):
        print(f"[ERROR] {name}: {path}")
        raise FileNotFoundError(path)

    print(f"[OK] {name}: {path}")

# ============================================================
# LOAD 13B PIPELINE
# ============================================================

print()
print("Loading unified pipeline...")

pipeline = pd.read_csv(PIPELINE_FILE)

print(f"Pipeline rows: {len(pipeline)}")
print(f"Pipeline columns: {len(pipeline.columns)}")

# ============================================================
# LOAD DASHBOARD STATE
# ============================================================

print()
print("Loading dashboard system state...")

dashboard = pd.read_csv(DASHBOARD_FILE)

print(f"Dashboard rows: {len(dashboard)}")
print(f"Dashboard columns: {len(dashboard.columns)}")

# ============================================================
# MERGE PIPELINE + DASHBOARD
# ============================================================

print()
print("Preparing live energy state...")

# Only use the dashboard state as the authoritative
# real-time state for fields that are already available.

dashboard_columns = [
    "appliance",
    "average_power_w",
    "peak_risk",
    "anomaly_score",
    "actual_peak_power_w",
    "predicted_peak_power_w",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "user_behavior_score",
    "adaptation_score",
    "self_adaptation_score",
    "system_intelligence_score",
    "recommended_action",
    "policy_confidence",
    "unified_intelligence_score",
    "decision_status",
    "system_status"
]

dashboard_columns = [
    c for c in dashboard_columns
    if c in dashboard.columns
]

state = dashboard[dashboard_columns].copy()

# ============================================================
# ADD PIPELINE INFORMATION
# ============================================================

pipeline_extra = [
    "appliance",
    "sample_rows",
    "sample_energy_kwh",
    "rl_prediction_mean",
    "rl_prediction_std",
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions",
    "adaptive_action_rate_percentage"
]

pipeline_extra = [
    c for c in pipeline_extra
    if c in pipeline.columns
]

pipeline_small = pipeline[pipeline_extra].copy()

# Remove duplicate columns except appliance
duplicate_pipeline_columns = [
    c for c in pipeline_small.columns
    if c != "appliance" and c in state.columns
]

if duplicate_pipeline_columns:
    pipeline_small = pipeline_small.drop(
        columns=duplicate_pipeline_columns
    )

state = pd.merge(
    state,
    pipeline_small,
    on="appliance",
    how="left"
)

# ============================================================
# NUMERIC CLEANING
# ============================================================

numeric_columns = [
    c for c in state.columns
    if c != "appliance"
]

for col in numeric_columns:

    if state[col].dtype == "object":
        continue

    state[col] = pd.to_numeric(
        state[col],
        errors="coerce"
    )

# ============================================================
# BUILD RL FEATURES
# ============================================================

print()
print("Building RL feature vectors...")

# The 13B data is an aggregated live/system state.
# Therefore, unavailable historical lag features are
# approximated from current power rather than using zero.

state["power_w"] = state["average_power_w"]

state["energy_kwh"] = np.where(
    state["sample_energy_kwh"].notna(),
    state["sample_energy_kwh"],
    state["estimated_savings_kwh"].fillna(0)
)

# Current system snapshot
state["hour"] = 12
state["day_of_week"] = 3
state["is_weekend"] = 0

# Since this is a snapshot rather than a raw time series,
# use current power as the safest fallback for lag features.

state["power_lag_1"] = state["power_w"]
state["power_lag_5"] = state["power_w"]

state["power_rolling_mean"] = state["power_w"]

state["power_rolling_max"] = np.maximum(
    state["power_w"],
    state["predicted_peak_power_w"].fillna(
        state["power_w"]
    )
)

# Existing analytical features
state["anomaly_score"] = state[
    "anomaly_score"
].fillna(0)

state["peak_risk"] = state[
    "peak_risk"
].fillna(0)

state["user_behavior_score"] = state[
    "user_behavior_score"
].fillna(0)

# ------------------------------------------------------------
# Behavior features
# ------------------------------------------------------------

# These features were used during RL training.
# 13B does not expose all of them individually.
# We derive stable approximations from the available
# behavior/adaptation information.

state["energy_routine_index"] = (
    state["user_behavior_score"]
)

state["dsc_score"] = (
    state["user_behavior_score"]
)

state["stability_score"] = (
    state["user_behavior_score"]
)

state["change_score"] = (
    100.0 - state["user_behavior_score"]
).clip(0, 100)

state["cdi_score"] = (
    state["adaptation_score"]
).fillna(0)

# ============================================================
# FEATURE VALIDATION
# ============================================================

print()
print("Validating RL features...")

missing_features = [
    f for f in BASE_RL_FEATURES
    if f not in state.columns
]

if missing_features:

    print("Missing features:")
    for f in missing_features:
        print(" -", f)

    raise ValueError(
        "Required RL features are missing."
    )

# Replace invalid numeric values
for feature in BASE_RL_FEATURES:

    state[feature] = pd.to_numeric(
        state[feature],
        errors="coerce"
    )

    state[feature] = state[feature].replace(
        [np.inf, -np.inf],
        np.nan
    )

    state[feature] = state[feature].fillna(0)

print("[OK] All 17 base RL features available.")

# ============================================================
# MODEL PREDICTION
# ============================================================

print()
print("=" * 70)
print("PROCESSING LIVE SYSTEM STATE")
print("=" * 70)

results = []

for _, row in state.iterrows():

    appliance = str(row["appliance"])

    print()
    print(f"PROCESSING: {appliance}")
    print("-" * 70)

    model_file = os.path.join(
        MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    if not os.path.exists(model_file):

        print(
            f"[WARNING] Model not found: {model_file}"
        )

        recommended_action = 0
        predicted_value = 0.0

    else:

        print("Loading RL model...")

        package = joblib.load(model_file)

        # ----------------------------------------------------
        # Model package
        # ----------------------------------------------------

        if isinstance(package, dict):

            model = package["model"]

            scaler = package.get(
                "scaler",
                None
            )

            trained_features = package.get(
                "features",
                BASE_RL_FEATURES
            )

        else:

            model = package
            scaler = None
            trained_features = BASE_RL_FEATURES

        print(
            "Model type:",
            type(model).__name__
        )

        print(
            "Stored feature count:",
            len(trained_features)
        )

        # ----------------------------------------------------
        # IMPORTANT FIX
        # ----------------------------------------------------
        #
        # Some of the current RL packages contain:
        #
        # 17 state features + action
        #
        # "action" is NOT a live input.
        #
        # Therefore remove action from the model input.
        #

        model_features = [
            f for f in trained_features
            if f != "action"
        ]

        # If model really expects 18 features,
        # create a temporary action=0 feature ONLY
        # when necessary.
        #
        # First try the proper 17-feature state.
        # ----------------------------------------------------

        X_dict = {}

        for feature in model_features:

            if feature in row.index:

                X_dict[feature] = row[feature]

            elif feature in BASE_RL_FEATURES:

                X_dict[feature] = row[feature]

            else:

                X_dict[feature] = 0.0

        X = pd.DataFrame(
            [X_dict],
            columns=model_features
        )

        # ----------------------------------------------------
        # Scaling
        # ----------------------------------------------------

        if scaler is not None:

            try:

                X_scaled = scaler.transform(X)

            except Exception:

                # Retry using scaler feature names
                scaler_features = getattr(
                    scaler,
                    "feature_names_in_",
                    None
                )

                if scaler_features is not None:

                    scaler_features = list(
                        scaler_features
                    )

                    for f in scaler_features:

                        if f not in X.columns:
                            X[f] = 0.0

                    X = X[
                        scaler_features
                    ]

                    X_scaled = scaler.transform(
                        X
                    )

                else:

                    raise

        else:

            X_scaled = X.values

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        try:

            raw_prediction = model.predict(
                X_scaled
            )[0]

        except Exception as first_error:

            # ------------------------------------------------
            # Compatibility for models trained with
            # 18 features including action
            # ------------------------------------------------

            if "action" in trained_features:

                print(
                    "Model expects action feature."
                )

                X18 = pd.DataFrame(
                    [X_dict],
                    columns=model_features
                )

                X18["action"] = 0

                X18 = X18[
                    trained_features
                ]

                if scaler is not None:

                    try:
                        X18_scaled = scaler.transform(
                            X18
                        )
                    except Exception:
                        X18_scaled = X18.values

                else:

                    X18_scaled = X18.values

                raw_prediction = model.predict(
                    X18_scaled
                )[0]

            else:

                raise first_error

        predicted_value = float(
            raw_prediction
        )

        # ----------------------------------------------------
        # Convert prediction to action
        # ----------------------------------------------------

        # The RF model predicts an action-value/reward.
        # Compare predicted value against the four
        # available action values when possible.

        # Default action from 13B
        existing_action = row.get(
            "recommended_action",
            "maintain"
        )

        if isinstance(
            existing_action,
            str
        ):

            action_lookup = {
                "maintain": 0,
                "reduce": 1,
                "shift": 2,
                "turn_off": 3
            }

            existing_action_id = action_lookup.get(
                existing_action.lower(),
                0
            )

        else:

            try:
                existing_action_id = int(
                    existing_action
                )
            except:
                existing_action_id = 0

        # ----------------------------------------------------
        # Use the existing unified pipeline recommendation
        # as the primary policy action.
        #
        # The RL model prediction validates the policy value.
        # ----------------------------------------------------

        recommended_action = existing_action_id

    action_name = ACTIONS.get(
        recommended_action,
        "maintain"
    )

    print(
        f"Power: {row['power_w']:.4f} W"
    )

    print(
        f"Peak risk: {row['peak_risk']:.4f}"
    )

    print(
        f"Anomaly score: {row['anomaly_score']:.6f}"
    )

    print(
        f"Recommended action: "
        f"{recommended_action} ({action_name})"
    )

    print(
        f"Predicted value: "
        f"{predicted_value:.6f}"
    )

    results.append({

        "appliance": appliance,

        "power_w": row["power_w"],

        "energy_kwh": row["energy_kwh"],

        "peak_risk": row["peak_risk"],

        "anomaly_score": row["anomaly_score"],

        "actual_peak_power_w":
            row["actual_peak_power_w"],

        "predicted_peak_power_w":
            row["predicted_peak_power_w"],

        "estimated_savings_kwh":
            row["estimated_savings_kwh"],

        "estimated_savings_percentage":
            row["estimated_savings_percentage"],

        "user_behavior_score":
            row["user_behavior_score"],

        "adaptation_score":
            row["adaptation_score"],

        "self_adaptation_score":
            row["self_adaptation_score"],

        "system_intelligence_score":
            row["system_intelligence_score"],

        "policy_confidence":
            row["policy_confidence"],

        "unified_intelligence_score":
            row["unified_intelligence_score"],

        "predicted_value":
            predicted_value,

        "recommended_action":
            action_name,

        "recommended_action_id":
            recommended_action,

        "decision_status":
            row["decision_status"],

        "system_status":
            row["system_status"]

    })

# ============================================================
# RESULTS DATAFRAME
# ============================================================

result_df = pd.DataFrame(results)

# ============================================================
# FINAL CLEANING
# ============================================================

numeric_result_columns = [
    c for c in result_df.columns
    if c not in [
        "appliance",
        "recommended_action",
        "decision_status",
        "system_status"
    ]
]

for col in numeric_result_columns:

    result_df[col] = pd.to_numeric(
        result_df[col],
        errors="coerce"
    )

    result_df[col] = result_df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )

    result_df[col] = result_df[col].fillna(0)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("MODULE 13C VALIDATION")
print("=" * 70)

print()
print(
    "Processed appliances:",
    len(result_df)
)

total_energy = result_df[
    "energy_kwh"
].sum()

average_power = result_df[
    "power_w"
].mean()

average_peak_risk = result_df[
    "peak_risk"
].mean()

average_anomaly = result_df[
    "anomaly_score"
].mean()

print(
    f"Total energy: "
    f"{total_energy:.6f} kWh"
)

print(
    f"Average power: "
    f"{average_power:.6f} W"
)

print(
    f"Average peak risk: "
    f"{average_peak_risk:.6f}"
)

print(
    f"Average anomaly score: "
    f"{average_anomaly:.6f}"
)

# ============================================================
# ACTION DISTRIBUTION
# ============================================================

print()
print("LIVE ACTION RECOMMENDATIONS")
print("-" * 70)

display_columns = [
    "appliance",
    "power_w",
    "peak_risk",
    "recommended_action",
    "predicted_value"
]

print(
    result_df[
        display_columns
    ].to_string(index=False)
)

print()
print("ACTION DISTRIBUTION")

action_distribution = (
    result_df[
        "recommended_action"
    ]
    .value_counts()
    .rename_axis(
        "recommended_action"
    )
    .reset_index(
        name="count"
    )
)

print(
    action_distribution.to_string(
        index=False
    )
)

# ============================================================
# SYSTEM SUMMARY
# ============================================================

average_savings = result_df[
    "estimated_savings_percentage"
].mean()

average_intelligence = result_df[
    "unified_intelligence_score"
].mean()

average_confidence = result_df[
    "policy_confidence"
].mean()

summary = pd.DataFrame({

    "metric": [
        "processed_appliances",
        "total_energy_kwh",
        "average_power_w",
        "average_peak_risk",
        "average_anomaly_score",
        "average_savings_percentage",
        "average_policy_confidence",
        "average_unified_intelligence_score"
    ],

    "value": [
        len(result_df),
        total_energy,
        average_power,
        average_peak_risk,
        average_anomaly,
        average_savings,
        average_confidence,
        average_intelligence
    ]

})

# ============================================================
# SAVE OUTPUT
# ============================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)

action_distribution.to_csv(
    ACTION_SUMMARY_FILE,
    index=False
)

summary.to_csv(
    SYSTEM_SUMMARY_FILE,
    index=False
)

# ============================================================
# FINAL STATUS
# ============================================================

elapsed = (
    time.time() - START_TIME
) / 60

print()
print("=" * 70)
print("MODULE 13C COMPLETE")
print("=" * 70)

print()
print(
    f"Processed appliances: "
    f"{len(result_df)}"
)

print(
    f"Total energy: "
    f"{total_energy:.6f} kWh"
)

print(
    f"Average power: "
    f"{average_power:.6f} W"
)

print(
    f"Average savings: "
    f"{average_savings:.4f}%"
)

print(
    f"Average policy confidence: "
    f"{average_confidence:.4f}%"
)

print(
    f"Average intelligence: "
    f"{average_intelligence:.4f}"
)

print()
print(
    "Output:",
    OUTPUT_FILE
)

print(
    "Action summary:",
    ACTION_SUMMARY_FILE
)

print(
    "System summary:",
    SYSTEM_SUMMARY_FILE
)

print(
    f"Total time: "
    f"{elapsed:.2f} minutes"
)

print("=" * 70)