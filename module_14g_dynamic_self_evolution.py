# ================================================================
# MODULE 14G — DYNAMIC SELF-EVOLUTION
# ================================================================
# Purpose:
#   Automatically evaluate the dynamic RL policy and evolve:
#       - adaptation factor
#       - learning rate
#       - action weights
#       - policy confidence
#       - self-adaptation score
#
# Input:
#   14A House Initialization
#   14D Dynamic Features
#   14E Dynamic ML/RL Model Training
#   14F Dynamic RL Optimization
#
# Output:
#   Dynamic self-evolution results
#   Evolved policy parameters
#   Evolution history
#   System summary
# ================================================================

import os
import json
import time
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

START_TIME = time.time()

# ================================================================
# PATHS
# ================================================================

BASE_DIR = r"E:\energy_project"

INIT_DIR = os.path.join(BASE_DIR, "initialization")
HOUSE_DATA_DIR = os.path.join(BASE_DIR, "house_data")

HOUSE_CONFIG = os.path.join(
    INIT_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG = os.path.join(
    INIT_DIR,
    "appliance_config.csv"
)

# ================================================================
# LOAD HOUSE CONFIGURATION
# ================================================================

print("=" * 70)
print("MODULE 14G — DYNAMIC SELF-EVOLUTION")
print("=" * 70)

print()
print("=" * 70)
print("CHECKING REQUIRED FILES")
print("=" * 70)

required_files = [
    ("House configuration", HOUSE_CONFIG),
    ("Appliance configuration", APPLIANCE_CONFIG),
]

for name, path in required_files:
    if os.path.exists(path):
        print(f"[OK] {name}: {path}")
    else:
        raise FileNotFoundError(
            f"[ERROR] Missing {name}: {path}"
        )

# ================================================================
# LOAD HOUSE CONFIG
# ================================================================

print()
print("Loading house configuration...")

with open(HOUSE_CONFIG, "r", encoding="utf-8") as f:
    house_config = json.load(f)

HOUSE_ID = (
    house_config.get("house_id")
    or house_config.get("id")
    or "UNKNOWN_HOUSE"
)

HOUSE_NAME = (
    house_config.get("house_name")
    or house_config.get("name")
    or HOUSE_ID
)

LOCATION = house_config.get(
    "location",
    ""
)

print(f"House ID   : {HOUSE_ID}")
print(f"House Name : {HOUSE_NAME}")
print(f"Location   : {LOCATION}")

# ================================================================
# HOUSE PATHS
# ================================================================

HOUSE_DIR = os.path.join(
    HOUSE_DATA_DIR,
    HOUSE_ID
)

FEATURE_DIR = os.path.join(
    HOUSE_DIR,
    "features"
)

MODEL_DIR = os.path.join(
    HOUSE_DIR,
    "models"
)

OPTIMIZATION_DIR = os.path.join(
    HOUSE_DIR,
    "optimization"
)

EVOLUTION_DIR = os.path.join(
    HOUSE_DIR,
    "evolution"
)

os.makedirs(EVOLUTION_DIR, exist_ok=True)

DYNAMIC_FEATURES = os.path.join(
    FEATURE_DIR,
    "dynamic_features.csv"
)

TRAINING_SUMMARY = os.path.join(
    MODEL_DIR,
    "dynamic_training_summary.csv"
)

MODEL_REGISTRY = os.path.join(
    MODEL_DIR,
    "model_registry.csv"
)

RL_OPTIMIZATION = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization.csv"
)

RL_OPTIMIZATION_SUMMARY = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_rl_optimization_summary.csv"
)

ACTION_SUMMARY = os.path.join(
    OPTIMIZATION_DIR,
    "dynamic_action_summary.csv"
)

# ================================================================
# OUTPUT FILES
# ================================================================

SELF_EVOLUTION_OUTPUT = os.path.join(
    EVOLUTION_DIR,
    "dynamic_self_evolution_summary.csv"
)

EVOLVED_PARAMETERS_OUTPUT = os.path.join(
    EVOLUTION_DIR,
    "dynamic_evolved_policy_parameters.csv"
)

EVOLUTION_HISTORY_OUTPUT = os.path.join(
    EVOLUTION_DIR,
    "dynamic_policy_evolution_history.csv"
)

SYSTEM_SUMMARY_OUTPUT = os.path.join(
    EVOLUTION_DIR,
    "dynamic_self_evolution_system_summary.csv"
)

# ================================================================
# CHECK REQUIRED INPUTS
# ================================================================

print()
for name, path in [
    ("Dynamic features", DYNAMIC_FEATURES),
    ("Training summary", TRAINING_SUMMARY),
    ("Model registry", MODEL_REGISTRY),
    ("RL optimization", RL_OPTIMIZATION),
    ("Optimization summary", RL_OPTIMIZATION_SUMMARY),
    ("Action summary", ACTION_SUMMARY),
]:
    if os.path.exists(path):
        print(f"[OK] {name}: {path}")
    else:
        raise FileNotFoundError(
            f"[ERROR] Required file missing: {path}"
        )

