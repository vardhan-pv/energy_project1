import os
import glob
import time
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ============================================================
# MODULE 11C — RL POLICY EVALUATION
# ============================================================

BASE_DIR = r"E:\energy_project"

RL_DATA_DIR = os.path.join(BASE_DIR, "rl_data")
RL_MODEL_DIR = os.path.join(BASE_DIR, "rl_models")
EVAL_DIR = os.path.join(BASE_DIR, "rl_evaluation")

os.makedirs(EVAL_DIR, exist_ok=True)

RANDOM_SEED = 42

# Number of rows evaluated per appliance
EVALUATION_ROWS = 100_000

# ============================================================
# STATE FEATURES
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

ACTIONS = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off",
}

EXPECTED_FEATURES = STATE_FEATURES + ["action"]

# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 11C — RL POLICY EVALUATION")
print("=" * 70)

print()
print("State features:", len(STATE_FEATURES))
print("Model features:", len(EXPECTED_FEATURES))
print("Actions:", ACTIONS)

# ============================================================
# FIND ENVIRONMENT FILES
# ============================================================

environment_files = sorted(
    glob.glob(
        os.path.join(
            RL_DATA_DIR,
            "*_rl_environment.csv"
        )
    )
)

if not environment_files:
    print("ERROR: No RL environment files found.")
    raise SystemExit(1)

print()
print("Environment files found:", len(environment_files))

# ============================================================
# EVALUATION FUNCTION
# ============================================================

