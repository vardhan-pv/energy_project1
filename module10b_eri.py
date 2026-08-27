import pandas as pd
import numpy as np
import os
import time

# ============================================================
# MODULE 10B — ENERGY ROUTINE INDEX (ERI)
# ============================================================

BASE_DIR = r"E:\energy_project\behavior_output"

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "energy_routine_index.csv"
)

APPLIANCES = [
    "fridge",
    "kitchen_lights",
    "laptop",
    "office_fan"
]

print("=" * 70)
print("MODULE 10B — ENERGY ROUTINE INDEX")
print("=" * 70)

start_time = time.time()


# ============================================================
# Helper function
# ============================================================

def consistency_score(values):
    """
    Converts coefficient of variation into a 0–100
    consistency score.

    Lower variation = higher consistency.
    """

    values = pd.Series(values).dropna()

    if len(values) == 0:
        return 0.0

    mean_value = values.mean()

    if mean_value == 0:
        return 100.0

    std_value = values.std()

    cv = std_value / abs(mean_value)

    # Convert variation to consistency.
    score = 100 / (1 + cv)

    return float(np.clip(score, 0, 100))


# ============================================================
# Process appliances
# ============================================================

results = []

for appliance in APPLIANCES:

    print("\n" + "=" * 70)
    print(f"Processing ERI: {appliance}")
    print("=" * 70)

    hourly_file = os.path.join(
        BASE_DIR,
        f"{appliance}_ATF_hourly.csv"
    )

    weekly_file = os.path.join(
        BASE_DIR,
        f"{appliance}_ATF_weekly.csv"
    )

    weekend_file = os.path.join(
        BASE_DIR,
        f"{appliance}_ATF_weekend.csv"
    )

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    for file in [hourly_file, weekly_file, weekend_file]:

        if not os.path.exists(file):
            raise FileNotFoundError(
                f"Required ATF file not found:\n{file}"
            )

    # --------------------------------------------------------
    # Read ATF files
    # --------------------------------------------------------

    hourly = pd.read_csv(hourly_file)
    weekly = pd.read_csv(weekly_file)
    weekend = pd.read_csv(weekend_file)

    # ========================================================
    # 1. HOURLY POWER CONSISTENCY
    # ========================================================

    hourly_power_consistency = consistency_score(
        hourly["avg_power_w"]
    )

    # ========================================================
    # 2. HOURLY ENERGY CONSISTENCY
    # ========================================================

    hourly_energy_consistency = consistency_score(
        hourly["avg_energy_kwh"]
    )

    # ========================================================
    # 3. HOURLY ON/OFF CONSISTENCY
    # ========================================================

    hourly_on_consistency = consistency_score(
        hourly["on_percentage"]
    )

    # ========================================================
    # 4. WEEKLY CONSISTENCY
    # ========================================================

    weekly_power_consistency = consistency_score(
        weekly["avg_power_w"]
    )

    weekly_on_consistency = consistency_score(
        weekly["on_percentage"]
    )

    # ========================================================
    # 5. WEEKDAY / WEEKEND CONSISTENCY
    # ========================================================

    weekday = weekend[
        weekend["is_weekend"] == 0
    ]

    weekend_data = weekend[
        weekend["is_weekend"] == 1
    ]

    if len(weekday) > 0 and len(weekend_data) > 0:

        weekday_power = weekday["avg_power_w"].mean()
        weekend_power = weekend_data["avg_power_w"].mean()

        denominator = max(
            abs(weekday_power),
            abs(weekend_power),
            1e-9
        )

        weekday_weekend_difference = (
            abs(weekday_power - weekend_power)
            / denominator
        )

        weekday_weekend_consistency = (
            100 / (1 + weekday_weekend_difference)
        )

    else:

        weekday_weekend_consistency = 100.0

    # ========================================================
    # 6. TEMPORAL RANGE
    # ========================================================

    active_hours = (
        hourly["on_percentage"] > 0
    ).sum()

    total_hours = len(hourly)

    if total_hours > 0:

        temporal_coverage = (
            active_hours / total_hours * 100
        )

    else:

        temporal_coverage = 0

    # ========================================================
    # FINAL ERI
    # ========================================================

    eri = (
        hourly_power_consistency * 0.25
        + hourly_energy_consistency * 0.15
        + hourly_on_consistency * 0.15
        + weekly_power_consistency * 0.15
        + weekly_on_consistency * 0.10
        + weekday_weekend_consistency * 0.10
        + temporal_coverage * 0.10
    )

    eri = float(np.clip(eri, 0, 100))

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    if eri >= 80:
        routine_class = "Highly Regular"

    elif eri >= 60:
        routine_class = "Regular"

    elif eri >= 40:
        routine_class = "Moderately Variable"

    elif eri >= 20:
        routine_class = "Variable"

    else:
        routine_class = "Highly Variable"

    # ========================================================
    # SAVE RESULT
    # ========================================================

    results.append({
        "appliance": appliance,
        "hourly_power_consistency": round(
            hourly_power_consistency, 4
        ),
        "hourly_energy_consistency": round(
            hourly_energy_consistency, 4
        ),
        "hourly_on_consistency": round(
            hourly_on_consistency, 4
        ),
        "weekly_power_consistency": round(
            weekly_power_consistency, 4
        ),
        "weekly_on_consistency": round(
            weekly_on_consistency, 4
        ),
        "weekday_weekend_consistency": round(
            weekday_weekend_consistency, 4
        ),
        "temporal_coverage": round(
            temporal_coverage, 4
        ),
        "energy_routine_index": round(
            eri, 4
        ),
        "routine_class": routine_class
    })

    print(
        f"ERI: {eri:.4f}"
    )

    print(
        f"Routine class: {routine_class}"
    )


# ============================================================
# CREATE FINAL ERI TABLE
# ============================================================

eri_df = pd.DataFrame(results)

eri_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# ============================================================
# COMPLETE
# ============================================================

elapsed = (time.time() - start_time) / 60

print("\n" + "=" * 70)
print("MODULE 10B COMPLETE")
print("=" * 70)

print("\nEnergy Routine Index:")
print(
    eri_df[
        [
            "appliance",
            "energy_routine_index",
            "routine_class"
        ]
    ].to_string(index=False)
)

print("\nOutput:")
print(OUTPUT_FILE)

print(f"\nTime taken: {elapsed:.2f} minutes")

print("=" * 70)