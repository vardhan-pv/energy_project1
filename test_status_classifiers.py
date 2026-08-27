import os
import joblib
import pandas as pd


# ============================================================
# STATUS CLASSIFIER VERIFICATION
# ============================================================

MODEL_DIR = r"E:\energy_project\ml_models"

MODELS = [
    "fridge_status_classifier.pkl",
    "kitchen_lights_status_classifier.pkl",
    "laptop_status_classifier.pkl",
    "office_fan_status_classifier.pkl"
]


# ============================================================
# FEATURE ORDER
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


# ============================================================
# TEST INPUT
# ============================================================

test_features = pd.DataFrame([
    {
        "power_w": 50,
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
print("STATUS CLASSIFIER VERIFICATION")
print("=" * 70)

print("\nTest features:")
print(test_features.to_string(index=False))

print("\nFeature order:")

for i, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{i}. {feature}")

print("\n" + "-" * 70)


# ============================================================
# TEST MODELS
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

        print(
            "Prediction:",
            prediction[0]
        )

        # ----------------------------------------------------
        # Probability if supported
        # ----------------------------------------------------

        if hasattr(model, "predict_proba"):

            probabilities = model.predict_proba(
                test_features[FEATURE_COLUMNS]
            )

            print(
                "OFF probability:",
                probabilities[0][0]
            )

            print(
                "ON probability:",
                probabilities[0][1]
            )

        # ----------------------------------------------------
        # Interpret
        # ----------------------------------------------------

        if prediction[0] == 0:

            print("Result: OFF")

        elif prediction[0] == 1:

            print("Result: ON")

        else:

            print("Result: UNKNOWN")

        print("Status: PASS")

    except Exception as e:

        print("Status: FAIL")
        print("Error:", e)


print("\n" + "=" * 70)
print("STATUS CLASSIFIER VERIFICATION COMPLETE")
print("=" * 70)