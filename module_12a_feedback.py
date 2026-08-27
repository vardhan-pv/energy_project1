import os
import pandas as pd
import numpy as np

# ============================================================
# MODULE 12A — FEEDBACK & PERFORMANCE MONITORING
# ============================================================

BASE_DIR = r"E:\energy_project"

RL_OPT_FILE = os.path.join(
    BASE_DIR,
    "rl_optimization",
    "rl_optimization_summary.csv"
)

RL_EVAL_FILE = os.path.join(
    BASE_DIR,
    "rl_evaluation",
    "rl_policy_evaluation_summary.csv"
)

UBD_FILE = os.path.join(
    BASE_DIR,
    "behavior_output",
    "user_behavior_descriptor.csv"
)

ANOMALY_FILE = os.path.join(
    BASE_DIR,
    "anomaly_output",
    "anomaly_summary.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "evolution_output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "feedback_performance_summary.csv"
)


print("=" * 70)
print("MODULE 12A — FEEDBACK & PERFORMANCE MONITORING")
print("=" * 70)


# ============================================================
# STEP 1 — CHECK FILES
# ============================================================

print("\nChecking required files...")

required_files = {
    "RL Optimization": RL_OPT_FILE,
    "RL Evaluation": RL_EVAL_FILE,
    "User Behavior": UBD_FILE,
    "Anomaly Summary": ANOMALY_FILE
}

missing = []

for name, path in required_files.items():
    if os.path.exists(path):
        print(f"[OK] {name}: {path}")
    else:
        print(f"[MISSING] {name}: {path}")
        missing.append(path)

if missing:
    print("\nERROR: Required files are missing.")
    print("Fix the missing files before continuing.")
    raise SystemExit(1)


# ============================================================
# STEP 2 — CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# STEP 3 — LOAD DATA
# ============================================================

print("\nLoading RL optimization summary...")
optimization = pd.read_csv(RL_OPT_FILE)

print("Loading RL policy evaluation summary...")
evaluation = pd.read_csv(RL_EVAL_FILE)

print("Loading user behavior descriptor...")
ubd = pd.read_csv(UBD_FILE)

print("Loading anomaly summary...")
anomaly = pd.read_csv(ANOMALY_FILE)


# ============================================================
# STEP 4 — DISPLAY INPUT SHAPES
# ============================================================

print("\nINPUT SHAPES")
print("-" * 70)

print("Optimization:", optimization.shape)
print("Evaluation:", evaluation.shape)
print("UBD:", ubd.shape)
print("Anomaly:", anomaly.shape)


# ============================================================
# STEP 5 — NORMALIZE APPLIANCE COLUMN
# ============================================================

for df in [optimization, evaluation, ubd, anomaly]:

    if "appliance" not in df.columns:
        print("\nERROR: 'appliance' column missing.")
        print("Available columns:")
        print(df.columns.tolist())
        raise SystemExit(1)

    df["appliance"] = df["appliance"].astype(str).str.strip()


# ============================================================
# STEP 6 — MERGE DATASETS
# ============================================================

print("\nMerging feedback sources...")

feedback = optimization.merge(
    evaluation,
    on="appliance",
    how="left",
    suffixes=("_optimization", "_evaluation")
)

feedback = feedback.merge(
    ubd,
    on="appliance",
    how="left",
    suffixes=("", "_ubd")
)

feedback = feedback.merge(
    anomaly,
    on="appliance",
    how="left",
    suffixes=("", "_anomaly")
)


# ============================================================
# STEP 7 — CALCULATE FEEDBACK METRICS
# ============================================================

print("Calculating feedback metrics...")


# ------------------------------------------------------------
# Energy savings
# ------------------------------------------------------------

if {
    "original_energy_kwh",
    "optimized_energy_kwh"
}.issubset(feedback.columns):

    feedback["actual_calculated_savings_kwh"] = (
        feedback["original_energy_kwh"]
        - feedback["optimized_energy_kwh"]
    )

    feedback["calculated_savings_percentage"] = np.where(
        feedback["original_energy_kwh"] > 0,
        (
            feedback["actual_calculated_savings_kwh"]
            / feedback["original_energy_kwh"]
        ) * 100,
        0
    )


# ------------------------------------------------------------
# Reward improvement
# ------------------------------------------------------------

if {
    "baseline_mean_reward",
    "recommended_mean_reward"
}.issubset(feedback.columns):

    feedback["reward_improvement"] = (
        feedback["recommended_mean_reward"]
        - feedback["baseline_mean_reward"]
    )

    feedback["reward_improvement_percentage"] = np.where(
        feedback["baseline_mean_reward"].abs() > 1e-9,
        (
            feedback["reward_improvement"]
            / feedback["baseline_mean_reward"].abs()
        ) * 100,
        0
    )


