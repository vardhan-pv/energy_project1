"""
=============================================================================
IREOS: SQLite to Neon PostgreSQL Migration Utility
=============================================================================
Migrates all tables, schemas, relations, and data from local SQLite
(ceos_database.db) to Neon PostgreSQL (ireos_db) safely and idempotently.

Guarantees:
1. Preserves users, houses, devices, appliances, and telemetry tables.
2. Preserves all server-assigned IDs and relations.
3. Preserves telemetry IDs and synchronizes the PostgreSQL serial sequence.
4. Transactional: Complete rollback on any failure.
5. Idempotent: Safe to rerun without creating duplicate rows or key errors.
6. Verification: Checks row counts and foreign-key integrity post-migration.
7. Read-Only on SQLite: Never modifies or deletes the source database.
8. Privacy: Never logs or prints password hashes or device secrets.
=============================================================================
"""

import os
import sys
import argparse
import sqlite3
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
except ImportError:
    psycopg2 = None

def _load_env():
    base_dir = Path(__file__).resolve().parent
    for fname in [".env.local", ".env"]:
        p = base_dir / fname
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_env()


# ---------------------------------------------------------------------------
# Helpers & Security Sanitizers
# ---------------------------------------------------------------------------
def mask_db_url(url: str) -> str:
    """Mask password in PostgreSQL URL for secure display."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        if parsed.password:
            netloc = f"{parsed.username}:******@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return "postgresql://***:***@***"


def sanitize_postgres_url(url: str) -> str:
    """Ensure standard postgresql:// scheme and sslmode=require for Neon."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "sslmode" not in qs:
        qs["sslmode"] = ["require"]
        new_query = urlencode(qs, doseq=True)
        url = urlunparse(parsed._replace(query=new_query))
    return url


