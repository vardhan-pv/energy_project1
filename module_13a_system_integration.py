# ============================================================
# MODULE 13A — SYSTEM INTEGRATION
# ============================================================
# Intelligent IoT-Driven Cognitive Energy Optimization System
#
# Purpose:
#   Integrate:
#       1. User Behavior Descriptor
#       2. Peak Load Prediction
#       3. RL Policy Evaluation
#       4. RL Optimization
#       5. Feedback & Performance Monitoring
#       6. Policy Evolution
#       7. Self-Evolution Validation
#
# Output:
#   E:\energy_project\integration_output\unified_system_state.csv
#   E:\energy_project\integration_output\unified_system_summary.csv
# ============================================================

import os
import time
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"E:\energy_project"

BEHAVIOR_FILE = os.path.join(
    BASE_DIR,
    "behavior_output",
    "user_behavior_descriptor.csv"
)

PEAK_FILE = os.path.join(
    BASE_DIR,
    "peak_output",
    "peak_prediction_summary.csv"
)

RL_EVAL_FILE = os.path.join(
    BASE_DIR,
    "rl_evaluation",
    "rl_policy_evaluation_summary.csv"
)

RL_OPT_FILE = os.path.join(
    BASE_DIR,
    "rl_optimization",
    "rl_optimization_summary.csv"
)

FEEDBACK_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "feedback_performance_summary.csv"
)

EVOLUTION_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "policy_evolution_summary.csv"
)

SELF_EVOLUTION_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "self_evolution_validation_summary.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "integration_output"
)

UNIFIED_STATE_FILE = os.path.join(
    OUTPUT_DIR,
    "unified_system_state.csv"
)

UNIFIED_SUMMARY_FILE = os.path.join(
    OUTPUT_DIR,
    "unified_system_summary.csv"
)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

start_time = time.time()

print("=" * 70)
print("MODULE 13A — SYSTEM INTEGRATION")
print("=" * 70)
print()


# ============================================================
# REQUIRED FILE CHECK
# ============================================================

print("Checking required files...")
print("-" * 70)

required_files = {
    "Behavior": BEHAVIOR_FILE,
    "Peak Prediction": PEAK_FILE,
    "RL Evaluation": RL_EVAL_FILE,
    "RL Optimization": RL_OPT_FILE,
    "Feedback": FEEDBACK_FILE,
    "Policy Evolution": EVOLUTION_FILE,
    "Self-Evolution": SELF_EVOLUTION_FILE
}

missing_files = []

for name, path in required_files.items():

    if os.path.exists(path):

        print(f"[OK] {name}: {path}")

    else:

        print(f"[MISSING] {name}: {path}")
        missing_files.append(path)


if missing_files:

    print()
    print("ERROR: Required files are missing.")
    print()

    for path in missing_files:
        print(path)

    raise SystemExit(1)


print()
print("All required files found.")
print()


# ============================================================
# LOAD DATA
# ============================================================

print("Loading system components...")
print()

behavior = pd.read_csv(
    BEHAVIOR_FILE
)

peak = pd.read_csv(
    PEAK_FILE
)

rl_eval = pd.read_csv(
    RL_EVAL_FILE
)

rl_opt = pd.read_csv(
    RL_OPT_FILE
)

feedback = pd.read_csv(
    FEEDBACK_FILE
)

evolution = pd.read_csv(
    EVOLUTION_FILE
)

self_evolution = pd.read_csv(
    SELF_EVOLUTION_FILE
)


# ============================================================
# INPUT SHAPES
# ============================================================

print("INPUT SHAPES")
print("-" * 70)

print(
    f"Behavior:        {behavior.shape}"
)

print(
    f"Peak Prediction: {peak.shape}"
)

print(
    f"RL Evaluation:   {rl_eval.shape}"
)

print(
    f"RL Optimization: {rl_opt.shape}"
)

print(
    f"Feedback:        {feedback.shape}"
)

print(
    f"Evolution:       {evolution.shape}"
)

print(
    f"Self-Evolution:  {self_evolution.shape}"
)

print()


