import os
import joblib
import pandas as pd


BASE_DIR = r"E:\energy_project"
MODEL_DIR = os.path.join(BASE_DIR, "peak_models")


APPLIANCES = [
    "fridge",
    "kitchen_lights",
    "laptop",
    "office_fan"
]


FEATURE_COLUMNS = [
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


test_data = pd.DataFrame([{
    "power_w": 50,
    "status": 1,
    "energy_kwh": 0.05,
    "hour": 12,
    "day_of_week": 3,
    "is_weekend": 0,
    "power_lag_1": 50,
    "power_lag_5": 50,
    "power_rolling_mean": 50,
    "power_rolling_max": 60,
    "hour_sin": 0,
    "hour_cos": -1,
    "day_sin": 0.4339,
    "day_cos": -0.9009
}])


print("=" * 70)
print("PEAK MODEL VERIFICATION")
print("=" * 70)

print("\nTest features:")
print(test_data.to_string(index=False))

print("\nFeature order:")

for i, feature in enumerate(FEATURE_COLUMNS, start=1):
    print(f"{i}. {feature}")

print("\n" + "-" * 70)


for appliance in APPLIANCES:

    model_file = os.path.join(
        MODEL_DIR,
        appliance + "_peak_model.pkl"
    )

    print("\nModel:", os.path.basename(model_file))

    if not os.path.exists(model_file):
        print("Status: FAIL - MODEL NOT FOUND")
        continue

    try:

        model = joblib.load(model_file)

        print("Loaded successfully")
        print("Model type:", type(model).__name__)

        prediction = model.predict(
            test_data[FEATURE_COLUMNS]
        )

        print("Predicted future peak:",
              float(prediction[0]), "W")

        print("Status: PASS")

    except Exception as e:

        print("Status: FAIL")
        print("Error:", e)


print("\n" + "=" * 70)
print("PEAK MODEL VERIFICATION COMPLETE")
print("=" * 70)