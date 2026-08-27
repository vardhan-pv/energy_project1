import os
import pandas as pd
import numpy as np

# ============================================================
# MODULE 12D — SELF-EVOLUTION VALIDATION
# ============================================================

print("=" * 70)
print("MODULE 12D — SELF-EVOLUTION VALIDATION")
print("=" * 70)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"E:\energy_project"

EVOLUTION_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "policy_evolution_summary.csv"
)

PARAM_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "evolved_policy_parameters.csv"
)

HISTORY_FILE = os.path.join(
    BASE_DIR,
    "evolution_output",
    "policy_evolution_history.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "evolution_output"
)

VALIDATION_FILE = os.path.join(
    OUTPUT_DIR,
    "self_evolution_validation_summary.csv"
)

REPORT_FILE = os.path.join(
    OUTPUT_DIR,
    "self_evolution_report.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# CHECK FILES
# ============================================================

print("\nChecking required files...")
print("-" * 70)

required_files = {
    "Policy Evolution": EVOLUTION_FILE,
    "Evolved Parameters": PARAM_FILE,
    "Evolution History": HISTORY_FILE
}

for name, path in required_files.items():

    if not os.path.exists(path):
        print("[ERROR] Missing:", path)
        raise SystemExit(1)

    print("[OK]", name + ":", path)

# ============================================================
# LOAD FILES
# ============================================================

print("\nLoading policy evolution...")
evolution = pd.read_csv(EVOLUTION_FILE)

print("Loading evolved parameters...")
params = pd.read_csv(PARAM_FILE)

print("Loading evolution history...")
history = pd.read_csv(HISTORY_FILE)

print("\nINPUT SHAPES")
print("-" * 70)
print("Evolution:", evolution.shape)
print("Parameters:", params.shape)
print("History:", history.shape)

# ============================================================
# VALIDATE APPLIANCE
# ============================================================

for name, df in [
    ("Evolution", evolution),
    ("Parameters", params),
    ("History", history)
]:

    if "appliance" not in df.columns:
        raise ValueError(
            name + " file does not contain appliance column"
        )

# ============================================================
# SELECT SAFE COLUMNS
# ============================================================

param_columns = [
    "appliance",
    "evolved_adaptation_factor",
    "evolved_learning_rate",
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight"
]

param_columns = [
    c for c in param_columns
    if c in params.columns
]

params_small = params[param_columns].copy()

# Remove overlapping columns before merge
overlap = [
    c for c in params_small.columns
    if c != "appliance" and c in evolution.columns
]

if overlap:

    print("\nRemoving duplicate parameter columns:")

    for col in overlap:
        print("  [REMOVE]", col)

    params_small = params_small.drop(
        columns=overlap
    )

# ============================================================
# MERGE
# ============================================================

print("\nMerging evolution data...")

df = pd.merge(
    evolution,
    params_small,
    on="appliance",
    how="left"
)

print("Merged rows:", len(df))

# ============================================================
# NUMERIC CLEANING
# ============================================================

numeric_columns = [
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_factor",
    "evolved_adaptation_factor",
    "recommended_learning_rate",
    "evolved_learning_rate",
    "policy_confidence",
    "self_adaptation_score"
]

for col in numeric_columns:

    if col not in df.columns:
        df[col] = 0.0

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).fillna(0.0)

# ============================================================
# ADAPTATION CHANGES
# ============================================================

print("\nCalculating adaptation changes...")

df["adaptation_factor_change"] = (
    df["evolved_adaptation_factor"]
    -
    df["adaptation_factor"]
)

df["adaptation_factor_change_pct"] = np.where(
    df["adaptation_factor"] != 0,
    (
        df["adaptation_factor_change"]
        /
        df["adaptation_factor"]
    ) * 100,
    0
)

df["learning_rate_change"] = (
    df["evolved_learning_rate"]
    -
    df["recommended_learning_rate"]
)

df["learning_rate_change_pct"] = np.where(
    df["recommended_learning_rate"] != 0,
    (
        df["learning_rate_change"]
        /
        df["recommended_learning_rate"]
    ) * 100,
    0
)

# ============================================================
# EVOLUTION EFFECTIVENESS
# ============================================================

print("Calculating evolution effectiveness...")

df["positive_reward"] = (
    df["reward_improvement"] > 0
)

df["positive_savings"] = (
    df["estimated_savings_percentage"] > 0
)

df["policy_changed"] = (
    (
        df["adaptation_factor_change"].abs()
        > 0.000001
    )
    |
    (
        df["learning_rate_change"].abs()
        > 0.000001
    )
)

# ============================================================
# EVOLUTION EFFECTIVENESS SCORE
# ============================================================

df["evolution_effectiveness_score"] = (
    df["estimated_savings_percentage"].clip(0, 100) * 0.40
    +
    df["reward_improvement"].clip(0, 1) * 100 * 0.25
    +
    df["policy_confidence"].clip(0, 100) * 0.15
    +
    df["self_adaptation_score"].clip(0, 100) * 0.20
)

df["evolution_effectiveness_score"] = (
    df["evolution_effectiveness_score"]
    .clip(0, 100)
)

# ============================================================
# VALIDATION STATUS
# ============================================================