# ============================================================
# BASIC VALIDATION
# ============================================================

datasets = {
    "behavior": behavior,
    "peak": peak,
    "rl_eval": rl_eval,
    "rl_opt": rl_opt,
    "feedback": feedback,
    "evolution": evolution,
    "self_evolution": self_evolution
}


for name, df_temp in datasets.items():

    if "appliance" not in df_temp.columns:

        print(
            f"ERROR: appliance column missing from {name}"
        )

        raise SystemExit(1)


# ============================================================
# PREPARE DATASETS
# ============================================================

print("Preparing integration datasets...")
print()


# ------------------------------------------------------------
# Keep appliance as string
# ------------------------------------------------------------

for name in datasets:

    datasets[name]["appliance"] = (
        datasets[name]["appliance"]
        .astype(str)
        .str.strip()
    )


# ============================================================
# REMOVE DUPLICATE COLUMNS BEFORE MERGING
# ============================================================

def remove_duplicate_columns(
    base_df,
    new_df,
    dataset_name
):

    overlapping = [
        col
        for col in new_df.columns
        if col in base_df.columns
        and col != "appliance"
    ]

    if overlapping:

        print(
            f"  {dataset_name}: removing overlapping columns:"
        )

        print(
            f"    {overlapping}"
        )

        new_df = new_df.drop(
            columns=overlapping
        )

    return new_df


# ============================================================
# START WITH BEHAVIOR
# ============================================================

df = behavior.copy()


# ============================================================
# MERGE PEAK PREDICTION
# ============================================================

print("Merging system components...")

peak = remove_duplicate_columns(
    df,
    peak,
    "peak"
)

df = pd.merge(
    df,
    peak,
    on="appliance",
    how="left"
)


# ============================================================
# MERGE RL EVALUATION
# ============================================================

rl_eval = remove_duplicate_columns(
    df,
    rl_eval,
    "rl_eval"
)

df = pd.merge(
    df,
    rl_eval,
    on="appliance",
    how="left"
)


# ============================================================
# MERGE RL OPTIMIZATION
# ============================================================

rl_opt = remove_duplicate_columns(
    df,
    rl_opt,
    "rl_opt"
)

df = pd.merge(
    df,
    rl_opt,
    on="appliance",
    how="left"
)


# ============================================================
# MERGE FEEDBACK
# ============================================================

feedback = remove_duplicate_columns(
    df,
    feedback,
    "feedback"
)

df = pd.merge(
    df,
    feedback,
    on="appliance",
    how="left"
)


# ============================================================
# MERGE EVOLUTION
# ============================================================

evolution = remove_duplicate_columns(
    df,
    evolution,
    "evolution"
)

df = pd.merge(
    df,
    evolution,
    on="appliance",
    how="left"
)


# ============================================================
# MERGE SELF-EVOLUTION
# ============================================================

self_evolution = remove_duplicate_columns(
    df,
    self_evolution,
    "self_evolution"
)

df = pd.merge(
    df,
    self_evolution,
    on="appliance",
    how="left"
)


print()
print(
    f"Merged rows: {len(df)}"
)

print(
    f"Merged columns: {len(df.columns)}"
)

print()


# ============================================================
# REMOVE pandas DUPLICATE COLUMN NAMES
# ============================================================

print("Cleaning duplicate column names...")

df = df.loc[
    :,
    ~df.columns.duplicated()
]


# ============================================================
# SAFE NUMERIC CLEANING
# ============================================================

print("Cleaning integrated data...")


# IMPORTANT:
# Only convert known numeric fields.
#
# DO NOT convert text fields such as:
#   behavior_class
#   dominant_behavior
#   interaction_class
#   demand_class
#   policy_class
#   evolution_class
#   validation_status
#   system_status
#
# This prevents text values from becoming 0.0.

