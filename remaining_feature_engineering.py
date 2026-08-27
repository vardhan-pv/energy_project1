import pandas as pd
import mysql.connector
import os
import time

# ============================================================
# REMAINING FEATURE ENGINEERING
# UK-DALE ENERGY PROJECT
# ============================================================

# ------------------------------------------------------------
# MYSQL CONNECTION
# ------------------------------------------------------------

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "energy_project1"
}

# ------------------------------------------------------------
# OUTPUT DIRECTORY
# ------------------------------------------------------------

OUTPUT_DIR = r"E:\energy_project\feature_output"

# ------------------------------------------------------------
# CHUNK SIZE
# ------------------------------------------------------------

CHUNK_SIZE = 100000

# ------------------------------------------------------------
# APPLIANCES STILL NEEDING FEATURES
# ------------------------------------------------------------

APPLIANCES = [
    "fridge",
]

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FEATURE ENGINEERING FUNCTION
# ============================================================

def process_appliance(appliance):

    print()
    print("=" * 70)
    print(f"STARTING FEATURE ENGINEERING: {appliance}")
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------------
    # CONNECT TO MYSQL
    # --------------------------------------------------------

    try:
        conn = mysql.connector.connect(**DB_CONFIG)

        print("MySQL connection successful!")

    except Exception as e:

        print("MySQL connection failed!")
        print(e)

        return

    # --------------------------------------------------------
    # SOURCE QUERY
    # --------------------------------------------------------

    query = f"""
        SELECT
            id,
            timestamp,
            appliance,
            power_w,
            status,
            energy_kwh
        FROM appliance_energy_clean_v3
        WHERE appliance = '{appliance}'
        ORDER BY timestamp, id
    """

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{appliance}_features.csv"
    )

    # Remove old output file if it exists
    if os.path.exists(output_file):

        print()
        print("Existing output file found.")

        os.remove(output_file)

        print("Old output file removed.")

    # --------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------

    first_chunk = True

    previous_tail = pd.DataFrame()

    total_rows = 0

    chunk_number = 0

    # --------------------------------------------------------
    # READ MYSQL DATA IN CHUNKS
    # --------------------------------------------------------

    try:

        for chunk in pd.read_sql(
            query,
            conn,
            chunksize=CHUNK_SIZE
        ):

            chunk_number += 1

            print()
            print(
                f"Reading chunk {chunk_number}: "
                f"{len(chunk):,} rows"
            )

            # ------------------------------------------------
            # DATETIME CONVERSION
            # ------------------------------------------------

            chunk["timestamp"] = pd.to_datetime(
                chunk["timestamp"]
            )

            # ------------------------------------------------
            # SORT DATA
            # ------------------------------------------------

            chunk = chunk.sort_values(
                ["timestamp", "id"]
            ).reset_index(drop=True)

            # ------------------------------------------------
            # COMBINE PREVIOUS TAIL + CURRENT CHUNK
            #
            # Previous 5 rows are required so lag_5 and
            # rolling calculations continue correctly
            # between chunks.
            # ------------------------------------------------

            if not previous_tail.empty:

                combined = pd.concat(
                    [
                        previous_tail,
                        chunk
                    ],
                    ignore_index=True
                )

            else:

                combined = chunk.copy()

            # ------------------------------------------------
            # TIME FEATURES
            # ------------------------------------------------

            combined["hour"] = (
                combined["timestamp"].dt.hour
            )

            combined["day_of_week"] = (
                combined["timestamp"].dt.dayofweek + 1
            )

            combined["is_weekend"] = (
                combined["day_of_week"] >= 6
            ).astype(int)

            combined["month"] = (
                combined["timestamp"].dt.month
            )

            # ------------------------------------------------
            # LAG FEATURES
            # ------------------------------------------------

            combined["power_lag_1"] = (
                combined["power_w"].shift(1)
            )

            combined["power_lag_5"] = (
                combined["power_w"].shift(5)
            )

            # ------------------------------------------------
            # ROLLING MEAN
            # ------------------------------------------------

            combined["power_rolling_mean"] = (
                combined["power_w"]
                .rolling(
                    window=5,
                    min_periods=1
                )
                .mean()
            )

            # ------------------------------------------------
            # ROLLING MAX
            # ------------------------------------------------

            combined["power_rolling_max"] = (
                combined["power_w"]
                .rolling(
                    window=5,
                    min_periods=1
                )
                .max()
            )

            # ------------------------------------------------
            # KEEP LAST 5 ROWS
            #
            # These rows are required for the next chunk.
            # ------------------------------------------------

            if len(combined) > CHUNK_SIZE:

                write_data = combined.iloc[:-5].copy()

                previous_tail = combined.iloc[-5:].copy()

            else:

                write_data = pd.DataFrame()

                previous_tail = combined.copy()

            # ------------------------------------------------
            # OUTPUT COLUMN ORDER
            # ------------------------------------------------

            columns = [
                "id",
                "timestamp",
                "appliance",
                "power_w",
                "status",
                "energy_kwh",
                "hour",
                "day_of_week",
                "is_weekend",
                "month",
                "power_lag_1",
                "power_lag_5",
                "power_rolling_mean",
                "power_rolling_max"
            ]

            if not write_data.empty:

                write_data = write_data[columns]

                # ------------------------------------------------
                # WRITE CSV
                # ------------------------------------------------

                write_data.to_csv(
                    output_file,
                    mode="w" if first_chunk else "a",
                    header=first_chunk,
                    index=False
                )

                first_chunk = False

                total_rows += len(write_data)

            # ------------------------------------------------
            # PROGRESS
            # ------------------------------------------------

            elapsed = time.time() - start_time

            print(
                f"Processed: {total_rows:,} rows | "
                f"Elapsed: {elapsed / 60:.2f} minutes"
            )

    except Exception as e:

        print()
        print("=" * 70)
        print("ERROR DURING PROCESSING")
        print("=" * 70)

        print(e)

        conn.close()

        return

    # ========================================================
    # PROCESS FINAL TAIL
    # ========================================================

    if not previous_tail.empty:

        # ----------------------------------------------------
        # IMPORTANT:
        # Recalculate final features using the tail.
        # ----------------------------------------------------

        previous_tail["hour"] = (
            previous_tail["timestamp"].dt.hour
        )

        previous_tail["day_of_week"] = (
            previous_tail["timestamp"].dt.dayofweek + 1
        )

        previous_tail["is_weekend"] = (
            previous_tail["day_of_week"] >= 6
        ).astype(int)

        previous_tail["month"] = (
            previous_tail["timestamp"].dt.month
        )

        previous_tail["power_lag_1"] = (
            previous_tail["power_w"].shift(1)
        )

        previous_tail["power_lag_5"] = (
            previous_tail["power_w"].shift(5)
        )

        previous_tail["power_rolling_mean"] = (
            previous_tail["power_w"]
            .rolling(
                window=5,
                min_periods=1
            )
            .mean()
        )

        previous_tail["power_rolling_max"] = (
            previous_tail["power_w"]
            .rolling(
                window=5,
                min_periods=1
            )
            .max()
        )

        columns = [
            "id",
            "timestamp",
            "appliance",
            "power_w",
            "status",
            "energy_kwh",
            "hour",
            "day_of_week",
            "is_weekend",
            "month",
            "power_lag_1",
            "power_lag_5",
            "power_rolling_mean",
            "power_rolling_max"
        ]

        previous_tail = previous_tail[columns]

        previous_tail.to_csv(
            output_file,
            mode="a",
            header=first_chunk,
            index=False
        )

        total_rows += len(previous_tail)

    # --------------------------------------------------------
    # CLOSE MYSQL CONNECTION
    # --------------------------------------------------------

    conn.close()

    # --------------------------------------------------------
    # FINAL INFORMATION
    # --------------------------------------------------------

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print(f"FEATURE ENGINEERING COMPLETE: {appliance}")
    print("=" * 70)

    print(
        f"Total rows written: {total_rows:,}"
    )

    print(
        f"Output file:"
    )

    print(
        output_file
    )

    print(
        f"Time taken: {elapsed / 60:.2f} minutes"
    )

    print("=" * 70)


# ============================================================
# MAIN PROGRAM
# ============================================================

print()
print("=" * 70)
print("UK-DALE REMAINING FEATURE ENGINEERING")
print("=" * 70)

print()
print("Source table:")
print("appliance_energy_clean_v3")

print()
print("Appliances:")
for appliance in APPLIANCES:
    print(f" - {appliance}")

print()
print(f"Chunk size: {CHUNK_SIZE:,}")

print()
print("Output directory:")
print(OUTPUT_DIR)

print()
print("=" * 70)


# ============================================================
# PROCESS EACH APPLIANCE
# ============================================================

for appliance in APPLIANCES:

    process_appliance(appliance)


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 70)
print("ALL REMAINING FEATURE ENGINEERING FINISHED")
print("=" * 70)

print()
print("Generated files should be:")

for appliance in APPLIANCES:

    print(
        os.path.join(
            OUTPUT_DIR,
            f"{appliance}_features.csv"
        )
    )

print()
print("=" * 70)