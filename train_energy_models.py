import pandas as pd
import numpy as np
import os
import glob
import time
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# MODULE 7 - ENERGY PREDICTION MODEL
# ============================================================

INPUT_DIR = r"E:\energy_project\ml_data"
MODEL_DIR = r"E:\energy_project\ml_models"

os.makedirs(MODEL_DIR, exist_ok=True)


FEATURE_COLUMNS = [
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

TARGET = "power_w"


FILES = [
    "fridge_ml.csv",
    "kitchen_lights_ml.csv",
    "laptop_ml.csv",
    "office_fan_ml.csv"
]


print("=" * 70)
print("MODULE 7 - ENERGY PREDICTION MODEL")
print("=" * 70)


results = []


for filename in FILES:

    appliance = filename.replace("_ml.csv", "")

    input_file = os.path.join(INPUT_DIR, filename)

    print("\n" + "=" * 70)
    print("APPLIANCE:", appliance)
    print("=" * 70)

    if not os.path.exists(input_file):
        print("ERROR: File not found:", input_file)
        continue

    start_time = time.time()

    print("Loading data...")

    df = pd.read_csv(input_file)

    print("Rows loaded:", f"{len(df):,}")

    # --------------------------------------------------------
    # Remove rows containing invalid ML values
    # --------------------------------------------------------

    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET])

    print("Rows after validation:", f"{len(df):,}")

    # --------------------------------------------------------
    # X and y
    # --------------------------------------------------------

    X = df[FEATURE_COLUMNS]
    y = df[TARGET]

    # --------------------------------------------------------
    # Chronological train/test split
    #
    # IMPORTANT:
    # Energy data is time-series data.
    # We do NOT randomly shuffle it.
    # --------------------------------------------------------

    split_index = int(len(df) * 0.80)

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    print("Training rows:", f"{len(X_train):,}")
    print("Testing rows :", f"{len(X_test):,}")

    # ========================================================
    # MODEL 1 - LINEAR REGRESSION
    # ========================================================

    print("\nTraining Linear Regression...")

    linear_model = LinearRegression()

    linear_model.fit(X_train, y_train)

    linear_pred = linear_model.predict(X_test)

    linear_mae = mean_absolute_error(y_test, linear_pred)
    linear_rmse = np.sqrt(mean_squared_error(y_test, linear_pred))
    linear_r2 = r2_score(y_test, linear_pred)

    print("\nLinear Regression")
    print("MAE :", round(linear_mae, 4))
    print("RMSE:", round(linear_rmse, 4))
    print("R2  :", round(linear_r2, 4))

    # ========================================================
    # MODEL 2 - RANDOM FOREST
    # ========================================================

    print("\nTraining Random Forest...")

    # Limit training data if extremely large.
    # This prevents excessive RAM usage.
    max_training_rows = 500000

    if len(X_train) > max_training_rows:

        print(
            "Training data is large.",
            "Using last",
            f"{max_training_rows:,}",
            "training rows."
        )

        X_rf_train = X_train.iloc[-max_training_rows:]
        y_rf_train = y_train.iloc[-max_training_rows:]

    else:

        X_rf_train = X_train
        y_rf_train = y_train

    random_forest = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    random_forest.fit(X_rf_train, y_rf_train)

    rf_pred = random_forest.predict(X_test)

    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
    rf_r2 = r2_score(y_test, rf_pred)

    print("\nRandom Forest")
    print("MAE :", round(rf_mae, 4))
    print("RMSE:", round(rf_rmse, 4))
    print("R2  :", round(rf_r2, 4))

    # ========================================================
    # SELECT BEST MODEL
    # ========================================================

    if rf_rmse < linear_rmse:

        best_model = random_forest
        best_name = "random_forest"
        best_rmse = rf_rmse
        best_mae = rf_mae
        best_r2 = rf_r2

    else:

        best_model = linear_model
        best_name = "linear_regression"
        best_rmse = linear_rmse
        best_mae = linear_mae
        best_r2 = linear_r2

    # ========================================================
    # SAVE BEST MODEL
    # ========================================================

    model_file = os.path.join(
        MODEL_DIR,
        appliance + "_energy_model.pkl"
    )

    joblib.dump(
        best_model,
        model_file
    )

    # Save feature information
    feature_file = os.path.join(
        MODEL_DIR,
        appliance + "_features.txt"
    )

    with open(feature_file, "w") as f:

        f.write("Appliance: " + appliance + "\n")
        f.write("Target: " + TARGET + "\n")
        f.write("Model: " + best_name + "\n\n")
        f.write("Features:\n")

        for feature in FEATURE_COLUMNS:
            f.write(feature + "\n")

    elapsed = time.time() - start_time

    print("\nBEST MODEL:", best_name)
    print("Best MAE :", round(best_mae, 4))
    print("Best RMSE:", round(best_rmse, 4))
    print("Best R2  :", round(best_r2, 4))

    print("Saved model:")
    print(model_file)

    results.append({
        "appliance": appliance,
        "model": best_name,
        "MAE": best_mae,
        "RMSE": best_rmse,
        "R2": best_r2,
        "training_time_minutes": elapsed / 60
    })


# ============================================================
# SAVE RESULTS
# ============================================================

results_df = pd.DataFrame(results)

results_file = os.path.join(
    MODEL_DIR,
    "model_comparison.csv"
)

results_df.to_csv(
    results_file,
    index=False
)


print("\n" + "=" * 70)
print("MODULE 7 COMPLETE")
print("=" * 70)

print(results_df.to_string(index=False))

print("\nResults saved to:")
print(results_file)

print("\nModels saved to:")
print(MODEL_DIR)

print("=" * 70)