numeric_columns = [

    # --------------------------------------------------------
    # Behavior
    # --------------------------------------------------------

    "user_behavior_score",
    "energy_routine_index",
    "dsc_score",
    "stability_score",
    "change_score",
    "cdi_score",

    # --------------------------------------------------------
    # Peak prediction
    # --------------------------------------------------------

    "MAE",
    "RMSE",
    "R2",
    "actual_peak_power_w",
    "predicted_peak_power_w",
    "peak_error_w",

    # --------------------------------------------------------
    # RL evaluation
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # RL optimization
    # --------------------------------------------------------

    "rows_optimized",
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",

    # --------------------------------------------------------
    # Feedback
    # --------------------------------------------------------

    "calculated_savings_percentage",
    "adaptive_action_rate_percentage",
    "adaptation_score",

    # --------------------------------------------------------
    # Evolution
    # --------------------------------------------------------

    "adaptation_factor",
    "evolved_adaptation_factor",

    "recommended_learning_rate",
    "evolved_learning_rate",

    "policy_confidence",
    "self_adaptation_score",

    # --------------------------------------------------------
    # Self-evolution
    # --------------------------------------------------------

    "adaptation_factor_change_pct",
    "learning_rate_change_pct",
    "evolution_effectiveness_score"
]


for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ============================================================
# REPLACE INFINITE VALUES
# ============================================================

numeric_cols_existing = df.select_dtypes(
    include=[np.number]
).columns

for col in numeric_cols_existing:

    df[col] = df[col].replace(
        [np.inf, -np.inf],
        np.nan
    )


# ============================================================
# NULL CHECK BEFORE CLEANING
# ============================================================

null_count = int(
    df.isnull().sum().sum()
)

print()
print("=" * 70)
print("MODULE 13A VALIDATION")
print("=" * 70)

print()

print(
    f"ROWS: {len(df)}"
)

print(
    f"COLUMNS: {len(df.columns)}"
)

print()

print("NULL CHECK:")

if null_count == 0:

    print("NO NULLS")

else:

    print(
        f"NULL VALUES: {null_count}"
    )


# ============================================================
# NULL CLEANING
# ============================================================

if null_count > 0:

    print()
    print("Cleaning NULL values...")

    # --------------------------------------------------------
    # Numeric → 0
    # --------------------------------------------------------

    numeric_cols = df.select_dtypes(
        include=[np.number]
    ).columns

    for col in numeric_cols:

        df[col] = df[col].fillna(0)


    # --------------------------------------------------------
    # Text → Unknown
    # --------------------------------------------------------

    text_cols = df.select_dtypes(
        include=["object"]
    ).columns

    for col in text_cols:

        df[col] = df[col].fillna(
            "Unknown"
        )


# ============================================================
# FINAL NULL CHECK
# ============================================================

remaining_nulls = int(
    df.isnull().sum().sum()
)

print()

print(
    f"NULLS AFTER CLEANING: {remaining_nulls}"
)


if remaining_nulls != 0:

    print(
        "ERROR: NULL values remain."
    )

    raise SystemExit(1)


# ============================================================
# ENSURE TEXT COLUMNS REMAIN TEXT
# ============================================================

text_columns = [

    "behavior_class",
    "dominant_behavior",
    "demand_class",
    "interaction_class",
    "policy_update",
    "policy_class",
    "policy_reason",
    "evolution_decision",
    "evolution_class",
    "evolution_status",
    "validation_status",
    "self_evolution_level"
]

for col in text_columns:

    if col in df.columns:

        df[col] = (
            df[col]
            .astype(str)
            .replace(
                ["nan", "NaN", "None"],
                "Unknown"
            )
        )


# ============================================================
# SYSTEM INTELLIGENCE COMPONENTS
# ============================================================

print()
print("Calculating system health indicators...")
print()


# ============================================================
# HELPER FUNCTION
# ============================================================

def get_numeric(
    dataframe,
    column,
    default=0.0
):

    if column not in dataframe.columns:

        return pd.Series(
            default,
            index=dataframe.index,
            dtype=float
        )

    return pd.to_numeric(
        dataframe[column],
        errors="coerce"
    ).fillna(default)


# ============================================================
# COMPONENT 1 — BEHAVIOR INTELLIGENCE
# ============================================================

