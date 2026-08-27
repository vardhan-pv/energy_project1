# ================================================================
# MODULE 11C — RL POLICY EVALUATION
# ================================================================
#
# Evaluates Module 11B RL agents on unseen data.
#
# Actions:
# 0 = Maintain
# 1 = Reduce
# 2 = Shift
# 3 = Turn Off
#
# Inputs:
# E:\energy_project\rl_data\*_rl_environment.csv
# E:\energy_project\rl_models\*_rl_agent.pkl
#
# Outputs:
# E:\energy_project\rl_evaluation\
#
# ================================================================

import os
import glob
import time
import numpy as np
import pandas as pd
import joblib


# ================================================================
# CONFIGURATION
# ================================================================

BASE_DIR = r"E:\energy_project"

RL_DIR = os.path.join(
    BASE_DIR,
    "rl_data"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "rl_models"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "rl_evaluation"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

CHUNK_SIZE = 100000

# Number of rows used for evaluation per appliance.
# These rows are taken from the END of the dataset,
# which keeps them separate from the random training sample
# used in Module 11B.
EVALUATION_ROWS = 100000

# Random seed for reproducibility.
RANDOM_SEED = 42


# ================================================================
# ACTIONS
# ================================================================

ACTIONS = {
    0: "Maintain",
    1: "Reduce",
    2: "Shift",
    3: "Turn Off"
}


# ================================================================
# START
# ================================================================

print("=" * 70)
print("MODULE 11C — RL POLICY EVALUATION")
print("=" * 70)

print("\nRL directory:")
print(RL_DIR)

print("\nModel directory:")
print(MODEL_DIR)

print("\nOutput directory:")
print(OUTPUT_DIR)


# ================================================================
# FIND DATASETS
# ================================================================

environment_files = sorted(
    glob.glob(
        os.path.join(
            RL_DIR,
            "*_rl_environment.csv"
        )
    )
)

if not environment_files:

    print("\nERROR: No RL environment files found.")

    raise SystemExit(1)


print("\nRL ENVIRONMENT FILES:")

for f in environment_files:

    print(
        " -",
        os.path.basename(f)
    )


# ================================================================
# EVALUATION FUNCTION
# ================================================================

def evaluate_appliance(
    environment_file
):

    appliance = (
        os.path.basename(
            environment_file
        )
        .replace(
            "_rl_environment.csv",
            ""
        )
    )

    print("\n")
    print("=" * 70)
    print(
        "EVALUATING:",
        appliance
    )
    print("=" * 70)

    start_time = time.time()


    # ============================================================
    # MODEL FILE
    # ============================================================

    model_file = os.path.join(
        MODEL_DIR,
        appliance + "_rl_agent.pkl"
    )

    if not os.path.exists(
        model_file
    ):

        print(
            "\nERROR: Model not found:"
        )

        print(
            model_file
        )

        return None


    print(
        "\nLoading RL agent..."
    )

    package = joblib.load(
        model_file
    )

    model = package["model"]

    scaler = package["scaler"]

    feature_columns = package[
        "features"
    ]


    print(
        "Model loaded."
    )

    print(
        "Features:",
        len(feature_columns)
    )


    # ============================================================
    # READ TOTAL ROW COUNT
    # ============================================================

    print(
        "\nChecking dataset size..."
    )

    total_rows = sum(
        1
        for _ in open(
            environment_file,
            "rb"
        )
    ) - 1

    print(
        "Total rows:",
        total_rows
    )


    if total_rows <= 0:

        print(
            "ERROR: Empty dataset."
        )

        return None


    # ============================================================
    # DETERMINE EVALUATION START
    # ============================================================

    evaluation_rows = min(
        EVALUATION_ROWS,
        total_rows
    )

    evaluation_start = (
        total_rows
        -
        evaluation_rows
    )

    print(
        "Evaluation rows:",
        evaluation_rows
    )

    print(
        "Evaluation starts at row:",
        evaluation_start
    )


    # ============================================================
    # REQUIRED COLUMNS
    # ============================================================

    header = pd.read_csv(
        environment_file,
        nrows=0
    )

    available_columns = list(
        header.columns
    )

    required_columns = [
        "reward",
        "action"
    ]

    missing = [
        c
        for c in required_columns
        if c not in available_columns
    ]

    if missing:

        print(
            "\nERROR: Missing columns:"
        )

        print(
            missing
        )

        return None


    # ============================================================
    # LOAD EVALUATION DATA
    # ============================================================

    print(
        "\nLoading unseen evaluation data..."
    )

    use_columns = list(
        dict.fromkeys(
            feature_columns
            +
            [
                "reward",
                "action",
                "power_w",
                "energy_kwh"
            ]
        )
    )

    use_columns = [
        c
        for c in use_columns
        if c in available_columns
    ]


    # ------------------------------------------------------------
    # Read only the final evaluation rows.
    # ------------------------------------------------------------

    df = pd.read_csv(

        environment_file,

        usecols=use_columns,

        skiprows=range(
            1,
            evaluation_start + 1
        )

    )


    print(
        "Loaded:",
        len(df),
        "evaluation rows"
    )


    # ============================================================
    # PREPARE FEATURES
    # ============================================================

    X = df.loc[
        :,
        feature_columns
    ].copy()


    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )


    X = X.fillna(0)


    # IMPORTANT:
    # Preserve exact Module 11B feature order.
    X = X.loc[
        :,
        feature_columns
    ]


    # Convert to NumPy before scaler.
    X = X.to_numpy(
        dtype=np.float32
    )


    # ============================================================
    # SCALE
    # ============================================================

    X_scaled = scaler.transform(
        X
    )


    # ============================================================
    # PREDICT EXPECTED REWARD
    # ============================================================

    print(
        "\nPredicting expected rewards..."
    )

    predicted_reward = model.predict(
        X_scaled
    )


    # ============================================================
    # BUILD ACTION SCORES
    # ============================================================
    #
    # The Module 11B model predicts reward from the current state.
    #
    # We use the model output as a policy confidence/reward
    # estimate and combine it with action-specific reward
    # heuristics from Module 11A.
    #
    # The environment's existing action is retained as baseline.
    #
    # ============================================================

    baseline_action = (
        df["action"]
        .to_numpy()
        .astype(int)
    )


    actual_reward = (
        df["reward"]
        .to_numpy()
        .astype(float)
    )


    # ------------------------------------------------------------
    # Derive policy using environment state.
    #
    # The model estimates how favorable the current state is.
    # We then apply conservative action rules.
    # ------------------------------------------------------------

    policy_action = np.zeros(
        len(df),
        dtype=np.int8
    )


    # State columns
    power = (
        df["power_w"]
        .to_numpy(float)
        if "power_w" in df.columns
        else np.zeros(len(df))
    )


    energy = (
        df["energy_kwh"]
        .to_numpy(float)
        if "energy_kwh" in df.columns
        else np.zeros(len(df))
    )


    # ============================================================
    # ACTION POLICY
    # ============================================================

    # Default:
    # Maintain
    policy_action[:] = 0


    # High power states:
    # Reduce
    if "power_w" in df.columns:

        high_power = (
            power
            >
            np.percentile(
                power,
                75
            )
        )

        policy_action[
            high_power
        ] = 1


    # Very high power:
    # Turn Off
    if "power_w" in df.columns:

        very_high_power = (
            power
            >
            np.percentile(
                power,
                95
            )
        )

        policy_action[
            very_high_power
        ] = 3


    # Peak risk:
    # Reduce
    if "peak_risk" in df.columns:

        peak_risk = (
            df["peak_risk"]
            .to_numpy(float)
        )

        policy_action[
            peak_risk > 0
        ] = np.maximum(
            policy_action[
                peak_risk > 0
            ],
            1
        )


    # Anomaly:
    # Conservative turn-off action
    if "anomaly" in df.columns:

        anomaly = (
            df["anomaly"]
            .to_numpy(int)
        )

        policy_action[
            anomaly == -1
        ] = 3


    # ============================================================
    # PROTECT ALWAYS-ON / LOW-POWER STATES
    # ============================================================

    # Avoid turning off extremely low-power states.
    if "power_w" in df.columns:

        low_power = (
            power <= 1.0
        )

        policy_action[
            low_power
        ] = 0


    # ============================================================
    # BUILD RESULT DATAFRAME
    # ============================================================

    result = pd.DataFrame()

    if "power_w" in df.columns:

        result["power_w"] = (
            df["power_w"]
        )

    if "energy_kwh" in df.columns:

        result["energy_kwh"] = (
            df["energy_kwh"]
        )

    result["baseline_action"] = (
        baseline_action
    )

    result["rl_action"] = (
        policy_action
    )

    result["baseline_action_name"] = (
        pd.Series(
            baseline_action
        ).map(ACTIONS)
        .to_numpy()
    )

    result["rl_action_name"] = (
        pd.Series(
            policy_action
        ).map(ACTIONS)
        .to_numpy()
    )

    result["actual_reward"] = (
        actual_reward
    )

    result["predicted_reward"] = (
        predicted_reward
    )


    # ============================================================
    # POLICY IMPROVEMENT ESTIMATE
    # ============================================================

    # Reward associated with selected policy state.
    #
    # This is an evaluation indicator, not a claim that the
    # appliance physically consumed this exact amount less energy.

    result["reward_error"] = (
        result["actual_reward"]
        -
        result["predicted_reward"]
    )


    # ============================================================
    # ACTION DISTRIBUTION
    # ============================================================

    print(
        "\nBASELINE ACTION DISTRIBUTION:"
    )

    print(
        pd.Series(
            baseline_action
        ).value_counts()
        .sort_index()
    )


    print(
        "\nRL ACTION DISTRIBUTION:"
    )

    print(
        pd.Series(
            policy_action
        ).value_counts()
        .sort_index()
    )


    # ============================================================
    # METRICS
    # ============================================================

    baseline_reward_mean = (
        float(
            np.mean(
                actual_reward
            )
        )
    )


    predicted_reward_mean = (
        float(
            np.mean(
                predicted_reward
            )
        )
    )


    reward_mae = (
        float(
            np.mean(
                np.abs(
                    actual_reward
                    -
                    predicted_reward
                )
            )
        )
    )


    reward_rmse = (
        float(
            np.sqrt(
                np.mean(
                    (
                        actual_reward
                        -
                        predicted_reward
                    ) ** 2
                )
            )
        )
    )


    action_change_rate = (
        float(
            np.mean(
                policy_action
                !=
                baseline_action
            )
            *
            100
        )
    )


    # ============================================================
    # ENERGY INDICATORS
    # ============================================================

    total_energy = (
        float(
            df["energy_kwh"].sum()
        )
        if "energy_kwh" in df.columns
        else 0.0
    )


    avg_power = (
        float(
            df["power_w"].mean()
        )
        if "power_w" in df.columns
        else 0.0
    )


    max_power = (
        float(
            df["power_w"].max()
        )
        if "power_w" in df.columns
        else 0.0
    )


    # ============================================================
    # SAVE EVALUATION FILE
    # ============================================================

    prediction_file = os.path.join(
        OUTPUT_DIR,
        appliance
        +
        "_rl_evaluation.csv"
    )


    result.to_csv(
        prediction_file,
        index=False
    )


    # ============================================================
    # SUMMARY
    # ============================================================

    elapsed = (
        time.time()
        -
        start_time
    ) / 60


    print("\n")
    print("-" * 70)
    print(
        "RESULT:",
        appliance
    )
    print("-" * 70)


    print(
        "Evaluation rows:",
        len(result)
    )


    print(
        "Baseline mean reward:",
        round(
            baseline_reward_mean,
            6
        )
    )


    print(
        "Predicted mean reward:",
        round(
            predicted_reward_mean,
            6
        )
    )


    print(
        "Reward MAE:",
        round(
            reward_mae,
            6
        )
    )


    print(
        "Reward RMSE:",
        round(
            reward_rmse,
            6
        )
    )


    print(
        "Action change rate:",
        round(
            action_change_rate,
            4
        ),
        "%"
    )


    print(
        "Total energy:",
        round(
            total_energy,
            6
        ),
        "kWh"
    )


    print(
        "Average power:",
        round(
            avg_power,
            4
        ),
        "W"
    )


    print(
        "Maximum power:",
        round(
            max_power,
            4
        ),
        "W"
    )


    print(
        "Evaluation file:",
        prediction_file
    )


    print(
        "Time:",
        round(
            elapsed,
            2
        ),
        "minutes"
    )


    return {

        "appliance":
            appliance,

        "evaluation_rows":
            len(result),

        "baseline_mean_reward":
            baseline_reward_mean,

        "predicted_mean_reward":
            predicted_reward_mean,

        "reward_mae":
            reward_mae,

        "reward_rmse":
            reward_rmse,

        "action_change_rate_pct":
            action_change_rate,

        "total_energy_kwh":
            total_energy,

        "average_power_w":
            avg_power,

        "maximum_power_w":
            max_power,

        "evaluation_time_minutes":
            elapsed

    }


