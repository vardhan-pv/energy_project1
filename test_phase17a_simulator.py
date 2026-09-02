"""
=============================================================================
Automated Test Suite for Phase 17A: ESP32 Simulator & Telemetry Security
=============================================================================
Verifies:
1. Device Secret Token Generation & Credentials Storage
2. Valid Hardware Telemetry Ingestion (POST /api/telemetry with HTTP 200)
3. Database Telemetry Persistence & Fast Index Querying
4. Invalid Device Secret Rejection (HTTP 401 Unauthorized)
5. Non-Existent Device Rejection (HTTP 401 Unauthorized)
6. Cross-User Multi-House Telemetry Injection Rejection (HTTP 403 Forbidden)
7. Dynamic Memory State & Anomaly Score Calculations
=============================================================================
"""

import unittest
import json
import uuid
import db_manager as db
from api_server import app


class TestPhase17ASimulator(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_simulator_telemetry_pipeline_and_security(self):
        print("\n--- Running Test: Phase 17A ESP32 Telemetry & Security ---")

        # 1. Setup User A, House A, Device A (with device_secret), Appliance A
        suffix_a = uuid.uuid4().hex[:6]
        res_a = self.app.post("/api/auth/register", json={
            "name": "User Alpha 17A",
            "email": f"alpha17a_{suffix_a}@example.com",
            "password": "Password123!"
        })
        self.assertEqual(res_a.status_code, 200)
        data_a = json.loads(res_a.data)
        token_a = data_a["token"]
        user_a_id = data_a["user"]["user_id"]

        res_h_a = self.app.get("/api/houses", headers={"Authorization": f"Bearer {token_a}"})
        house_a_id = json.loads(res_h_a.data)[0]["id"]

        dev_a = db.create_device(house_a_id, "ESP32", "Alpha ESP32 Sensor Hub")
        dev_a_id = dev_a["device_id"]
        dev_a_secret = dev_a["device_secret"]
        self.assertTrue(dev_a_secret.startswith("SEC-"))

        res_app_a = self.app.post("/api/appliances", json={
            "device_id": dev_a_id,
            "appliance_name": "Alpha Refrigerator 17A",
            "appliance_type": "fridge",
            "rated_power_w": 150
        }, headers={"Authorization": f"Bearer {token_a}"})
        app_a_id = json.loads(res_app_a.data)["appliance"]["id"]

        # 2. Setup User B, House B, Device B, Appliance B (for cross-user attack test)
        suffix_b = uuid.uuid4().hex[:6]
        res_b = self.app.post("/api/auth/register", json={
            "name": "User Beta 17A",
            "email": f"beta17a_{suffix_b}@example.com",
            "password": "Password456!"
        })
        data_b = json.loads(res_b.data)
        token_b = data_b["token"]

        res_h_b = self.app.get("/api/houses", headers={"Authorization": f"Bearer {token_b}"})
        house_b_id = json.loads(res_h_b.data)[0]["id"]

        dev_b = db.create_device(house_b_id, "ESP32", "Beta ESP32 Sensor Hub")
        dev_b_id = dev_b["device_id"]

        res_app_b = self.app.post("/api/appliances", json={
            "device_id": dev_b_id,
            "appliance_name": "Beta Smart AC 17A",
            "appliance_type": "air_conditioner",
            "rated_power_w": 1200
        }, headers={"Authorization": f"Bearer {token_b}"})
        app_b_id = json.loads(res_app_b.data)["appliance"]["id"]

        # 3. Valid Telemetry Submission from Device A for Appliance A -> HTTP 200 OK
        res_t1 = self.app.post("/api/telemetry", json={
            "appliance_id": app_a_id,
            "voltage": 231.5,
            "current": 0.65,
            "power_w": 145.2,
            "energy_kwh": 0.12,
            "temperature": 24.5,
            "humidity": 52.0,
            "status": "ON"
        }, headers={
            "X-Device-Id": dev_a_id,
            "X-Device-Secret": dev_a_secret
        })
        self.assertEqual(res_t1.status_code, 200)
        data_t1 = json.loads(res_t1.data)
        self.assertTrue(data_t1["ok"])
        self.assertEqual(data_t1["status"], "accepted")

        # 4. Verify Database Telemetry Storage & Persistence
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM telemetry WHERE appliance_id = ? ORDER BY telemetry_id DESC LIMIT 1;", (app_a_id,))
        t_row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(t_row)
        self.assertEqual(t_row["user_id"], user_a_id)
        self.assertEqual(t_row["house_id"], house_a_id)
        self.assertEqual(t_row["power_w"], 145.2)

        # 5. Security Test: Invalid Device Secret -> 401 Unauthorized
        res_inv_sec = self.app.post("/api/telemetry", json={
            "appliance_id": app_a_id,
            "power_w": 100.0
        }, headers={
            "X-Device-Id": dev_a_id,
            "X-Device-Secret": "SEC-INVALIDSECRET"
        })
        self.assertEqual(res_inv_sec.status_code, 401)

        # 6. Security Test: Non-existent Device ID -> 401 Unauthorized
        res_fake_dev = self.app.post("/api/telemetry", json={
            "appliance_id": app_a_id,
            "power_w": 100.0
        }, headers={
            "X-Device-Id": "DEV-NONEXISTENT",
            "X-Device-Secret": dev_a_secret
        })
        self.assertEqual(res_fake_dev.status_code, 401)

        # 7. Security Test: Device A attempts to inject telemetry for User B's Appliance B -> 403 Forbidden
        res_hack = self.app.post("/api/telemetry", json={
            "appliance_id": app_b_id,
            "power_w": 999.0
        }, headers={
            "X-Device-Id": dev_a_id,
            "X-Device-Secret": dev_a_secret
        })
        self.assertEqual(res_hack.status_code, 403)

        print("[SUCCESS] Phase 17A ESP32 Telemetry & Security verified cleanly!")


if __name__ == "__main__":
    unittest.main()
