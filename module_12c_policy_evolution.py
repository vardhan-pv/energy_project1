import os
import pandas as pd
import numpy as np

# ============================================================
# MODULE 12C — POLICY EVOLUTION & SELF-ADAPTATION
# ============================================================

print("=" * 70)
print("MODULE 12C — POLICY EVOLUTION & SELF-ADAPTATION")
print("=" * 70)

# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"E:\energy_project"

INPUT_FILE = os.path.join(
    BASE_DIR,
    "adaptive_policy",
    "adaptive_policy_summary.csv"
)

PARAM_FILE = os.path.join(
    BASE_DIR,
    "adaptive_policy",
    "adaptive_policy_parameters.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "evolution_output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "policy_evolution_summary.csv"
)

PARAM_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "evolved_policy_parameters.csv"
)

HISTORY_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "policy_evolution_history.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# CHECK FILES
# ============================================================

print("\nChecking required files...")
print("-" * 70)

if not os.path.exists(INPUT_FILE):
    print("[ERROR] Missing:")
    print(INPUT_FILE)
    raise SystemExit(1)

if not os.path.exists(PARAM_FILE):
    print("[ERROR] Missing:")
    print(PARAM_FILE)
    raise SystemExit(1)

print("[OK] Adaptive policy summary:")
print(INPUT_FILE)

print("[OK] Adaptive policy parameters:")
print(PARAM_FILE)

# ============================================================
# LOAD
# ============================================================

print("\nLoading adaptive policy summary...")
policy = pd.read_csv(INPUT_FILE)

print("Loading adaptive policy parameters...")
params = pd.read_csv(PARAM_FILE)

print("\nINPUT SHAPES")
print("-" * 70)
print("Policy:", policy.shape)
print("Parameters:", params.shape)

# ============================================================
# VALIDATE APPLIANCE COLUMN
# ============================================================

if "appliance" not in policy.columns:
    raise ValueError("Policy file does not contain 'appliance' column")

if "appliance" not in params.columns:
    raise ValueError("Parameter file does not contain 'appliance' column")

# ============================================================
# REMOVE OVERLAPPING COLUMNS BEFORE MERGE
# ============================================================

print("\nPreparing policy data...")

parameter_columns = [
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

available_parameter_columns = [
    c for c in parameter_columns
    if c in params.columns
]

params_small = params[available_parameter_columns].copy()

# Columns already existing in policy
overlap = [
    c for c in params_small.columns
    if c != "appliance" and c in policy.columns
]

if overlap:
    print("\nRemoving overlapping parameter columns before merge:")
    for col in overlap:
        print("  [REMOVE]", col)

    params_small = params_small.drop(columns=overlap)

# ============================================================
# MERGE
# ============================================================

print("\nMerging adaptive policy + policy parameters...")

df = pd.merge(
    policy,
    params_small,
    on="appliance",
    how="left"
)

print("Merged rows:", len(df))

# ============================================================
# REQUIRED NUMERIC COLUMNS
# ============================================================

numeric_defaults = {
    "estimated_savings_percentage": 0.0,
    "reward_improvement": 0.0,
    "adaptation_factor": 1.0,
    "recommended_learning_rate": 0.01,
    "policy_confidence": 0.0,
    "maintain_weight": 1.0,
    "reduce_weight": 1.0,
    "shift_weight": 1.0,
    "turn_off_weight": 1.0
}

for col, default in numeric_defaults.items():

    if col not in df.columns:
        df[col] = default

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).fillna(default)

# ============================================================
# CLEAN STRING COLUMNS
# ============================================================

if "policy_class" not in df.columns:
    df["policy_class"] = "Unknown"

if "policy_update" not in df.columns:
    df["policy_update"] = "maintain_policy"

df["policy_class"] = df["policy_class"].fillna("Unknown")
df["policy_update"] = df["policy_update"].fillna("maintain_policy")

# ============================================================
# EVOLUTION LOGIC
# ============================================================

print("\nCalculating policy evolution...")

