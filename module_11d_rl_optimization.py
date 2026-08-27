import os
import time
import joblib
import numpy as np
import pandas as pd

# ============================================================
# MODULE 11D — RL ENERGY OPTIMIZATION
# ============================================================

BASE_DIR = r"E:\energy_project"

RL_MODEL_DIR = os.path.join(BASE_DIR, "rl_models")
RL_DATA_DIR = os.path.join(BASE_DIR, "rl_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "rl_optimization")

os.makedirs(OUTPUT_DIR, exist_ok=True)

APPLIANCES = [
    "fridge",
    "kitchen_lights",
    "laptop",
    "office_fan"
]

CHUNK_SIZE = 100000

# ============================================================
# ACTION DEFINITIONS
# ============================================================

ACTION_NAMES = {
    0: "maintain",
    1: "reduce",
    2: "shift",
    3: "turn_off"
}

# ============================================================
# ENERGY OPTIMIZATION ASSUMPTIONS
# ============================================================

REDUCE_FACTOR = 0.80
SHIFT_FACTOR = 0.85
TURN_OFF_FACTOR = 0.00


# ============================================================
# FIND ENVIRONMENT FILE
# ============================================================

def find_environment_file(appliance):

    file_path = os.path.join(
        RL_DATA_DIR,
        f"{appliance}_rl_environment.csv"
    )

    if os.path.exists(file_path):
        return file_path

    raise FileNotFoundError(
        f"Missing RL environment file:\n{file_path}"
    )


# ============================================================
# LOAD MODEL PACKAGE
# ============================================================

def load_model_package(appliance):

    model_file = os.path.join(
        RL_MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    if not os.path.exists(model_file):
        raise FileNotFoundError(model_file)

    package = joblib.load(model_file)

    if not isinstance(package, dict):
        raise ValueError(
            f"Invalid model package: {model_file}"
        )

    model = package["model"]
    scaler = package["scaler"]
    features = package["features"]
    actions = package["actions"]

    print("Model package loaded.")
    print(
        "Model type:",
        type(model).__name__
    )

    print(
        "Scaler type:",
        type(scaler).__name__
    )

    print(
        "Features:",
        len(features)
    )

    print(
        "Feature list:",
        features
    )

    print(
        "Actions:",
        actions
    )

    if "action" not in features:

        raise ValueError(
            "The RL model does not contain "
            "'action' as a feature."
        )

    if len(features) != 18:

        raise ValueError(
            f"Expected 18 features, "
            f"found {len(features)}"
        )

    return model, scaler, features, actions


# ============================================================
# OPTIMIZED POWER
# ============================================================

def optimized_power(power, action):

    if action == 0:
        return power

    if action == 1:
        return power * REDUCE_FACTOR

    if action == 2:
        return power * SHIFT_FACTOR

    if action == 3:
        return 0.0

    return power


# ============================================================
# PROCESS APPLIANCE
# ============================================================

def process_appliance(appliance):

    start = time.time()

    print()
    print("=" * 70)
    print("PROCESSING:", appliance)
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    print("Loading RL model...")

    model, scaler, features, actions = \
        load_model_package(appliance)

    # --------------------------------------------------------
    # LOAD ENVIRONMENT
    # --------------------------------------------------------

    environment_file = \
        find_environment_file(appliance)

    print()
    print("Loading RL environment...")
    print(environment_file)

    header = pd.read_csv(
        environment_file,
        nrows=0
    )

    columns = list(header.columns)

    missing = [
        f for f in features
        if f not in columns
    ]

    if missing:

        raise ValueError(
            f"Missing features: {missing}"
        )

    print("All model features found.")

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{appliance}_optimized.csv"
    )

    if os.path.exists(output_file):
        os.remove(output_file)

    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    total_rows = 0

    original_energy = 0.0
    optimized_energy = 0.0

    action_counts = {
        0: 0,
        1: 0,
        2: 0,
        3: 0
    }

    first_chunk = True

    # ========================================================
    # CHUNK PROCESSING
    # ========================================================

    for chunk_no, df in enumerate(
        pd.read_csv(
            environment_file,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        print(
            f"Chunk {chunk_no}: "
            f"{len(df):,} rows"
        )

        # ----------------------------------------------------
        # BUILD BASE FEATURES
        # ----------------------------------------------------

        base_features = [
            f for f in features
            if f != "action"
        ]

        X_base = df[
            base_features
        ].copy()

        # ----------------------------------------------------
        # NUMERIC CONVERSION
        # ----------------------------------------------------

        for col in base_features:

            X_base[col] = pd.to_numeric(
                X_base[col],
                errors="coerce"
            )

        X_base = X_base.replace(
            [np.inf, -np.inf],
            np.nan
        )

        valid = X_base.notna().all(axis=1)

        # Default maintain
        selected_actions = np.zeros(
            len(df),
            dtype=np.int8
        )

        # ----------------------------------------------------
        # SCORE ALL FOUR ACTIONS
        # ----------------------------------------------------

        if valid.any():

            X_valid = X_base.loc[
                valid
            ].copy()

            action_predictions = []

            for action in [0, 1, 2, 3]:

                # --------------------------------------------
                # COPY STATE
                # --------------------------------------------

                candidate = X_valid.copy()

                # --------------------------------------------
                # ADD ACTION
                # --------------------------------------------

                candidate["action"] = action

                # --------------------------------------------
                # EXACT MODEL FEATURE ORDER
                # --------------------------------------------

                candidate = candidate[
                    features
                ]

                # --------------------------------------------
                # SCALE
                # --------------------------------------------

                candidate_scaled = scaler.transform(
                    candidate
                )

                # --------------------------------------------
                # PREDICT REWARD / VALUE
                # --------------------------------------------

                predicted_reward = model.predict(
                    candidate_scaled
                )

                action_predictions.append(
                    np.asarray(
                        predicted_reward,
                        dtype=np.float64
                    )
                )

            # ------------------------------------------------
            # STACK:
            #
            # rows × actions
            # ------------------------------------------------

            values = np.column_stack(
                action_predictions
            )

            # ------------------------------------------------
            # SELECT BEST ACTION
            # ------------------------------------------------

            best_actions = np.argmax(
                values,
                axis=1
            )

            selected_actions[
                valid.to_numpy()
            ] = best_actions.astype(
                np.int8
            )

        # ----------------------------------------------------
        # POWER
        # ----------------------------------------------------

        power = pd.to_numeric(
            df["power_w"],
            errors="coerce"
        ).fillna(0.0)

        power = power.clip(
            lower=0
        )

        power_array = power.to_numpy(
            dtype=np.float64
        )

        # ----------------------------------------------------
        # OPTIMIZED POWER
        # ----------------------------------------------------

        new_power = power_array.copy()

        mask = selected_actions == 1

        new_power[mask] = (
            power_array[mask]
            * REDUCE_FACTOR
        )

        mask = selected_actions == 2

        new_power[mask] = (
            power_array[mask]
            * SHIFT_FACTOR
        )

        mask = selected_actions == 3

        new_power[mask] = 0.0

        # ----------------------------------------------------
        # TIME INTERVAL
        # ----------------------------------------------------

        if "timestamp" in df.columns:

            timestamps = pd.to_datetime(
                df["timestamp"],
                errors="coerce"
            )

            delta = (
                timestamps.diff()
                .dt.total_seconds()
            )

            delta = delta.fillna(6.0)

            delta = delta.clip(
                lower=0,
                upper=3600
            )

            seconds = delta.to_numpy()

        else:

            seconds = np.full(
                len(df),
                6.0
            )

        # ----------------------------------------------------
        # ENERGY
        # ----------------------------------------------------

        original_energy_chunk = np.sum(
            power_array
            * seconds
            / 3600000.0
        )

        optimized_energy_chunk = np.sum(
            new_power
            * seconds
            / 3600000.0
        )

        original_energy += (
            original_energy_chunk
        )

        optimized_energy += (
            optimized_energy_chunk
        )

        # ----------------------------------------------------
        # ACTION COUNTS
        # ----------------------------------------------------

        counts = np.bincount(
            selected_actions,
            minlength=4
        )

        for action in range(4):

            action_counts[action] += int(
                counts[action]
            )

        # ----------------------------------------------------
        # OUTPUT COLUMNS
        # ----------------------------------------------------

        df["rl_action"] = selected_actions

        df["rl_action_name"] = [
            ACTION_NAMES[int(a)]
            for a in selected_actions
        ]

        df["original_power_w"] = \
            power_array

        df["optimized_power_w"] = \
            new_power

        df["power_saving_w"] = (
            power_array
            - new_power
        )

        # ----------------------------------------------------
        # WRITE CHUNK
        # ----------------------------------------------------

        df.to_csv(
            output_file,
            mode="w" if first_chunk else "a",
            header=first_chunk,
            index=False
        )

        first_chunk = False

        total_rows += len(df)

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    savings = (
        original_energy
        - optimized_energy
    )

    if original_energy > 0:

        savings_pct = (
            savings
            / original_energy
            * 100
        )

    else:

        savings_pct = 0.0

    elapsed = (
        time.time() - start
    ) / 60.0

    # ========================================================
    # PRINT RESULT
    # ========================================================

    print()
    print("-" * 70)
    print("RESULT:", appliance)
    print("-" * 70)

    print(
        "Rows optimized:",
        f"{total_rows:,}"
    )

    print(
        f"Original energy: "
        f"{original_energy:.6f} kWh"
    )

    print(
        f"Optimized energy: "
        f"{optimized_energy:.6f} kWh"
    )

    print(
        f"Estimated savings: "
        f"{savings:.6f} kWh"
    )

    print(
        f"Estimated savings %: "
        f"{savings_pct:.4f}%"
    )

    print()
    print("ACTION DISTRIBUTION")

    print(
        "0 (maintain):",
        f"{action_counts[0]:,}"
    )

    print(
        "1 (reduce):",
        f"{action_counts[1]:,}"
    )

    print(
        "2 (shift):",
        f"{action_counts[2]:,}"
    )

    print(
        "3 (turn_off):",
        f"{action_counts[3]:,}"
    )

    print()
    print(
        "Output:",
        output_file
    )

    print(
        f"Time: {elapsed:.2f} minutes"
    )

    return {
        "appliance": appliance,
        "rows_optimized": total_rows,
        "original_energy_kwh": original_energy,
        "optimized_energy_kwh": optimized_energy,
        "estimated_savings_kwh": savings,
        "estimated_savings_percentage": savings_pct,
        "maintain_actions": action_counts[0],
        "reduce_actions": action_counts[1],
        "shift_actions": action_counts[2],
        "turn_off_actions": action_counts[3],
        "optimization_time_minutes": elapsed
    }


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("MODULE 11D — RL ENERGY OPTIMIZATION")
print("=" * 70)

print()
print("Checking required files...")

for appliance in APPLIANCES:

    model_file = os.path.join(
        RL_MODEL_DIR,
        f"{appliance}_rl_agent.pkl"
    )

    environment_file = find_environment_file(
        appliance
    )

    if not os.path.exists(model_file):

        raise FileNotFoundError(
            model_file
        )

print("All required files found.")

results = []

overall_start = time.time()

for appliance in APPLIANCES:

    result = process_appliance(
        appliance
    )

    results.append(result)

# ============================================================
# SUMMARY
# ============================================================

summary = pd.DataFrame(
    results
)

summary_file = os.path.join(
    OUTPUT_DIR,
    "rl_optimization_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False
)

total_time = (
    time.time() - overall_start
) / 60.0

print()
print("=" * 70)
print("MODULE 11D COMPLETE")
print("=" * 70)

print(
    summary.to_string(
        index=False
    )
)

print()
print(
    "Summary saved to:"
)

print(summary_file)

print()
print(
    "Optimization files saved to:"
)

print(OUTPUT_DIR)

print()
print(
    f"Total time: "
    f"{total_time:.2f} minutes"
)

print("=" * 70)