# ================================================================
# LOAD APPLIANCES
# ================================================================

print()
print("Loading appliance configuration...")

appliances = pd.read_csv(
    APPLIANCE_CONFIG
)

print(
    f"Registered appliances: {len(appliances)}"
)

print()

display_columns = [
    c for c in [
        "appliance_id",
        "house_id",
        "appliance_name",
        "appliance_type",
        "sensor_id",
        "rated_power_w",
        "status",
        "created_at",
    ]
    if c in appliances.columns
]

print(
    appliances[display_columns].to_string(
        index=False
    )
)

# ================================================================
# LOAD INPUT DATA
# ================================================================

print()
print("Loading dynamic features...")
features = pd.read_csv(
    DYNAMIC_FEATURES
)

print(
    f"Rows loaded    : {len(features)}"
)
print(
    f"Columns loaded : {len(features.columns)}"
)

print()
print("Loading RL optimization...")
optimization = pd.read_csv(
    RL_OPTIMIZATION
)

print(
    f"Rows loaded    : {len(optimization)}"
)
print(
    f"Columns loaded : {len(optimization.columns)}"
)

print()
print("Loading training summary...")
training = pd.read_csv(
    TRAINING_SUMMARY
)

print(
    f"Training records: {len(training)}"
)

# ================================================================
# INPUT VALIDATION
# ================================================================

print()
print("=" * 70)
print("INPUT VALIDATION")
print("=" * 70)

print(
    f"House appliances : {len(appliances)}"
)

print(
    f"Feature rows     : {len(features)}"
)

print(
    f"Optimization rows: {len(optimization)}"
)

print(
    f"Training records : {len(training)}"
)

# ================================================================
# NORMALIZE COLUMN NAMES
# ================================================================

def normalize_columns(df):
    df = df.copy()
    df.columns = [
        str(c).strip()
        for c in df.columns
    ]
    return df


appliances = normalize_columns(appliances)
features = normalize_columns(features)
optimization = normalize_columns(optimization)
training = normalize_columns(training)

# ================================================================
# DETERMINE APPLIANCE KEY
# ================================================================

if "appliance_id" in optimization.columns:
    OPT_KEY = "appliance_id"

elif "appliance" in optimization.columns:
    OPT_KEY = "appliance"

elif "appliance_name" in optimization.columns:
    OPT_KEY = "appliance_name"

else:
    raise ValueError(
        "Optimization file does not contain an appliance identifier."
    )

# ================================================================
# PREPARE APPLIANCE IDENTIFIERS
# ================================================================

if "appliance_id" in appliances.columns:

    appliance_ids = (
        appliances["appliance_id"]
        .astype(str)
        .str.strip()
    )

else:

    appliance_ids = pd.Series(
        range(len(appliances)),
        dtype=str
    )

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def ensure_numeric(
    df,
    column,
    default=0.0
):
    """
    Guarantee that a column exists and is numeric.
    Most importantly, returns a pandas Series rather
    than a Python integer.
    """

    if column not in df.columns:

        df[column] = pd.Series(
            default,
            index=df.index,
            dtype=float
        )

    else:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(default)

    return df[column]


def safe_divide(
    numerator,
    denominator
):
    """
    Safe element-wise division.
    """

    numerator = pd.to_numeric(
        numerator,
        errors="coerce"
    ).fillna(0)

    denominator = pd.to_numeric(
        denominator,
        errors="coerce"
    ).fillna(0)

    result = pd.Series(
        np.zeros(len(numerator)),
        index=numerator.index,
        dtype=float
    )

    mask = denominator != 0

    result.loc[mask] = (
        numerator.loc[mask]
        /
        denominator.loc[mask]
    )

    return result


def clip_series(
    series,
    low,
    high
):
    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0).clip(
        lower=low,
        upper=high
    )


# ================================================================
# PREPARE OPTIMIZATION DATA
# ================================================================

print()
print("=" * 70)
print("AGGREGATING OPTIMIZATION PERFORMANCE")
print("=" * 70)

opt = optimization.copy()

# ------------------------------------------------
# Ensure action columns exist
# ------------------------------------------------

action_columns = [
    "maintain_actions",
    "reduce_actions",
    "shift_actions",
    "turn_off_actions",
]

for col in action_columns:
    ensure_numeric(
        opt,
        col,
        0.0
    )

# ------------------------------------------------
# Ensure important numerical columns
# ------------------------------------------------

numeric_columns = [
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "policy_confidence",
    "mae",
    "rmse",
]

for col in numeric_columns:
    if col in opt.columns:
        ensure_numeric(
            opt,
            col,
            0.0
        )

# ================================================================
# FIND ENERGY COLUMNS
# ================================================================