def evolution_decision(row):

    savings = row["estimated_savings_percentage"]
    reward = row["reward_improvement"]
    confidence = row["policy_confidence"]

    # Strong improvement
    if savings >= 7 and reward > 0.01:
        return "accelerate_evolution"

    # Moderate improvement
    elif savings >= 3 and reward > 0.001:
        return "continue_evolution"

    # Small positive improvement
    elif savings > 0 and reward >= 0:
        return "slow_evolution"

    # Negative feedback
    elif reward < 0:
        return "policy_review"

    # Otherwise maintain
    return "maintain_evolution"


df["evolution_decision"] = df.apply(
    evolution_decision,
    axis=1
)

# ============================================================
# EVOLUTION GENERATION
# ============================================================

df["previous_generation"] = 1

df["evolution_generation"] = np.where(
    df["evolution_decision"].isin([
        "accelerate_evolution",
        "continue_evolution",
        "slow_evolution"
    ]),
    2,
    1
)

# ============================================================
# ADAPTIVE FACTOR UPDATE
# ============================================================

def evolve_factor(row):

    factor = row["adaptation_factor"]
    decision = row["evolution_decision"]

    if decision == "accelerate_evolution":
        factor *= 1.15

    elif decision == "continue_evolution":
        factor *= 1.08

    elif decision == "slow_evolution":
        factor *= 1.03

    elif decision == "policy_review":
        factor *= 0.95

    else:
        factor *= 1.00

    return float(np.clip(factor, 0.5, 2.0))


df["evolved_adaptation_factor"] = df.apply(
    evolve_factor,
    axis=1
)

# ============================================================
# LEARNING RATE EVOLUTION
# ============================================================

def evolve_learning_rate(row):

    lr = row["recommended_learning_rate"]
    decision = row["evolution_decision"]

    if decision == "accelerate_evolution":
        lr *= 1.20

    elif decision == "continue_evolution":
        lr *= 1.10

    elif decision == "slow_evolution":
        lr *= 1.03

    elif decision == "policy_review":
        lr *= 0.80

    return float(np.clip(lr, 0.001, 0.10))


df["evolved_learning_rate"] = df.apply(
    evolve_learning_rate,
    axis=1
)

# ============================================================
# ACTION WEIGHT EVOLUTION
# ============================================================

print("Updating action weights...")

df["evolved_maintain_weight"] = df["maintain_weight"]
df["evolved_reduce_weight"] = df["reduce_weight"]
df["evolved_shift_weight"] = df["shift_weight"]
df["evolved_turn_off_weight"] = df["turn_off_weight"]

for i in df.index:

    decision = df.loc[i, "evolution_decision"]

    if decision == "accelerate_evolution":

        df.loc[i, "evolved_reduce_weight"] *= 1.15
        df.loc[i, "evolved_shift_weight"] *= 1.10
        df.loc[i, "evolved_turn_off_weight"] *= 1.05

    elif decision == "continue_evolution":

        df.loc[i, "evolved_reduce_weight"] *= 1.08
        df.loc[i, "evolved_shift_weight"] *= 1.05

    elif decision == "slow_evolution":

        df.loc[i, "evolved_reduce_weight"] *= 1.03

    elif decision == "policy_review":

        df.loc[i, "evolved_maintain_weight"] *= 1.10
        df.loc[i, "evolved_reduce_weight"] *= 0.90

# ============================================================
# NORMALIZE ACTION WEIGHTS
# ============================================================

weight_columns = [
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight"
]

for col in weight_columns:
    df[col] = df[col].clip(lower=0.1)

weight_sum = df[weight_columns].sum(axis=1)

for col in weight_columns:
    df[col] = df[col] / weight_sum * 4.0

# ============================================================
# SELF-ADAPTATION SCORE
# ============================================================

print("Calculating self-adaptation score...")

