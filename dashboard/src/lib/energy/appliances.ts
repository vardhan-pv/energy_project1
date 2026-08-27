import type { ApplianceId, ApplianceProfile } from "./types";

/**
 * The four trained/connected appliance models.
 *
 * Model metadata reflects the actual trained models:
 *   - Fridge:         Random Forest  (R² = 0.9976)
 *   - Kitchen Lights: Random Forest  (R² = 0.9632)
 *   - Laptop:         Linear Regression (R² = 0.9547)
 *   - Office Fan:     Random Forest  (R² = 0.9795)
 *
 * When "Use Live API" is enabled in Settings, the Flask backend serves
 * predictions from these exact models.  In simulation mode the dashboard
 * uses a deterministic client-side engine instead.
 */
export const APPLIANCES: ApplianceProfile[] = [
  {
    id: "laptop",
    name: "Laptop",
    room: "Study",
    icon: "laptop",
    ratedPowerW: 55,
    minPowerW: 8,
    maxPowerW: 95,
    criticalAlwaysOn: false,
    hasTemperature: true,
    description: "Work laptop and charger. Uses more power while charging.",
    model: {
      name: "Linear Regression",
      version: "v1.0-trained",
      trainedOn: "UK-DALE real household data (R²=0.9547)",
      accuracyPct: 95.5,
    },
  },
  {
    id: "kitchen_lights",
    name: "Kitchen Lights",
    room: "Kitchen",
    icon: "lightbulb",
    ratedPowerW: 42,
    minPowerW: 0,
    maxPowerW: 60,
    criticalAlwaysOn: false,
    hasTemperature: false,
    description: "Dimmable LED ceiling lights above the counter.",
    model: {
      name: "Random Forest",
      version: "v1.0-trained",
      trainedOn: "UK-DALE real household data (R²=0.9632)",
      accuracyPct: 96.3,
    },
  },
  {
    id: "office_fan",
    name: "Office Fan",
    room: "Study",
    icon: "fan",
    ratedPowerW: 48,
    minPowerW: 12,
    maxPowerW: 75,
    criticalAlwaysOn: false,
    hasTemperature: true,
    description: "Pedestal fan with variable speed, tied to room comfort.",
    model: {
      name: "Random Forest",
      version: "v1.0-trained",
      trainedOn: "UK-DALE real household data (R²=0.9795)",
      accuracyPct: 97.9,
    },
  },
  {
    id: "fridge",
    name: "Fridge",
    room: "Kitchen",
    icon: "refrigerator",
    ratedPowerW: 120,
    minPowerW: 2,
    maxPowerW: 190,
    criticalAlwaysOn: true,
    hasTemperature: true,
    description: "Always-on refrigerator. Cycles its compressor to stay cold.",
    model: {
      name: "Random Forest",
      version: "v1.0-trained",
      trainedOn: "UK-DALE real household data (R²=0.9976)",
      accuracyPct: 99.8,
    },
  },
];

export const APPLIANCE_MAP: Record<ApplianceId, ApplianceProfile> = Object.fromEntries(
  APPLIANCES.map((a) => [a.id, a]),
) as Record<ApplianceId, ApplianceProfile>;

export const APPLIANCE_IDS = APPLIANCES.map((a) => a.id);
