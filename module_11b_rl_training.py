import os
import glob
import time
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# ============================================================
# MODULE 11B — RL AGENT TRAINING
# ============================================================

BASE_DIR = r"E:\energy_project"

RL_DATA_DIR = os.path.join(BASE_DIR, "rl_data")
RL_MODEL_DIR = os.path.join(BASE_DIR, "rl_models")

os.makedirs(RL_MODEL_DIR, exist_ok=True)

RANDOM_SEED = 42
TRAINING_SAMPLES = 1_000_000

# ============================================================
# 17 STATE FEATURES + ACTION = 18 FEATURES
# ============================================================

STATE_FEATURES = [
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

RL_FEATURES = STATE_FEATURES + ["action"]

ACTIONS = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off",
}

# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 11B — RL AGENT TRAINING")
print("=" * 70)

print()
print("RL FEATURES:")
for i, feature in enumerate(RL_FEATURES, 1):
    print(f" {i:2d}. {feature}")

print()
print("Total features:", len(RL_FEATURES))

if len(RL_FEATURES) != 18:
    raise RuntimeError(
        f"ERROR: Expected 18 features but found {len(RL_FEATURES)}"
    )

# ============================================================
# FIND RL ENVIRONMENT FILES
# ============================================================

environment_files = sorted(
    glob.glob(os.path.join(RL_DATA_DIR, "*_rl_environment.csv"))
)

if not environment_files:
    print()
    print("ERROR: No RL environment files found.")
    print(RL_DATA_DIR)
    raise SystemExit(1)

print()
print("RL environment files found:", len(environment_files))

for f in environment_files:
    print(" -", os.path.basename(f))

# ============================================================
# TRAINING FUNCTION
# ============================================================

