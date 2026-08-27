import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# MODULE 14B — DYNAMIC DATABASE & DATA INGESTION
# ============================================================

BASE_DIR = r"E:\energy_project"

INIT_DIR = os.path.join(BASE_DIR, "initialization")
HOUSE_DATA_DIR = os.path.join(BASE_DIR, "house_data")

HOUSE_CONFIG_FILE = os.path.join(
    INIT_DIR,
    "house_config.json"
)

APPLIANCE_CONFIG_FILE = os.path.join(
    INIT_DIR,
    "appliance_config.csv"
)

# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("MODULE 14B — DYNAMIC DATABASE & DATA INGESTION")
print("=" * 70)

# ============================================================
# CHECK REQUIRED FILES
# ============================================================

print()
print("Checking required files...")
print("-" * 70)

if not os.path.exists(HOUSE_CONFIG_FILE):
    raise FileNotFoundError(
        f"House configuration not found:\n{HOUSE_CONFIG_FILE}\n"
        f"Run Module 14A first."
    )

print(f"[OK] House configuration: {HOUSE_CONFIG_FILE}")

if not os.path.exists(APPLIANCE_CONFIG_FILE):
    raise FileNotFoundError(
        f"Appliance configuration not found:\n"
        f"{APPLIANCE_CONFIG_FILE}\n"
        f"Run Module 14A first."
    )

print(f"[OK] Appliance configuration: {APPLIANCE_CONFIG_FILE}")

# ============================================================
# LOAD HOUSE CONFIGURATION
# ============================================================

print()
print("Loading house configuration...")

with open(HOUSE_CONFIG_FILE, "r", encoding="utf-8") as f:
    house = json.load(f)

house_id = house["house_id"]
house_name = house["house_name"]

print(f"House ID   : {house_id}")
print(f"House Name : {house_name}")

# ============================================================
# LOAD APPLIANCE CONFIGURATION
# ============================================================

print()
print("Loading appliance configuration...")

appliances = pd.read_csv(APPLIANCE_CONFIG_FILE)

required_appliance_columns = [
    "appliance_id",
    "appliance_name",
    "appliance_type",
    "sensor_id",
    "rated_power_w",
    "status"
]

missing_columns = [
    c for c in required_appliance_columns
    if c not in appliances.columns
]

if missing_columns:
    raise ValueError(
        f"Missing appliance columns: {missing_columns}"
    )

print(f"Registered appliances: {len(appliances)}")

print()
print("REGISTERED APPLIANCES")
print("-" * 70)

print(
    appliances[
        [
            "appliance_id",
            "appliance_name",
            "appliance_type",
            "sensor_id",
            "rated_power_w"
        ]
    ].to_string(index=False)
)

# ============================================================
# CREATE HOUSE DIRECTORY
# ============================================================

house_dir = os.path.join(
    HOUSE_DATA_DIR,
    house_id
)

raw_dir = os.path.join(
    house_dir,
    "raw"
)

processed_dir = os.path.join(
    house_dir,
    "processed"
)

features_dir = os.path.join(
    house_dir,
    "features"
)

models_dir = os.path.join(
    house_dir,
    "models"
)

optimization_dir = os.path.join(
    house_dir,
    "optimization"
)

evolution_dir = os.path.join(
    house_dir,
    "evolution"
)

for directory in [
    house_dir,
    raw_dir,
    processed_dir,
    features_dir,
    models_dir,
    optimization_dir,
    evolution_dir
]:
    os.makedirs(directory, exist_ok=True)

print()
print("HOUSE DATA DIRECTORIES")
print("-" * 70)

print(f"House directory : {house_dir}")
print(f"Raw data        : {raw_dir}")
print(f"Processed       : {processed_dir}")
print(f"Features        : {features_dir}")
print(f"Models          : {models_dir}")
print(f"Optimization    : {optimization_dir}")
print(f"Evolution       : {evolution_dir}")

# ============================================================
# DATABASE
# ============================================================

DATABASE_FILE = os.path.join(
    house_dir,
    f"{house_id}.db"
)

print()
print("Creating dynamic database...")
print(f"Database: {DATABASE_FILE}")

conn = sqlite3.connect(DATABASE_FILE)

cursor = conn.cursor()

