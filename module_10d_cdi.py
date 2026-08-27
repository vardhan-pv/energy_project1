import pandas as pd
import numpy as np
import glob
import os
import time

# ============================================================
# MODULE 10D — CDI
# Comfort / Device Interaction
# ============================================================

BASE_DIR = r"E:\energy_project"
FEATURE_DIR = os.path.join(BASE_DIR, "feature_output")
OUTPUT_DIR = os.path.join(BASE_DIR, "behavior_output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = {
    "fridge": os.path.join(FEATURE_DIR, "fridge_features.csv"),
    "kitchen_lights": os.path.join(FEATURE_DIR, "kitchen_lights_features.csv"),
    "laptop": os.path.join(FEATURE_DIR, "laptop_features.csv"),
    "office_fan": os.path.join(FEATURE_DIR, "office_fan_features.csv"),
}

CHUNK_SIZE = 100_000

print("=" * 70)
print("MODULE 10D — CDI")
print("COMFORT / DEVICE INTERACTION")
print("=" * 70)

results = []

for appliance, filepath in FILES.items():

    start_time = time.time()

    print()
    print("=" * 70)
    print("Processing:", appliance)
    print("=" * 70)

    if not os.path.exists(filepath):
        print("ERROR: File not found:")
        print(filepath)
        continue

    # --------------------------------------------------------
    # Accumulators
    # --------------------------------------------------------

    total_rows = 0
    on_rows = 0

    power_sum = 0.0
    power_sq_sum = 0.0

    hourly_power = {}
    hourly_on = {}

    weekday_power = {}
    weekend_power = {}

    status_changes = 0

    previous_status = None

    # Power/time interaction statistics
    active_hour_power = {}
    active_hour_count = {}

    # --------------------------------------------------------
    # Read feature data
    # --------------------------------------------------------

    reader = pd.read_csv(
        filepath,
        usecols=[
            "timestamp",
            "power_w",
            "status",
            "hour",
            "day_of_week",
            "is_weekend"
        ],
        chunksize=CHUNK_SIZE
    )

    for chunk_no, df in enumerate(reader, start=1):

        total_rows += len(df)

        power = pd.to_numeric(df["power_w"], errors="coerce").fillna(0)
        status = pd.to_numeric(df["status"], errors="coerce").fillna(0).astype(int)

        hours = pd.to_numeric(df["hour"], errors="coerce").fillna(0).astype(int)
        weekend = pd.to_numeric(
            df["is_weekend"],
            errors="coerce"
        ).fillna(0).astype(int)

        # ----------------------------------------------------
        # Basic interaction
        # ----------------------------------------------------

        on_mask = status == 1

        on_rows += int(on_mask.sum())

        power_sum += float(power.sum())
        power_sq_sum += float((power ** 2).sum())

        # ----------------------------------------------------
        # Hourly behavior
        # ----------------------------------------------------

        for h, p, s in zip(hours, power, status):

            if h not in hourly_power:
                hourly_power[h] = []
                hourly_on[h] = []

            hourly_power[h].append(float(p))
            hourly_on[h].append(int(s))

            if s == 1:
                if h not in active_hour_power:
                    active_hour_power[h] = 0.0
                    active_hour_count[h] = 0

                active_hour_power[h] += float(p)
                active_hour_count[h] += 1

        # ----------------------------------------------------
        # Weekday / weekend behavior
        # ----------------------------------------------------

        weekday_mask = weekend == 0
        weekend_mask = weekend == 1

        if weekday_mask.any():
            weekday_power.setdefault("values", [])
            weekday_power["values"].extend(
                power[weekday_mask].tolist()
            )

        if weekend_mask.any():
            weekend_power.setdefault("values", [])
            weekend_power["values"].extend(
                power[weekend_mask].tolist()
            )

        # ----------------------------------------------------
        # Status transitions
        # ----------------------------------------------------

        status_values = status.to_numpy()

        if len(status_values) > 0:

            if previous_status is not None:
                if previous_status != status_values[0]:
                    status_changes += 1

            status_changes += int(
                np.sum(status_values[1:] != status_values[:-1])
            )

            previous_status = status_values[-1]

        if chunk_no % 20 == 0:
            elapsed = (time.time() - start_time) / 60

            print(
                f"Chunk {chunk_no}: "
                f"{total_rows:,} rows | "
                f"Elapsed: {elapsed:.2f} minutes"
            )

    # ========================================================
    # Calculate CDI metrics
    # ========================================================

    overall_mean_power = power_sum / total_rows if total_rows else 0

    variance = (
        power_sq_sum / total_rows
        - overall_mean_power ** 2
    )

    variance = max(variance, 0)

    overall_std_power = np.sqrt(variance)

    on_percentage = (
        on_rows / total_rows * 100
        if total_rows else 0
    )

    # --------------------------------------------------------
    # Hourly interaction
    # --------------------------------------------------------

    hourly_means = {}

    for h in hourly_power:
        if hourly_power[h]:
            hourly_means[h] = np.mean(hourly_power[h])

    if hourly_means:
        peak_hour = max(
            hourly_means,
            key=hourly_means.get
        )

        peak_hour_power = hourly_means[peak_hour]
    else:
        peak_hour = 0
        peak_hour_power = 0

    # --------------------------------------------------------
    # Active-hour interaction
    # --------------------------------------------------------

    active_hour_means = {}

    for h in active_hour_power:

        if active_hour_count[h] > 0:
            active_hour_means[h] = (
                active_hour_power[h]
                / active_hour_count[h]
            )

    if active_hour_means:

        most_active_hour = max(
            active_hour_means,
            key=active_hour_means.get
        )

        most_active_hour_power = active_hour_means[
            most_active_hour
        ]

    else:

        most_active_hour = 0
        most_active_hour_power = 0

    # --------------------------------------------------------
    # Weekday / weekend interaction
    # --------------------------------------------------------

    weekday_values = weekday_power.get("values", [])
    weekend_values = weekend_power.get("values", [])

    weekday_mean = (
        np.mean(weekday_values)
        if weekday_values else 0
    )

    weekend_mean = (
        np.mean(weekend_values)
        if weekend_values else 0
    )

    if weekday_mean != 0:
        weekend_weekday_change = (
            abs(weekend_mean - weekday_mean)
            / weekday_mean
            * 100
        )
    else:
        weekend_weekday_change = 0

    # --------------------------------------------------------
    # Temporal interaction score
    # --------------------------------------------------------

    if overall_mean_power > 0:

        peak_ratio = (
            peak_hour_power
            / overall_mean_power
        )

    else:

        peak_ratio = 0

    peak_ratio = min(peak_ratio, 10)

    # --------------------------------------------------------
    # Stability component
    # --------------------------------------------------------

    if overall_mean_power > 0:

        cv = (
            overall_std_power
            / overall_mean_power
        )

    else:

        cv = 0

    # --------------------------------------------------------
    # Interaction intensity
    # --------------------------------------------------------

    interaction_intensity = (
        on_percentage
        * peak_ratio
        / 100
    )

    # --------------------------------------------------------
    # Weekend behavior component
    # --------------------------------------------------------

    weekend_component = min(
        weekend_weekday_change,
        100
    )

    # --------------------------------------------------------
    # CDI score
    #
    # Higher score = stronger / more structured
    # device interaction pattern.
    # --------------------------------------------------------

    temporal_component = min(
        peak_ratio * 10,
        100
    )

    activity_component = min(
        on_percentage,
        100
    )

    stability_component = max(
        0,
        100 - min(cv * 20, 100)
    )

    interaction_component = min(
        interaction_intensity * 10,
        100
    )

    cdi_score = (
        temporal_component * 0.25
        + activity_component * 0.25
        + stability_component * 0.20
        + interaction_component * 0.20
        + weekend_component * 0.10
    )

    cdi_score = max(
        0,
        min(100, cdi_score)
    )

    # --------------------------------------------------------
    # CDI class
    # --------------------------------------------------------

    if cdi_score >= 75:
        interaction_class = "Strong Interaction"

    elif cdi_score >= 50:
        interaction_class = "Moderate Interaction"

    elif cdi_score >= 25:
        interaction_class = "Weak Interaction"

    else:
        interaction_class = "Low Interaction"

    # ========================================================
    # Result
    # ========================================================

    results.append({
        "appliance": appliance,
        "total_rows": total_rows,
        "avg_power_w": overall_mean_power,
        "std_power_w": overall_std_power,
        "on_percentage": on_percentage,
        "peak_hour": peak_hour,
        "peak_hour_power_w": peak_hour_power,
        "most_active_hour": most_active_hour,
        "most_active_hour_power_w": most_active_hour_power,
        "weekday_mean_power_w": weekday_mean,
        "weekend_mean_power_w": weekend_mean,
        "weekend_weekday_change_pct": weekend_weekday_change,
        "status_change_count": status_changes,
        "coefficient_variation": cv,
        "peak_to_average_ratio": peak_ratio,
        "interaction_intensity": interaction_intensity,
        "temporal_interaction_score": temporal_component,
        "activity_score": activity_component,
        "stability_component": stability_component,
        "interaction_component": interaction_component,
        "weekend_component": weekend_component,
        "cdi_score": cdi_score,
        "interaction_class": interaction_class
    })

    elapsed = (time.time() - start_time) / 60

    print()
    print("-" * 70)
    print("CDI COMPLETE:", appliance)
    print("Rows:", f"{total_rows:,}")
    print("ON percentage:", f"{on_percentage:.4f}%")
    print("Peak hour:", peak_hour)
    print("CDI score:", f"{cdi_score:.4f}")
    print("Class:", interaction_class)
    print("Time:", f"{elapsed:.2f} minutes")
    print("-" * 70)


# ============================================================
# SAVE RESULTS
# ============================================================

result_df = pd.DataFrame(results)

output_file = os.path.join(
    OUTPUT_DIR,
    "cdi_summary.csv"
)

result_df.to_csv(
    output_file,
    index=False
)

print()
print("=" * 70)
print("MODULE 10D COMPLETE")
print("=" * 70)

print(result_df.to_string(index=False))

print()
print("NULLS:")
print(result_df.isna().sum())

print()
print(
    "CDI RANGE:",
    f"{result_df.cdi_score.min():.4f}",
    "to",
    f"{result_df.cdi_score.max():.4f}"
)

print()
print("CLASSES:")
print(
    result_df[
        ["appliance", "cdi_score", "interaction_class"]
    ].to_string(index=False)
)

print()
print("Output:")
print(output_file)

print("=" * 70)