if "original_energy_kwh" not in opt.columns:

    if "energy_kwh" in opt.columns:

        opt["original_energy_kwh"] = (
            pd.to_numeric(
                opt["energy_kwh"],
                errors="coerce"
            ).fillna(0)
        )

    else:

        opt["original_energy_kwh"] = pd.Series(
            0.0,
            index=opt.index
        )


if "optimized_energy_kwh" not in opt.columns:

    opt["optimized_energy_kwh"] = (
        opt["original_energy_kwh"]
        .astype(float)
    )


# ================================================================
# CALCULATE SAVINGS
# ================================================================

opt["estimated_savings_kwh"] = (
    pd.to_numeric(
        opt["original_energy_kwh"],
        errors="coerce"
    ).fillna(0)
    -
    pd.to_numeric(
        opt["optimized_energy_kwh"],
        errors="coerce"
    ).fillna(0)
)

opt["estimated_savings_kwh"] = (
    opt["estimated_savings_kwh"]
    .clip(lower=0)
)

opt["calculated_savings_percentage"] = (
    safe_divide(
        opt["estimated_savings_kwh"],
        opt["original_energy_kwh"]
    ) * 100
)

# ================================================================
# USE PROVIDED SAVINGS % IF AVAILABLE
# ================================================================

if "estimated_savings_percentage" in opt.columns:

    opt["estimated_savings_percentage"] = (
        pd.to_numeric(
            opt["estimated_savings_percentage"],
            errors="coerce"
        )
        .fillna(
            opt["calculated_savings_percentage"]
        )
    )

else:

    opt["estimated_savings_percentage"] = (
        opt["calculated_savings_percentage"]
    )

# ================================================================
# AGGREGATE BY APPLIANCE
# ================================================================

grouped = []

for appliance_key, group in opt.groupby(
    OPT_KEY,
    dropna=False
):

    original_energy = (
        group["original_energy_kwh"]
        .sum()
    )

    optimized_energy = (
        group["optimized_energy_kwh"]
        .sum()
    )

    savings = (
        max(
            0.0,
            original_energy -
            optimized_energy
        )
    )

    savings_pct = (
        (savings / original_energy) * 100
        if original_energy > 0
        else group[
            "estimated_savings_percentage"
        ].mean()
    )

    maintain = int(
        group[
            "maintain_actions"
        ].sum()
    )

    reduce = int(
        group[
            "reduce_actions"
        ].sum()
    )

    shift = int(
        group[
            "shift_actions"
        ].sum()
    )

    turn_off = int(
        group[
            "turn_off_actions"
        ].sum()
    )

    total_actions = (
        maintain +
        reduce +
        shift +
        turn_off
    )

    if total_actions > 0:

        maintain_rate = (
            maintain /
            total_actions *
            100
        )

        reduce_rate = (
            reduce /
            total_actions *
            100
        )

        shift_rate = (
            shift /
            total_actions *
            100
        )

        turn_off_rate = (
            turn_off /
            total_actions *
            100
        )

    else:

        maintain_rate = 0.0
        reduce_rate = 0.0
        shift_rate = 0.0
        turn_off_rate = 0.0

    if "policy_confidence" in group.columns:

        confidence = float(
            group[
                "policy_confidence"
            ].mean()
        )

    else:

        confidence = 50.0

    grouped.append({

        OPT_KEY: appliance_key,

        "optimization_rows":
            len(group),

        "original_energy_kwh":
            original_energy,

        "optimized_energy_kwh":
            optimized_energy,

        "estimated_savings_kwh":
            savings,

        "estimated_savings_percentage":
            savings_pct,

        "maintain_actions":
            maintain,

        "reduce_actions":
            reduce,

        "shift_actions":
            shift,

        "turn_off_actions":
            turn_off,

        "maintain_rate":
            maintain_rate,

        "reduce_rate":
            reduce_rate,

        "shift_rate":
            shift_rate,

        "turn_off_rate":
            turn_off_rate,

        "policy_confidence":
            confidence,

        "total_actions":
            total_actions,
    })


performance = pd.DataFrame(
    grouped
)

# ================================================================
# MERGE APPLIANCE METADATA
# ================================================================

print()
print("Merging appliance metadata...")

if (
    OPT_KEY == "appliance_id"
    and
    "appliance_id" in appliances.columns
):

    metadata_columns = [
        c for c in [
            "appliance_id",
            "appliance_name",
            "appliance_type",
            "sensor_id",
            "rated_power_w",
        ]
        if c in appliances.columns
    ]

    metadata = appliances[
        metadata_columns
    ].drop_duplicates(
        subset=["appliance_id"]
    )

    performance = performance.merge(
        metadata,
        on="appliance_id",
        how="left"
    )

