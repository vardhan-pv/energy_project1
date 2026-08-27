import pandas as pd
import numpy as np
import os
import glob
import time

# ============================================================
# MODULE 11A — REINFORCEMENT LEARNING
# RL ENVIRONMENT / STATE CONSTRUCTION
# ============================================================

print("=" * 70)
print("MODULE 11A — REINFORCEMENT LEARNING")
print("RL STATE + ACTION + REWARD CONSTRUCTION")
print("=" * 70)

BASE_DIR = r"E:\energy_project"

FEATURE_DIR = os.path.join(BASE_DIR, "feature_output")
BEHAVIOR_DIR = os.path.join(BASE_DIR, "behavior_output")
ANOMALY_DIR = os.path.join(BASE_DIR, "anomaly_output")
PEAK_DIR = os.path.join(BASE_DIR, "peak_output")
RL_DIR = os.path.join(BASE_DIR, "rl_data")

os.makedirs(RL_DIR, exist_ok=True)

# ============================================================
# REQUIRED BEHAVIOR FILES
# ============================================================

UBD_FILE = os.path.join(
    BEHAVIOR_DIR,
    "user_behavior_descriptor.csv"
)

ERI_FILE = os.path.join(
    BEHAVIOR_DIR,
    "energy_routine_index.csv"
)

DSC_FILE = os.path.join(
    BEHAVIOR_DIR,
    "demand_stability_change.csv"
)

CDI_FILE = os.path.join(
    BEHAVIOR_DIR,
    "cdi_summary.csv"
)

# ============================================================
# CHECK REQUIRED FILES
# ============================================================

required_files = {
    "UBD": UBD_FILE,
    "ERI": ERI_FILE,
    "DSC": DSC_FILE,
    "CDI": CDI_FILE
}

for name, path in required_files.items():

    if not os.path.exists(path):

        print("ERROR: Missing", name)
        print(path)

        raise SystemExit(1)

print("\nAll behavior files found.")

# ============================================================
# LOAD BEHAVIOR
# ============================================================

print("\nLoading UBD...")
ubd = pd.read_csv(UBD_FILE)

print("Loading ERI...")
eri = pd.read_csv(ERI_FILE)

print("Loading DSC...")
dsc = pd.read_csv(DSC_FILE)

print("Loading CDI...")
cdi = pd.read_csv(CDI_FILE)

# ============================================================
# SELECT USEFUL COLUMNS
# ============================================================

ubd = ubd[
    [
        "appliance",
        "user_behavior_score"
    ]
]

eri = eri[
    [
        "appliance",
        "energy_routine_index"
    ]
]

dsc = dsc[
    [
        "appliance",
        "dsc_score",
        "stability_score",
        "change_score"
    ]
]

cdi = cdi[
    [
        "appliance",
        "cdi_score"
    ]
]

# ============================================================
# MERGE BEHAVIOR PROFILE
# ============================================================

behavior = ubd.merge(
    eri,
    on="appliance",
    how="left"
)

behavior = behavior.merge(
    dsc,
    on="appliance",
    how="left"
)

behavior = behavior.merge(
    cdi,
    on="appliance",
    how="left"
)

print("\nBehavior profile:")
print(behavior.to_string(index=False))

# ============================================================
# FIND FEATURE FILES
# ============================================================

feature_files = glob.glob(
    os.path.join(
        FEATURE_DIR,
        "*_features.csv"
    )
)

if not feature_files:

    print("ERROR: No feature files found.")
    raise SystemExit(1)

print(
    "\nFeature files found:",
    len(feature_files)
)

# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

results = []

overall_start = time.time()