# ------------------------------------------------------------
# Action rate
# ------------------------------------------------------------

action_columns = [
    "reduce_actions",
    "shift_actions",
    "turn_off_actions"
]

for col in action_columns:
    if col not in feedback.columns:
        feedback[col] = 0

if "rows_optimized" in feedback.columns:

    feedback["adaptive_action_count"] = (
        feedback["reduce_actions"]
        + feedback["shift_actions"]
        + feedback["turn_off_actions"]
    )

    feedback["adaptive_action_rate_percentage"] = np.where(
        feedback["rows_optimized"] > 0,
        (
            feedback["adaptive_action_count"]
            / feedback["rows_optimized"]
        ) * 100,
        0
    )


# ------------------------------------------------------------
# Optimization effectiveness
# ------------------------------------------------------------

if "calculated_savings_percentage" in feedback.columns:

    feedback["optimization_effectiveness"] = np.select(
        [
            feedback["calculated_savings_percentage"] >= 10,
            feedback["calculated_savings_percentage"] >= 5,
            feedback["calculated_savings_percentage"] > 0
        ],
        [
            "High",
            "Moderate",
            "Low"
        ],
        default="No Improvement"
    )


# ============================================================
# STEP 8 — FEEDBACK STATUS
# ============================================================

def feedback_status(row):

    savings = row.get(
        "calculated_savings_percentage",
        0
    )

    reward = row.get(
        "reward_improvement",
        0
    )

    action_rate = row.get(
        "adaptive_action_rate_percentage",
        0
    )

    if savings >= 5 and reward > 0:
        return "Positive Adaptation"

    elif savings > 0 and reward >= 0:
        return "Improving"

    elif action_rate > 0:
        return "Adaptive Activity"

    else:
        return "Needs Further Learning"


feedback["feedback_status"] = feedback.apply(
    feedback_status,
    axis=1
)


# ============================================================
# STEP 9 — ADAPTATION SCORE
# ============================================================

savings_component = (
    feedback.get(
        "calculated_savings_percentage",
        pd.Series(0, index=feedback.index)
    ).clip(0, 20) / 20 * 40
)

reward_component = (
    feedback.get(
        "reward_improvement",
        pd.Series(0, index=feedback.index)
    ).clip(0, 0.1) / 0.1 * 30
)

action_component = (
    feedback.get(
        "adaptive_action_rate_percentage",
        pd.Series(0, index=feedback.index)
    ).clip(0, 50) / 50 * 30
)

feedback["adaptation_score"] = (
    savings_component
    + reward_component
    + action_component
).clip(0, 100)


# ============================================================
# STEP 10 — ADAPTATION CLASS
# ============================================================

feedback["adaptation_class"] = np.select(
    [
        feedback["adaptation_score"] >= 70,
        feedback["adaptation_score"] >= 40,
        feedback["adaptation_score"] >= 20
    ],
    [
        "Highly Adaptive",
        "Moderately Adaptive",
        "Low Adaptive"
    ],
    default="Minimal Adaptation"
)


# ============================================================
# STEP 11 — ROUND NUMERIC VALUES
# ============================================================

numeric_columns = feedback.select_dtypes(
    include=[np.number]
).columns

feedback[numeric_columns] = feedback[numeric_columns].round(6)


# ============================================================
# STEP 12 — VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12A VALIDATION")
print("=" * 70)

print("\nROWS:", len(feedback))
print("COLUMNS:", len(feedback.columns))

print("\nNULL CHECK:")

null_count = feedback.isnull().sum()

if null_count.sum() == 0:
    print("NO NULLS")
else:
    print(null_count[null_count > 0])


# ============================================================
# STEP 13 — DISPLAY IMPORTANT RESULTS
# ============================================================

display_columns = [
    "appliance",
    "calculated_savings_percentage",
    "reward_improvement",
    "adaptive_action_rate_percentage",
    "optimization_effectiveness",
    "adaptation_score",
    "adaptation_class",
    "feedback_status"
]

display_columns = [
    col for col in display_columns
    if col in feedback.columns
]

print("\nFEEDBACK RESULTS")
print("-" * 70)

print(
    feedback[display_columns].to_string(index=False)
)


# ============================================================
# STEP 14 — SCORE RANGE
# ============================================================

print("\nADAPTATION SCORE RANGE:")

print(
    f"{feedback['adaptation_score'].min():.4f}"
    f" to "
    f"{feedback['adaptation_score'].max():.4f}"
)


# ============================================================
# STEP 15 — SAVE OUTPUT
# ============================================================

feedback.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nOutput:")
print(OUTPUT_FILE)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12A COMPLETE")
print("=" * 70)

print(
    feedback[display_columns].to_string(index=False)
)

print("\nOutput saved to:")
print(OUTPUT_FILE)

print("=" * 70)