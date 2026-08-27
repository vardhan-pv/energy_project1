import pandas as pd
import numpy as np
import os
import time
import joblib

from sklearn.ensemble import IsolationForest


# ============================================================
# MODULE 9 - ENERGY ANOMALY DETECTION
# ============================================================

INPUT_DIR = r"E:\energy_project\ml_data"
OUTPUT_DIR = r"E:\energy_project\anomaly_output"
MODEL_DIR = r"E:\energy_project\ml_models"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# FEATURES USED FOR ANOMALY DETECTION
# ============================================================

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


FILES = [
    "fridge_ml.csv",
    "kitchen_lights_ml.csv",
    "laptop_ml.csv",
    "office_fan_ml.csv"
]


# ============================================================
# SETTINGS
# ============================================================

CHUNK_SIZE = 100000

# Number of rows used to train Isolation Forest
MAX_TRAIN_ROWS = 300000

# Expected approximate anomaly percentage
# Isolation Forest contamination is only an initial assumption.
CONTAMINATION = 0.01


print("=" * 70)
print("MODULE 9 - ENERGY ANOMALY DETECTION")
print("=" * 70)

results = []


# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

for filename in FILES:

    appliance = filename.replace("_ml.csv", "")

    input_file = os.path.join(
        INPUT_DIR,
        filename
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        appliance + "_anomalies.csv"
    )

    model_file = os.path.join(
        MODEL_DIR,
        appliance + "_anomaly_model.pkl"
    )

    print("\n" + "=" * 70)
    print("APPLIANCE:", appliance)
    print("=" * 70)

    if not os.path.exists(input_file):

        print("ERROR: Input file not found:")
        print(input_file)

        continue

    start_time = time.time()

    # ========================================================
    # STEP 1 - LOAD REPRESENTATIVE TRAINING SAMPLE
    # ========================================================

    print("\nCollecting training sample...")

    sample_parts = []
    sample_rows = 0

    for chunk in pd.read_csv(
        input_file,
        chunksize=CHUNK_SIZE
    ):

        chunk = chunk.dropna(
            subset=FEATURE_COLUMNS
        )

        remaining = MAX_TRAIN_ROWS - sample_rows

        if remaining <= 0:
            break

        if len(chunk) > remaining:

            chunk = chunk.iloc[:remaining]

        sample_parts.append(
            chunk[FEATURE_COLUMNS]
        )

        sample_rows += len(chunk)

        if sample_rows >= MAX_TRAIN_ROWS:
            break

    train_df = pd.concat(
        sample_parts,
        ignore_index=True
    )

    print(
        "Training sample:",
        f"{len(train_df):,}",
        "rows"
    )

    # ========================================================
    # STEP 2 - TRAIN ISOLATION FOREST
    # ========================================================

    print("\nTraining Isolation Forest...")

    model = IsolationForest(

        n_estimators=150,

        max_samples="auto",

        contamination=CONTAMINATION,

        random_state=42,

        n_jobs=-1
    )

    model.fit(
        train_df[FEATURE_COLUMNS]
    )

    print("Isolation Forest training complete.")

    # ========================================================
    # SAVE MODEL
    # ========================================================

    joblib.dump(
        model,
        model_file
    )

    print("Saved model:")
    print(model_file)

    # ========================================================
    # STEP 3 - SCORE FULL DATASET
    # ========================================================

    print("\nScanning complete dataset for anomalies...")

    first_chunk = True

    total_rows = 0
    anomaly_rows = 0

    anomaly_scores_sum = 0.0

    chunk_number = 0

    for chunk in pd.read_csv(
        input_file,
        chunksize=CHUNK_SIZE
    ):

        chunk_number += 1

        original_length = len(chunk)

        # ----------------------------------------------------
        # Remove rows with missing ML features
        # ----------------------------------------------------

        chunk = chunk.dropna(
            subset=FEATURE_COLUMNS
        ).copy()

        if len(chunk) == 0:
            continue

        # ----------------------------------------------------
        # Prediction
        #
        # Isolation Forest:
        #  1  = normal
        # -1  = anomaly
        # ----------------------------------------------------

        predictions = model.predict(
            chunk[FEATURE_COLUMNS]
        )

        scores = model.decision_function(
            chunk[FEATURE_COLUMNS]
        )

        chunk["anomaly"] = predictions

        chunk["anomaly_score"] = scores

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        chunk_anomalies = (
            chunk["anomaly"] == -1
        ).sum()

        total_rows += len(chunk)

        anomaly_rows += chunk_anomalies

        anomaly_scores_sum += scores.sum()

        # ----------------------------------------------------
        # Write output
        # ----------------------------------------------------

        chunk.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

        print(
            f"Chunk {chunk_number}: "
            f"{len(chunk):,} rows | "
            f"Anomalies: {chunk_anomalies:,} | "
            f"Total: {total_rows:,}"
        )

    # ========================================================
    # FINAL STATISTICS
    # ========================================================

    if total_rows > 0:

        anomaly_percentage = (
            anomaly_rows / total_rows
        ) * 100

        average_score = (
            anomaly_scores_sum / total_rows
        )

    else:

        anomaly_percentage = 0
        average_score = 0


    elapsed = time.time() - start_time

    # ========================================================
    # SAVE SUMMARY
    # ========================================================

    results.append({

        "appliance": appliance,

        "rows_scored": total_rows,

        "anomalies": anomaly_rows,

        "anomaly_percentage":
            anomaly_percentage,

        "average_anomaly_score":
            average_score,

        "processing_time_minutes":
            elapsed / 60
    })


    print("\n" + "-" * 70)

    print(
        "ANOMALY DETECTION COMPLETE:",
        appliance
    )

    print(
        "Rows scored:",
        f"{total_rows:,}"
    )

    print(
        "Anomalies:",
        f"{anomaly_rows:,}"
    )

    print(
        "Anomaly percentage:",
        f"{anomaly_percentage:.4f}%"
    )

    print(
        "Average anomaly score:",
        f"{average_score:.6f}"
    )

    print(
        "Output:",
        output_file
    )

    print(
        "Time:",
        f"{elapsed / 60:.2f} minutes"
    )


# ============================================================
# SAVE GLOBAL SUMMARY
# ============================================================

results_df = pd.DataFrame(results)

summary_file = os.path.join(
    OUTPUT_DIR,
    "anomaly_summary.csv"
)

results_df.to_csv(
    summary_file,
    index=False
)


# ============================================================
# MODULE COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("MODULE 9 COMPLETE")
print("=" * 70)

print(
    results_df.to_string(
        index=False
    )
)

print("\nSummary saved to:")
print(summary_file)

print("\nAnomaly files saved to:")
print(OUTPUT_DIR)

print("\nModels saved to:")
print(MODEL_DIR)

print("=" * 70)