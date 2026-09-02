/**
 * Shared domain types for the Cognitive Energy Optimization demo.
 *
 * These types are intentionally transport-agnostic: the same shapes are
 * produced by the local deterministic simulator today and can be produced by a
 * Flask/Python API later (see src/lib/energy/api.ts).
 */

export type ApplianceId = "laptop" | "kitchen_lights" | "office_fan" | "fridge";

export type ControlMode = "maintain" | "reduce" | "increase" | "eco";

export type ApplianceStatus = "on" | "off" | "standby";

export type RiskLevel = "normal" | "watch" | "risk";

export type HouseStatus =
  | "INITIALIZING"
  | "READY"
  | "ONLINE"
  | "OFFLINE"
  | "ERROR";

export type DataStatus =
  | "PENDING"
  | "AVAILABLE"
  | "PARTIAL"
  | "ERROR";

export interface House {
  id: string;
  name: string;
  location: string;
  status: HouseStatus;
  dataStatus: DataStatus;
}

export interface ApplianceProfile {
  id: ApplianceId;
  name: string;
  room: string;
  icon: "laptop" | "lightbulb" | "fan" | "refrigerator";
  /** Nominal power draw when running, in watts. */
  ratedPowerW: number;
  minPowerW: number;
  maxPowerW: number;
  /** Appliance may never be switched off from the UI (safety interlock). */
  criticalAlwaysOn: boolean;
  hasTemperature: boolean;
  /** Short, non-technical description shown to the homeowner. */
  description: string;
  /** Demo model metadata shown in the Predictions area. */
  model: {
    name: string;
    version: string;
    trainedOn: string;
    accuracyPct: number;
  };
}

export interface TelemetrySample {
  /** Epoch milliseconds. */
  t: number;
  powerW: number;
  /** Cumulative energy for the day, kWh. */
  energyKwh: number;
  temperatureC?: number;
  status: ApplianceStatus;
}

export interface ApplianceRuntime {
  id: ApplianceId;
  status: ApplianceStatus;
  mode: ControlMode;
  powerW: number;
  targetPowerW: number;
  energyTodayKwh: number;
  temperatureC?: number;
  /** 0-1, how far the measurement is from the model's expected band. */
  anomalyScore: number;
  risk: RiskLevel;
  online: boolean;
  signalPct: number;
  batteryPct?: number;
  lastSeen: number;
  history: TelemetrySample[];
}

export interface Prediction {
  id: ApplianceId;
  /** Predicted average power over the horizon, watts. */
  nextPowerW: number;
  /** Expected energy over the horizon, kWh. */
  expectedUsageKwh: number;
  /** Model confidence 0-100. */
  confidencePct: number;
  horizonMinutes: number;
  risk: RiskLevel;
  riskNote: string;
  /** Predicted power curve for the horizon. */
  curve: { t: number; predictedW: number; lowerW: number; upperW: number }[];
}

export interface ControlLoopState {
  id: ApplianceId;
  action: string;
  targetPowerW: number;
  measuredPowerW: number;
  powerErrorW: number;
  reward: number;
  policyConfidencePct: number;
  nextAction: string;
  safetyStatus: "safe" | "guarded" | "blocked";
  controlSuccess: boolean;
  iterations: number;
}

export type EventSeverity = "info" | "success" | "warning" | "critical";

export interface ActivityEvent {
  id: string;
  t: number;
  appliance?: ApplianceId;
  severity: EventSeverity;
  title: string;
  detail: string;
  source: "sensor" | "policy" | "user" | "safety" | "system";
}

export interface AlertItem {
  id: string;
  t: number;
  appliance: ApplianceId;
  severity: EventSeverity;
  title: string;
  detail: string;
  acknowledged: boolean;
}

export interface Settings {
  tariffPerKwh: number;
  currency: string;
  refreshMs: number;
  autopilot: boolean;
  safetyInterlocks: boolean;
  ecoTargetPct: number;
  budgetKwhPerDay: number;
  notifications: boolean;
  reduceMotion: boolean;
  apiBaseUrl: string;
  useLiveApi: boolean;
}

export interface SystemSnapshot {
  t: number;
  totalPowerW: number;
  energyTodayKwh: number;
  savingsKwh: number;
  savingsPct: number;
  costToday: number;
  comfort: "optimal" | "acceptable" | "attention";
  safety: "safe" | "guarded" | "blocked";
}
