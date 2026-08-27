/**
 * Deterministic, seeded client-side simulator.
 *
 * Everything here is pure: given the same seed, tick index and appliance state
 * you always get the same numbers. This keeps the demo reproducible and means
 * the whole engine can be replaced by a real Flask/Python API later without
 * touching the UI (see src/lib/energy/api.ts).
 */
import { APPLIANCE_MAP } from "./appliances";
import type {
  ApplianceId,
  ApplianceProfile,
  ApplianceRuntime,
  ControlLoopState,
  ControlMode,
  Prediction,
  RiskLevel,
  TelemetrySample,
} from "./types";

export const DEMO_SEED = 20260827;

/** Small deterministic hash -> [0,1). */
function rand(...parts: number[]): number {
  let h = DEMO_SEED >>> 0;
  for (const p of parts) {
    h ^= Math.imul(Math.floor(p) ^ 0x9e3779b9, 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    h ^= h >>> 16;
  }
  return (h >>> 0) / 4294967296;
}

function idSeed(id: ApplianceId): number {
  let n = 0;
  for (let i = 0; i < id.length; i++) n = (n * 31 + id.charCodeAt(i)) >>> 0;
  return n;
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export const MODE_FACTOR: Record<ControlMode, number> = {
  maintain: 1,
  reduce: 0.75,
  increase: 1.2,
  eco: 0.6,
};

/** Fraction of rated power the appliance should sit at, before noise. */
export function targetPowerW(
  profile: ApplianceProfile,
  mode: ControlMode,
  status: ApplianceRuntime["status"],
): number {
  if (status === "off") return 0;
  if (status === "standby") return Math.max(profile.minPowerW, profile.ratedPowerW * 0.06);
  return clamp(profile.ratedPowerW * MODE_FACTOR[mode], profile.minPowerW, profile.maxPowerW);
}

/** Hour-of-day usage shape (0-1), makes charts look like a real household. */
function dailyShape(id: ApplianceId, hour: number): number {
  switch (id) {
    case "laptop":
      return hour >= 9 && hour <= 18 ? 1 : hour >= 19 && hour <= 22 ? 0.7 : 0.18;
    case "kitchen_lights":
      return hour >= 6 && hour <= 8 ? 0.9 : hour >= 17 && hour <= 22 ? 1 : 0.1;
    case "office_fan":
      return hour >= 11 && hour <= 17 ? 1 : hour >= 18 && hour <= 21 ? 0.6 : 0.15;
    case "fridge":
      return 0.85 + 0.15 * Math.sin(((hour - 6) / 24) * Math.PI * 2);
  }
}

/** Fridge compressor duty cycle: deterministic on/off square-ish wave. */
function compressorDuty(t: number): number {
  const periodMs = 12 * 60 * 1000;
  const phase = (t % periodMs) / periodMs;
  return phase < 0.42 ? 1 : 0.12;
}

export interface TickInput {
  profile: ApplianceProfile;
  status: ApplianceRuntime["status"];
  mode: ControlMode;
  t: number;
  tick: number;
  /** Injected demo fault for the Alerts & Safety demo. */
  faultActive?: boolean;
}

export interface TickResult {
  powerW: number;
  temperatureC?: number;
  anomalyScore: number;
  risk: RiskLevel;
  targetW: number;
}

export function simulateTick(input: TickInput): TickResult {
  const { profile, status, mode, t, tick, faultActive } = input;
  const seed = idSeed(profile.id);
  const hour = new Date(t).getHours();
  const target = targetPowerW(profile, mode, status);

  let power = target;
  if (status !== "off") {
    power *= 0.75 + 0.25 * dailyShape(profile.id, hour);
    if (profile.id === "fridge") power *= compressorDuty(t);
    const wobble = (rand(seed, tick) - 0.5) * 0.14 * profile.ratedPowerW;
    const drift = Math.sin(tick / 9 + seed) * 0.05 * profile.ratedPowerW;
    power = clamp(power + wobble + drift, 0, profile.maxPowerW);
  }
  if (faultActive && status !== "off") power = clamp(power * 1.55, 0, profile.maxPowerW * 1.3);

  const deviation = target > 0 ? Math.abs(power - target) / Math.max(target, 1) : 0;
  const anomalyScore = clamp(faultActive ? 0.55 + deviation * 0.5 : deviation * 0.55, 0, 1);
  const risk: RiskLevel = anomalyScore > 0.6 ? "risk" : anomalyScore > 0.32 ? "watch" : "normal";

  let temperatureC: number | undefined;
  if (profile.hasTemperature) {
    if (profile.id === "fridge") {
      temperatureC = 4.2 + Math.sin(t / 900000) * 0.9 + (rand(seed, tick, 3) - 0.5) * 0.4;
      if (faultActive) temperatureC += 3.4;
    } else if (profile.id === "laptop") {
      temperatureC = 38 + (power / profile.maxPowerW) * 18 + (rand(seed, tick, 5) - 0.5) * 1.5;
    } else {
      temperatureC = 25.5 + (rand(seed, tick, 7) - 0.5) * 1.6 - (power / profile.maxPowerW) * 1.4;
    }
    temperatureC = Math.round(temperatureC * 10) / 10;
  }

  return {
    powerW: Math.round(power * 10) / 10,
    temperatureC,
    anomalyScore: Math.round(anomalyScore * 100) / 100,
    risk,
    targetW: Math.round(target),
  };
}

/** Build a plausible history so charts are never empty on first paint. */
export function seedHistory(
  profile: ApplianceProfile,
  status: ApplianceRuntime["status"],
  mode: ControlMode,
  now: number,
  points: number,
  stepMs: number,
): TelemetrySample[] {
  const out: TelemetrySample[] = [];
  let energy = 0;
  for (let i = points; i > 0; i--) {
    const t = now - i * stepMs;
    const r = simulateTick({ profile, status, mode, t, tick: Math.floor(t / stepMs) });
    energy += (r.powerW * (stepMs / 3600000)) / 1000;
    out.push({
      t,
      powerW: r.powerW,
      energyKwh: Math.round(energy * 10000) / 10000,
      temperatureC: r.temperatureC,
      status,
    });
  }
  return out;
}

/** Energy already used today before the app was opened (deterministic). */
export function seedEnergyToday(id: ApplianceId, now: number): number {
  const profile = APPLIANCE_MAP[id];
  const hoursElapsed = new Date(now).getHours() + new Date(now).getMinutes() / 60;
  const avg = profile.ratedPowerW * (0.45 + rand(idSeed(id), 11) * 0.25);
  return Math.round(((avg * hoursElapsed) / 1000) * 1000) / 1000;
}

/** Demo "trained model" forecast for one appliance. */
export function predict(
  runtime: ApplianceRuntime,
  horizonMinutes: number,
  now: number,
): Prediction {
  const profile = APPLIANCE_MAP[runtime.id];
  const seed = idSeed(runtime.id);
  const steps = 12;
  const stepMs = (horizonMinutes * 60000) / steps;
  const curve: Prediction["curve"] = [];
  let sum = 0;

  for (let i = 1; i <= steps; i++) {
    const t = now + i * stepMs;
    const hour = new Date(t).getHours();
    const base =
      runtime.status === "off"
        ? 0
        : targetPowerW(profile, runtime.mode, runtime.status) *
          (0.8 + 0.2 * dailyShape(runtime.id, hour)) *
          (runtime.id === "fridge" ? 0.55 + compressorDuty(t) * 0.45 : 1);
    const trend = 1 + Math.sin(i / 3 + seed) * 0.06;
    const p = Math.max(0, base * trend);
    const spread = Math.max(2, p * (0.07 + i * 0.012));
    sum += p;
    curve.push({
      t,
      predictedW: Math.round(p * 10) / 10,
      lowerW: Math.round(Math.max(0, p - spread) * 10) / 10,
      upperW: Math.round((p + spread) * 10) / 10,
    });
  }

  const avgW = sum / steps;
  const baseConfidence = profile.model.accuracyPct - horizonMinutes * 0.06;
  const confidencePct = clamp(
    Math.round(baseConfidence - runtime.anomalyScore * 22 + (rand(seed, 42) - 0.5) * 2),
    55,
    99,
  );

  const risk: RiskLevel =
    runtime.risk === "risk" ? "risk" : avgW > profile.ratedPowerW * 1.15 ? "watch" : runtime.risk;

  const riskNote =
    risk === "risk"
      ? "Predicted draw is well above the learned pattern — check this appliance."
      : risk === "watch"
        ? "Slightly higher than usual for this time of day."
        : "Usage matches the learned pattern for this time of day.";

  return {
    id: runtime.id,
    nextPowerW: Math.round(avgW * 10) / 10,
    expectedUsageKwh: Math.round(((avgW * (horizonMinutes / 60)) / 1000) * 1000) / 1000,
    confidencePct,
    horizonMinutes,
    risk,
    riskNote,
    curve,
  };
}

const ACTION_LABEL: Record<ControlMode, string> = {
  maintain: "HOLD_SETPOINT",
  reduce: "REDUCE_LOAD",
  increase: "INCREASE_LOAD",
  eco: "ECO_OPTIMIZE",
};

/** Module 17 closed-loop control state. */
export function controlLoop(
  runtime: ApplianceRuntime,
  iterations: number,
  safetyInterlocks: boolean,
): ControlLoopState {
  const profile = APPLIANCE_MAP[runtime.id];
  const target = runtime.targetPowerW;
  const measured = runtime.powerW;
  const error = Math.round((measured - target) * 10) / 10;
  const normErr = Math.abs(error) / Math.max(profile.ratedPowerW, 1);
  const reward = Math.round((1 - normErr * 1.6 - runtime.anomalyScore * 0.5) * 100) / 100;
  const success = Math.abs(error) <= Math.max(4, profile.ratedPowerW * 0.12);

  const safetyStatus: ControlLoopState["safetyStatus"] =
    runtime.risk === "risk" && safetyInterlocks
      ? "blocked"
      : runtime.risk === "watch"
        ? "guarded"
        : "safe";

  const nextAction =
    safetyStatus === "blocked"
      ? "HOLD + NOTIFY_USER"
      : error > profile.ratedPowerW * 0.12
        ? "REDUCE_LOAD"
        : error < -profile.ratedPowerW * 0.12
          ? "INCREASE_LOAD"
          : "HOLD_SETPOINT";

  return {
    id: runtime.id,
    action: runtime.status === "off" ? "POWER_OFF" : ACTION_LABEL[runtime.mode],
    targetPowerW: target,
    measuredPowerW: measured,
    powerErrorW: error,
    reward,
    policyConfidencePct: clamp(
      Math.round(88 - normErr * 90 + (1 - runtime.anomalyScore) * 10),
      40,
      99,
    ),
    nextAction,
    safetyStatus,
    controlSuccess: success && safetyStatus !== "blocked",
    iterations,
  };
}

/** Deterministic daily history for the History / Analytics pages. */
export function dailyHistory(days: number, now: number) {
  const out: {
    date: string;
    t: number;
    laptop: number;
    kitchen_lights: number;
    office_fan: number;
    fridge: number;
    total: number;
    savingsKwh: number;
  }[] = [];
  for (let i = days - 1; i >= 0; i--) {
    const t = now - i * 86400000;
    const d = new Date(t);
    const dow = d.getDay();
    const weekend = dow === 0 || dow === 6 ? 1.12 : 1;
    const row = {
      date: d.toISOString().slice(0, 10),
      t,
      laptop: round3(0.45 * weekend * (0.8 + rand(1, i) * 0.45)),
      kitchen_lights: round3(0.28 * weekend * (0.8 + rand(2, i) * 0.5)),
      office_fan: round3(0.39 * weekend * (0.7 + rand(3, i) * 0.6)),
      fridge: round3(1.28 * (0.92 + rand(4, i) * 0.18)),
      total: 0,
      savingsKwh: 0,
    };
    row.total = round3(row.laptop + row.kitchen_lights + row.office_fan + row.fridge);
    row.savingsKwh = round3(row.total * (0.09 + rand(5, i) * 0.09));
    out.push(row);
  }
  return out;
}

function round3(n: number) {
  return Math.round(n * 1000) / 1000;
}

export { rand as deterministicRand };
