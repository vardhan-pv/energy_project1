import os
import time
import warnings
import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ============================================================
# MODULE 13B — UNIFIED PREDICTION + RL PIPELINE
# ============================================================

BASE_DIR = r"E:\energy_project"

INTEGRATION_DIR = os.path.join(BASE_DIR, "integration_output")
RL_MODEL_DIR = os.path.join(BASE_DIR, "rl_models")
PEAK_MODEL_DIR = os.path.join(BASE_DIR, "peak_models")
RL_DATA_DIR = os.path.join(BASE_DIR, "rl_data")

OUTPUT_DIR = os.path.join(BASE_DIR, "unified_pipeline")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_STATE_FILE = os.path.join(
    INTEGRATION_DIR,
    "unified_system_state.csv"
)

APPLIANCES = [
    "fridge",
    "kitchen_lights",
    "laptop",
    "office_fan"
]

# ============================================================
# RL FEATURES
# ============================================================

RL_FEATURES = [
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
# HELPERS
# ============================================================

def safe_numeric(value, default=0.0):
    try:
        value = float(value)

        if np.isnan(value) or np.isinf(value):
            return default

        return value

    except Exception:
        return default


def load_model_package(path):

    package = joblib.load(path)

    if not isinstance(package, dict):
        raise ValueError(
            f"Invalid model package: {path}"
        )

    if "model" not in package:
        raise ValueError(
            f"'model' missing from package: {path}"
        )

    model = package["model"]

    scaler = package.get("scaler", None)

    features = package.get(
        "features",
        RL_FEATURES
    )

    return model, scaler, features


def prepare_features(df, features):

    missing = [
        col for col in features
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing RL features: {missing}"
        )

    X = df[features].copy()

    for col in features:
        X[col] = pd.to_numeric(
            X[col],
            errors="coerce"
        )

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    X = X.fillna(0)

    return X


def choose_action(predicted_value):

    """
    RL model is trained as an action-value predictor.

    The model output is converted into a safe discrete action.
    """

    value = safe_numeric(predicted_value)

    if value <= 0:
        return 0

    if value <= 1:
        return 1

    if value <= 2:
        return 2

    return 3


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 13B — UNIFIED PREDICTION + RL PIPELINE")
print("=" * 70)

start_time = time.time()

# ============================================================
# CHECK FILES
# ============================================================

print("\nChecking required files...")
print("-" * 70)

required_files = [
    SYSTEM_STATE_FILE
]

for appliance in APPLIANCES:

    required_files.append(
        os.path.join(
            RL_MODEL_DIR,
            f"{appliance}_rl_agent.pkl"
        )
    )

    required_files.append(
        os.path.join(
            RL_DATA_DIR,
            f"{appliance}_rl_environment.csv"
        )
    )

missing_files = []

for path in required_files:

    if os.path.exists(path):

        print(f"[OK] {path}")

    else:

        print(f"[MISSING] {path}")
        missing_files.append(path)

if missing_files:

    print("\nERROR: Required files are missing.")

    for path in missing_files:
        print(path)

    raise SystemExit(1)

print("\nAll required files found.")

# ============================================================
# LOAD SYSTEM STATE
# ============================================================

print("\nLoading unified system state...")

system_state = pd.read_csv(
    SYSTEM_STATE_FILE
)

print(
    f"System state rows: {len(system_state)}"
)

if "appliance" not in system_state.columns:

    raise ValueError(
        "unified_system_state.csv must contain appliance column."
    )

# Remove duplicate appliance rows safely

system_state = (
    system_state
    .drop_duplicates(
        subset=["appliance"],
        keep="last"
    )
    .copy()
)

# ============================================================
# PROCESS APPLIANCES
# ============================================================

results = []

for appliance in APPLIANCES:

    print("\n" + "=" * 70)
    print(f"PROCESSING: {appliance}")
    print("=" * 70)

    appliance_start = time.time()

    # --------------------------------------------------------
    # SYSTEM PROFILE
    # --------------------------------------------------------

    profile = system_state[
        system_state["appliance"] == appliance
    ]

    if profile.empty:

        print(
            f"[WARNING] No system profile for {appliance}"
        )

        continue

    profile = profile.iloc[0]

    # --------------------------------------------------------
    # LOAD RL MODEL
    # --------------------------------------------------------

    model_file = os.path.join(
        RL_MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    print("Loading RL model...")

    model, scaler, model_features = load_model_package(
        model_file
    )

    print(
        f"Model: {type(model).__name__}"
    )

    print(
        f"RL features: {len(model_features)}"
    )

    # --------------------------------------------------------
    # VALIDATE FEATURE LIST
    # --------------------------------------------------------

    if len(model_features) != 17:

        print(
            f"[WARNING] Expected 17 RL features, "
            f"found {len(model_features)}"
        )

    # --------------------------------------------------------
    # LOAD ENVIRONMENT
    # --------------------------------------------------------

    env_file = os.path.join(
        RL_DATA_DIR,
        f"{appliance}_rl_environment.csv"
    )

    print("Loading RL environment sample...")

    # IMPORTANT:
    # Never load the entire 23M-row dataset.
    # Only read a manageable sample.

    SAMPLE_ROWS = 10000

    try:

        env = pd.read_csv(
            env_file,
            nrows=SAMPLE_ROWS
        )

    except Exception as e:

        print(
            f"[ERROR] Could not load environment: {e}"
        )

        continue

    print(
        f"Environment sample rows: {len(env)}"
    )

    # --------------------------------------------------------
    # FEATURE PREPARATION
    # --------------------------------------------------------

    try:

        X = prepare_features(
            env,
            model_features
        )

    except Exception as e:

        print(
            f"[ERROR] Feature preparation failed: {e}"
        )

        continue

    # --------------------------------------------------------
    # SCALING
    # --------------------------------------------------------

    if scaler is not None:

        print("Applying model scaler...")

        try:

            X_scaled = scaler.transform(X)

        except Exception as e:

            print(
                f"[ERROR] Scaler failed: {e}"
            )

            continue

    else:

        X_scaled = X

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    print("Generating RL predictions...")

    try:

        predictions = model.predict(
            X_scaled
        )

    except Exception as e:

        print(
            f"[ERROR] Prediction failed: {e}"
        )

        continue

    predictions = np.asarray(
        predictions,
        dtype=float
    )

    # --------------------------------------------------------
    # ACTION GENERATION
    # --------------------------------------------------------

    predicted_actions = np.array(
        [
            choose_action(x)
            for x in predictions
        ],
        dtype=int
    )

    action_counts = pd.Series(
        predicted_actions
    ).value_counts()

    maintain_count = int(
        action_counts.get(0, 0)
    )

    reduce_count = int(
        action_counts.get(1, 0)
    )

    shift_count = int(
        action_counts.get(2, 0)
    )

    turn_off_count = int(
        action_counts.get(3, 0)
    )

    total_actions = len(
        predicted_actions
    )

    # --------------------------------------------------------
    # CURRENT SYSTEM METRICS
    # --------------------------------------------------------

    current_power = safe_numeric(
        env["power_w"].mean()
        if "power_w" in env.columns
        else 0
    )

    current_energy = safe_numeric(
        env["energy_kwh"].sum()
        if "energy_kwh" in env.columns
        else 0
    )

    peak_risk = safe_numeric(
        env["peak_risk"].mean()
        if "peak_risk" in env.columns
        else 0
    )

    anomaly_score = safe_numeric(
        env["anomaly_score"].mean()
        if "anomaly_score" in env.columns
        else 0
    )

    # --------------------------------------------------------
    # PROFILE METRICS FROM 13A
    # --------------------------------------------------------

    user_behavior_score = safe_numeric(
        profile.get(
            "user_behavior_score",
            0
        )
    )

    predicted_peak = safe_numeric(
        profile.get(
            "predicted_peak_power_w",
            0
        )
    )

    actual_peak = safe_numeric(
        profile.get(
            "actual_peak_power_w",
            0
        )
    )

    savings_kwh = safe_numeric(
        profile.get(
            "estimated_savings_kwh",
            0
        )
    )

    savings_percentage = safe_numeric(
        profile.get(
            "estimated_savings_percentage",
            0
        )
    )

    adaptation_score = safe_numeric(
        profile.get(
            "adaptation_score",
            0
        )
    )

    self_adaptation_score = safe_numeric(
        profile.get(
            "self_adaptation_score",
            0
        )
    )

    intelligence_score = safe_numeric(
        profile.get(
            "system_intelligence_score",
            0
        )
    )

    system_status = str(
        profile.get(
            "system_status",
            "Unknown"
        )
    )

    # --------------------------------------------------------
    # RECOMMENDED ACTION
    # --------------------------------------------------------

    if turn_off_count >= max(
        reduce_count,
        shift_count,
        maintain_count
    ):

        recommended_action = "turn_off"

    elif shift_count >= max(
        reduce_count,
        maintain_count
    ):

        recommended_action = "shift"

    elif reduce_count > maintain_count:

        recommended_action = "reduce"

    else:

        recommended_action = "maintain"

    # --------------------------------------------------------
    # ACTION RATE
    # --------------------------------------------------------

    if total_actions > 0:

        adaptive_action_rate = (
            (
                reduce_count
                + shift_count
                + turn_off_count
            )
            /
            total_actions
            * 100
        )

    else:

        adaptive_action_rate = 0

    # --------------------------------------------------------
    # POLICY CONFIDENCE
    # --------------------------------------------------------

    if total_actions > 0:

        action_counts_values = np.array(
            [
                maintain_count,
                reduce_count,
                shift_count,
                turn_off_count
            ],
            dtype=float
        )

        dominant_ratio = (
            action_counts_values.max()
            /
            total_actions
        )

        policy_confidence = (
            dominant_ratio * 100
        )

    else:

        policy_confidence = 0

    # --------------------------------------------------------
    # PREDICTION QUALITY
    # --------------------------------------------------------

    prediction_mean = safe_numeric(
        np.mean(predictions)
    )

    prediction_std = safe_numeric(
        np.std(predictions)
    )

    # --------------------------------------------------------
    # UNIFIED INTELLIGENCE SCORE
    # --------------------------------------------------------

    unified_score = (
        intelligence_score * 0.30
        +
        user_behavior_score * 0.15
        +
        adaptation_score * 0.15
        +
        self_adaptation_score * 0.15
        +
        savings_percentage * 2.0 * 0.15
        +
        policy_confidence * 0.10
    )

    unified_score = min(
        100,
        max(
            0,
            unified_score
        )
    )

    # --------------------------------------------------------
    # DECISION STATUS
    # --------------------------------------------------------

    if unified_score >= 70:

        decision_status = (
            "Highly Intelligent"
        )

    elif unified_score >= 45:

        decision_status = (
            "Developing Intelligence"
        )

    elif unified_score >= 20:

        decision_status = (
            "Basic Intelligence"
        )

    else:

        decision_status = (
            "Early Intelligence"
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = {

        "appliance": appliance,

        "sample_rows": total_actions,

        "average_power_w": current_power,

        "sample_energy_kwh": current_energy,

        "peak_risk": peak_risk,

        "anomaly_score": anomaly_score,

        "actual_peak_power_w": actual_peak,

        "predicted_peak_power_w": predicted_peak,

        "peak_prediction_error_w":
            abs(
                actual_peak
                -
                predicted_peak
            ),

        "estimated_savings_kwh":
            savings_kwh,

        "estimated_savings_percentage":
            savings_percentage,

        "user_behavior_score":
            user_behavior_score,

        "adaptation_score":
            adaptation_score,

        "self_adaptation_score":
            self_adaptation_score,

        "system_intelligence_score":
            intelligence_score,

        "rl_prediction_mean":
            prediction_mean,

        "rl_prediction_std":
            prediction_std,

        "maintain_actions":
            maintain_count,

        "reduce_actions":
            reduce_count,

        "shift_actions":
            shift_count,

        "turn_off_actions":
            turn_off_count,

        "adaptive_action_rate_percentage":
            adaptive_action_rate,

        "policy_confidence":
            policy_confidence,

        "recommended_action":
            recommended_action,

        "unified_intelligence_score":
            unified_score,

        "decision_status":
            decision_status,

        "system_status":
            system_status,

        "processing_time_minutes":
            (
                time.time()
                -
                appliance_start
            )
            / 60
    }

    results.append(result)

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print(f"RESULT: {appliance}")
    print("-" * 70)

    print(
        f"Average power: "
        f"{current_power:.4f} W"
    )

    print(
        f"Peak risk: "
        f"{peak_risk:.4f}"
    )

    print(
        f"Actual peak: "
        f"{actual_peak:.2f} W"
    )

    print(
        f"Predicted peak: "
        f"{predicted_peak:.2f} W"
    )

    print(
        f"Estimated savings: "
        f"{savings_kwh:.4f} kWh"
    )

    print(
        f"Savings percentage: "
        f"{savings_percentage:.4f}%"
    )

    print(
        "\nACTION DISTRIBUTION"
    )

    print(
        f"0 (maintain): "
        f"{maintain_count}"
    )

    print(
        f"1 (reduce): "
        f"{reduce_count}"
    )

    print(
        f"2 (shift): "
        f"{shift_count}"
    )

    print(
        f"3 (turn_off): "
        f"{turn_off_count}"
    )

    print(
        f"\nRecommended action: "
        f"{recommended_action}"
    )

    print(
        f"Policy confidence: "
        f"{policy_confidence:.2f}%"
    )

    print(
        f"Unified intelligence score: "
        f"{unified_score:.2f}"
    )

    print(
        f"Decision status: "
        f"{decision_status}"
    )

# ============================================================
# FINAL DATAFRAME
# ============================================================

if not results:

    print("\nERROR: No appliance results generated.")

    raise SystemExit(1)

final_df = pd.DataFrame(
    results
)

# ============================================================
# VALIDATION
# ============================================================

print("\n")
print("=" * 70)
print("MODULE 13B VALIDATION")
print("=" * 70)

print(
    f"\nROWS: {len(final_df)}"
)

print(
    f"COLUMNS: {len(final_df.columns)}"
)

null_count = int(
    final_df.isnull().sum().sum()
)

print(
    f"\nNULLS: {null_count}"
)

if null_count > 0:

    final_df = final_df.fillna(0)

    print(
        "NULLS AFTER CLEANING:",
        int(
            final_df.isnull()
            .sum()
            .sum()
        )
    )

else:

    print("NO NULLS")

# ============================================================
# DUPLICATE CHECK
# ============================================================

duplicate_columns = (
    final_df.columns[
        final_df.columns.duplicated()
    ]
    .tolist()
)

print(
    f"Duplicate columns: "
    f"{len(duplicate_columns)}"
)

# ============================================================
# UNIFIED PIPELINE RESULTS
# ============================================================

print("\n")
print("=" * 70)
print("UNIFIED PIPELINE RESULTS")
print("=" * 70)

display_columns = [

    "appliance",
    "average_power_w",
    "peak_risk",
    "actual_peak_power_w",
    "predicted_peak_power_w",
    "estimated_savings_percentage",
    "recommended_action",
    "policy_confidence",
    "unified_intelligence_score",
    "decision_status"
]

print(
    final_df[
        display_columns
    ].to_string(index=False)
)

# ============================================================
# SUMMARY STATISTICS
# ============================================================

print("\n")
print("=" * 70)
print("PIPELINE SUMMARY")
print("=" * 70)

print(
    f"\nAverage savings: "
    f"{final_df['estimated_savings_percentage'].mean():.4f}%"
)

print(
    f"Average policy confidence: "
    f"{final_df['policy_confidence'].mean():.4f}%"
)

print(
    f"Average intelligence score: "
    f"{final_df['unified_intelligence_score'].mean():.4f}"
)

print(
    f"Total estimated savings: "
    f"{final_df['estimated_savings_kwh'].sum():.4f} kWh"
)

# ============================================================
# SAVE MAIN OUTPUT
# ============================================================

main_output = os.path.join(
    OUTPUT_DIR,
    "unified_prediction_rl_pipeline.csv"
)

final_df.to_csv(
    main_output,
    index=False
)

# ============================================================
# SAVE ACTION SUMMARY
# ============================================================

action_summary = final_df[
    [
        "appliance",
        "maintain_actions",
        "reduce_actions",
        "shift_actions",
        "turn_off_actions",
        "adaptive_action_rate_percentage",
        "recommended_action",
        "policy_confidence"
    ]
].copy()

action_output = os.path.join(
    OUTPUT_DIR,
    "unified_action_summary.csv"
)

action_summary.to_csv(
    action_output,
    index=False
)

# ============================================================
# SAVE DASHBOARD SUMMARY
# ============================================================

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

dashboard_df = final_df[
    dashboard_columns
].copy()

dashboard_output = os.path.join(
    OUTPUT_DIR,
    "dashboard_system_state.csv"
)

dashboard_df.to_csv(
    dashboard_output,
    index=False
)

# ============================================================
# FINAL
# ============================================================

total_time = (
    time.time()
    -
    start_time
) / 60

print("\n")
print("=" * 70)
print("MODULE 13B COMPLETE")
print("=" * 70)

print(
    f"\nUnified pipeline output:"
)

print(
    main_output
)

print(
    "\nAction summary:"
)

print(
    action_output
)

print(
    "\nDashboard system state:"
)

print(
    dashboard_output
)

print(
    f"\nTotal time: "
    f"{total_time:.2f} minutes"
)

print("=" * 70)