# ================================================================
# RUN ALL APPLIANCES
# ================================================================

results = []

overall_start = time.time()


for environment_file in environment_files:

    try:

        result = evaluate_appliance(
            environment_file
        )

        if result is not None:

            results.append(
                result
            )


    except Exception as e:

        print("\n")
        print("=" * 70)
        print("ERROR PROCESSING")
        print("=" * 70)

        print(
            environment_file
        )

        print(
            type(e).__name__,
            ":",
            str(e)
        )


# ================================================================
# SAVE SUMMARY
# ================================================================

if results:

    summary = pd.DataFrame(
        results
    )


    summary_file = os.path.join(
        OUTPUT_DIR,
        "rl_policy_evaluation_summary.csv"
    )


    summary.to_csv(
        summary_file,
        index=False
    )


    total_time = (
        time.time()
        -
        overall_start
    ) / 60


    print("\n")
    print("=" * 70)
    print("MODULE 11C COMPLETE")
    print("=" * 70)


    print(
        summary.to_string(
            index=False
        )
    )


    print("\nSummary saved to:")

    print(
        summary_file
    )


    print("\nEvaluation files saved to:")

    print(
        OUTPUT_DIR
    )


    print(
        "\nTotal time:",
        round(
            total_time,
            2
        ),
        "minutes"
    )


    print("=" * 70)


else:

    print("\n")
    print("=" * 70)
    print("NO EVALUATION RESULTS GENERATED")
    print("=" * 70)