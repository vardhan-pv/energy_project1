"""Integration checks for authenticated physical ESP32 API ingestion."""

import json
import unittest
import uuid

import db_manager as db
from api_server import app


class TestPhysicalEsp32Api(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        suffix = uuid.uuid4().hex[:8]
        registration = self.client.post(
            "/api/auth/register",
            json={"name": "Physical API Test", "email": f"esp32-{suffix}@example.com", "password": "TestPassword123!"},
        )
        self.assertEqual(registration.status_code, 200)
        self.token = registration.get_json()["token"]
        self.house_id = self.client.get(
            "/api/houses", headers={"Authorization": f"Bearer {self.token}"}
        ).get_json()[0]["id"]
        self.device = db.create_device(self.house_id, "ESP32", "Physical API Test Node")
        self.appliance = db.create_appliance(
            self.house_id, self.device["device_id"], "Test Controlled Load", "generic", 500.0
        )
        self.headers = {
            "X-Device-Id": self.device["device_id"],
            "X-Device-Secret": self.device["device_secret"],
            "User-Agent": "IREOS-ESP32-Physical/v1",
        }
        self.payload = {
            "device_id": self.device["device_id"],
            "house_id": self.house_id,
            "appliance_id": self.appliance["id"],
            "appliance": "Test Controlled Load",
            "voltage": 229.8,
            "current": 0.0,
            "power_w": 0.0,
            "energy_kwh": 0.001,
            "frequency": 50.0,
            "pf": 0.0,
            "temperature": 27.4,
            "humidity": 73.8,
            "relay_state": False,
            "status": "OFF",
        }

    def test_authenticated_sensor_ingestion_and_loop(self):
        missing_credentials = self.client.post("/api/telemetry", json=self.payload)
        self.assertEqual(missing_credentials.status_code, 401)
        bad_secret = self.client.post(
            "/api/telemetry", json=self.payload,
            headers={**self.headers, "X-Device-Secret": "incorrect"},
        )
        self.assertEqual(bad_secret.status_code, 401)

        accepted = self.client.post("/api/telemetry", json=self.payload, headers=self.headers)
        self.assertEqual(accepted.status_code, 200, accepted.get_data(as_text=True))
        response = accepted.get_json()
        self.assertEqual(response["source"], "esp32")
        self.assertEqual(response["power_w"], 0.0)

        with self.subTest("database persistence"):
            conn = db.get_db()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM telemetry WHERE device_id = ? ORDER BY telemetry_id DESC LIMIT 1;",
                (self.device["device_id"],),
            )
            saved = cursor.fetchone()
            conn.close()
            self.assertIsNotNone(saved)
            self.assertEqual(saved["source"], "esp32")
            self.assertEqual(saved["frequency"], 50.0)
            self.assertEqual(saved["power_factor"], 0.0)
            self.assertEqual(saved["relay_state"], 0)
            self.assertEqual(saved["power_w"], 0.0)

        live = self.client.get("/api/telemetry", headers={"Authorization": f"Bearer {self.token}"}).get_json()
        runtime = next(item for item in live if item["id"] == self.appliance["id"])
        self.assertTrue(runtime["isHardware"])
        self.assertEqual(runtime["source"], "esp32")
        self.assertEqual(runtime["powerW"], 0.0)
        self.assertEqual(runtime["frequencyHz"], 50.0)

        loop = self.client.get("/api/control-loop", headers={
            "X-Device-Id": self.device["device_id"],
            "X-Device-Secret": self.device["device_secret"],
        }).get_json()
        decision = next(item for item in loop if item["id"] == self.appliance["id"])
        self.assertEqual(decision["measuredPowerW"], 0.0)
        self.assertIn(decision["decisionSource"], {"baseline", "rl_model"})
        self.assertIn("nextAction", decision)

        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        health_data = health.get_json()
        self.assertEqual(health_data["database"]["status"], "ok")
        self.assertEqual(health_data["hardware_telemetry"]["latest"]["source"], "esp32")
        self.assertIn("model_artifacts_missing", health_data)

    def test_simulator_is_not_marked_as_physical_hardware(self):
        simulator_payload = {**self.payload, "power_w": 12.0}
        accepted = self.client.post(
            "/api/telemetry", json=simulator_payload,
            headers={**self.headers, "User-Agent": "ESP32-Hardware-Simulator/v1"},
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.get_json()["source"], "simulator")
        live = self.client.get("/api/telemetry", headers={"Authorization": f"Bearer {self.token}"}).get_json()
        runtime = next(item for item in live if item["id"] == self.appliance["id"])
        self.assertFalse(runtime["isHardware"])
        self.assertEqual(runtime["source"], "simulator")


if __name__ == "__main__":
    unittest.main()
