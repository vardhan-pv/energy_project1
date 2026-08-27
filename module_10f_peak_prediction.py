import pandas as pd
import numpy as np
import os
import glob
import time
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ============================================================
# MODULE 10F — PEAK LOAD PREDICTION
# ============================================================

print("=" * 70)
print("MODULE 10F — PEAK LOAD PREDICTION")
print("=" * 70)

BASE_DIR = r"E:\energy_project"

FEATURE_DIR = os.path.join(BASE_DIR, "feature_output")
OUTPUT_DIR = os.path.join(BASE_DIR, "peak_output")
MODEL_DIR = os.path.join(BASE_DIR, "peak_models")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ============================================================
# SETTINGS
# ============================================================

CHUNK_SIZE = 100000

# Future peak window.
# 5 future observations are used to define the target peak.
FUTURE_WINDOW = 5

# Random Forest settings
N_ESTIMATORS = 100
RANDOM_STATE = 42

# ============================================================
# FEATURE FILES
# ============================================================

feature_files = glob.glob(
    os.path.join(
        FEATURE_DIR,
        "*_features.csv"
    )
)

if not feature_files:
    print("ERROR: No feature files found.")
    raise SystemExit(1)

print("\nFeature files found:", len(feature_files))

# ============================================================
# SUMMARY
# ============================================================

results = []

overall_start = time.time()

# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

for feature_file in feature_files:

    appliance = os.path.basename(
        feature_file
    ).replace(
        "_features.csv",
        ""
    )

    print("\n" + "=" * 70)
    print("PROCESSING:", appliance)
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    usecols = [
        "id",
        "timestamp",
        "appliance",
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max"
    ]

    print("Loading data...")

    df = pd.read_csv(
        feature_file,
        usecols=usecols
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # CREATE FUTURE PEAK TARGET
    # --------------------------------------------------------

    print("Creating future peak target...")

    future_values = []

    power = df["power_w"].values

    for shift in range(1, FUTURE_WINDOW + 1):

        future_values.append(
            pd.Series(power)
            .shift(-shift)
        )

    future_matrix = pd.concat(
        future_values,
        axis=1
    )

    df["future_peak_power_w"] = (
        future_matrix.max(axis=1)
    )

    # Last FUTURE_WINDOW rows don't have a complete future window
    df = df.iloc[
        :-FUTURE_WINDOW
    ].copy()

    # --------------------------------------------------------
    # REMOVE FEATURE NaNs
    # --------------------------------------------------------

    feature_columns = [
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max"
    ]

    df[feature_columns] = df[
        feature_columns
    ].replace(
        [np.inf, -np.inf],
        np.nan
    )

    df[feature_columns] = df[
        feature_columns
    ].fillna(0)

    # --------------------------------------------------------
    # CYCLIC TIME FEATURES
    # --------------------------------------------------------

    df["hour_sin"] = np.sin(
        2 * np.pi * df["hour"] / 24
    )

    df["hour_cos"] = np.cos(
        2 * np.pi * df["hour"] / 24
    )

    df["day_sin"] = np.sin(
        2 * np.pi * df["day_of_week"] / 7
    )

    df["day_cos"] = np.cos(
        2 * np.pi * df["day_of_week"] / 7
    )

    # --------------------------------------------------------
    # FINAL FEATURES
    # --------------------------------------------------------

    X_columns = [
        "power_w",
        "status",
        "energy_kwh",
        "hour",
        "day_of_week",
        "is_weekend",
        "power_lag_1",
        "power_lag_5",
        "power_rolling_mean",
        "power_rolling_max",
        "hour_sin",
        "hour_cos",
        "day_sin",
        "day_cos"
    ]

    X = df[X_columns]
    y = df["future_peak_power_w"]

    # --------------------------------------------------------
    # TIME-BASED TRAIN / TEST SPLIT
    # --------------------------------------------------------

    split_index = int(
        len(df) * 0.8
    )

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print(
        "Training rows:",
        len(X_train)
    )

    print(
        "Testing rows:",
        len(X_test)
    )

    # --------------------------------------------------------
    # TRAIN RANDOM FOREST
    # --------------------------------------------------------

    print("\nTraining Random Forest...")

    model = RandomForestRegressor(
        n_estimators=N_ESTIMATORS,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_depth=20,
        min_samples_leaf=2
    )

    model.fit(
        X_train,
        y_train
    )

    # --------------------------------------------------------
    # PREDICTION
    # --------------------------------------------------------

    print("Generating predictions...")

    predictions = model.predict(
        X_test
    )

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    r2 = r2_score(
        y_test,
        predictions
    )

    # --------------------------------------------------------
    # PEAK METRICS
    # --------------------------------------------------------

    actual_peak = float(
        y_test.max()
    )

    predicted_peak = float(
        predictions.max()
    )

    peak_error = abs(
        actual_peak -
        predicted_peak
    )

    # --------------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------------

    model_file = os.path.join(
        MODEL_DIR,
        appliance +
        "_peak_model.pkl"
    )

    joblib.dump(
        model,
        model_file
    )

    # --------------------------------------------------------
    # SAVE PREDICTIONS
    # --------------------------------------------------------

    result_df = df.iloc[
        split_index:
    ][
        [
            "id",
            "timestamp",
            "appliance",
            "power_w",
            "status",
            "future_peak_power_w"
        ]
    ].copy()

    result_df[
        "predicted_peak_power_w"
    ] = predictions

    result_df[
        "prediction_error_w"
    ] = (
        result_df[
            "future_peak_power_w"
        ]
        -
        result_df[
            "predicted_peak_power_w"
        ]
    )

    prediction_file = os.path.join(
        OUTPUT_DIR,
        appliance +
        "_peak_predictions.csv"
    )

    result_df.to_csv(
        prediction_file,
        index=False
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    elapsed = (
        time.time() -
        start_time
    ) / 60

    print("\n" + "-" * 70)
    print("RESULT:", appliance)
    print("-" * 70)

    print(
        "MAE :",
        round(mae, 4)
    )

    print(
        "RMSE:",
        round(rmse, 4)
    )

    print(
        "R2  :",
        round(r2, 4)
    )

    print(
        "Actual Peak Power:",
        round(actual_peak, 4),
        "W"
    )

    print(
        "Predicted Peak Power:",
        round(predicted_peak, 4),
        "W"
    )

    print(
        "Peak Error:",
        round(peak_error, 4),
        "W"
    )

    print(
        "Training time:",
        round(elapsed, 2),
        "minutes"
    )

    print(
        "Model:",
        model_file
    )

    print(
        "Predictions:",
        prediction_file
    )

    results.append({
        "appliance": appliance,
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
        "actual_peak_power_w": actual_peak,
        "predicted_peak_power_w": predicted_peak,
        "peak_error_w": peak_error,
        "training_time_minutes": elapsed
    })

# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    results
)

summary_file = os.path.join(
    OUTPUT_DIR,
    "peak_prediction_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

total_time = (
    time.time() -
    overall_start
) / 60

# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("MODULE 10F COMPLETE")
print("=" * 70)

print(
    summary.to_string(
        index=False
    )
)

print("\nSummary saved to:")
print(summary_file)

print("\nModels saved to:")
print(MODEL_DIR)

print("\nPredictions saved to:")
print(OUTPUT_DIR)

print(
    "\nTotal time:",
    round(total_time, 2),
    "minutes"
)

print("=" * 70)