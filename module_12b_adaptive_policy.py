import os
import sys
import pandas as pd
import numpy as np

# ============================================================
# MODULE 12B — ADAPTIVE POLICY UPDATE
# ============================================================

print("=" * 70)
print("MODULE 12B — ADAPTIVE POLICY UPDATE")
print("=" * 70)

BASE_DIR = r"E:\energy_project"

FEEDBACK_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "feedback_performance_summary.csv"
)

OPTIMIZATION_FILE = os.path.join(
    BASE_DIR,
    "rl_optimization",
    "rl_optimization_summary.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "adaptive_policy"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "adaptive_policy_summary.csv"
)

POLICY_FILE = os.path.join(
    OUTPUT_DIR,
    "adaptive_policy_parameters.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FILE CHECK
# ============================================================

print()
print("Checking required files...")
print("-" * 70)

for name, path in {
    "Feedback": FEEDBACK_FILE,
    "Optimization": OPTIMIZATION_FILE
}.items():

    if os.path.exists(path):
        print(f"[OK] {name}: {path}")
    else:
        print(f"[ERROR] Missing {name}: {path}")
        sys.exit(1)


# ============================================================
# LOAD
# ============================================================

print()
print("Loading feedback performance...")
feedback = pd.read_csv(FEEDBACK_FILE)

print("Loading RL optimization summary...")
optimization = pd.read_csv(OPTIMIZATION_FILE)


print()
print("INPUT SHAPES")
print("-" * 70)

print("Feedback:", feedback.shape)
print("Optimization:", optimization.shape)


# ============================================================
# VALIDATE APPLIANCE
# ============================================================

if "appliance" not in feedback.columns:
    print("[ERROR] Feedback file has no appliance column.")
    sys.exit(1)

if "appliance" not in optimization.columns:
    print("[ERROR] Optimization file has no appliance column.")
    sys.exit(1)


# ============================================================
# IMPORTANT FIX
# ============================================================
# Module 12A already contains several optimization columns.
# Therefore we DO NOT merge duplicate columns blindly.
#
# We only copy optimization columns that are not already present.
# ============================================================

optimization_columns = [
    "appliance",
    "rows_optimized",
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions"
]

missing_optimization_columns = [
    col for col in optimization_columns
    if col not in feedback.columns
]

print()
print("Optimization columns already present:")
for col in optimization_columns:
    if col in feedback.columns:
        print("  [EXISTS]", col)

print()
print("Optimization columns to add:")

for col in missing_optimization_columns:
    print("  [ADD]", col)


# ============================================================
# MERGE ONLY MISSING COLUMNS
# ============================================================

if missing_optimization_columns:

    opt_subset = optimization[
        ["appliance"] + missing_optimization_columns
    ].copy()

    print()
    print("Merging missing optimization columns...")

    df = pd.merge(
        feedback,
        opt_subset,
        on="appliance",
        how="left"
    )

else:

    print()
    print("No optimization columns need to be merged.")

    df = feedback.copy()


# ============================================================
# VALIDATE MERGE
# ============================================================

if df.empty:
    print("[ERROR] Result contains zero rows.")
    sys.exit(1)

print()
print("Merged rows:", len(df))


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "calculated_savings_percentage",
    "reward_improvement",
    "adaptive_action_rate_percentage",
    "adaptation_score",

    "rows_optimized",
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",

    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

        df[col] = df[col].fillna(0)


# ============================================================
# ACTION RATES
# ============================================================

print()
print("Calculating action rates...")

rows = df["rows_optimized"].replace(0, np.nan)

df["maintain_rate"] = (
    df["maintain_actions"] / rows * 100
)

df["reduce_rate"] = (
    df["reduce_actions"] / rows * 100
)

df["shift_rate"] = (
    df["shift_actions"] / rows * 100
)

df["turn_off_rate"] = (
    df["turn_off_actions"] / rows * 100
)

for col in [
    "maintain_rate",
    "reduce_rate",
    "shift_rate",
    "turn_off_rate"
]:
    df[col] = df[col].fillna(0)


# ============================================================
# ADAPTIVE POLICY DECISION
# ============================================================

print("Calculating adaptive policy decisions...")


def determine_policy(row):

    savings = float(
        row["estimated_savings_percentage"]
    )

    reward = float(
        row["reward_improvement"]
    )

    effectiveness = str(
        row.get(
            "optimization_effectiveness",
            ""
        )
    ).strip().lower()

    # Strong positive result
    if savings >= 5 and reward > 0:

        return (
            "increase_adaptation",
            1.15,
            "Strong positive optimization feedback"
        )

    # Moderate positive result
    elif savings >= 2 and reward > 0:

        return (
            "moderate_adaptation",
            1.08,
            "Positive optimization feedback"
        )

    # Small positive result
    elif savings > 0 and reward >= 0:

        return (
            "maintain_policy",
            1.02,
            "Policy improving with limited adaptation"
        )

    # Negative reward
    elif reward < 0:

        return (
            "reduce_adaptation",
            0.90,
            "Negative reward feedback"
        )

    # Default
    else:

        return (
            "maintain_policy",
            1.00,
            "No significant policy change required"
        )


policy_results = df.apply(
    determine_policy,
    axis=1,
    result_type="expand"
)

policy_results.columns = [
    "policy_update",
    "adaptation_factor",
    "policy_reason"
]

df = pd.concat(
    [df, policy_results],
    axis=1
)


# ============================================================
# ACTION WEIGHTS
# ============================================================

print("Calculating action weights...")


def action_weights(row):

    factor = float(
        row["adaptation_factor"]
    )

    reduce_rate = float(
        row["reduce_rate"]
    )

    shift_rate = float(
        row["shift_rate"]
    )

    turnoff_rate = float(
        row["turn_off_rate"]
    )

    maintain_weight = 1.00
    reduce_weight = 1.00
    shift_weight = 1.00
    turn_off_weight = 1.00

    if reduce_rate > 0:
        reduce_weight = factor

    if shift_rate > 0:
        shift_weight = factor

    if turnoff_rate > 0:
        turn_off_weight = factor

    return pd.Series([
        maintain_weight,
        reduce_weight,
        shift_weight,
        turn_off_weight
    ])


weights = df.apply(
    action_weights,
    axis=1
)

weights.columns = [
    "maintain_weight",
    "reduce_weight",
    "shift_weight",
    "turn_off_weight"
]

df = pd.concat(
    [df, weights],
    axis=1
)


# ============================================================
# POLICY CONFIDENCE
# ============================================================

print("Calculating policy confidence...")


def calculate_confidence(row):

    savings = abs(
        float(row["estimated_savings_percentage"])
    )

    reward = abs(
        float(row["reward_improvement"])
    )

    adaptation = float(
        row["adaptation_score"]
    )

    savings_component = min(
        savings / 10.0,
        1.0
    ) * 40

    reward_component = min(
        reward / 0.02,
        1.0
    ) * 30

    adaptation_component = min(
        adaptation / 100.0,
        1.0
    ) * 30

    score = (
        savings_component
        + reward_component
        + adaptation_component
    )

    return min(
        max(score, 0),
        100
    )


df["policy_confidence"] = df.apply(
    calculate_confidence,
    axis=1
)


# ============================================================
# LEARNING RATE
# ============================================================

def calculate_learning_rate(row):

    factor = float(
        row["adaptation_factor"]
    )

    confidence = float(
        row["policy_confidence"]
    )

    base_learning_rate = 0.05

    if confidence >= 70:

        return (
            base_learning_rate
            * factor
        )

    elif confidence >= 40:

        return (
            base_learning_rate
            * 0.75
            * factor
        )

    else:

        return (
            base_learning_rate
            * 0.50
            * factor
        )


df["recommended_learning_rate"] = df.apply(
    calculate_learning_rate,
    axis=1
)


# ============================================================
# POLICY CLASS
# ============================================================

def classify_policy(row):

    update = row["policy_update"]

    confidence = float(
        row["policy_confidence"]
    )

    if update == "increase_adaptation":

        return "Aggressive Adaptation"

    elif update == "moderate_adaptation":

        return "Moderate Adaptation"

    elif update == "reduce_adaptation":

        return "Conservative Adaptation"

    elif confidence >= 40:

        return "Stable Adaptive Policy"

    else:

        return "Stable Policy"


df["policy_class"] = df.apply(
    classify_policy,
    axis=1
)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("MODULE 12B VALIDATION")
print("=" * 70)

print()
print("ROWS:", len(df))
print("COLUMNS:", len(df.columns))

null_count = int(
    df.isnull().sum().sum()
)

print()
print("NULL CHECK:")

if null_count == 0:

    print("NO NULLS")

else:

    print(
        "NULL VALUES:",
        null_count
    )

    print(
        df.isnull().sum()[
            df.isnull().sum() > 0
        ]
    )


# ============================================================
# SUMMARY
# ============================================================

summary_columns = [
    "appliance",

    "estimated_savings_percentage",
    "reward_improvement",

    "maintain_rate",
    "reduce_rate",
    "shift_rate",
    "turn_off_rate",

    "adaptation_factor",
    "policy_confidence",
    "recommended_learning_rate",

    "policy_update",
    "policy_class",
    "policy_reason"
]

summary = df[
    summary_columns
].copy()

summary = summary.sort_values(
    "policy_confidence",
    ascending=False
)


# ============================================================
# POLICY PARAMETERS
# ============================================================

policy_columns = [
    "appliance",

    "maintain_weight",
    "reduce_weight",
    "shift_weight",
    "turn_off_weight",

    "adaptation_factor",
    "recommended_learning_rate",
    "policy_confidence",

    "policy_class"
]

policy_parameters = df[
    policy_columns
].copy()


# ============================================================
# SAVE
# ============================================================

summary.to_csv(
    OUTPUT_FILE,
    index=False
)

policy_parameters.to_csv(
    POLICY_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("ADAPTIVE POLICY RESULTS")
print("-" * 70)

print(
    summary.to_string(
        index=False
    )
)

print()
print("POLICY PARAMETERS")
print("-" * 70)

print(
    policy_parameters.to_string(
        index=False
    )
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 70)
print("MODULE 12B COMPLETE")
print("=" * 70)

print()
print("Output:")
print(OUTPUT_FILE)

print()
print("Policy parameters:")
print(POLICY_FILE)

print()
print("Policy classes:")

print(
    summary[
        [
            "appliance",
            "policy_update",
            "policy_class"
        ]
    ].to_string(
        index=False
    )
)

print()
print("=" * 70)