def train_appliance(environment_file):

    appliance = os.path.basename(environment_file).replace(
        "_rl_environment.csv", ""
    )

    print()
    print("=" * 70)
    print("PROCESSING:", appliance)
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print("Loading RL environment...")

    df = pd.read_csv(environment_file)

    print("Rows loaded:", len(df))
    print("Columns loaded:", len(df.columns))

    # --------------------------------------------------------
    # CHECK REQUIRED COLUMNS
    # --------------------------------------------------------

    required_columns = RL_FEATURES + ["base_reward", "reward"]

    missing_columns = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing_columns:
        print()
        print("ERROR: Missing columns:")
        for c in missing_columns:
            print(" -", c)

        return None

    print("All required columns found.")

    # --------------------------------------------------------
    # CHECK ACTION VALUES
    # --------------------------------------------------------

    print()
    print("Action distribution:")

    print(
        df["action"]
        .value_counts()
        .sort_index()
    )

    invalid_actions = ~df["action"].isin(ACTIONS.keys())

    if invalid_actions.any():
        print()
        print(
            "ERROR: Invalid action values:",
            df.loc[invalid_actions, "action"].unique()
        )

        return None

    # --------------------------------------------------------
    # SELECT REQUIRED COLUMNS
    # --------------------------------------------------------

    print()
    print("Selecting RL training columns...")

    training_columns = RL_FEATURES + [
        "base_reward",
        "reward"
    ]

    data = df[training_columns].copy()

    # --------------------------------------------------------
    # REMOVE INFINITE VALUES
    # --------------------------------------------------------

    data.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    # --------------------------------------------------------
    # REMOVE NULLS
    # --------------------------------------------------------

    before = len(data)

    data.dropna(
        subset=RL_FEATURES + ["reward"],
        inplace=True
    )

    after = len(data)

    print("Rows before cleaning:", before)
    print("Rows after cleaning:", after)
    print("Rows removed:", before - after)

    if after == 0:
        print("ERROR: No usable training rows.")
        return None

    # --------------------------------------------------------
    # SAMPLE TRAINING DATA
    # --------------------------------------------------------

    sample_size = min(
        TRAINING_SAMPLES,
        len(data)
    )

    print()
    print("Training sample size:", sample_size)

    if len(data) > sample_size:

        data = data.sample(
            n=sample_size,
            random_state=RANDOM_SEED
        )

    data.reset_index(drop=True, inplace=True)

    # --------------------------------------------------------
    # PREPARE X / Y
    # --------------------------------------------------------

    print()
    print("Preparing training matrix...")

    X = data[RL_FEATURES].copy()

    y = data["reward"].astype(float)

    print("X shape:", X.shape)
    print("Y shape:", y.shape)

    if X.shape[1] != 18:
        raise RuntimeError(
            f"ERROR: X contains {X.shape[1]} features. "
            f"Expected 18."
        )

    # --------------------------------------------------------
    # VERIFY FEATURE ORDER
    # --------------------------------------------------------

    print()
    print("FEATURE ORDER:")

    for i, feature in enumerate(X.columns, 1):
        print(f" {i:2d}. {feature}")

    if list(X.columns) != RL_FEATURES:
        raise RuntimeError(
            "ERROR: Feature order mismatch."
        )

    # --------------------------------------------------------
    # SCALER
    # --------------------------------------------------------

    print()
    print("Fitting feature scaler...")

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    # --------------------------------------------------------
    # RANDOM FOREST
    # --------------------------------------------------------

    print()
    print("Training Random Forest...")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=2,
        random_state=RANDOM_SEED,
        n_jobs=-1
    )

    train_start = time.time()

    model.fit(
        X_scaled,
        y
    )

    training_time = (
        time.time() - train_start
    ) / 60

    # --------------------------------------------------------
    # TRAINING PREDICTIONS
    # --------------------------------------------------------

    print("Generating training predictions...")

    predictions = model.predict(X_scaled)

    mae = mean_absolute_error(
        y,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y,
            predictions
        )
    )

    # --------------------------------------------------------
    # REWARD STATISTICS
    # --------------------------------------------------------

    reward_mean = float(y.mean())
    reward_min = float(y.min())
    reward_max = float(y.max())

    # --------------------------------------------------------
    # MODEL PACKAGE
    # --------------------------------------------------------

    model_package = {
        "module": "11B",
        "appliance": appliance,

        # Actual trained model
        "model": model,

        # Scaler fitted on exactly 18 features
        "scaler": scaler,

        # Exact feature order
        "features": RL_FEATURES.copy(),

        # Available actions
        "actions": ACTIONS.copy(),

        # Training information
        "training_samples": len(data),
        "random_seed": RANDOM_SEED,

        # Metrics
        "mae": float(mae),
        "rmse": float(rmse),
        "reward_mean": reward_mean,
        "reward_min": reward_min,
        "reward_max": reward_max,
    }

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    model_file = os.path.join(
        RL_MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    joblib.dump(
        model_package,
        model_file
    )

    # --------------------------------------------------------
    # VERIFY SAVED MODEL
    # --------------------------------------------------------

    print()
    print("Verifying saved model...")

    saved_package = joblib.load(
        model_file
    )

    saved_features = saved_package["features"]
    saved_model = saved_package["model"]
    saved_scaler = saved_package["scaler"]

    print(
        "Saved model type:",
        type(saved_model).__name__
    )

    print(
        "Saved scaler type:",
        type(saved_scaler).__name__
    )

    print(
        "Saved features:",
        len(saved_features)
    )

    if len(saved_features) != 18:
        raise RuntimeError(
            "ERROR: Saved model does not contain 18 features."
        )

    if saved_features != RL_FEATURES:
        raise RuntimeError(
            "ERROR: Saved feature order does not match RL_FEATURES."
        )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    total_time = (
        time.time() - start_time
    ) / 60

    print()
    print("-" * 70)
    print("RESULT:", appliance)
    print("-" * 70)

    print(
        f"Training samples: {len(data)}"
    )

    print(
        f"Features: {len(RL_FEATURES)}"
    )

    print(
        f"MAE: {mae:.6f}"
    )

    print(
        f"RMSE: {rmse:.6f}"
    )

    print(
        f"Reward mean: {reward_mean:.6f}"
    )

    print(
        f"Reward min: {reward_min:.6f}"
    )

    print(
        f"Reward max: {reward_max:.6f}"
    )

    print(
        f"Training time: {training_time:.2f} minutes"
    )

    print(
        "Model:",
        model_file
    )

    return {
        "appliance": appliance,
        "training_samples": len(data),
        "features": len(RL_FEATURES),
        "MAE": mae,
        "RMSE": rmse,
        "reward_mean": reward_mean,
        "reward_min": reward_min,
        "reward_max": reward_max,
        "training_time_minutes": training_time,
        "model_file": model_file,
    }


# ============================================================
# TRAIN ALL APPLIANCES
# ============================================================

results = []

overall_start = time.time()

for environment_file in environment_files:

    try:

        result = train_appliance(
            environment_file
        )

        if result is not None:
            results.append(result)

    except Exception as e:

        print()
        print("ERROR PROCESSING:")
        print(environment_file)

        print(
            type(e).__name__,
            ":",
            str(e)
        )

        print()
        print("Continuing with next appliance...")

# ============================================================
# SAVE SUMMARY
# ============================================================

if not results:

    print()
    print("=" * 70)
    print("NO MODELS WERE TRAINED")
    print("=" * 70)

    raise SystemExit(1)

summary = pd.DataFrame(results)

summary_file = os.path.join(
    RL_MODEL_DIR,
    "rl_training_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

# ============================================================
# FINAL OUTPUT
# ============================================================

total_time = (
    time.time() - overall_start
) / 60

print()
print("=" * 70)
print("MODULE 11B COMPLETE")
print("=" * 70)

print(
    summary[
        [
            "appliance",
            "training_samples",
            "features",
            "MAE",
            "RMSE",
            "reward_mean",
            "reward_min",
            "reward_max",
            "training_time_minutes",
        ]
    ].to_string(index=False)
)

print()
print("Summary saved to:")
print(summary_file)

print()
print("Models saved to:")
print(RL_MODEL_DIR)

print()
print(
    f"Total time: {total_time:.2f} minutes"
)

print("=" * 70)