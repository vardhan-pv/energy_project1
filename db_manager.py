"""
=============================================================================
Cognitive Energy Optimization System — Database & Entity Manager
=============================================================================
Provides SQLite storage for Phase 15 multi-user architecture:
- Users (`users`)
- Digital Houses (`houses`)
- Hardware Devices (`devices`)
- Dynamic Appliances (`appliances`)
- Multi-User Telemetry (`telemetry`)

Generates server-side secure IDs (USR-XXXXXX, HSE-XXXXXX, DEV-XXXXXXXX, APP-XXXXXXXX)
and handles password hashing & JWT token verification.
=============================================================================
"""

import os
import sqlite3
import secrets
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ceos_database.db"
JWT_SECRET = os.environ.get("JWT_SECRET", "ceos-super-secret-key-2026-phase15-production-token")
JWT_ALGORITHM = "HS256"


def get_db():
    """Get a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Houses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS houses (
        house_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        house_name TEXT NOT NULL,
        location TEXT,
        status TEXT DEFAULT 'ONLINE',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # 3. Devices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        house_id TEXT NOT NULL,
        device_type TEXT NOT NULL,
        device_name TEXT,
        mac_address TEXT,
        status TEXT DEFAULT 'ONLINE',
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (house_id) REFERENCES houses(house_id) ON DELETE CASCADE
    );
    """)

    # 4. Appliances table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appliances (
        appliance_id TEXT PRIMARY KEY,
        house_id TEXT NOT NULL,
        device_id TEXT,
        appliance_name TEXT NOT NULL,
        appliance_type TEXT NOT NULL,
        rated_power_w REAL NOT NULL,
        status TEXT DEFAULT 'ON',
        mode TEXT DEFAULT 'maintain',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (house_id) REFERENCES houses(house_id) ON DELETE CASCADE,
        FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE SET NULL
    );
    """)

    # 5. Telemetry table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry (
        telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME NOT NULL,
        user_id TEXT NOT NULL,
        house_id TEXT NOT NULL,
        appliance_id TEXT NOT NULL,
        voltage REAL,
        current REAL,
        power_w REAL,
        energy_kwh REAL,
        temperature REAL,
        humidity REAL,
        status TEXT,
        anomaly_score REAL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (house_id) REFERENCES houses(house_id) ON DELETE CASCADE,
        FOREIGN KEY (appliance_id) REFERENCES appliances(appliance_id) ON DELETE CASCADE
    );
    """)

    # Create indexes for telemetry fast querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_time ON telemetry(user_id, timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_house_time ON telemetry(house_id, timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_appliance_time ON telemetry(appliance_id, timestamp);")

    conn.commit()
    conn.close()
    print("[db] Database schema initialized successfully.")


# ---------------------------------------------------------------------------
# Cryptographic ID Generators
# ---------------------------------------------------------------------------
def generate_user_id() -> str:
    return "USR-" + secrets.token_hex(3).upper()


def generate_house_id() -> str:
    return "HSE-" + secrets.token_hex(3).upper()


def generate_device_id() -> str:
    return "DEV-" + secrets.token_hex(4).upper()


def generate_appliance_id() -> str:
    return "APP-" + secrets.token_hex(4).upper()


# ---------------------------------------------------------------------------
# JWT Token Helpers
# ---------------------------------------------------------------------------
from datetime import datetime, timezone

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# User Authentication & CRUD
# ---------------------------------------------------------------------------
def register_user(name: str, email: str, password: str) -> dict:
    """Register a new user and generate USR-XXXXXX ID."""
    conn = get_db()
    cursor = conn.cursor()

    email_clean = email.strip().lower()
    cursor.execute("SELECT user_id FROM users WHERE email = ?;", (email_clean,))
    if cursor.fetchone():
        conn.close()
        raise ValueError("User with this email already exists.")

    user_id = generate_user_id()
    pwd_hash = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (user_id, name, email, password_hash) VALUES (?, ?, ?, ?);",
        (user_id, name.strip(), email_clean, pwd_hash),
    )
    conn.commit()
    conn.close()

    token = create_token(user_id)
    return {"user_id": user_id, "name": name.strip(), "email": email_clean, "token": token}


def authenticate_user(identifier: str, password: str) -> dict:
    """Authenticate via User ID or Email + Password."""
    conn = get_db()
    cursor = conn.cursor()

    clean_id = identifier.strip()

    cursor.execute(
        "SELECT user_id, name, email, password_hash FROM users WHERE user_id = ? OR email = ?;",
        (clean_id, clean_id.lower()),
    )
    row = cursor.fetchone()
    conn.close()

    if not row or not check_password_hash(row["password_hash"], password):
        raise ValueError("Invalid User ID/email or password.")

    token = create_token(row["user_id"])
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "token": token,
    }


