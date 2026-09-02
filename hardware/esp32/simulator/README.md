# Software ESP32 Hardware Simulator (Phase 17A)

The **Software ESP32 Telemetry Simulator** emulates a physical ESP32 microcontroller equipped with energy monitoring sensors (voltage, current, power factor, DHT22 temperature/humidity). It transmits real-time telemetry over HTTP POST to the Cognitive Energy Optimization System backend API.

---

## 🚀 Quick Usage

### Prerequisites
- Python 3.8+
- Active Flask backend running locally (`http://127.0.0.1:5000`) or deployed on Render (`https://energy-project1.onrender.com`).

### Command Line Flags
| Parameter | Description | Default |
| :--- | :--- | :--- |
| `--backend` | Target API base URL | `http://127.0.0.1:5000` |
| `--device-id` | Device ID (`DEV-XXXXXXXX`) | **Required** |
| `--device-secret` | Device secret token (`SEC-XXXXXXXX`) | **Required** |
| `--appliance-id` | Target Appliance ID (`APP-XXXXXXXX`) | **Required** |
| `--appliance-type` | Category (`fridge`, `laptop`, `fan`, `ac`, `generic`) | `fridge` |
| `--interval` | Transmission frequency in seconds | `5.0` |
| `--rated-power` | Rated power wattage for physics simulation | `150.0` |

---

## 💻 Execution Examples

### Local Development Test
```powershell
python hardware/esp32/simulator/esp32_simulator.py `
  --backend http://127.0.0.1:5000 `
  --device-id DEV-TEST01 `
  --device-secret SEC-TEST01 `
  --appliance-id APP-TEST01 `
  --appliance-type fridge `
  --interval 3
```

### Production Render Test
```powershell
python hardware/esp32/simulator/esp32_simulator.py `
  --backend https://energy-project1.onrender.com `
  --device-id DEV-PROD01 `
  --device-secret SEC-PROD01 `
  --appliance-id APP-PROD01 `
  --interval 5
```

---

## 🔒 Security & Verification

- **Device Token Auth**: Sends `X-Device-Id` and `X-Device-Secret` headers with every request.
- **Multi-User Isolation**: Backend verifies that the target `appliance_id` belongs to the registered device's house. Attempts to inject telemetry into another user's house return `403 Forbidden`.
- **Output Identification**: All console output is explicitly labeled as `[SIMULATED ESP32 TELEMETRY]`.
