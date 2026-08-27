import os
import joblib
import pandas as pd

MODEL_DIR = r"E:\energy_project\ml_models"

FEATURE_COLUMNS = [
    "status",
    "hour",
    "day_of_week",
    "is_weekend",
    "month",
    "power_lag_1",
    "power_lag_5",
    "power_rolling_mean",
    "power_rolling_max",
]

MODELS = [
    "fridge_energy_model.pkl",
    "kitchen_lights_energy_model.pkl",
    "laptop_energy_model.pkl",
    "office_fan_energy_model.pkl",
]

print("=" * 70)
print("ENERGY MODEL VERIFICATION")
print("=" * 70)

# Test input with the exact training feature names
test_data = pd.DataFrame([{
    "status": 1,
    "hour": 12,
    "day_of_week": 3,
    "is_weekend": 0,
    "month": 8,
    "power_lag_1": 50,
    "power_lag_5": 50,
    "power_rolling_mean": 50,
    "power_rolling_max": 60,
}])

print("\nTest features:")
print(test_data)

print("\nFeature order:")
for i, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{i}. {feature}")

print("\n" + "-" * 70)

for filename in MODELS:

    model_path = os.path.join(MODEL_DIR, filename)

    print("\nModel:", filename)

    if not os.path.exists(model_path):
        print("ERROR: Model not found")
        continue

    try:
        model = joblib.load(model_path)

        print("Loaded successfully")
        print("Model type:", type(model).__name__)

        prediction = model.predict(test_data)

        print("Prediction:", prediction[0])
        print("Status: PASS")

    except Exception as e:
        print("Status: FAILED")
        print("Error:", repr(e))

print("\n" + "=" * 70)
print("MODEL VERIFICATION COMPLETE")
print("=" * 70)