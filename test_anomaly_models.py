import os
import joblib
import pandas as pd


# ============================================================
# ANOMALY MODEL VERIFICATION
# ============================================================

MODEL_DIR = r"E:\energy_project\ml_models"

MODELS = [
    "fridge_anomaly_model.pkl",
    "kitchen_lights_anomaly_model.pkl",
    "laptop_anomaly_model.pkl",
    "office_fan_anomaly_model.pkl"
]


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


# ============================================================
# TEST DATA
# ============================================================

test_features = pd.DataFrame([
    {
        "power_w": 50,
        "status": 1,
        "hour": 12,
        "day_of_week": 3,
        "is_weekend": 0,
        "month": 8,
        "power_lag_1": 50,
        "power_lag_5": 50,
        "power_rolling_mean": 50,
        "power_rolling_max": 60
    }
])


print("=" * 70)
print("ANOMALY MODEL VERIFICATION")
print("=" * 70)

print("\nTest features:")
print(test_features.to_string(index=False))

print("\nFeature order:")

for i, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{i}. {feature}")

print("\n" + "-" * 70)


# ============================================================
# TEST EACH MODEL
# ============================================================

for filename in MODELS:

    print(f"\nModel: {filename}")

    model_file = os.path.join(
        MODEL_DIR,
        filename
    )

    try:

        # ----------------------------------------------------
        # Load model
        # ----------------------------------------------------

        model = joblib.load(model_file)

        print("Loaded successfully")

        print(
            "Model type:",
            type(model).__name__
        )

        # ----------------------------------------------------
        # Prediction
        # ----------------------------------------------------

        prediction = model.predict(
            test_features[FEATURE_COLUMNS]
        )

        score = model.decision_function(
            test_features[FEATURE_COLUMNS]
        )

        print(
            "Prediction:",
            prediction[0]
        )

        print(
            "Anomaly score:",
            score[0]
        )

        # ----------------------------------------------------
        # Interpret result
        # ----------------------------------------------------

        if prediction[0] == 1:

            print(
                "Result: NORMAL"
            )

        elif prediction[0] == -1:

            print(
                "Result: ANOMALY"
            )

        else:

            print(
                "Result: UNKNOWN"
            )

        print("Status: PASS")

    except Exception as e:

        print("Status: FAIL")
        print("Error:", e)


print("\n" + "=" * 70)
print("ANOMALY MODEL VERIFICATION COMPLETE")
print("=" * 70)