# ============================================================
# HOUSE TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS house (
    house_id TEXT PRIMARY KEY,
    house_name TEXT NOT NULL,
    location TEXT,
    owner_name TEXT,
    appliance_count INTEGER,
    created_at TEXT
)
""")

# ============================================================
# APPLIANCE TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS appliances (
    appliance_id TEXT PRIMARY KEY,
    house_id TEXT NOT NULL,
    appliance_name TEXT NOT NULL,
    appliance_type TEXT,
    sensor_id TEXT,
    rated_power_w REAL,
    status TEXT,
    created_at TEXT,
    FOREIGN KEY (house_id) REFERENCES house(house_id)
)
""")

# ============================================================
# RAW ENERGY TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS raw_energy (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    house_id TEXT NOT NULL,
    appliance_id TEXT NOT NULL,
    sensor_id TEXT,
    voltage REAL,
    current REAL,
    power_w REAL,
    energy_kwh REAL,
    temperature REAL,
    humidity REAL,
    status TEXT,
    source TEXT,
    FOREIGN KEY (house_id) REFERENCES house(house_id),
    FOREIGN KEY (appliance_id) REFERENCES appliances(appliance_id)
)
""")

# ============================================================
# PIPELINE LOG TABLE
# ============================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS ingestion_log (
    ingestion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingestion_time TEXT,
    source TEXT,
    rows_ingested INTEGER,
    status TEXT,
    message TEXT
)
""")

conn.commit()

print("[OK] House table created")
print("[OK] Appliance table created")
print("[OK] Raw energy table created")
print("[OK] Ingestion log table created")

# ============================================================
# INSERT HOUSE
# ============================================================

now = datetime.now().isoformat()

cursor.execute("""
INSERT OR REPLACE INTO house (
    house_id,
    house_name,
    location,
    owner_name,
    appliance_count,
    created_at
)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    house_id,
    house_name,
    house.get("location", ""),
    house.get("owner_name", ""),
    len(appliances),
    now
))

# ============================================================
# INSERT APPLIANCES
# ============================================================

for _, row in appliances.iterrows():

    cursor.execute("""
    INSERT OR REPLACE INTO appliances (
        appliance_id,
        house_id,
        appliance_name,
        appliance_type,
        sensor_id,
        rated_power_w,
        status,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        row["appliance_id"],
        house_id,
        row["appliance_name"],
        row["appliance_type"],
        row["sensor_id"],
        float(row["rated_power_w"]),
        row["status"],
        now
    ))

conn.commit()

print()
print("[OK] House registered")
print(f"[OK] {len(appliances)} appliances registered")

# ============================================================
# INGESTION FUNCTION
# ============================================================