elif (
    OPT_KEY == "appliance"
    and
    "appliance_name" in appliances.columns
):

    metadata = appliances[
        [
            c for c in [
                "appliance_name",
                "appliance_type",
                "sensor_id",
                "rated_power_w",
            ]
            if c in appliances.columns
        ]
    ].drop_duplicates(
        subset=["appliance_name"]
    )

    performance = performance.merge(
        metadata,
        left_on="appliance",
        right_on="appliance_name",
        how="left"
    )

# ================================================================
# MERGE TRAINING QUALITY
# ================================================================

if (
    "appliance_id" in performance.columns
    and
    "appliance_id" in training.columns
):

    train_columns = [
        c for c in [
            "appliance_id",
            "mae",
            "rmse",
            "training_samples",
            "features",
            "data_quality",
            "model_status",
        ]
        if c in training.columns
    ]

    if len(train_columns) > 1:

        train_data = training[
            train_columns
        ].drop_duplicates(
            subset=["appliance_id"]
        )

        performance = performance.merge(
            train_data,
            on="appliance_id",
            how="left"
        )

# ================================================================
# FILL TRAINING INFORMATION
# ================================================================

if "training_samples" not in performance.columns:

    performance["training_samples"] = (
        performance["optimization_rows"]
    )

if "features" not in performance.columns:

    performance["features"] = 17

if "data_quality" not in performance.columns:

    performance["data_quality"] = (
        "DEMO_LOW_DATA"
    )

if "model_status" not in performance.columns:

    performance["model_status"] = (
        "TRAINED_DYNAMIC"
    )

performance["training_samples"] = (
    pd.to_numeric(
        performance["training_samples"],
        errors="coerce"
    ).fillna(0)
)

# ================================================================
# CALCULATE SELF-EVOLUTION METRICS
# ================================================================

print()
print("Calculating self-evolution metrics...")

# ------------------------------------------------
# Savings score
# ------------------------------------------------

performance["savings_score"] = (
    clip_series(
        performance[
            "estimated_savings_percentage"
        ],
        0,
        100
    )
)

# Normalize to 0–100
performance["savings_score_normalized"] = (
    performance["savings_score"]
    .clip(0, 100)
)

# ------------------------------------------------
# Action diversity
# ------------------------------------------------

performance["action_diversity"] = (
    (
        (performance["maintain_actions"] > 0)
        .astype(int)
        +
        (performance["reduce_actions"] > 0)
        .astype(int)
        +
        (performance["shift_actions"] > 0)
        .astype(int)
        +
        (performance["turn_off_actions"] > 0)
        .astype(int)
    )
)

performance["action_diversity_score"] = (
    performance["action_diversity"]
    / 4
    * 100
)

# ------------------------------------------------
# Adaptation pressure
# ------------------------------------------------

performance["adaptation_pressure"] = (
    (
        performance["reduce_rate"]
        +
        performance["shift_rate"]
        +
        performance["turn_off_rate"]
    )
    .clip(0, 100)
)

# ------------------------------------------------
# Policy confidence
# ------------------------------------------------

performance["policy_confidence"] = (
    pd.to_numeric(
        performance["policy_confidence"],
        errors="coerce"
    )
    .fillna(50)
    .clip(0, 100)
)

# ================================================================
# DATA QUALITY SCORE
# ================================================================

performance["data_quality_score"] = 0.0

for idx in performance.index:

    samples = float(
        performance.loc[
            idx,
            "training_samples"
        ]
    )

    if samples >= 1000:
        score = 100.0

    elif samples >= 500:
        score = 85.0

    elif samples >= 100:
        score = 70.0

    elif samples >= 50:
        score = 55.0

    elif samples >= 20:
        score = 40.0

    else:
        score = 25.0

    performance.loc[
        idx,
        "data_quality_score"
    ] = score

# ================================================================
# MODEL PERFORMANCE SCORE
# ================================================================

if "rmse" in performance.columns:

    performance["rmse"] = (
        pd.to_numeric(
            performance["rmse"],
            errors="coerce"
        ).fillna(0)
    )

    rmse_score = (
        100 /
        (
            1 +
            performance["rmse"]
        )
    )

    performance["model_performance_score"] = (
        rmse_score.clip(0, 100)
    )

else:

    performance["model_performance_score"] = 50.0

# ================================================================
# SELF-ADAPTATION SCORE
# ================================================================

performance["self_adaptation_score"] = (
    performance["savings_score_normalized"] * 0.30
    +
    performance["policy_confidence"] * 0.25
    +
    performance["action_diversity_score"] * 0.15
    +
    performance["adaptation_pressure"] * 0.15
    +
    performance["data_quality_score"] * 0.10
    +
    performance["model_performance_score"] * 0.05
)

performance["self_adaptation_score"] = (
    performance["self_adaptation_score"]
    .clip(0, 100)
)

# ================================================================
# EVOLUTION EFFECTIVENESS
# ================================================================