df["self_adaptation_score"] = (
    df["estimated_savings_percentage"].clip(0, 100) * 0.40
    +
    df["reward_improvement"].clip(0, 1) * 100 * 0.25
    +
    df["policy_confidence"].clip(0, 100) * 0.20
    +
    (df["evolved_adaptation_factor"] / 2.0 * 100) * 0.15
)

df["self_adaptation_score"] = df[
    "self_adaptation_score"
].clip(0, 100)

# ============================================================
# EVOLUTION CLASS
# ============================================================

def evolution_class(score):

    if score >= 70:
        return "Highly Adaptive"

    elif score >= 50:
        return "Adaptive"

    elif score >= 25:
        return "Moderately Adaptive"

    else:
        return "Limited Adaptation"


df["evolution_class"] = df[
    "self_adaptation_score"
].apply(evolution_class)

# ============================================================
# POLICY VERSION
# ============================================================

df["policy_version"] = "v2.0"

# ============================================================
# EVOLUTION STATUS
# ============================================================

def evolution_status(row):

    decision = row["evolution_decision"]

    if decision == "accelerate_evolution":
        return "Rapid Self-Adaptation"

    elif decision == "continue_evolution":
        return "Active Self-Adaptation"

    elif decision == "slow_evolution":
        return "Gradual Self-Adaptation"

    elif decision == "policy_review":
        return "Requires Policy Review"

    return "Stable"


df["evolution_status"] = df.apply(
    evolution_status,
    axis=1
)

# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12C VALIDATION")
print("=" * 70)

print("\nROWS:", len(df))
print("COLUMNS:", len(df.columns))

print("\nNULL CHECK:")

null_count = df.isnull().sum().sum()

if null_count == 0:
    print("NO NULLS")
else:
    print("NULLS FOUND:", null_count)

# ============================================================
# RESULTS
# ============================================================

display_columns = [
    "appliance",
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_factor",
    "evolved_adaptation_factor",
    "recommended_learning_rate",
    "evolved_learning_rate",
    "policy_confidence",
    "evolution_decision",
    "self_adaptation_score",
    "evolution_class",
    "evolution_status",
    "policy_version"
]

print("\nPOLICY EVOLUTION RESULTS")
print("-" * 70)

print(
    df[display_columns].to_string(index=False)
)

print("\nSELF-ADAPTATION SCORE RANGE:")

print(
    round(df["self_adaptation_score"].min(), 4),
    "to",
    round(df["self_adaptation_score"].max(), 4)
)

print("\nEVOLUTION CLASSES")
print(
    df[
        ["appliance", "evolution_class"]
    ].to_string(index=False)
)

print("\nEVOLUTION DECISIONS")
print(
    df[
        ["appliance", "evolution_decision"]
    ].to_string(index=False)
)

# ============================================================
# SAVE MAIN OUTPUT
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# SAVE EVOLVED PARAMETERS
# ============================================================

parameter_output_columns = [
    "appliance",
    "policy_version",
    "evolution_generation",
    "evolved_adaptation_factor",
    "evolved_learning_rate",
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_class",
    "evolution_decision",
    "evolution_status"
]

df[
    parameter_output_columns
].to_csv(
    PARAM_OUTPUT,
    index=False
)

# ============================================================
# SAVE HISTORY
# ============================================================

history_columns = [
    "appliance",
    "previous_generation",
    "evolution_generation",
    "policy_version",
    "estimated_savings_percentage",
    "reward_improvement",
    "adaptation_factor",
    "evolved_adaptation_factor",
    "recommended_learning_rate",
    "evolved_learning_rate",
    "self_adaptation_score",
    "evolution_decision",
    "evolution_class",
    "evolution_status"
]

df[
    history_columns
].to_csv(
    HISTORY_OUTPUT,
    index=False
)

# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MODULE 12C COMPLETE")
print("=" * 70)

print("\nMain output:")
print(OUTPUT_FILE)

print("\nEvolved parameters:")
print(PARAM_OUTPUT)

print("\nEvolution history:")
print(HISTORY_OUTPUT)

print("\n" + "=" * 70)