# ---------------------------------------------------------------------------
# Schema Initialization
# ---------------------------------------------------------------------------
SCHEMA_STATEMENTS = [
    # 1. users
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 2. houses
    """
    CREATE TABLE IF NOT EXISTS houses (
        house_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        house_name TEXT NOT NULL,
        location TEXT,
        status TEXT DEFAULT 'ONLINE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 3. devices
    """
    CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        house_id TEXT NOT NULL REFERENCES houses(house_id) ON DELETE CASCADE,
        device_type TEXT NOT NULL,
        device_name TEXT,
        mac_address TEXT,
        device_secret TEXT,
        status TEXT DEFAULT 'ONLINE',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 4. appliances
    """
    CREATE TABLE IF NOT EXISTS appliances (
        appliance_id TEXT PRIMARY KEY,
        house_id TEXT NOT NULL REFERENCES houses(house_id) ON DELETE CASCADE,
        device_id TEXT REFERENCES devices(device_id) ON DELETE SET NULL,
        appliance_name TEXT NOT NULL,
        appliance_type TEXT NOT NULL,
        rated_power_w REAL NOT NULL,
        status TEXT DEFAULT 'ON',
        mode TEXT DEFAULT 'maintain',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    # 5. telemetry
    """
    CREATE TABLE IF NOT EXISTS telemetry (
        telemetry_id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP NOT NULL,
        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        house_id TEXT NOT NULL REFERENCES houses(house_id) ON DELETE CASCADE,
        appliance_id TEXT NOT NULL REFERENCES appliances(appliance_id) ON DELETE CASCADE,
        voltage REAL,
        current REAL,
        power_w REAL,
        energy_kwh REAL,
        temperature REAL,
        humidity REAL,
        status TEXT,
        anomaly_score REAL,
        frequency REAL,
        power_factor REAL,
        relay_state INTEGER,
        device_id TEXT,
        source TEXT,
        rl_action_code INTEGER,
        rl_action TEXT
    );
    """,
    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_user_time ON telemetry(user_id, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_house_time ON telemetry(house_id, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_appliance_time ON telemetry(appliance_id, timestamp);"
]


def init_target_schema(pg_cursor):
    """Create target tables and indexes if not already present."""
    print("[1/6] Initializing PostgreSQL schema and indexes...")
    for stmt in SCHEMA_STATEMENTS:
        pg_cursor.execute(stmt)
    print("      [OK] Schema and indexes verified.")


# ---------------------------------------------------------------------------
# Table Migration Handlers (Idempotent UPSERTs)
# ---------------------------------------------------------------------------
def migrate_users(sqlite_cursor, pg_cursor):
    sqlite_cursor.execute("SELECT user_id, name, email, password_hash, status, created_at FROM users;")
    rows = sqlite_cursor.fetchall()
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO users (user_id, name, email, password_hash, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            password_hash = EXCLUDED.password_hash,
            status = EXCLUDED.status,
            created_at = EXCLUDED.created_at;
    """
    for r in rows:
        pg_cursor.execute(insert_sql, (
            r["user_id"], r["name"], r["email"], r["password_hash"], r["status"], r["created_at"]
        ))
    return len(rows)


def migrate_houses(sqlite_cursor, pg_cursor):
    sqlite_cursor.execute("SELECT house_id, user_id, house_name, location, status, created_at FROM houses;")
    rows = sqlite_cursor.fetchall()
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO houses (house_id, user_id, house_name, location, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (house_id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            house_name = EXCLUDED.house_name,
            location = EXCLUDED.location,
            status = EXCLUDED.status,
            created_at = EXCLUDED.created_at;
    """
    for r in rows:
        pg_cursor.execute(insert_sql, (
            r["house_id"], r["user_id"], r["house_name"], r["location"], r["status"], r["created_at"]
        ))
    return len(rows)


def migrate_devices(sqlite_cursor, pg_cursor):
    sqlite_cursor.execute("""
        SELECT device_id, house_id, device_type, device_name, mac_address, device_secret, status, registered_at
        FROM devices;
    """)
    rows = sqlite_cursor.fetchall()
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO devices (device_id, house_id, device_type, device_name, mac_address, device_secret, status, registered_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (device_id) DO UPDATE SET
            house_id = EXCLUDED.house_id,
            device_type = EXCLUDED.device_type,
            device_name = EXCLUDED.device_name,
            mac_address = EXCLUDED.mac_address,
            device_secret = EXCLUDED.device_secret,
            status = EXCLUDED.status,
            registered_at = EXCLUDED.registered_at;
    """
    for r in rows:
        pg_cursor.execute(insert_sql, (
            r["device_id"], r["house_id"], r["device_type"], r["device_name"],
            r["mac_address"], r["device_secret"], r["status"], r["registered_at"]
        ))
    return len(rows)


def migrate_appliances(sqlite_cursor, pg_cursor):
    sqlite_cursor.execute("""
        SELECT appliance_id, house_id, device_id, appliance_name, appliance_type, rated_power_w, status, mode, created_at
        FROM appliances;
    """)
    rows = sqlite_cursor.fetchall()
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO appliances (appliance_id, house_id, device_id, appliance_name, appliance_type, rated_power_w, status, mode, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (appliance_id) DO UPDATE SET
            house_id = EXCLUDED.house_id,
            device_id = EXCLUDED.device_id,
            appliance_name = EXCLUDED.appliance_name,
            appliance_type = EXCLUDED.appliance_type,
            rated_power_w = EXCLUDED.rated_power_w,
            status = EXCLUDED.status,
            mode = EXCLUDED.mode,
            created_at = EXCLUDED.created_at;
    """
    for r in rows:
        pg_cursor.execute(insert_sql, (
            r["appliance_id"], r["house_id"], r["device_id"], r["appliance_name"],
            r["appliance_type"], r["rated_power_w"], r["status"], r["mode"], r["created_at"]
        ))
    return len(rows)


def migrate_telemetry(sqlite_cursor, pg_cursor):
    sqlite_cursor.execute("""
        SELECT telemetry_id, timestamp, user_id, house_id, appliance_id, voltage, current, power_w, energy_kwh,
               temperature, humidity, status, anomaly_score, frequency, power_factor, relay_state,
               device_id, source, rl_action_code, rl_action
        FROM telemetry;
    """)
    rows = sqlite_cursor.fetchall()
    if not rows:
        return 0

    insert_sql = """
        INSERT INTO telemetry (
            telemetry_id, timestamp, user_id, house_id, appliance_id, voltage, current, power_w, energy_kwh,
            temperature, humidity, status, anomaly_score, frequency, power_factor, relay_state,
            device_id, source, rl_action_code, rl_action
        )
        VALUES %s
        ON CONFLICT (telemetry_id) DO UPDATE SET
            timestamp = EXCLUDED.timestamp,
            user_id = EXCLUDED.user_id,
            house_id = EXCLUDED.house_id,
            appliance_id = EXCLUDED.appliance_id,
            voltage = EXCLUDED.voltage,
            current = EXCLUDED.current,
            power_w = EXCLUDED.power_w,
            energy_kwh = EXCLUDED.energy_kwh,
            temperature = EXCLUDED.temperature,
            humidity = EXCLUDED.humidity,
            status = EXCLUDED.status,
            anomaly_score = EXCLUDED.anomaly_score,
            frequency = EXCLUDED.frequency,
            power_factor = EXCLUDED.power_factor,
            relay_state = EXCLUDED.relay_state,
            device_id = EXCLUDED.device_id,
            source = EXCLUDED.source,
            rl_action_code = EXCLUDED.rl_action_code,
            rl_action = EXCLUDED.rl_action;
    """
    data = [
        (
            r["telemetry_id"], r["timestamp"], r["user_id"], r["house_id"], r["appliance_id"],
            r["voltage"], r["current"], r["power_w"], r["energy_kwh"], r["temperature"], r["humidity"],
            r["status"], r["anomaly_score"], r["frequency"], r["power_factor"], r["relay_state"],
            r["device_id"], r["source"], r["rl_action_code"], r["rl_action"]
        )
        for r in rows
    ]
    execute_values(pg_cursor, insert_sql, data, page_size=100)
    return len(rows)


def reset_telemetry_sequence(pg_cursor):
    """Synchronize PostgreSQL SERIAL sequence to MAX(telemetry_id)."""
    pg_cursor.execute("""
        SELECT setval(
            pg_get_serial_sequence('telemetry', 'telemetry_id'),
            COALESCE((SELECT MAX(telemetry_id) FROM telemetry), 1)
        );
    """)
    current_val = pg_cursor.fetchone()[0]
    print(f"      [OK] PostgreSQL telemetry_id sequence reset to: {current_val}")


# ---------------------------------------------------------------------------
# Verification & Integrity Checks
# ---------------------------------------------------------------------------
def verify_migration(sqlite_conn, pg_cursor):
    """Verify that row counts match exactly and foreign keys are valid."""
    print("[4/6] Verifying table row counts...")
    tables = ["users", "houses", "devices", "appliances", "telemetry"]
    sc = sqlite_conn.cursor()

    all_counts_match = True
    for table in tables:
        sc.execute(f"SELECT COUNT(*) FROM {table};")
        s_count = sc.fetchone()[0]

        pg_cursor.execute(f"SELECT COUNT(*) FROM {table};")
        pg_count = pg_cursor.fetchone()[0]

        status = "[MATCH]" if s_count == pg_count else "[MISMATCH]"
        print(f"      - {table:12s}: Source SQLite = {s_count:5d} | Target Neon = {pg_count:5d}  [{status}]")
        if s_count != pg_count:
            all_counts_match = False

    if not all_counts_match:
        raise ValueError("Verification failed: Row counts between source and destination do not match.")

    print("[5/6] Verifying relational integrity on target...")
    # 1. Orphan houses
    pg_cursor.execute("SELECT COUNT(*) FROM houses h LEFT JOIN users u ON h.user_id = u.user_id WHERE u.user_id IS NULL;")
    orphan_houses = pg_cursor.fetchone()[0]

    # 2. Orphan devices
    pg_cursor.execute("SELECT COUNT(*) FROM devices d LEFT JOIN houses h ON d.house_id = h.house_id WHERE h.house_id IS NULL;")
    orphan_devices = pg_cursor.fetchone()[0]

    # 3. Orphan appliances
    pg_cursor.execute("SELECT COUNT(*) FROM appliances a LEFT JOIN houses h ON a.house_id = h.house_id WHERE h.house_id IS NULL;")
    orphan_apps = pg_cursor.fetchone()[0]

    # 4. Appliance devices pointing to non-existent device
    pg_cursor.execute("""
        SELECT COUNT(*) FROM appliances a
        LEFT JOIN devices d ON a.device_id = d.device_id
        WHERE a.device_id IS NOT NULL AND d.device_id IS NULL;
    """)
    invalid_app_devs = pg_cursor.fetchone()[0]

    # 5. Orphan telemetry
    pg_cursor.execute("""
        SELECT COUNT(*) FROM telemetry t
        LEFT JOIN users u ON t.user_id = u.user_id
        LEFT JOIN houses h ON t.house_id = h.house_id
        LEFT JOIN appliances a ON t.appliance_id = a.appliance_id
        WHERE u.user_id IS NULL OR h.house_id IS NULL OR a.appliance_id IS NULL;
    """)
    orphan_telemetry = pg_cursor.fetchone()[0]

    print(f"      - Orphan houses:            {orphan_houses}")
    print(f"      - Orphan devices:           {orphan_devices}")
    print(f"      - Orphan appliances:        {orphan_apps}")
    print(f"      - Invalid appliance-device: {invalid_app_devs}")
    print(f"      - Orphan telemetry rows:    {orphan_telemetry}")

    if any([orphan_houses, orphan_devices, orphan_apps, invalid_app_devs, orphan_telemetry]):
        raise ValueError("Relational integrity verification failed on target database.")

    print("      [OK] Foreign key relationships and integrity verified cleanly.")


# ---------------------------------------------------------------------------
# Migration Controller
# ---------------------------------------------------------------------------
def run_migration(sqlite_path: str, target_url: str, dry_run: bool = False):
    if not psycopg2:
        print("[ERROR] psycopg2 or psycopg2-binary is required. Run 'pip install psycopg2-binary'.")
        sys.exit(1)

    sqlite_file = Path(sqlite_path).resolve()
    if not sqlite_file.exists():
        print(f"[ERROR] Source SQLite database not found at: {sqlite_file}")
        sys.exit(1)

    clean_target_url = sanitize_postgres_url(target_url)
    masked_url = mask_db_url(clean_target_url)

    print("=" * 75)
    print("IREOS DATABASE MIGRATION: SQLite -> Neon PostgreSQL")
    print("=" * 75)
    print(f"Source Database: {sqlite_file}")
    print(f"Target Database: {masked_url}")
    print(f"Execution Mode:  {'DRY RUN (no commit)' if dry_run else 'LIVE MIGRATION'}")
    print("-" * 75)

    # Connect to SQLite in read-only URI mode to guarantee zero modification
    sqlite_uri = f"file:{sqlite_file.as_posix()}?mode=ro"
    try:
        sqlite_conn = sqlite3.connect(sqlite_uri, uri=True)
        sqlite_conn.row_factory = sqlite3.Row
    except Exception as exc:
        print(f"[ERROR] Failed to open SQLite database in read-only mode: {exc}")
        sys.exit(1)

    # Connect to Neon PostgreSQL
    try:
        pg_conn = psycopg2.connect(clean_target_url)
        pg_conn.autocommit = False  # Explicit transactional control
        pg_cursor = pg_conn.cursor()
    except Exception as exc:
        print(f"[ERROR] Failed to connect to Neon PostgreSQL target: {exc}")
        sqlite_conn.close()
        sys.exit(1)

    try:
        # Step 1: Initialize tables and indexes
        init_target_schema(pg_cursor)

        # Step 2: Migrate records preserving PKs and relations
        print("[2/6] Migrating records in relational order...")
        n_users = migrate_users(sqlite_conn.cursor(), pg_cursor)
        print(f"      - users:      {n_users:4d} rows migrated")

        n_houses = migrate_houses(sqlite_conn.cursor(), pg_cursor)
        print(f"      - houses:     {n_houses:4d} rows migrated")

        n_devices = migrate_devices(sqlite_conn.cursor(), pg_cursor)
        print(f"      - devices:    {n_devices:4d} rows migrated")

        n_appliances = migrate_appliances(sqlite_conn.cursor(), pg_cursor)
        print(f"      - appliances: {n_appliances:4d} rows migrated")

        n_telemetry = migrate_telemetry(sqlite_conn.cursor(), pg_cursor)
        print(f"      - telemetry:  {n_telemetry:4d} rows migrated")

        # Step 3: Synchronize PostgreSQL serial sequence
        print("[3/6] Synchronizing telemetry serial sequence...")
        reset_telemetry_sequence(pg_cursor)

        # Step 4 & 5: Verify counts and integrity
        verify_migration(sqlite_conn, pg_cursor)

        # Step 6: Commit or rollback
        if dry_run:
            pg_conn.rollback()
            print("[6/6] Dry run complete. Transaction rolled back successfully.")
        else:
            pg_conn.commit()
            print("[6/6] Transaction committed successfully to Neon PostgreSQL!")

        print("-" * 75)
        print("MIGRATION COMPLETED SUCCESSFULLY.")
        print("=" * 75)

    except Exception as exc:
        print("\n" + "!" * 75)
        print(f"[MIGRATION FAILED] Rolling back all changes: {exc}")
        print("!" * 75)
        try:
            if pg_conn and not pg_conn.closed:
                pg_conn.rollback()
        except Exception:
            pass
        sys.exit(1)
    finally:
        try:
            sqlite_conn.close()
        except Exception:
            pass
        try:
            if pg_conn and not pg_conn.closed:
                pg_conn.close()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Migrate IREOS SQLite database to Neon PostgreSQL")
    parser.add_argument(
        "--target-url",
        default=os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL"),
        help="Neon PostgreSQL connection URL (e.g., postgresql://user:pass@ep-xyz.neon.tech/ireos_db?sslmode=require)"
    )
    parser.add_argument(
        "--sqlite-path",
        default="ceos_database.db",
        help="Path to source ceos_database.db file (default: ceos_database.db)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migration and rollback without persisting changes"
    )
    args = parser.parse_args()

    if not args.target_url:
        parser.error(
            "Target PostgreSQL URL must be provided via --target-url or DATABASE_URL / NEON_DATABASE_URL environment variable."
        )

    run_migration(args.sqlite_path, args.target_url, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
