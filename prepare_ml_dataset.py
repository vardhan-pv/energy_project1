import pandas as pd
import os
import glob
import time

# ============================================================
# ML DATASET PREPARATION
# Intelligent Energy Optimization Project
# ============================================================

INPUT_DIR = r"E:\energy_project\feature_output"
OUTPUT_DIR = r"E:\energy_project\ml_data"

os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = [
    "fridge_features.csv",
    "kitchen_lights_features.csv",
    "laptop_features.csv",
    "office_fan_features.csv"
]

# Features that will be used by ML models
FEATURE_COLUMNS = [
    "power_w",
    "status",
    "hour",
    "day_of_week",
    "is_weekend",
    "month",
    "power_lag_1",
    "power_lag_5",
    "power_rolling_mean",
    "power_rolling_max"
]

TARGET_COLUMN = "power_w"

print("=" * 70)
print("ML DATASET PREPARATION")
print("=" * 70)

total_rows = 0

for filename in FILES:

    input_file = os.path.join(INPUT_DIR, filename)

    if not os.path.exists(input_file):
        print(f"\nERROR: File not found: {input_file}")
        continue

    appliance = filename.replace("_features.csv", "")

    output_file = os.path.join(
        OUTPUT_DIR,
        appliance + "_ml.csv"
    )

    print("\n" + "-" * 70)
    print("Appliance:", appliance)
    print("Input:", input_file)
    print("-" * 70)

    start_time = time.time()

    first_chunk = True
    rows_written = 0

    # Read in chunks to avoid loading everything into RAM
    for chunk_number, df in enumerate(
        pd.read_csv(input_file, chunksize=100000),
        start=1
    ):

        # ----------------------------------------------------
        # Keep required ML columns
        # ----------------------------------------------------

        required_columns = [
            "timestamp",
            "appliance"
        ] + FEATURE_COLUMNS

        df = df[required_columns].copy()

        # ----------------------------------------------------
        # Convert timestamp
        # ----------------------------------------------------

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

        # ----------------------------------------------------
        # Remove rows with invalid timestamp
        # ----------------------------------------------------

        df = df.dropna(subset=["timestamp"])

        # ----------------------------------------------------
        # Remove rows where target is missing
        # ----------------------------------------------------

        df = df.dropna(subset=[TARGET_COLUMN])

        # ----------------------------------------------------
        # Fill missing lag features
        #
        # These occur naturally at the beginning of a
        # time series.
        # ----------------------------------------------------

        lag_columns = [
            "power_lag_1",
            "power_lag_5"
        ]

        for col in lag_columns:
            df[col] = df[col].fillna(0)

        # ----------------------------------------------------
        # Fill rolling feature missing values
        # ----------------------------------------------------

        rolling_columns = [
            "power_rolling_mean",
            "power_rolling_max"
        ]

        for col in rolling_columns:

            df[col] = df[col].fillna(
                df[TARGET_COLUMN]
            )

        # ----------------------------------------------------
        # Write output
        # ----------------------------------------------------

        df.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

        rows_written += len(df)

        print(
            f"Chunk {chunk_number}: "
            f"{len(df):,} rows | "
            f"Total: {rows_written:,}"
        )

    elapsed = time.time() - start_time

    total_rows += rows_written

    print("\nCompleted:", appliance)
    print("Rows:", f"{rows_written:,}")
    print("Output:", output_file)
    print("Time:", f"{elapsed / 60:.2f} minutes")


print("\n" + "=" * 70)
print("ML DATASET PREPARATION COMPLETE")
print("=" * 70)

print("Total rows:", f"{total_rows:,}")
print("Output directory:")
print(OUTPUT_DIR)

print("=" * 70)