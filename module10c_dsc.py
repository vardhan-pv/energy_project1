import pandas as pd
import numpy as np
import os
import time

# ============================================================
# MODULE 10C — DEMAND STABILITY / CHANGE (DSC)
# ============================================================

INPUT_DIR = r"E:\energy_project\feature_output"
OUTPUT_DIR = r"E:\energy_project\behavior_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = [
    "fridge_features.csv",
    "kitchen_lights_features.csv",
    "laptop_features.csv",
    "office_fan_features.csv"
]

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "demand_stability_change.csv"
)

print("=" * 70)
print("MODULE 10C — DEMAND STABILITY / CHANGE")
print("=" * 70)

start_all = time.time()

results = []


# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

for filename in FILES:

    filepath = os.path.join(INPUT_DIR, filename)

    if not os.path.exists(filepath):
        print(f"\nWARNING: File not found: {filepath}")
        continue

    appliance = filename.replace("_features.csv", "")

    print("\n" + "=" * 70)
    print(f"Processing DSC: {appliance}")
    print("=" * 70)

    start = time.time()

    # --------------------------------------------------------
    # Read only required columns
    # --------------------------------------------------------

    columns = [
        "power_w",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max",
        "status",
        "hour",
        "day_of_week",
        "is_weekend"
    ]

    df = pd.read_csv(
        filepath,
        usecols=columns
    )

    print(f"Rows loaded: {len(df):,}")

    # ========================================================
    # 1. BASIC DEMAND STATISTICS
    # ========================================================

    avg_power = df["power_w"].mean()
    std_power = df["power_w"].std()
    max_power = df["power_w"].max()
    min_power = df["power_w"].min()

    # ========================================================
    # 2. COEFFICIENT OF VARIATION
    # ========================================================

    if avg_power != 0:

        coefficient_variation = (
            std_power / abs(avg_power)
        )

    else:

        coefficient_variation = 0.0

    # ========================================================
    # 3. LAG-1 POWER CHANGE
    # ========================================================

    lag1_valid = df[
        df["power_lag_1"].notna()
    ].copy()

    if len(lag1_valid) > 0:

        absolute_change_1 = (
            lag1_valid["power_w"]
            - lag1_valid["power_lag_1"]
        ).abs()

        mean_change_1 = absolute_change_1.mean()

        max_change_1 = absolute_change_1.max()

        median_change_1 = absolute_change_1.median()

    else:

        mean_change_1 = 0.0
        max_change_1 = 0.0
        median_change_1 = 0.0

    # ========================================================
    # 4. LAG-5 POWER CHANGE
    # ========================================================

    lag5_valid = df[
        df["power_lag_5"].notna()
    ].copy()

    if len(lag5_valid) > 0:

        absolute_change_5 = (
            lag5_valid["power_w"]
            - lag5_valid["power_lag_5"]
        ).abs()

        mean_change_5 = absolute_change_5.mean()

        max_change_5 = absolute_change_5.max()

        median_change_5 = absolute_change_5.median()

    else:

        mean_change_5 = 0.0
        max_change_5 = 0.0
        median_change_5 = 0.0

    # ========================================================
    # 5. ROLLING MEAN DEVIATION
    # ========================================================

    rolling_valid = df[
        df["power_rolling_mean"].notna()
    ].copy()

    if len(rolling_valid) > 0:

        rolling_deviation = (
            rolling_valid["power_w"]
            - rolling_valid["power_rolling_mean"]
        ).abs()

        mean_rolling_deviation = (
            rolling_deviation.mean()
        )

        max_rolling_deviation = (
            rolling_deviation.max()
        )

    else:

        mean_rolling_deviation = 0.0
        max_rolling_deviation = 0.0

    # ========================================================
    # 6. ROLLING MAX GAP
    # ========================================================

    rolling_max_valid = df[
        df["power_rolling_max"].notna()
    ].copy()

    if len(rolling_max_valid) > 0:

        rolling_max_gap = (
            rolling_max_valid["power_rolling_max"]
            - rolling_max_valid["power_w"]
        ).abs()

        mean_rolling_max_gap = (
            rolling_max_gap.mean()
        )

    else:

        mean_rolling_max_gap = 0.0

    # ========================================================
    # 7. HIGH-CHANGE EVENTS
    # ========================================================

    if len(lag1_valid) > 0:

        change_threshold = (
            lag1_valid["power_w"]
            .quantile(0.95)
        )

        high_change_events = (
            absolute_change_1 > change_threshold
        ).sum()

        high_change_percentage = (
            high_change_events
            / len(lag1_valid)
            * 100
        )

    else:

        change_threshold = 0.0
        high_change_events = 0
        high_change_percentage = 0.0

    # ========================================================
    # 8. STATUS TRANSITIONS
    # ========================================================

    status_change_count = (
        df["status"]
        .ne(df["status"].shift())
        .sum()
        - 1
    )

    if len(df) > 1:

        status_change_rate = (
            status_change_count
            / (len(df) - 1)
            * 100
        )

    else:

        status_change_rate = 0.0

    # ========================================================
    # 9. HOURLY STABILITY
    # ========================================================

    hourly_stats = (
        df.groupby("hour")["power_w"]
        .agg(["mean", "std"])
        .reset_index()
    )

    hourly_stats["std"] = (
        hourly_stats["std"].fillna(0)
    )

    hourly_mean = hourly_stats["mean"].mean()

    hourly_std = hourly_stats["std"].mean()

    if hourly_mean != 0:

        hourly_cv = (
            hourly_std / abs(hourly_mean)
        )

    else:

        hourly_cv = 0.0

    # ========================================================
    # 10. WEEKLY STABILITY
    # ========================================================

    weekly_stats = (
        df.groupby("day_of_week")["power_w"]
        .agg(["mean", "std"])
        .reset_index()
    )

    weekly_stats["std"] = (
        weekly_stats["std"].fillna(0)
    )

    weekly_mean = weekly_stats["mean"].mean()

    weekly_std = weekly_stats["std"].mean()

    if weekly_mean != 0:

        weekly_cv = (
            weekly_std / abs(weekly_mean)
        )

    else:

        weekly_cv = 0.0

    # ========================================================
    # 11. WEEKEND VS WEEKDAY CHANGE
    # ========================================================

    weekday_power = df.loc[
        df["is_weekend"] == 0,
        "power_w"
    ]

    weekend_power = df.loc[
        df["is_weekend"] == 1,
        "power_w"
    ]

    if (
        len(weekday_power) > 0
        and len(weekend_power) > 0
    ):

        weekday_mean = weekday_power.mean()
        weekend_mean = weekend_power.mean()

        baseline = max(
            abs(weekday_mean),
            abs(weekend_mean),
            1e-9
        )

        weekend_weekday_change = (
            abs(weekend_mean - weekday_mean)
            / baseline
            * 100
        )

    else:

        weekday_mean = 0.0
        weekend_mean = 0.0
        weekend_weekday_change = 0.0

    # ========================================================
    # 12. NORMALIZED CHANGE INDEX
    # ========================================================

    if avg_power != 0:

        normalized_change = (
            mean_change_1
            / abs(avg_power)
        )

    else:

        normalized_change = 0.0

    # ========================================================
    # 13. STABILITY SCORE
    # ========================================================

    # Higher score = more stable demand.
    stability_score = (
        100
        / (
            1
            + coefficient_variation
        )
    )

    stability_score = float(
        np.clip(
            stability_score,
            0,
            100
        )
    )

    # ========================================================
    # 14. CHANGE SCORE
    # ========================================================

    # Higher score = more demand change.
    change_score = (
        (
            normalized_change
            + coefficient_variation
            + status_change_rate / 100
        )
        / 3
    )

    change_score = float(
        np.clip(
            change_score * 100,
            0,
            100
        )
    )

    # ========================================================
    # 15. OVERALL DSC SCORE
    # ========================================================

    # DSC represents both stability and change.

    dsc_score = (
        stability_score * 0.60
        + (100 - change_score) * 0.40
    )

    dsc_score = float(
        np.clip(
            dsc_score,
            0,
            100
        )
    )

    # ========================================================
    # 16. DEMAND BEHAVIOR CLASS
    # ========================================================

    if dsc_score >= 80:

        demand_class = "Highly Stable"

    elif dsc_score >= 60:

        demand_class = "Stable"

    elif dsc_score >= 40:

        demand_class = "Moderately Variable"

    elif dsc_score >= 20:

        demand_class = "Variable"

    else:

        demand_class = "Highly Variable"

    # ========================================================
    # SAVE RESULT
    # ========================================================

    results.append({

        "appliance": appliance,

        "total_rows": len(df),

        "avg_power_w": round(
            avg_power,
            6
        ),

        "std_power_w": round(
            std_power,
            6
        ),

        "min_power_w": round(
            min_power,
            6
        ),

        "max_power_w": round(
            max_power,
            6
        ),

        "coefficient_variation": round(
            coefficient_variation,
            6
        ),

        "mean_change_lag1_w": round(
            mean_change_1,
            6
        ),

        "median_change_lag1_w": round(
            median_change_1,
            6
        ),

        "max_change_lag1_w": round(
            max_change_1,
            6
        ),

        "mean_change_lag5_w": round(
            mean_change_5,
            6
        ),

        "median_change_lag5_w": round(
            median_change_5,
            6
        ),

        "max_change_lag5_w": round(
            max_change_5,
            6
        ),

        "mean_rolling_deviation_w": round(
            mean_rolling_deviation,
            6
        ),

        "max_rolling_deviation_w": round(
            max_rolling_deviation,
            6
        ),

        "mean_rolling_max_gap_w": round(
            mean_rolling_max_gap,
            6
        ),

        "high_change_events": int(
            high_change_events
        ),

        "high_change_percentage": round(
            high_change_percentage,
            6
        ),

        "status_change_count": int(
            status_change_count
        ),

        "status_change_rate": round(
            status_change_rate,
            6
        ),

        "hourly_cv": round(
            hourly_cv,
            6
        ),

        "weekly_cv": round(
            weekly_cv,
            6
        ),

        "weekday_mean_power_w": round(
            weekday_mean,
            6
        ),

        "weekend_mean_power_w": round(
            weekend_mean,
            6
        ),

        "weekend_weekday_change_pct": round(
            weekend_weekday_change,
            6
        ),

        "normalized_change": round(
            normalized_change,
            6
        ),

        "stability_score": round(
            stability_score,
            6
        ),

        "change_score": round(
            change_score,
            6
        ),

        "dsc_score": round(
            dsc_score,
            6
        ),

        "demand_class": demand_class
    })

    elapsed = (
        time.time() - start
    ) / 60

    print(
        f"DSC score: {dsc_score:.4f}"
    )

    print(
        f"Stability score: {stability_score:.4f}"
    )

    print(
        f"Change score: {change_score:.4f}"
    )

    print(
        f"Demand class: {demand_class}"
    )

    print(
        f"Time taken: {elapsed:.2f} minutes"
    )


# ============================================================
# SAVE FINAL DSC
# ============================================================

dsc_df = pd.DataFrame(results)

dsc_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# COMPLETE
# ============================================================

elapsed_all = (
    time.time() - start_all
) / 60

print("\n" + "=" * 70)
print("MODULE 10C COMPLETE")
print("=" * 70)

print("\nDemand Stability / Change:")
print(
    dsc_df[
        [
            "appliance",
            "stability_score",
            "change_score",
            "dsc_score",
            "demand_class"
        ]
    ].to_string(index=False)
)

print("\nOutput:")
print(OUTPUT_FILE)

print(
    f"\nTotal time: {elapsed_all:.2f} minutes"
)

print("=" * 70)