def get_user_profile(user_id: str) -> dict:
    """Retrieve user details and associated digital house/devices."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, name, email, status, created_at FROM users WHERE user_id = ?;", (user_id,))
    u_row = cursor.fetchone()
    if not u_row:
        conn.close()
        return None

    user_dict = dict(u_row)

    # Fetch primary house
    cursor.execute("SELECT * FROM houses WHERE user_id = ? LIMIT 1;", (user_id,))
    h_row = cursor.fetchone()
    conn.close()

    user_dict["house"] = dict(h_row) if h_row else None
    return user_dict


# ---------------------------------------------------------------------------
# House CRUD
# ---------------------------------------------------------------------------
def create_house(user_id: str, house_name: str, location: str) -> dict:
    """Create a digital house associated with the authenticated user."""
    conn = get_db()
    cursor = conn.cursor()

    house_id = generate_house_id()
    cursor.execute(
        "INSERT INTO houses (house_id, user_id, house_name, location) VALUES (?, ?, ?, ?);",
        (house_id, user_id, house_name.strip(), location.strip()),
    )
    conn.commit()
    conn.close()

    return {
        "house_id": house_id,
        "user_id": user_id,
        "house_name": house_name.strip(),
        "location": location.strip(),
        "status": "ONLINE",
        "dataStatus": "AVAILABLE",
    }


def get_user_houses(user_id: str) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM houses WHERE user_id = ?;", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["house_id"],
            "house_id": r["house_id"],
            "name": r["house_name"],
            "location": r["location"],
            "status": r["status"],
            "dataStatus": "AVAILABLE",
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Device CRUD
# ---------------------------------------------------------------------------
def create_device(house_id: str, device_type: str, device_name: str, mac_address: str = None) -> dict:
    conn = get_db()
    cursor = conn.cursor()

    device_id = generate_device_id()
    cursor.execute(
        "INSERT INTO devices (device_id, house_id, device_type, device_name, mac_address) VALUES (?, ?, ?, ?, ?);",
        (device_id, house_id, device_type, device_name, mac_address),
    )
    conn.commit()
    conn.close()

    return {
        "device_id": device_id,
        "house_id": house_id,
        "device_type": device_type,
        "device_name": device_name,
        "mac_address": mac_address,
        "status": "ONLINE",
    }


def get_house_devices(house_id: str) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices WHERE house_id = ?;", (house_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Appliance CRUD
# ---------------------------------------------------------------------------
def create_appliance(
    house_id: str,
    device_id: str,
    appliance_name: str,
    appliance_type: str,
    rated_power_w: float,
) -> dict:
    conn = get_db()
    cursor = conn.cursor()

    appliance_id = generate_appliance_id()
    cursor.execute(
        """
        INSERT INTO appliances (appliance_id, house_id, device_id, appliance_name, appliance_type, rated_power_w)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (appliance_id, house_id, device_id, appliance_name, appliance_type, rated_power_w),
    )
    conn.commit()
    conn.close()

    return {
        "id": appliance_id,
        "appliance_id": appliance_id,
        "house_id": house_id,
        "device_id": device_id,
        "name": appliance_name,
        "type": appliance_type,
        "ratedPowerW": rated_power_w,
        "status": "ON",
        "mode": "maintain",
    }


def get_house_appliances(house_id: str) -> list[dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appliances WHERE house_id = ?;", (house_id,))
    rows = cursor.fetchall()
    conn.close()

    icon_map = {
        "laptop": "laptop",
        "kitchen_lights": "lightbulb",
        "lights": "lightbulb",
        "office_fan": "fan",
        "fan": "fan",
        "fridge": "refrigerator",
        "refrigerator": "refrigerator",
        "ac": "air-conditioner",
        "air_conditioner": "air-conditioner",
        "tv": "tv",
    }

    result = []
    for r in rows:
        aid = r["appliance_id"]
        atype = r["appliance_type"] or "generic"
        rated = r["rated_power_w"] or 100.0
        icon = icon_map.get(atype.lower(), "plug")

        # Determine model metadata
        known_types = ["laptop", "kitchen_lights", "office_fan", "fridge"]
        if atype.lower() in known_types:
            model_info = {
                "name": f"{atype.replace('_', ' ').title()} Trained Model",
                "version": "v1.0-trained",
                "trainedOn": "UK-DALE real household dataset",
                "accuracyPct": 95.0,
            }
        else:
            model_info = {
                "name": "Generic Adaptive Baseline Model",
                "version": "v1.0-generic",
                "trainedOn": "Dynamic baseline feature adaptation",
                "accuracyPct": 88.0,
            }

        result.append({
            "id": aid,
            "name": r["appliance_name"],
            "room": "General",
            "icon": icon,
            "ratedPowerW": rated,
            "minPowerW": 0,
            "maxPowerW": round(rated * 1.5),
            "criticalAlwaysOn": (atype.lower() in ["fridge", "refrigerator"]),
            "hasTemperature": (atype.lower() in ["laptop", "office_fan", "fan", "fridge", "refrigerator", "ac"]),
            "description": f"Registered {r['appliance_name']} ({atype}).",
            "model": model_info,
            "status": r["status"],
            "mode": r["mode"],
        })
    return result


def update_appliance_state(appliance_id: str, status: str = None, mode: str = None) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    vals = []
    if status is not None:
        fields.append("status = ?")
        vals.append(status)
    if mode is not None:
        fields.append("mode = ?")
        vals.append(mode)
    if not fields:
        conn.close()
        return False
    vals.append(appliance_id)
    query = f"UPDATE appliances SET {', '.join(fields)} WHERE appliance_id = ?;"
    cursor.execute(query, tuple(vals))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


# Initialize database upon module import
init_db()
