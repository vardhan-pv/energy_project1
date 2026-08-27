import pandas as pd
import os
import glob
import time

# ============================================================
# MODULE 10A — APPLIANCE TEMPORAL FINGERPRINT (ATF)
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

print("=" * 70)
print("MODULE 10A — APPLIANCE TEMPORAL FINGERPRINT")
print("=" * 70)

start_all = time.time()

results = []

for filename in FILES:

    filepath = os.path.join(INPUT_DIR, filename)

    if not os.path.exists(filepath):
        print(f"\nWARNING: File not found: {filepath}")
        continue

    appliance = filename.replace("_features.csv", "")

    print("\n" + "=" * 70)
    print(f"Processing: {appliance}")
    print("=" * 70)

    start = time.time()

    # --------------------------------------------------------
    # Read only required columns
    # --------------------------------------------------------

    columns = [
        "timestamp",
        "appliance",
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend"
    ]

    df = pd.read_csv(
        filepath,
        usecols=columns
    )

    print(f"Rows loaded: {len(df):,}")

    # --------------------------------------------------------
    # Ensure timestamp is datetime
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Hourly temporal fingerprint
    # --------------------------------------------------------

    hourly = (
        df.groupby("hour")
        .agg(
            avg_power_w=("power_w", "mean"),
            max_power_w=("power_w", "max"),
            min_power_w=("power_w", "min"),
            power_std_w=("power_w", "std"),
            avg_energy_kwh=("energy_kwh", "mean"),
            on_count=("status", lambda x: (x == 1).sum()),
            total_count=("status", "count")
        )
        .reset_index()
    )

    hourly["on_percentage"] = (
        hourly["on_count"] /
        hourly["total_count"] * 100
    )

    hourly["appliance"] = appliance

    # --------------------------------------------------------
    # Weekday / Weekend behavior
    # --------------------------------------------------------

    day_pattern = (
        df.groupby(["is_weekend", "hour"])
        .agg(
            avg_power_w=("power_w", "mean"),
            max_power_w=("power_w", "max"),
            power_std_w=("power_w", "std"),
            on_percentage=("status", lambda x: (x == 1).mean() * 100)
        )
        .reset_index()
    )

    day_pattern["appliance"] = appliance

    # --------------------------------------------------------
    # Day-of-week fingerprint
    # --------------------------------------------------------

    weekly = (
        df.groupby("day_of_week")
        .agg(
            avg_power_w=("power_w", "mean"),
            max_power_w=("power_w", "max"),
            power_std_w=("power_w", "std"),
            avg_energy_kwh=("energy_kwh", "mean"),
            on_percentage=("status", lambda x: (x == 1).mean() * 100)
        )
        .reset_index()
    )

    weekly["appliance"] = appliance

    # --------------------------------------------------------
    # Overall appliance fingerprint
    # --------------------------------------------------------

    overall = {
        "appliance": appliance,
        "total_rows": len(df),
        "avg_power_w": df["power_w"].mean(),
        "max_power_w": df["power_w"].max(),
        "min_power_w": df["power_w"].min(),
        "power_std_w": df["power_w"].std(),
        "avg_energy_kwh": df["energy_kwh"].mean(),
        "total_energy_kwh": df["energy_kwh"].sum(),
        "on_percentage": (df["status"] == 1).mean() * 100,
        "unique_hours": df["hour"].nunique(),
        "unique_days_of_week": df["day_of_week"].nunique(),
        "weekend_on_percentage": (
            df.loc[df["is_weekend"] == 1, "status"].eq(1).mean() * 100
            if (df["is_weekend"] == 1).any()
            else 0
        ),
        "weekday_on_percentage": (
            df.loc[df["is_weekend"] == 0, "status"].eq(1).mean() * 100
            if (df["is_weekend"] == 0).any()
            else 0
        )
    }

    results.append(overall)

    # --------------------------------------------------------
    # Save hourly fingerprint
    # --------------------------------------------------------

    hourly_file = os.path.join(
        OUTPUT_DIR,
        f"{appliance}_ATF_hourly.csv"
    )

    hourly = hourly[
        [
            "appliance",
            "hour",
            "avg_power_w",
            "max_power_w",
            "min_power_w",
            "power_std_w",
            "avg_energy_kwh",
            "on_count",
            "total_count",
            "on_percentage"
        ]
    ]

    hourly.to_csv(
        hourly_file,
        index=False
    )

    # --------------------------------------------------------
    # Save weekday/weekend fingerprint
    # --------------------------------------------------------

    day_file = os.path.join(
        OUTPUT_DIR,
        f"{appliance}_ATF_weekend.csv"
    )

    day_pattern = day_pattern[
        [
            "appliance",
            "is_weekend",
            "hour",
            "avg_power_w",
            "max_power_w",
            "power_std_w",
            "on_percentage"
        ]
    ]

    day_pattern.to_csv(
        day_file,
        index=False
    )

    # --------------------------------------------------------
    # Save weekly fingerprint
    # --------------------------------------------------------

    weekly_file = os.path.join(
        OUTPUT_DIR,
        f"{appliance}_ATF_weekly.csv"
    )

    weekly = weekly[
        [
            "appliance",
            "day_of_week",
            "avg_power_w",
            "max_power_w",
            "power_std_w",
            "avg_energy_kwh",
            "on_percentage"
        ]
    ]

    weekly.to_csv(
        weekly_file,
        index=False
    )

    elapsed = (time.time() - start) / 60

    print(f"Hourly fingerprint : {hourly_file}")
    print(f"Weekend fingerprint: {day_file}")
    print(f"Weekly fingerprint : {weekly_file}")
    print(f"Time taken: {elapsed:.2f} minutes")


# ============================================================
# SAVE OVERALL ATF
# ============================================================

overall_file = os.path.join(
    OUTPUT_DIR,
    "appliance_temporal_fingerprint.csv"
)

overall_df = pd.DataFrame(results)

overall_df.to_csv(
    overall_file,
    index=False
)

print("\n" + "=" * 70)
print("MODULE 10A COMPLETE")
print("=" * 70)

print("\nOverall ATF:")
print(
    overall_df[
        [
            "appliance",
            "total_rows",
            "avg_power_w",
            "max_power_w",
            "power_std_w",
            "total_energy_kwh",
            "on_percentage"
        ]
    ].to_string(index=False)
)

print("\nOutput directory:")
print(OUTPUT_DIR)

print(f"\nTotal time: {(time.time() - start_all) / 60:.2f} minutes")

print("=" * 70)