behavior_score = get_numeric(
    df,
    "user_behavior_score"
)

# Score expected between 0–100

behavior_component = (
    behavior_score
    .clip(0, 100)
)


# ============================================================
# COMPONENT 2 — PEAK PREDICTION
# ============================================================

actual_peak = get_numeric(
    df,
    "actual_peak_power_w"
)

predicted_peak = get_numeric(
    df,
    "predicted_peak_power_w"
)

peak_accuracy = np.where(
    actual_peak > 0,

    1 -
    (
        np.abs(
            actual_peak -
            predicted_peak
        )
        /
        actual_peak
    ),

    0
)

peak_accuracy = (
    pd.Series(
        peak_accuracy,
        index=df.index
    )
    .clip(0, 1)
    * 100
)


# ============================================================
# COMPONENT 3 — ENERGY SAVINGS
# ============================================================

savings = get_numeric(
    df,
    "estimated_savings_percentage"
)

savings_component = (
    savings
    .clip(0, 20)
    / 20
    * 100
)


# ============================================================
# COMPONENT 4 — RL IMPROVEMENT
# ============================================================

rl_improvement = get_numeric(
    df,
    "reward_improvement"
)

# Reward improvement is usually small.
# Scale it safely instead of multiplying directly by 100.

rl_component = (
    (
        rl_improvement
        /
        0.02
    )
    .clip(0, 1)
    * 100
)


# ============================================================
# COMPONENT 5 — ADAPTATION
# ============================================================

adaptation_score = get_numeric(
    df,
    "adaptation_score"
)

adaptation_component = (
    adaptation_score
    .clip(0, 100)
)


# ============================================================
# COMPONENT 6 — SELF EVOLUTION
# ============================================================

self_adaptation_score = get_numeric(
    df,
    "self_adaptation_score"
)

self_adaptation_component = (
    self_adaptation_score
    .clip(0, 100)
)


# ============================================================
# COMPONENT 7 — EVOLUTION EFFECTIVENESS
# ============================================================

evolution_effectiveness = get_numeric(
    df,
    "evolution_effectiveness_score"
)

evolution_component = (
    evolution_effectiveness
    .clip(0, 100)
)


# ============================================================
# SYSTEM INTELLIGENCE SCORE
# ============================================================
#
# Weighted combination:
#
# Behavior intelligence        20%
# Peak prediction              15%
# Energy optimization          15%
# RL improvement               15%
# Adaptation                   10%
# Self-adaptation              10%
# Evolution effectiveness      15%
#
# Total = 100%
# ============================================================

df["system_intelligence_score"] = (

    behavior_component * 0.20

    +

    peak_accuracy * 0.15

    +

    savings_component * 0.15

    +

    rl_component * 0.15

    +

    adaptation_component * 0.10

    +

    self_adaptation_component * 0.10

    +

    evolution_component * 0.15

)


df["system_intelligence_score"] = (
    df["system_intelligence_score"]
    .clip(0, 100)
    .round(6)
)


# ============================================================
# SYSTEM STATUS
# ============================================================

def determine_system_status(score):

    if score >= 75:

        return "Advanced"

    elif score >= 50:

        return "Adaptive"

    elif score >= 25:

        return "Developing"

    else:

        return "Basic"


df["system_status"] = (
    df["system_intelligence_score"]
    .apply(determine_system_status)
)


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

preferred_columns = [

    "appliance",

    # Behavior
    "user_behavior_score",
    "behavior_class",
    "dominant_behavior",
    "energy_routine_index",
    "dsc_score",
    "stability_score",
    "change_score",
    "cdi_score",

    # Peak prediction
    "actual_peak_power_w",
    "predicted_peak_power_w",
    "peak_error_w",

    # RL
    "baseline_mean_reward",
    "recommended_mean_reward",
    "reward_improvement",

    # Optimization
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",

    # Adaptation
    "adaptation_score",

    # Evolution
    "adaptation_factor",
    "evolved_adaptation_factor",
    "recommended_learning_rate",
    "evolved_learning_rate",
    "policy_confidence",

    # Self evolution
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "validation_status",
    "self_evolution_level",

    # System
    "system_intelligence_score",
    "system_status"
]