performance["evolution_effectiveness_score"] = (
    performance["self_adaptation_score"] * 0.60
    +
    performance["savings_score_normalized"] * 0.25
    +
    performance["policy_confidence"] * 0.15
)

performance["evolution_effectiveness_score"] = (
    performance[
        "evolution_effectiveness_score"
    ]
    .clip(0, 100)
)

# ================================================================
# ADAPTATION FACTOR
# ================================================================

def calculate_adaptation_factor(row):

    savings = float(
        row[
            "estimated_savings_percentage"
        ]
    )

    confidence = float(
        row[
            "policy_confidence"
        ]
    )

    score = float(
        row[
            "self_adaptation_score"
        ]
    )

    # Base factor
    factor = 1.0

    if savings >= 10 and confidence >= 50:
        factor = 1.15

    elif savings >= 5 and confidence >= 40:
        factor = 1.10

    elif savings >= 2:
        factor = 1.05

    else:
        factor = 1.02

    # Self-evolution adjustment
    if score >= 70:
        factor += 0.05

    elif score >= 50:
        factor += 0.02

    return round(
        min(
            factor,
            1.30
        ),
        4
    )


performance["adaptation_factor"] = (
    performance.apply(
        calculate_adaptation_factor,
        axis=1
    )
)

# ================================================================
# LEARNING RATE
# ================================================================

performance["base_learning_rate"] = (
    0.025
)

performance["recommended_learning_rate"] = (
    performance[
        "base_learning_rate"
    ]
    *
    performance[
        "adaptation_factor"
    ]
)

# Keep learning rate stable
performance["recommended_learning_rate"] = (
    performance[
        "recommended_learning_rate"
    ]
    .clip(
        lower=0.005,
        upper=0.10
    )
)

# ================================================================
# ACTION WEIGHTS
# ================================================================

# Start from equal policy weights.
performance["maintain_weight"] = 1.0
performance["reduce_weight"] = 1.0
performance["shift_weight"] = 1.0
performance["turn_off_weight"] = 1.0

# Reduce action becomes stronger when savings are good
performance["reduce_weight"] = (
    1.0
    +
    (
        performance[
            "estimated_savings_percentage"
        ]
        / 100
    )
    .clip(0, 0.50)
)

# Shift action becomes stronger when shift is actually used
performance["shift_weight"] = (
    1.0
    +
    (
        performance["shift_rate"]
        / 100
    )
    .clip(0, 0.50)
)

# Turn-off action
performance["turn_off_weight"] = (
    1.0
    +
    (
        performance["turn_off_rate"]
        / 100
    )
    .clip(0, 0.50)
)

# Maintain weight protects comfort
performance["maintain_weight"] = (
    1.0
    +
    (
        performance["maintain_rate"]
        / 100
    )
    .clip(0, 0.30)
)

# ================================================================
# EVOLVED ACTION WEIGHTS
# ================================================================

performance["evolved_maintain_weight"] = (
    performance["maintain_weight"]
    *
    performance["adaptation_factor"]
)

performance["evolved_reduce_weight"] = (
    performance["reduce_weight"]
    *
    performance["adaptation_factor"]
)

performance["evolved_shift_weight"] = (
    performance["shift_weight"]
    *
    performance["adaptation_factor"]
)

performance["evolved_turn_off_weight"] = (
    performance["turn_off_weight"]
    *
    performance["adaptation_factor"]
)

# ================================================================
# EVOLUTION DECISION
# ================================================================

def evolution_decision(row):

    score = float(
        row[
            "evolution_effectiveness_score"
        ]
    )

    savings = float(
        row[
            "estimated_savings_percentage"
        ]
    )

    confidence = float(
        row[
            "policy_confidence"
        ]
    )

    if (
        score >= 60
        and
        savings >= 5
        and
        confidence >= 60
    ):
        return "accelerate_evolution"

    elif (
        score >= 40
        and
        savings >= 2
    ):
        return "continue_evolution"

    elif score >= 20:
        return "gradual_evolution"

    else:
        return "maintain_policy"


performance["evolution_decision"] = (
    performance.apply(
        evolution_decision,
        axis=1
    )
)

# ================================================================
# EVOLUTION CLASS
# ================================================================

def evolution_class(score):

    if score >= 70:
        return "Highly Adaptive"

    elif score >= 50:
        return "Moderately Adaptive"

    elif score >= 25:
        return "Limited Adaptation"

    return "Stable Policy"


performance["evolution_class"] = (
    performance[
        "evolution_effectiveness_score"
    ]
    .apply(evolution_class)
)

# ================================================================
# EVOLUTION STATUS
# ================================================================

def evolution_status(row):

    decision = row[
        "evolution_decision"
    ]

    if decision == "accelerate_evolution":
        return "Rapid Self-Adaptation"

    elif decision == "continue_evolution":
        return "Active Self-Adaptation"

    elif decision == "gradual_evolution":
        return "Gradual Self-Adaptation"

    return "Stable Policy"