def ingest_energy_data(data, source="hardware"):

    if isinstance(data, dict):
        data = [data]

    df = pd.DataFrame(data)

    required_columns = [
        "timestamp",
        "appliance_id",
        "voltage",
        "current",
        "power_w",
        "energy_kwh",
        "temperature",
        "humidity",
        "status"
    ]

    for column in required_columns:

        if column not in df.columns:
            df[column] = np.nan

    df["house_id"] = house_id

    df["sensor_id"] = df["appliance_id"].map(
        dict(
            zip(
                appliances["appliance_id"],
                appliances["sensor_id"]
            )
        )
    )

    df["source"] = source

    insert_columns = [
        "timestamp",
        "house_id",
        "appliance_id",
        "sensor_id",
        "voltage",
        "current",
        "power_w",
        "energy_kwh",
        "temperature",
        "humidity",
        "status",
        "source"
    ]

    df[insert_columns].to_sql(
        "raw_energy",
        conn,
        if_exists="append",
        index=False
    )

    cursor.execute("""
    INSERT INTO ingestion_log (
        ingestion_time,
        source,
        rows_ingested,
        status,
        message
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        source,
        len(df),
        "SUCCESS",
        "Energy data ingested successfully"
    ))

    conn.commit()

    return len(df)

# ============================================================
# SIMULATION MODE
# ============================================================

print()
print("=" * 70)
print("SIMULATED ENERGY DATA INGESTION")
print("=" * 70)

print()
print("Hardware is currently unavailable.")
print("Generating test sensor data...")
print()

np.random.seed(42)

simulation_rows = []

start_time = datetime.now()

for appliance_index, appliance in appliances.iterrows():

    appliance_id = appliance["appliance_id"]
    rated_power = float(appliance["rated_power_w"])

    # Generate 10 samples per appliance
    for i in range(10):

        timestamp = (
            start_time +
            timedelta(seconds=i * 5)
        )

        voltage = np.random.normal(
            230,
            2
        )

        # Simulated load
        utilization = np.random.uniform(
            0.10,
            0.90
        )

        power = rated_power * utilization

        current = power / voltage

        # Energy consumed during 5 seconds
        energy_kwh = (
            power * 5
        ) / (
            1000 * 3600
        )

        temperature = np.random.normal(
            25,
            2
        )

        humidity = np.random.normal(
            55,
            5
        )

        status = (
            "ON"
            if power > rated_power * 0.05
            else "OFF"
        )

        simulation_rows.append({
            "timestamp": timestamp.isoformat(),
            "appliance_id": appliance_id,
            "voltage": round(voltage, 3),
            "current": round(current, 5),
            "power_w": round(power, 3),
            "energy_kwh": round(energy_kwh, 8),
            "temperature": round(temperature, 3),
            "humidity": round(humidity, 3),
            "status": status
        })

rows_inserted = ingest_energy_data(
    simulation_rows,
    source="simulation"
)

print(
    f"[OK] Simulated rows ingested: {rows_inserted}"
)

# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("MODULE 14B VALIDATION")
print("=" * 70)

# House count
house_count = pd.read_sql_query(
    "SELECT COUNT(*) AS count FROM house",
    conn
).iloc[0]["count"]

# Appliance count
appliance_count = pd.read_sql_query(
    "SELECT COUNT(*) AS count FROM appliances",
    conn
).iloc[0]["count"]

# Energy rows
energy_count = pd.read_sql_query(
    "SELECT COUNT(*) AS count FROM raw_energy",
    conn
).iloc[0]["count"]

# NULL check
null_check = pd.read_sql_query("""
SELECT
    COUNT(*) AS total_rows,
    SUM(
        CASE
            WHEN timestamp IS NULL
              OR appliance_id IS NULL
              OR power_w IS NULL
            THEN 1
            ELSE 0
        END
    ) AS invalid_rows
FROM raw_energy
""", conn)

invalid_rows = int(
    null_check.iloc[0]["invalid_rows"]
    or 0
)

print()
print(f"House records       : {house_count}")
print(f"Appliance records   : {appliance_count}")
print(f"Energy records      : {energy_count}")
print(f"Invalid energy rows : {invalid_rows}")

# ============================================================
# ENERGY SUMMARY
# ============================================================

summary = pd.read_sql_query("""
SELECT
    appliance_id,
    COUNT(*) AS rows,
    ROUND(SUM(energy_kwh), 8) AS total_energy_kwh,
    ROUND(AVG(power_w), 3) AS average_power_w,
    ROUND(MAX(power_w), 3) AS maximum_power_w
FROM raw_energy
GROUP BY appliance_id
ORDER BY appliance_id
""", conn)

print()
print("ENERGY DATA SUMMARY")
print("-" * 70)

print(summary.to_string(index=False))

# ============================================================
# EXPORT RAW DATA
# ============================================================

raw_csv = os.path.join(
    raw_dir,
    "raw_energy_data.csv"
)

raw_df = pd.read_sql_query(
    """
    SELECT *
    FROM raw_energy
    """,
    conn
)

raw_df.to_csv(
    raw_csv,
    index=False
)

print()
print(f"[OK] Raw CSV exported: {raw_csv}")

# ============================================================
# EXPORT DATABASE SUMMARY
# ============================================================

database_summary = pd.DataFrame([{
    "house_id": house_id,
    "house_name": house_name,
    "appliance_count": appliance_count,
    "energy_rows": energy_count,
    "invalid_rows": invalid_rows,
    "database": DATABASE_FILE,
    "raw_csv": raw_csv,
    "created_at": datetime.now().isoformat()
}])

summary_file = os.path.join(
    HOUSE_DATA_DIR,
    f"{house_id}_database_summary.csv"
)

database_summary.to_csv(
    summary_file,
    index=False
)

# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()

# ============================================================
# FINAL OUTPUT
# ============================================================

print()
print("=" * 70)
print("MODULE 14B COMPLETE")
print("=" * 70)

print()
print("HOUSE DATABASE")
print("-" * 70)

print(f"House ID       : {house_id}")
print(f"Database       : {DATABASE_FILE}")
print(f"Appliances     : {appliance_count}")
print(f"Energy rows    : {energy_count}")

print()
print("OUTPUT FILES")
print("-" * 70)

print(f"Database:")
print(DATABASE_FILE)

print()
print(f"Raw energy CSV:")
print(raw_csv)

print()
print(f"Database summary:")
print(summary_file)

print()
print("=" * 70)