available_preferred = [
    col
    for col in preferred_columns
    if col in df.columns
]

remaining_columns = [
    col
    for col in df.columns
    if col not in available_preferred
]

df = df[
    available_preferred +
    remaining_columns
]


# ============================================================
# SORT BY APPLIANCE
# ============================================================

df = df.sort_values(
    by="appliance"
).reset_index(
    drop=True
)


# ============================================================
# FINAL DUPLICATE CHECK
# ============================================================

if df.columns.duplicated().any():

    print(
        "ERROR: Duplicate columns remain."
    )

    duplicated = df.columns[
        df.columns.duplicated()
    ]

    print(
        duplicated.tolist()
    )

    raise SystemExit(1)


# ============================================================
# FINAL NULL CHECK
# ============================================================

final_nulls = int(
    df.isnull().sum().sum()
)

if final_nulls != 0:

    print(
        f"ERROR: Final NULL count = {final_nulls}"
    )

    raise SystemExit(1)


# ============================================================
# DISPLAY SYSTEM RESULTS
# ============================================================

print()
print("=" * 70)
print("SYSTEM INTEGRATION RESULTS")
print("=" * 70)

display_columns = [

    "appliance",
    "user_behavior_score",
    "behavior_class",
    "actual_peak_power_w",
    "predicted_peak_power_w",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_score",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "system_intelligence_score",
    "system_status"
]

display_columns = [
    col
    for col in display_columns
    if col in df.columns
]

print(
    df[display_columns].to_string(
        index=False
    )
)


# ============================================================
# SCORE RANGE
# ============================================================

score_min = df[
    "system_intelligence_score"
].min()

score_max = df[
    "system_intelligence_score"
].max()

print()
print(
    "SYSTEM INTELLIGENCE SCORE RANGE:"
)

print(
    f"{score_min:.4f} to {score_max:.4f}"
)


# ============================================================
# SYSTEM STATUS
# ============================================================

print()
print("SYSTEM STATUS")

print(
    df[
        [
            "appliance",
            "system_status"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# SUMMARY DATASET
# ============================================================

summary_columns = [

    "appliance",
    "user_behavior_score",
    "behavior_class",

    "actual_peak_power_w",
    "predicted_peak_power_w",

    "estimated_savings_kwh",
    "estimated_savings_percentage",

    "reward_improvement",

    "adaptation_score",
    "self_adaptation_score",

    "evolution_effectiveness_score",

    "system_intelligence_score",
    "system_status"
]

summary_columns = [
    col
    for col in summary_columns
    if col in df.columns
]

summary = df[
    summary_columns
].copy()


# ============================================================
# SAVE UNIFIED SYSTEM STATE
# ============================================================

df.to_csv(
    UNIFIED_STATE_FILE,
    index=False
)


# ============================================================
# SAVE UNIFIED SYSTEM SUMMARY
# ============================================================

summary.to_csv(
    UNIFIED_SUMMARY_FILE,
    index=False
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print()

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {len(df.columns)}"
)

print(
    f"Final NULLS: {int(df.isnull().sum().sum())}"
)

print(
    f"Duplicate columns: {df.columns.duplicated().sum()}"
)

print()

print(
    "Behavior classes:"
)

if "behavior_class" in df.columns:

    print(
        df[
            [
                "appliance",
                "behavior_class"
            ]
        ].to_string(
            index=False
        )
    )


print()

print(
    "System statuses:"
)

print(
    df[
        [
            "appliance",
            "system_intelligence_score",
            "system_status"
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 70)
print("MODULE 13A COMPLETE")
print("=" * 70)

print()

print(
    "Unified system state:"
)

print(
    UNIFIED_STATE_FILE
)

print()

print(
    "Unified system summary:"
)

print(
    UNIFIED_SUMMARY_FILE
)

print()

elapsed = (
    time.time() -
    start_time
)

print(
    f"Total time: {elapsed / 60:.2f} minutes"
)

print("=" * 70)