performance["evolution_status"] = (
    performance.apply(
        evolution_status,
        axis=1
    )
)

# ================================================================
# POLICY VERSION
# ================================================================

performance["previous_generation"] = 1

performance["evolution_generation"] = 2

performance["policy_version"] = "v2.0"

# ================================================================
# VALIDATION STATUS
# ================================================================

performance["validation_status"] = (
    np.where(
        (
            performance[
                "evolution_effectiveness_score"
            ] >= 20
        )
        &
        (
            performance[
                "estimated_savings_kwh"
            ] >= 0
        ),
        "Successful Evolution",
        "Needs Review"
    )
)

# ================================================================
# SELF-EVOLUTION LEVEL
# ================================================================

def self_evolution_level(score):

    if score >= 70:
        return "Advanced Self-Evolution"

    elif score >= 50:
        return "Active Self-Evolution"

    elif score >= 25:
        return "Early Self-Evolution"

    return "Pre-Self-Evolution"


performance["self_evolution_level"] = (
    performance[
        "evolution_effectiveness_score"
    ]
    .apply(
        self_evolution_level
    )
)

# ================================================================
# HOUSE ID / HOUSE NAME
# ================================================================

performance.insert(
    0,
    "house_id",
    HOUSE_ID
)

performance.insert(
    1,
    "house_name",
    HOUSE_NAME
)

# ================================================================
# ROUND NUMERICAL VALUES
# ================================================================

numeric_output_columns = [
    "original_energy_kwh",
    "optimized_energy_kwh",
    "estimated_savings_kwh",
    "estimated_savings_percentage",
    "maintain_rate",
    "reduce_rate",
    "shift_rate",
    "turn_off_rate",
    "policy_confidence",
    "savings_score",
    "action_diversity_score",
    "adaptation_pressure",
    "data_quality_score",
    "model_performance_score",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "adaptation_factor",
    "base_learning_rate",
    "recommended_learning_rate",
    "maintain_weight",
    "reduce_weight",
    "shift_weight",
    "turn_off_weight",
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight",
]

for col in numeric_output_columns:

    if col in performance.columns:

        performance[col] = pd.to_numeric(
            performance[col],
            errors="coerce"
        ).fillna(0).round(6)

# ================================================================
# NULL CLEANUP
# ================================================================

performance = performance.replace(
    [np.inf, -np.inf],
    np.nan
)

performance = performance.fillna(0)

# Restore text columns that could have been affected
for col in [
    "house_id",
    "house_name",
    "data_quality",
    "model_status",
    "policy_version",
    "evolution_decision",
    "evolution_class",
    "evolution_status",
    "validation_status",
    "self_evolution_level",
]:

    if col in performance.columns:

        performance[col] = (
            performance[col]
            .astype(str)
        )

# ================================================================
# VALIDATION
# ================================================================

print()
print("=" * 70)
print("MODULE 14G VALIDATION")
print("=" * 70)

print()
print(
    f"ROWS: {len(performance)}"
)

print(
    f"COLUMNS: {len(performance.columns)}"
)

null_count = int(
    performance.isnull()
    .sum()
    .sum()
)

print()
print("NULL CHECK:")

if null_count == 0:
    print("NO NULLS")
else:
    print(
        f"NULL VALUES: {null_count}"
    )

# ================================================================
# SELF-EVOLUTION RESULTS
# ================================================================

result_columns = [
    "appliance_name",
    "estimated_savings_percentage",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "adaptation_factor",
    "recommended_learning_rate",
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight",
    "evolution_decision",
    "evolution_class",
    "evolution_status",
    "validation_status",
    "self_evolution_level",
]

# Determine display appliance name
if "appliance_name" in performance.columns:
    display_result = performance[
        [
            c for c in result_columns
            if c in performance.columns
        ]
    ].copy()

elif "appliance" in performance.columns:

    display_result = performance[
        [
            c for c in result_columns
            if c in performance.columns
        ]
    ].copy()

else:

    display_result = performance.copy()

print()
print("DYNAMIC SELF-EVOLUTION RESULTS")
print("-" * 70)

print(
    display_result.to_string(
        index=False
    )
)

# ================================================================
# EVOLUTION RANGES
# ================================================================

print()
print(
    "SELF-ADAPTATION SCORE RANGE:"
)

print(
    f"{performance['self_adaptation_score'].min():.4f}"
    f" to "
    f"{performance['self_adaptation_score'].max():.4f}"
)

print()
print(
    "EVOLUTION EFFECTIVENESS SCORE RANGE:"
)

print(
    f"{performance['evolution_effectiveness_score'].min():.4f}"
    f" to "
    f"{performance['evolution_effectiveness_score'].max():.4f}"
)

# ================================================================
# EVOLUTION DECISIONS
# ================================================================

print()
print("EVOLUTION DECISIONS")
print("-" * 70)