def evaluate_appliance(environment_file):

    appliance = os.path.basename(
        environment_file
    ).replace(
        "_rl_environment.csv",
        ""
    )

    print()
    print("=" * 70)
    print("PROCESSING:", appliance)
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------------
    # MODEL FILE
    # --------------------------------------------------------

    model_file = os.path.join(
        RL_MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    if not os.path.exists(model_file):
        print("ERROR: Model not found:")
        print(model_file)
        return None

    print("Loading RL model...")

    package = joblib.load(model_file)

    model = package["model"]
    scaler = package["scaler"]
    model_features = package["features"]

    print(
        "Model type:",
        type(model).__name__
    )

    print(
        "Model features:",
        len(model_features)
    )

    # --------------------------------------------------------
    # MODEL VALIDATION
    # --------------------------------------------------------

    if model_features != EXPECTED_FEATURES:
        print()
        print("ERROR: Model feature mismatch.")
        print("Expected:")
        print(EXPECTED_FEATURES)
        print()
        print("Found:")
        print(model_features)
        return None

    if len(model_features) != 18:
        print("ERROR: Model does not contain 18 features.")
        return None

    print("Model feature validation: PASS")

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    print()
    print("Loading RL environment...")

    required_columns = STATE_FEATURES + [
        "action",
        "reward",
        "base_reward",
        "power_w",
        "energy_kwh",
    ]

    # Remove duplicates while preserving order
    required_columns = list(
        dict.fromkeys(required_columns)
    )

    df = pd.read_csv(
        environment_file,
        usecols=required_columns
    )

    print("Rows loaded:", len(df))

    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    df.replace(
        [np.inf, -np.inf],
        np.nan,
        inplace=True
    )

    df.dropna(
        subset=STATE_FEATURES + ["reward"],
        inplace=True
    )

    print(
        "Rows after cleaning:",
        len(df)
    )

    if len(df) == 0:
        print("ERROR: No valid rows.")
        return None

    # --------------------------------------------------------
    # SAMPLE
    # --------------------------------------------------------

    evaluation_rows = min(
        EVALUATION_ROWS,
        len(df)
    )

    if len(df) > evaluation_rows:

        df = df.sample(
            n=evaluation_rows,
            random_state=RANDOM_SEED
        )

    df.reset_index(
        drop=True,
        inplace=True
    )

    print(
        "Evaluation rows:",
        len(df)
    )

    # --------------------------------------------------------
    # STATE MATRIX
    # --------------------------------------------------------

    X_state = df[
        STATE_FEATURES
    ].copy()

    # --------------------------------------------------------
    # BASELINE REWARD
    # --------------------------------------------------------

    baseline_reward = df[
        "reward"
    ].astype(float)

    # --------------------------------------------------------
    # EVALUATE ALL ACTIONS
    # --------------------------------------------------------

    print()
    print(
        "Evaluating all 4 candidate actions..."
    )

    action_rewards = {}

    for action in ACTIONS.keys():

        print(
            f"Evaluating action {action}: "
            f"{ACTIONS[action]}"
        )

        X_action = X_state.copy()

        # Add candidate action
        X_action["action"] = action

        # Exact model order
        X_action = X_action[
            EXPECTED_FEATURES
        ]

        # Verify order
        if list(X_action.columns) != EXPECTED_FEATURES:
            raise RuntimeError(
                "Feature order mismatch."
            )

        # Scale
        X_scaled = scaler.transform(
            X_action
        )

        # Predict reward
        predicted_reward = model.predict(
            X_scaled
        )

        action_rewards[action] = (
            predicted_reward
        )

    # --------------------------------------------------------
    # BUILD REWARD MATRIX
    # --------------------------------------------------------

    reward_matrix = np.column_stack(
        [
            action_rewards[0],
            action_rewards[1],
            action_rewards[2],
            action_rewards[3],
        ]
    )

    # --------------------------------------------------------
    # SELECT BEST ACTION
    # --------------------------------------------------------

    best_action_index = np.argmax(
        reward_matrix,
        axis=1
    )

    best_predicted_reward = np.max(
        reward_matrix,
        axis=1
    )

    # --------------------------------------------------------
    # CREATE EVALUATION DATAFRAME
    # --------------------------------------------------------

    result = df.copy()

    result["baseline_reward"] = (
        baseline_reward.values
    )

    result["predicted_reward_maintain"] = (
        action_rewards[0]
    )

    result["predicted_reward_reduce"] = (
        action_rewards[1]
    )

    result["predicted_reward_shift"] = (
        action_rewards[2]
    )

    result["predicted_reward_turn_off"] = (
        action_rewards[3]
    )

    result["recommended_action"] = (
        best_action_index
    )

    result["recommended_action_name"] = [
        ACTIONS[int(a)]
        for a in best_action_index
    ]

    result["recommended_reward"] = (
        best_predicted_reward
    )

    # --------------------------------------------------------
    # REWARD IMPROVEMENT
    # --------------------------------------------------------

    result["reward_improvement"] = (
        result["recommended_reward"]
        - result["baseline_reward"]
    )

    # --------------------------------------------------------
    # ACTION DISTRIBUTION
    # --------------------------------------------------------

    action_counts = (
        result[
            "recommended_action"
        ]
        .value_counts()
        .sort_index()
    )

    print()
    print("RECOMMENDED ACTION DISTRIBUTION")

    for action in ACTIONS.keys():

        count = int(
            action_counts.get(
                action,
                0
            )
        )

        percentage = (
            count / len(result) * 100
        )

        print(
            f"{action} "
            f"({ACTIONS[action]}): "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    baseline_mean = (
        result["baseline_reward"].mean()
    )

    recommended_mean = (
        result["recommended_reward"].mean()
    )

    reward_mae = np.mean(
        np.abs(
            result["baseline_reward"]
            -
            result["recommended_reward"]
        )
    )

    reward_rmse = np.sqrt(
        np.mean(
            (
                result["baseline_reward"]
                -
                result["recommended_reward"]
            ) ** 2
        )
    )

    # --------------------------------------------------------
    # ENERGY
    # --------------------------------------------------------

    total_energy = (
        result["energy_kwh"]
        .astype(float)
        .sum()
    )

    average_power = (
        result["power_w"]
        .astype(float)
        .mean()
    )

    maximum_power = (
        result["power_w"]
        .astype(float)
        .max()
    )

    # --------------------------------------------------------
    # SAVE EVALUATION FILE
    # --------------------------------------------------------

    output_file = os.path.join(
        EVAL_DIR,
        f"{appliance}_rl_policy_evaluation.csv"
    )

    result.to_csv(
        output_file,
        index=False
    )

    elapsed = (
        time.time() - start_time
    ) / 60

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("RESULT:", appliance)
    print("-" * 70)

    print(
        f"Evaluation rows: {len(result)}"
    )

    print(
        f"Baseline mean reward: "
        f"{baseline_mean:.6f}"
    )

    print(
        f"Recommended mean reward: "
        f"{recommended_mean:.6f}"
    )

    print(
        f"Reward MAE: "
        f"{reward_mae:.6f}"
    )

    print(
        f"Reward RMSE: "
        f"{reward_rmse:.6f}"
    )

    print(
        f"Reward improvement: "
        f"{recommended_mean - baseline_mean:.6f}"
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
        f"Maximum power: "
        f"{maximum_power:.2f} W"
    )

    print(
        "Output:",
        output_file
    )

    print(
        f"Time: {elapsed:.2f} minutes"
    )

    return {
        "appliance": appliance,
        "evaluation_rows": len(result),
        "baseline_mean_reward": baseline_mean,
        "recommended_mean_reward": recommended_mean,
        "reward_mae": reward_mae,
        "reward_rmse": reward_rmse,
        "reward_improvement": (
            recommended_mean - baseline_mean
        ),
        "total_energy_kwh": total_energy,
        "average_power_w": average_power,
        "maximum_power_w": maximum_power,
        "maintain_actions": int(
            action_counts.get(0, 0)
        ),
        "reduce_actions": int(
            action_counts.get(1, 0)
        ),
        "shift_actions": int(
            action_counts.get(2, 0)
        ),
        "turn_off_actions": int(
            action_counts.get(3, 0)
        ),
        "evaluation_time_minutes": elapsed,
    }


# ============================================================
# RUN ALL
# ============================================================

results = []

overall_start = time.time()

for environment_file in environment_files:

    try:

        result = evaluate_appliance(
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

# ============================================================
# SUMMARY
# ============================================================

if not results:

    print()
    print("No appliances evaluated.")
    raise SystemExit(1)

summary = pd.DataFrame(results)

summary_file = os.path.join(
    EVAL_DIR,
    "rl_policy_evaluation_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

total_time = (
    time.time() - overall_start
) / 60

# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("MODULE 11C COMPLETE")
print("=" * 70)

display_columns = [
    "appliance",
    "evaluation_rows",
    "baseline_mean_reward",
    "recommended_mean_reward",
    "reward_mae",
    "reward_rmse",
    "reward_improvement",
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions",
    "total_energy_kwh",
    "average_power_w",
    "maximum_power_w",
    "evaluation_time_minutes",
]

print(
    summary[
        display_columns
    ].to_string(index=False)
)

print()
print("Summary saved to:")
print(summary_file)

print()
print("Evaluation files saved to:")
print(EVAL_DIR)

print()
print(
    f"Total time: {total_time:.2f} minutes"
)

print("=" * 70)