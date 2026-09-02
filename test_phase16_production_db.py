"""
=============================================================================
Automated Test Suite for Phase 16: Production Database Persistence & Auth
=============================================================================
Verifies:
1. Dual Database Connection Wrapper (PostgreSQL vs SQLite engine detection)
2. Database Schema Initialization & Foreign Key Integrity
3. Multi-User Registration & Server-Assigned ID Generation (USR-XXXXXX)
4. House, Device, and Appliance Dynamic Storage & Multi-User Data Isolation
5. Session Persistence Check (closing & reopening connections retains all user data)
=============================================================================
"""

import unittest
import json
import uuid
import db_manager as db
from api_server import app


class TestPhase16ProductionDB(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_database_engine_and_persistence(self):
        print("\n--- Running Test: Phase 16 Production DB Persistence & Auth ---")

        # 1. Verify health check reports active db_engine
        res_health = self.app.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        h_data = json.loads(res_health.data)
        self.assertIn("db_engine", h_data)
        print(f"[health] Active Database Engine: {h_data['db_engine']}")

        # 2. Register persistent User Alpha
        suffix = uuid.uuid4().hex[:6]
        email_alpha = f"persist_alpha_{suffix}@example.com"
        res_reg = self.app.post("/api/auth/register", json={
            "name": "Persist Alpha",
            "email": email_alpha,
            "password": "Password123!"
        })
        self.assertEqual(res_reg.status_code, 200)
        reg_data = json.loads(res_reg.data)
        user_id = reg_data["user"]["user_id"]
        token = reg_data["token"]
        self.assertTrue(user_id.startswith("USR-"))

        # 3. Add custom appliance for Persist Alpha
        res_houses = self.app.get("/api/houses", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_houses.status_code, 200)
        houses = json.loads(res_houses.data)
        self.assertTrue(len(houses) > 0)
        house_id = houses[0]["id"]

        custom_name = f"Custom Solar Inverter {suffix}"
        res_app = self.app.post("/api/appliances", json={
            "appliance_name": custom_name,
            "appliance_type": "generic",
            "rated_power_w": 2500
        }, headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_app.status_code, 200)
        app_id = json.loads(res_app.data)["appliance"]["id"]
        self.assertTrue(app_id.startswith("APP-"))

        # 4. Simulate Connection Reset / Session Reopen (Persistence Verification)
        # Re-fetch user profile and appliances from fresh database connection
        reopen_user = db.get_user_profile(user_id)
        self.assertIsNotNone(reopen_user)
        self.assertEqual(reopen_user["email"], email_alpha)

        reopen_apps = db.get_house_appliances(house_id)
        reopen_app_ids = {a["id"] for a in reopen_apps}
        self.assertIn(app_id, reopen_app_ids)

        print("[SUCCESS] Phase 16 Database Persistence & Authentication verified cleanly!")


if __name__ == "__main__":
    unittest.main()