decision_columns = [
    c for c in [
        "appliance_name",
        "evolution_decision",
    ]
    if c in performance.columns
]

print(
    performance[
        decision_columns
    ].to_string(
        index=False
    )
)

# ================================================================
# SAVE MAIN OUTPUT
# ================================================================

performance.to_csv(
    SELF_EVOLUTION_OUTPUT,
    index=False
)

print()
print(
    f"[OK] Self-evolution summary:"
)
print(
    SELF_EVOLUTION_OUTPUT
)

# ================================================================
# EVOLVED POLICY PARAMETERS
# ================================================================

parameter_columns = [
    "house_id",
    "house_name",
]

for col in [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
]:

    if col in performance.columns:
        parameter_columns.append(col)

parameter_columns += [
    "policy_version",
    "previous_generation",
    "evolution_generation",
    "adaptation_factor",
    "recommended_learning_rate",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "maintain_weight",
    "reduce_weight",
    "shift_weight",
    "turn_off_weight",
    "evolved_maintain_weight",
    "evolved_reduce_weight",
    "evolved_shift_weight",
    "evolved_turn_off_weight",
    "evolution_decision",
    "evolution_class",
    "evolution_status",
]

parameter_columns = [
    c for c in parameter_columns
    if c in performance.columns
]

parameters = performance[
    parameter_columns
].copy()

parameters.to_csv(
    EVOLVED_PARAMETERS_OUTPUT,
    index=False
)

print(
    f"[OK] Evolved policy parameters:"
)
print(
    EVOLVED_PARAMETERS_OUTPUT
)

# ================================================================
# EVOLUTION HISTORY
# ================================================================

history_columns = [
    "house_id",
    "house_name",
]

for col in [
    "appliance_id",
    "appliance_name",
]:

    if col in performance.columns:
        history_columns.append(col)

history_columns += [
    "policy_version",
    "previous_generation",
    "evolution_generation",
    "estimated_savings_percentage",
    "policy_confidence",
    "self_adaptation_score",
    "evolution_effectiveness_score",
    "adaptation_factor",
    "recommended_learning_rate",
    "evolution_decision",
    "evolution_class",
    "evolution_status",
    "validation_status",
    "self_evolution_level",
]

history_columns = [
    c for c in history_columns
    if c in performance.columns
]

history = performance[
    history_columns
].copy()

history.insert(
    0,
    "evolution_timestamp",
    pd.Timestamp.now().isoformat()
)

history.to_csv(
    EVOLUTION_HISTORY_OUTPUT,
    index=False
)

print(
    f"[OK] Evolution history:"
)
print(
    EVOLUTION_HISTORY_OUTPUT
)

# ================================================================
# SYSTEM LEVEL SUMMARY
# ================================================================

total_original = float(
    performance[
        "original_energy_kwh"
    ].sum()
)

total_optimized = float(
    performance[
        "optimized_energy_kwh"
    ].sum()
)

total_savings = max(
    0.0,
    total_original -
    total_optimized
)

if total_original > 0:

    overall_savings_pct = (
        total_savings /
        total_original *
        100
    )

else:

    overall_savings_pct = float(
        performance[
            "estimated_savings_percentage"
        ].mean()
    )

average_confidence = float(
    performance[
        "policy_confidence"
    ].mean()
)

average_self_adaptation = float(
    performance[
        "self_adaptation_score"
    ].mean()
)

average_effectiveness = float(
    performance[
        "evolution_effectiveness_score"
    ].mean()
)

average_learning_rate = float(
    performance[
        "recommended_learning_rate"
    ].mean()
)

average_adaptation_factor = float(
    performance[
        "adaptation_factor"
    ].mean()
)

successful_count = int(
    (
        performance[
            "validation_status"
        ]
        ==
        "Successful Evolution"
    )
    .sum()
)

# ================================================================
# OVERALL SYSTEM STATUS
# ================================================================

if (
    successful_count ==
    len(performance)
    and
    average_effectiveness >= 60
):

    overall_status = (
        "ACTIVE_SELF_EVOLUTION"
    )

elif (
    successful_count ==
    len(performance)
    and
    average_effectiveness >= 30
):

    overall_status = (
        "EARLY_SELF_EVOLUTION"
    )

elif successful_count > 0:

    overall_status = (
        "PARTIAL_SELF_EVOLUTION"
    )

else:

    overall_status = (
        "SELF_EVOLUTION_REVIEW_REQUIRED"
    )

# ================================================================
# SYSTEM SUMMARY DATAFRAME
# ================================================================