def validation_status(row):

    if (
        row["positive_savings"]
        and row["positive_reward"]
        and row["policy_changed"]
    ):
        return "Successful Evolution"

    elif (
        row["positive_savings"]
        and row["policy_changed"]
    ):
        return "Partial Evolution"

    elif row["positive_savings"]:
        return "Improvement Without Major Evolution"

    elif row["policy_changed"]:
        return "Policy Changed - Monitor"

    return "No Significant Evolution"


df["validation_status"] = df.apply(
    validation_status,
    axis=1
)

# ============================================================
# SELF-EVOLUTION LEVEL
# ============================================================

def evolution_level(score):

    if score >= 70:
        return "Strong Self-Evolution"

    elif score >= 50:
        return "Moderate Self-Evolution"

    elif score >= 25:
        return "Developing Self-Evolution"

    else:
        return "Early Self-Evolution"


df["self_evolution_level"] = (
    df["evolution_effectiveness_score"]
    .apply(evolution_level)
)

# ============================================================
# POLICY STABILITY
# ============================================================

df["policy_stability_score"] = (
    100
    -
    df["learning_rate_change_pct"].abs().clip(0, 100)
)

df["policy_stability_score"] = (
    df["policy_stability_score"]
    .clip(0, 100)
)

# ============================================================
# ADAPTATION QUALITY
# ============================================================

def adaptation_quality(row):

    score = row["evolution_effectiveness_score"]

    if score >= 70:
        return "High Quality"

    elif score >= 50:
        return "Good Quality"

    elif score >= 25:
        return "Developing Quality"

    return "Early Stage"


df["adaptation_quality"] = df.apply(
    adaptation_quality,
    axis=1
)

# ============================================================
# GENERATION VALIDATION
# ============================================================

if "evolution_generation" in df.columns:

    df["generation_valid"] = (
        pd.to_numeric(
            df["evolution_generation"],
            errors="coerce"
        ).fillna(0)
        >= 1
    )

else:

    df["generation_valid"] = True

# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12D VALIDATION")
print("=" * 70)

print("\nROWS:", len(df))
print("COLUMNS:", len(df.columns))

null_count = df.isnull().sum().sum()

print("\nNULL CHECK:")

if null_count == 0:
    print("NO NULLS")
else:
    print("NULLS FOUND:", null_count)

# ============================================================
# DISPLAY RESULTS
# ============================================================

display_columns = [
    "appliance",
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_factor",
    "evolved_adaptation_factor",
    "adaptation_factor_change_pct",
    "recommended_learning_rate",
    "evolved_learning_rate",
    "learning_rate_change_pct",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "validation_status",
    "self_evolution_level"
]

print("\nSELF-EVOLUTION RESULTS")
print("-" * 70)

print(
    df[display_columns]
    .to_string(index=False)
)

# ============================================================
# SCORE RANGE
# ============================================================

print("\nEVOLUTION EFFECTIVENESS SCORE RANGE:")

print(
    round(
        df["evolution_effectiveness_score"].min(),
        4
    ),
    "to",
    round(
        df["evolution_effectiveness_score"].max(),
        4
    )
)

# ============================================================
# VALIDATION CLASSES
# ============================================================

print("\nVALIDATION STATUS")

print(
    df[
        [
            "appliance",
            "validation_status"
        ]
    ].to_string(index=False)
)

print("\nSELF-EVOLUTION LEVEL")

print(
    df[
        [
            "appliance",
            "self_evolution_level"
        ]
    ].to_string(index=False)
)

# ============================================================
# OVERALL SYSTEM SCORE
# ============================================================

overall_score = (
    df["evolution_effectiveness_score"]
    .mean()
)

overall_savings = (
    df["estimated_savings_percentage"]
    .mean()
)

overall_reward = (
    df["reward_improvement"]
    .mean()
)

policy_change_rate = (
    df["policy_changed"].mean()
    * 100
)

print("\n" + "=" * 70)
print("OVERALL SELF-EVOLUTION")
print("-" * 70)

print(
    "Average evolution effectiveness:",
    round(overall_score, 4)
)

print(
    "Average savings percentage:",
    round(overall_savings, 4),
    "%"
)

print(
    "Average reward improvement:",
    round(overall_reward, 6)
)

print(
    "Policy change rate:",
    round(policy_change_rate, 2),
    "%"
)

# ============================================================
# OVERALL CLASS
# ============================================================

if overall_score >= 70:
    overall_class = "Strong Self-Evolution"

elif overall_score >= 50:
    overall_class = "Moderate Self-Evolution"

elif overall_score >= 25:
    overall_class = "Developing Self-Evolution"

else:
    overall_class = "Early Self-Evolution"

print(
    "Overall system status:",
    overall_class
)

# ============================================================
# SAVE VALIDATION SUMMARY
# ============================================================

df.to_csv(
    VALIDATION_FILE,
    index=False
)

# ============================================================
# SAVE COMPACT REPORT
# ============================================================

report_columns = [
    "appliance",
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_factor_change_pct",
    "learning_rate_change_pct",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "validation_status",
    "self_evolution_level",
    "adaptation_quality"
]

df[
    report_columns
].to_csv(
    REPORT_FILE,
    index=False
)

# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12D COMPLETE")
print("=" * 70)

print("\nValidation output:")
print(VALIDATION_FILE)

print("\nCompact report:")
print(REPORT_FILE)

print("\n" + "=" * 70)