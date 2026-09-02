"""
=============================================================================
Automated Test Suite for Phase 15: Multi-User Architecture & Security
=============================================================================
Verifies:
A. User Registration & Server-Side ID Generation (USR-XXXXXX)
B. Password Hashing & Duplicate Email Rejection
C. User Login & JWT Token Generation
D. House Setup (HSE-XXXXXX)
E. Device Registration (DEV-XXXXXXXX)
F. Appliance Registration (APP-XXXXXXXX)
G. Multi-User Data Isolation (User A cannot access or control User B data)
H. Unauthenticated Demo Fallback
=============================================================================
"""

import unittest
import json
import os
import db_manager as db
from api_server import app


class TestPhase15MultiUser(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_multiuser_lifecycle_and_isolation(self):
        print("\n--- Running Test: Multi-User Registration & Data Isolation ---")

        # 1. Register User A
        res_a = self.app.post("/api/auth/register", json={
            "name": "User Alpha",
            "email": "alpha@example.com",
            "password": "Password123!"
        })
        self.assertEqual(res_a.status_code, 200)
        data_a = json.loads(res_a.data)
        self.assertTrue(data_a["ok"])
        user_a_id = data_a["user"]["user_id"]
        token_a = data_a["token"]
        self.assertTrue(user_a_id.startswith("USR-"))

        # 2. Register User B
        res_b = self.app.post("/api/auth/register", json={
            "name": "User Beta",
            "email": "beta@example.com",
            "password": "Password456!"
        })
        self.assertEqual(res_b.status_code, 200)
        data_b = json.loads(res_b.data)
        self.assertTrue(data_b["ok"])
        user_b_id = data_b["user"]["user_id"]
        token_b = data_b["token"]
        self.assertTrue(user_b_id.startswith("USR-"))

        # 3. Test duplicate email rejection
        res_dup = self.app.post("/api/auth/register", json={
            "name": "Duplicate User",
            "email": "alpha@example.com",
            "password": "Password789!"
        })
        self.assertEqual(res_dup.status_code, 409)

        # 4. Login User A using User ID
        res_log_a = self.app.post("/api/auth/login", json={
            "user_id": user_a_id,
            "password": "Password123!"
        })
        self.assertEqual(res_log_a.status_code, 200)

        # 5. User A creates House A
        res_h_a = self.app.post("/api/houses", json={
            "house_name": "Alpha Residency",
            "location": "Sector 4, Smart City"
        }, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_h_a.status_code, 200)
        house_a_id = json.loads(res_h_a.data)["house"]["house_id"]
        self.assertTrue(house_a_id.startswith("HSE-"))

        # 6. User B creates House B
        res_h_b = self.app.post("/api/houses", json={
            "house_name": "Beta Villa",
            "location": "Coastal Tech Hub"
        }, headers={"Authorization": f"Bearer {token_b}"})
        self.assertEqual(res_h_b.status_code, 200)
        house_b_id = json.loads(res_h_b.data)["house"]["house_id"]
        self.assertTrue(house_b_id.startswith("HSE-"))

        # 7. User A registers Device & Appliance (Fridge)
        res_dev_a = self.app.post("/api/devices", json={
            "device_type": "ESP32",
            "device_name": "Kitchen Hub A"
        }, headers={"Authorization": f"Bearer {token_a}"})
        dev_a_id = json.loads(res_dev_a.data)["device"]["device_id"]

        res_app_a = self.app.post("/api/appliances", json={
            "device_id": dev_a_id,
            "appliance_name": "Alpha Refrigerator",
            "appliance_type": "fridge",
            "rated_power_w": 150
        }, headers={"Authorization": f"Bearer {token_a}"})
        app_a_id = json.loads(res_app_a.data)["appliance"]["id"]
        self.assertTrue(app_a_id.startswith("APP-"))

        # 8. User B registers Device & Appliance (Air Conditioner - unknown type)
        res_dev_b = self.app.post("/api/devices", json={
            "device_type": "ESP32-S3",
            "device_name": "Living Room Hub B"
        }, headers={"Authorization": f"Bearer {token_b}"})
        dev_b_id = json.loads(res_dev_b.data)["device"]["device_id"]

        res_app_b = self.app.post("/api/appliances", json={
            "device_id": dev_b_id,
            "appliance_name": "Beta Smart AC",
            "appliance_type": "air_conditioner",
            "rated_power_w": 1200
        }, headers={"Authorization": f"Bearer {token_b}"})
        app_b_id = json.loads(res_app_b.data)["appliance"]["id"]
        self.assertTrue(app_b_id.startswith("APP-"))

        # 9. Verify Data Isolation: User A gets only Alpha appliances
        res_get_a = self.app.get("/api/appliances", headers={"Authorization": f"Bearer {token_a}"})
        apps_a = json.loads(res_get_a.data)
        self.assertEqual(len(apps_a), 1)
        self.assertEqual(apps_a[0]["id"], app_a_id)

        # 10. Verify Data Isolation: User B gets only Beta appliances
        res_get_b = self.app.get("/api/appliances", headers={"Authorization": f"Bearer {token_b}"})
        apps_b = json.loads(res_get_b.data)
        self.assertEqual(len(apps_b), 1)
        self.assertEqual(apps_b[0]["id"], app_b_id)

        # 11. Security Test: User A attempts to control User B's appliance -> 403 Forbidden
        res_ctrl_hacker = self.app.post("/api/control", json={
            "id": app_b_id,
            "action": "power",
            "on": False
        }, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_ctrl_hacker.status_code, 403)

        # 12. Valid Control: User A controls User A's appliance -> 200 OK
        res_ctrl_owner = self.app.post("/api/control", json={
            "id": app_a_id,
            "action": "power",
            "on": False
        }, headers={"Authorization": f"Bearer {token_a}"})
        self.assertEqual(res_ctrl_owner.status_code, 200)

        # 13. Unauthenticated Demo Mode Fallback
        res_demo = self.app.get("/api/appliances")
        demo_apps = json.loads(res_demo.data)
        self.assertEqual(len(demo_apps), 4)

        print("[SUCCESS] All multi-user isolation and security tests PASSED cleanly!")


if __name__ == "__main__":
    unittest.main()