system_summary = pd.DataFrame([
    {
        "house_id":
            HOUSE_ID,

        "house_name":
            HOUSE_NAME,

        "appliances":
            len(performance),

        "total_original_energy_kwh":
            round(
                total_original,
                6
            ),

        "total_optimized_energy_kwh":
            round(
                total_optimized,
                6
            ),

        "total_estimated_savings_kwh":
            round(
                total_savings,
                6
            ),

        "overall_savings_percentage":
            round(
                overall_savings_pct,
                6
            ),

        "average_policy_confidence":
            round(
                average_confidence,
                6
            ),

        "average_self_adaptation_score":
            round(
                average_self_adaptation,
                6
            ),

        "average_evolution_effectiveness":
            round(
                average_effectiveness,
                6
            ),

        "average_adaptation_factor":
            round(
                average_adaptation_factor,
                6
            ),

        "average_learning_rate":
            round(
                average_learning_rate,
                6
            ),

        "successful_evolutions":
            successful_count,

        "policy_generation":
            2,

        "policy_version":
            "v2.0",

        "system_status":
            overall_status,

        "processing_time_minutes":
            round(
                (
                    time.time()
                    -
                    START_TIME
                )
                / 60,
                4
            ),
    }
])

system_summary.to_csv(
    SYSTEM_SUMMARY_OUTPUT,
    index=False
)

# ================================================================
# FINAL SYSTEM SUMMARY
# ================================================================

print()
print("=" * 70)
print("SYSTEM SELF-EVOLUTION SUMMARY")
print("=" * 70)

print(
    f"House ID                  : {HOUSE_ID}"
)

print(
    f"House Name                : {HOUSE_NAME}"
)

print(
    f"Appliances                : {len(performance)}"
)

print(
    f"Original energy           : "
    f"{total_original:.6f} kWh"
)

print(
    f"Optimized energy          : "
    f"{total_optimized:.6f} kWh"
)

print(
    f"Estimated savings         : "
    f"{total_savings:.6f} kWh"
)

print(
    f"Savings percentage        : "
    f"{overall_savings_pct:.4f}%"
)

print(
    f"Average policy confidence : "
    f"{average_confidence:.4f}%"
)

print(
    f"Average self-adaptation   : "
    f"{average_self_adaptation:.4f}"
)

print(
    f"Average effectiveness     : "
    f"{average_effectiveness:.4f}"
)

print(
    f"Average adaptation factor : "
    f"{average_adaptation_factor:.4f}"
)

print(
    f"Average learning rate     : "
    f"{average_learning_rate:.6f}"
)

print(
    f"Successful evolutions     : "
    f"{successful_count}/{len(performance)}"
)

print(
    f"Policy version            : v2.0"
)

print(
    f"System status             : "
    f"{overall_status}"
)

# ================================================================
# FINAL VALIDATION
# ================================================================

print()
print("=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

final_nulls = int(
    performance.isnull()
    .sum()
    .sum()
)

duplicate_count = int(
    performance.columns.duplicated()
    .sum()
)

print(
    f"Rows             : {len(performance)}"
)

print(
    f"Columns          : {len(performance.columns)}"
)

print(
    f"Final NULLs      : {final_nulls}"
)

print(
    f"Duplicate columns: {duplicate_count}"
)

if final_nulls == 0:
    print(
        "[OK] No NULL values"
    )
else:
    print(
        "[WARNING] NULL values detected"
    )

if duplicate_count == 0:
    print(
        "[OK] No duplicate columns"
    )
else:
    print(
        "[WARNING] Duplicate columns detected"
    )

# ================================================================
# COMPLETION
# ================================================================

elapsed = (
    time.time()
    -
    START_TIME
)

print()
print("=" * 70)
print("MODULE 14G COMPLETE")
print("=" * 70)

print()
print(
    f"House ID            : {HOUSE_ID}"
)

print(
    f"House Name          : {HOUSE_NAME}"
)

print(
    f"Appliances          : {len(performance)}"
)

print(
    f"Policy version      : v2.0"
)

print(
    f"Successful evolution: "
    f"{successful_count}/{len(performance)}"
)

print(
    f"Average savings     : "
    f"{overall_savings_pct:.4f}%"
)

print(
    f"Average confidence  : "
    f"{average_confidence:.4f}%"
)

print(
    f"Self-adaptation     : "
    f"{average_self_adaptation:.4f}"
)

print(
    f"Evolution effective : "
    f"{average_effectiveness:.4f}"
)

print(
    f"System status       : "
    f"{overall_status}"
)

print()
print("OUTPUT FILES")
print("-" * 70)

print(
    f"Self-evolution summary:"
)
print(
    SELF_EVOLUTION_OUTPUT
)

print()
print(
    f"Evolved policy parameters:"
)
print(
    EVOLVED_PARAMETERS_OUTPUT
)

print()
print(
    f"Evolution history:"
)
print(
    EVOLUTION_HISTORY_OUTPUT
)

print()
print(
    f"System summary:"
)
print(
    SYSTEM_SUMMARY_OUTPUT
)

print()
print(
    f"Total time: {elapsed / 60:.2f} minutes"
)

print("=" * 70)