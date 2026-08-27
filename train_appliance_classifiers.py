import pandas as pd
import numpy as np
import os
import time
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


# ============================================================
# MODULE 8 - APPLIANCE ON/OFF CLASSIFICATION
# ============================================================

INPUT_DIR = r"E:\energy_project\ml_data"
MODEL_DIR = r"E:\energy_project\ml_models"

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# FEATURES
# ============================================================

FEATURE_COLUMNS = [
    "power_w",
    "hour",
    "day_of_week",
    "is_weekend",
    "month",
    "power_lag_1",
    "power_lag_5",
    "power_rolling_mean",
    "power_rolling_max"
]

TARGET = "status"


FILES = [
    "fridge_ml.csv",
    "kitchen_lights_ml.csv",
    "laptop_ml.csv",
    "office_fan_ml.csv"
]


print("=" * 70)
print("MODULE 8 - APPLIANCE ON/OFF CLASSIFICATION")
print("=" * 70)


results = []


# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

for filename in FILES:

    appliance = filename.replace("_ml.csv", "")

    input_file = os.path.join(INPUT_DIR, filename)

    print("\n" + "=" * 70)
    print("APPLIANCE:", appliance)
    print("=" * 70)

    if not os.path.exists(input_file):

        print("ERROR: File not found:")
        print(input_file)

        continue


    start_time = time.time()

    print("Loading data...")

    df = pd.read_csv(input_file)

    print("Rows loaded:", f"{len(df):,}")


    # ========================================================
    # VALIDATE DATA
    # ========================================================

    df = df.dropna(
        subset=FEATURE_COLUMNS + [TARGET]
    )

    print(
        "Rows after validation:",
        f"{len(df):,}"
    )


    # ========================================================
    # CHECK CLASS DISTRIBUTION
    # ========================================================

    print("\nClass distribution:")

    print(
        df[TARGET]
        .value_counts()
        .sort_index()
        .to_string()
    )


    # ========================================================
    # X AND Y
    # ========================================================

    X = df[FEATURE_COLUMNS]

    y = df[TARGET].astype(int)


    # ========================================================
    # CHRONOLOGICAL TRAIN / TEST SPLIT
    # ========================================================

    split_index = int(len(df) * 0.80)


    X_train = X.iloc[:split_index]

    X_test = X.iloc[split_index:]


    y_train = y.iloc[:split_index]

    y_test = y.iloc[split_index:]


    print("\nTraining rows:", f"{len(X_train):,}")

    print("Testing rows :", f"{len(X_test):,}")


    # ========================================================
    # MODEL 1 - LOGISTIC REGRESSION
    # ========================================================

    print("\nTraining Logistic Regression...")

    logistic_model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    )

    logistic_model.fit(
        X_train,
        y_train
    )


    logistic_pred = logistic_model.predict(
        X_test
    )


    logistic_accuracy = accuracy_score(
        y_test,
        logistic_pred
    )

    logistic_precision = precision_score(
        y_test,
        logistic_pred,
        zero_division=0
    )

    logistic_recall = recall_score(
        y_test,
        logistic_pred,
        zero_division=0
    )

    logistic_f1 = f1_score(
        y_test,
        logistic_pred,
        zero_division=0
    )


    print("\nLogistic Regression")

    print(
        "Accuracy :",
        round(logistic_accuracy, 4)
    )

    print(
        "Precision:",
        round(logistic_precision, 4)
    )

    print(
        "Recall   :",
        round(logistic_recall, 4)
    )

    print(
        "F1       :",
        round(logistic_f1, 4)
    )


    # ========================================================
    # MODEL 2 - RANDOM FOREST CLASSIFIER
    # ========================================================

    print("\nTraining Random Forest Classifier...")


    # Avoid excessive RAM usage
    max_training_rows = 500000


    if len(X_train) > max_training_rows:

        print(
            "Large training dataset."
        )

        print(
            "Using last",
            f"{max_training_rows:,}",
            "training rows."
        )


        X_rf_train = X_train.iloc[
            -max_training_rows:
        ]

        y_rf_train = y_train.iloc[
            -max_training_rows:
        ]

    else:

        X_rf_train = X_train

        y_rf_train = y_train


    random_forest = RandomForestClassifier(

        n_estimators=100,

        max_depth=20,

        min_samples_leaf=2,

        class_weight="balanced",

        random_state=42,

        n_jobs=-1
    )


    random_forest.fit(
        X_rf_train,
        y_rf_train
    )


    rf_pred = random_forest.predict(
        X_test
    )


    rf_accuracy = accuracy_score(
        y_test,
        rf_pred
    )

    rf_precision = precision_score(
        y_test,
        rf_pred,
        zero_division=0
    )

    rf_recall = recall_score(
        y_test,
        rf_pred,
        zero_division=0
    )

    rf_f1 = f1_score(
        y_test,
        rf_pred,
        zero_division=0
    )


    print("\nRandom Forest Classifier")

    print(
        "Accuracy :",
        round(rf_accuracy, 4)
    )

    print(
        "Precision:",
        round(rf_precision, 4)
    )

    print(
        "Recall   :",
        round(rf_recall, 4)
    )

    print(
        "F1       :",
        round(rf_f1, 4)
    )


    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    print("\nRandom Forest Confusion Matrix:")

    cm = confusion_matrix(
        y_test,
        rf_pred
    )

    print(cm)


    # ========================================================
    # SELECT BEST MODEL
    # ========================================================

    if rf_f1 >= logistic_f1:

        best_model = random_forest

        best_name = "random_forest"

        best_accuracy = rf_accuracy

        best_precision = rf_precision

        best_recall = rf_recall

        best_f1 = rf_f1

        best_cm = cm

    else:

        best_model = logistic_model

        best_name = "logistic_regression"

        best_accuracy = logistic_accuracy

        best_precision = logistic_precision

        best_recall = logistic_recall

        best_f1 = logistic_f1

        best_cm = confusion_matrix(
            y_test,
            logistic_pred
        )


    # ========================================================
    # SAVE MODEL
    # ========================================================

    model_file = os.path.join(
        MODEL_DIR,
        appliance + "_status_classifier.pkl"
    )


    joblib.dump(
        best_model,
        model_file
    )


    # ========================================================
    # SAVE FEATURE INFORMATION
    # ========================================================

    feature_file = os.path.join(
        MODEL_DIR,
        appliance + "_status_features.txt"
    )


    with open(
        feature_file,
        "w"
    ) as f:

        f.write(
            "Appliance: "
            + appliance
            + "\n"
        )

        f.write(
            "Target: status\n"
        )

        f.write(
            "0 = OFF\n"
        )

        f.write(
            "1 = ON\n"
        )

        f.write(
            "Model: "
            + best_name
            + "\n\n"
        )

        f.write(
            "Features:\n"
        )

        for feature in FEATURE_COLUMNS:

            f.write(
                feature
                + "\n"
            )


    elapsed = time.time() - start_time


    # ========================================================
    # RESULTS
    # ========================================================

    print("\nBEST MODEL:", best_name)

    print(
        "Best Accuracy :",
        round(best_accuracy, 4)
    )

    print(
        "Best Precision:",
        round(best_precision, 4)
    )

    print(
        "Best Recall   :",
        round(best_recall, 4)
    )

    print(
        "Best F1       :",
        round(best_f1, 4)
    )

    print("\nSaved model:")

    print(model_file)


    results.append({

        "appliance": appliance,

        "model": best_name,

        "accuracy": best_accuracy,

        "precision": best_precision,

        "recall": best_recall,

        "f1": best_f1,

        "training_time_minutes":
            elapsed / 60
    })


# ============================================================
# SAVE COMPARISON
# ============================================================

results_df = pd.DataFrame(
    results
)


results_file = os.path.join(
    MODEL_DIR,
    "status_classifier_comparison.csv"
)


results_df.to_csv(
    results_file,
    index=False
)


# ============================================================
# COMPLETE
# ============================================================

print("\n" + "=" * 70)

print(
    "MODULE 8 COMPLETE"
)

print("=" * 70)


print(
    results_df.to_string(
        index=False
    )
)


print("\nResults saved to:")

print(results_file)


print("\nModels saved to:")

print(MODEL_DIR)


print("=" * 70)