for feature_file in feature_files:

    appliance = os.path.basename(
        feature_file
    ).replace(
        "_features.csv",
        ""
    )

    print("\n" + "=" * 70)
    print("PROCESSING:", appliance)
    print("=" * 70)

    start_time = time.time()

    # ========================================================
    # LOAD FEATURES
    # ========================================================

    usecols = [
        "id",
        "timestamp",
        "appliance",
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max"
    ]

    print("Loading feature data...")

    df = pd.read_csv(
        feature_file,
        usecols=usecols
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

      # ========================================================
    # ANOMALY DATA
    # ========================================================

    anomaly_file = os.path.join(
        ANOMALY_DIR,
        appliance + "_anomalies.csv"
    )

    if os.path.exists(anomaly_file):

        print("Loading anomaly data...")

        anomaly = pd.read_csv(
            anomaly_file,
            usecols=[
                "anomaly",
                "anomaly_score"
            ]
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Module 9 anomaly files do not contain ID.
        # They preserve the same row order as the feature data.
        # Therefore align anomaly values by row position.
        # ----------------------------------------------------

        if len(anomaly) != len(df):

            print(
                "ERROR: Row count mismatch between "
                "feature and anomaly files."
            )

            print(
                "Feature rows:",
                len(df)
            )

            print(
                "Anomaly rows:",
                len(anomaly)
            )

            raise SystemExit(1)

        df["anomaly"] = (
            anomaly["anomaly"]
            .to_numpy()
        )

        df["anomaly_score"] = (
            anomaly["anomaly_score"]
            .to_numpy()
        )

        print(
            "Anomaly rows aligned:",
            len(anomaly)
        )

    else:

        print(
            "WARNING: anomaly file missing."
        )

        df["anomaly"] = 1

        df["anomaly_score"] = 0.0

    # ========================================================
    # PEAK PREDICTION
    # ========================================================

    peak_file = os.path.join(
        PEAK_DIR,
        appliance +
        "_peak_predictions.csv"
    )

    if os.path.exists(peak_file):

        print("Loading peak prediction...")

        peak = pd.read_csv(
            peak_file,
            usecols=[
                "id",
                "predicted_peak_power_w"
            ]
        )

        df = df.merge(
            peak,
            on="id",
            how="left"
        )

    else:

        print(
            "WARNING: peak prediction missing."
        )

        df["predicted_peak_power_w"] = 0.0

    # ========================================================
    # BEHAVIOR PROFILE
    # ========================================================

    profile = behavior[
        behavior["appliance"] == appliance
    ]

    if len(profile) == 0:

        print(
            "WARNING: Behavior profile missing."
        )

        df["user_behavior_score"] = 0
        df["energy_routine_index"] = 0
        df["dsc_score"] = 0
        df["stability_score"] = 0
        df["change_score"] = 0
        df["cdi_score"] = 0

    else:

        row = profile.iloc[0]

        df["user_behavior_score"] = row[
            "user_behavior_score"
        ]

        df["energy_routine_index"] = row[
            "energy_routine_index"
        ]

        df["dsc_score"] = row[
            "dsc_score"
        ]

        df["stability_score"] = row[
            "stability_score"
        ]

        df["change_score"] = row[
            "change_score"
        ]

        df["cdi_score"] = row[
            "cdi_score"
        ]

    # ========================================================
    # CLEAN NUMERIC DATA
    # ========================================================

    numeric_columns = [
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max",
        "anomaly",
        "anomaly_score",
        "predicted_peak_power_w",
        "user_behavior_score",
        "energy_routine_index",
        "dsc_score",
        "stability_score",
        "change_score",
        "cdi_score"
    ]

    df[numeric_columns] = df[
        numeric_columns
    ].replace(
        [np.inf, -np.inf],
        np.nan
    )

    df[numeric_columns] = df[
        numeric_columns
    ].fillna(0)

    # ========================================================
    # NORMALIZED POWER
    # ========================================================

    df["power_ratio"] = np.where(
        df["power_rolling_max"] > 0,
        df["power_w"] /
        df["power_rolling_max"],
        0
    )

    df["power_ratio"] = df[
        "power_ratio"
    ].clip(0, 1)

    # ========================================================
    # PREDICTED PEAK RATIO
    # ========================================================

    df["predicted_peak_ratio"] = np.where(
        df["power_w"] > 0,
        df["predicted_peak_power_w"] /
        df["power_w"],
        0
    )

    df["predicted_peak_ratio"] = df[
        "predicted_peak_ratio"
    ].replace(
        [np.inf, -np.inf],
        0
    )

    df["predicted_peak_ratio"] = df[
        "predicted_peak_ratio"
    ].clip(0, 20)

    # ========================================================
    # CYCLIC TIME FEATURES
    # ========================================================

    df["hour_sin"] = np.sin(
        2 * np.pi *
        df["hour"] / 24
    )

    df["hour_cos"] = np.cos(
        2 * np.pi *
        df["hour"] / 24
    )

    df["day_sin"] = np.sin(
        2 * np.pi *
        df["day_of_week"] / 7
    )

    df["day_cos"] = np.cos(
        2 * np.pi *
        df["day_of_week"] / 7
    )

    # ========================================================
    # PEAK RISK
    # ========================================================

    df["peak_risk"] = np.where(
        df["predicted_peak_power_w"] >
        df["power_rolling_mean"] * 1.5,
        1,
        0
    )

    # ========================================================
    # RL ACTION SPACE
    # ========================================================

    # 0 = Maintain
    # 1 = Reduce Load
    # 2 = Shift Usage
    # 3 = Turn OFF

    # Start with a transparent heuristic policy.
    # Module 11B will learn from this environment.

    conditions = [

        # Extreme anomaly or high predicted peak
        (
            (df["anomaly"] == -1)
            &
            (df["power_w"] > 0)
        ),

        (
            (df["peak_risk"] == 1)
            &
            (df["power_ratio"] > 0.7)
        ),

        (
            (df["power_ratio"] > 0.8)
            &
            (df["user_behavior_score"] < 50)
        ),

        (
            (df["energy_routine_index"] < 60)
            &
            (df["power_ratio"] > 0.6)
        )
    ]

    choices = [
        3,
        1,
        1,
        2
    ]

    df["action"] = np.select(
        conditions,
        choices,
        default=0
    ).astype(np.int8)

    # ========================================================
    # REWARD DESIGN
    # ========================================================

    # Energy consumption penalty
    energy_penalty = (
        df["power_w"] / 1000.0
    )

    # Peak penalty
    peak_penalty = np.where(
        df["peak_risk"] == 1,
        0.5,
        0
    )

    # Anomaly penalty
    anomaly_penalty = np.where(
        df["anomaly"] == -1,
        0.5,
        0
    )

    # Routine preservation
    routine_bonus = (
        df["energy_routine_index"] /
        100.0
    ) * 0.2

    # Stability bonus
    stability_bonus = (
        df["stability_score"] /
        100.0
    ) * 0.2

    # Base reward
    df["base_reward"] = (
        -energy_penalty
        -peak_penalty
        -anomaly_penalty
        +routine_bonus
        +stability_bonus
    )

    # ========================================================
    # ACTION-SPECIFIC REWARD
    # ========================================================

    df["reward"] = df[
        "base_reward"
    ].astype(float)

    # Maintain
    df.loc[
        df["action"] == 0,
        "reward"
    ] += 0.10

    # Reduce
    df.loc[
        df["action"] == 1,
        "reward"
    ] += (
        df["power_w"] /
        1000.0
    ) * 0.5

    # Shift
    df.loc[
        df["action"] == 2,
        "reward"
    ] += 0.20

    # Turn OFF
    df.loc[
        df["action"] == 3,
        "reward"
    ] += (
        df["power_w"] /
        1000.0
    ) * 0.8

    # Avoid unnecessary OFF action
    df.loc[
        (
            (df["action"] == 3)
            &
            (df["status"] == 0)
        ),
        "reward"
    ] -= 0.5

    # ========================================================
    # STATE ID
    # ========================================================

    df["state_id"] = np.arange(
        len(df),
        dtype=np.int64
    )

    # ========================================================
    # NEXT STATE ID
    # ========================================================

    df["next_state_id"] = (
        df["state_id"] + 1
    )

    df.loc[
        df["next_state_id"] >= len(df),
        "next_state_id"
    ] = -1

    # ========================================================
    # FINAL RL DATASET
    # ========================================================

    final_columns = [

        # state identification
        "state_id",
        "next_state_id",
        "id",
        "timestamp",
        "appliance",

        # current energy state
        "power_w",
        "status",
        "energy_kwh",

        # temporal state
        "hour",
        "day_of_week",
        "is_weekend",
        "hour_sin",
        "hour_cos",
        "day_sin",
        "day_cos",

        # power state
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max",
        "power_ratio",

        # behavior state
        "user_behavior_score",
        "energy_routine_index",
        "dsc_score",
        "stability_score",
        "change_score",
        "cdi_score",

        # anomaly state
        "anomaly",
        "anomaly_score",

        # peak state
        "predicted_peak_power_w",
        "predicted_peak_ratio",
        "peak_risk",

        # RL
        "action",
        "base_reward",
        "reward"
    ]

    df = df[
        final_columns
    ]

    # ========================================================
    # SAVE
    # ========================================================

    output_file = os.path.join(
        RL_DIR,
        appliance +
        "_rl_environment.csv"
    )

    print("\nSaving:")
    print(output_file)

    df.to_csv(
        output_file,
        index=False
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    elapsed = (
        time.time() -
        start_time
    ) / 60

    action_counts = (
        df["action"]
        .value_counts()
        .sort_index()
    )

    print("\nRows:", len(df))
    print("Columns:", len(df.columns))

    print("\nACTION DISTRIBUTION")
    print(action_counts)

    print(
        "\nReward range:",
        round(df["reward"].min(), 6),
        "to",
        round(df["reward"].max(), 6)
    )

    print(
        "Peak-risk rows:",
        int(df["peak_risk"].sum())
    )

    print(
        "Anomaly rows:",
        int((df["anomaly"] == -1).sum())
    )

    print(
        "Time:",
        round(elapsed, 2),
        "minutes"
    )

    results.append({
        "appliance": appliance,
        "rows": len(df),
        "columns": len(df.columns),
        "maintain": int(
            (df["action"] == 0).sum()
        ),
        "reduce": int(
            (df["action"] == 1).sum()
        ),
        "shift": int(
            (df["action"] == 2).sum()
        ),
        "turn_off": int(
            (df["action"] == 3).sum()
        ),
        "peak_risk": int(
            df["peak_risk"].sum()
        ),
        "anomalies": int(
            (df["anomaly"] == -1).sum()
        ),
        "reward_mean": df["reward"].mean(),
        "reward_min": df["reward"].min(),
        "reward_max": df["reward"].max(),
        "time_minutes": elapsed
    })

# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    results
)

summary_file = os.path.join(
    RL_DIR,
    "rl_environment_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

total_time = (
    time.time() -
    overall_start
) / 60

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MODULE 11A COMPLETE")
print("=" * 70)

print(
    summary.to_string(
        index=False
    )
)

print("\nSummary:")
print(summary_file)

print("\nRL datasets:")
print(RL_DIR)

print(
    "\nTotal time:",
    round(total_time, 2),
    "minutes"
)

print("=" * 70)