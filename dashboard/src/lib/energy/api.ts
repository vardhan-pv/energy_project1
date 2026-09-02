/**
 * ---------------------------------------------------------------------------
 * HTTP / Flask Backend Connection & Phase 15 Auth APIs
 * ---------------------------------------------------------------------------
 */
import type {
  AlertItem,
  ApplianceId,
  ApplianceProfile,
  ApplianceRuntime,
  ControlLoopState,
  ControlMode,
  Prediction,
  House,
} from "./types";

export const ENDPOINTS = {
  register: "POST /api/auth/register",
  login: "POST /api/auth/login",
  me: "GET /api/auth/me",
  createHouse: "POST /api/houses",
  getHouses: "GET /api/houses",
  createDevice: "POST /api/devices",
  getDevices: "GET /api/devices",
  createAppliance: "POST /api/appliances",
  getAppliances: "GET /api/appliances",
  house: "GET /api/house",
  telemetry: "GET /api/telemetry?window=5m",
  predictions: "GET /api/predictions?horizon=30",
  control: "POST /api/control { id, action, on?, mode?, targetW? }",
  controlLoop: "GET /api/control-loop",
  alerts: "GET /api/alerts",
  history: "GET /api/history?range=7d",
  health: "GET /api/health",
} as const;

export interface UserProfile {
  user_id: string;
  name: string;
  email: string;
  status?: string;
  house?: House | null;
}

export interface EnergyDataSource {
  register(name: string, email: string, password: string): Promise<{ ok: boolean; user: UserProfile; token: string }>;
  login(identifier: string, password: string): Promise<{ ok: boolean; user: UserProfile; token: string }>;
  getCurrentUser(): Promise<{ ok: boolean; user: UserProfile }>;
  createHouse(houseName: string, location: string): Promise<{ ok: boolean; house: House }>;
  getHouses(): Promise<House[]>;
  createDevice(deviceType: string, deviceName: string, macAddress?: string): Promise<{ ok: boolean; device: any }>;
  getDevices(): Promise<any[]>;
  createAppliance(deviceId: string | null, name: string, type: string, ratedPowerW: number): Promise<{ ok: boolean; appliance: any }>;
  getHouse(): Promise<House>;
  listAppliances(): Promise<ApplianceProfile[]>;
  getTelemetry(): Promise<ApplianceRuntime[]>;
  getPredictions(horizonMinutes: number): Promise<Prediction[]>;
  getControlLoop(): Promise<ControlLoopState[]>;
  getAlerts(): Promise<AlertItem[]>;
  getHistory(range?: string): Promise<
    {
      date: string;
      t: number;
      laptop: number;
      kitchen_lights: number;
      office_fan: number;
      fridge: number;
      total: number;
      savingsKwh: number;
    }[]
  >;
  sendControl(input: {
    id: ApplianceId;
    action: "power" | "mode" | "target";
    on?: boolean;
    mode?: ControlMode;
    targetW?: number;
  }): Promise<{ ok: boolean }>;
  checkHealth(): Promise<{ status: string; models_loaded: Record<string, number> }>;
}

/** HTTP implementation with optional Bearer JWT token support. */
export function createHttpDataSource(baseUrl: string, getToken?: () => string | null): EnergyDataSource {
  const url = (p: string) => `${baseUrl.replace(/\/$/, "")}${p}`;
  const json = async <T>(p: string, init?: RequestInit): Promise<T> => {
    const token = getToken ? getToken() : null;
    const reqHeaders: Record<string, string> = { "content-type": "application/json" };
    if (token) {
      reqHeaders["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(url(p), {
      headers: { ...reqHeaders, ...(init?.headers || {}) },
      ...init,
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `${res.status} ${res.statusText}`);
    }
    return (await res.json()) as T;
  };

  return {
    register: (name, email, password) =>
      json<{ ok: boolean; user: UserProfile; token: string }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      }),
    login: (identifier, password) =>
      json<{ ok: boolean; user: UserProfile; token: string }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ user_id: identifier, password }),
      }),
    getCurrentUser: () => json<{ ok: boolean; user: UserProfile }>("/api/auth/me"),
    createHouse: (houseName, location) =>
      json<{ ok: boolean; house: House }>("/api/houses", {
        method: "POST",
        body: JSON.stringify({ house_name: houseName, location }),
      }),
    getHouses: () => json<House[]>("/api/houses"),
    createDevice: (deviceType, deviceName, macAddress) =>
      json<{ ok: boolean; device: any }>("/api/devices", {
        method: "POST",
        body: JSON.stringify({ device_type: deviceType, device_name: deviceName, mac_address: macAddress }),
      }),
    getDevices: () => json<any[]>("/api/devices"),
    createAppliance: (deviceId, name, type, ratedPowerW) =>
      json<{ ok: boolean; appliance: any }>("/api/appliances", {
        method: "POST",
        body: JSON.stringify({ device_id: deviceId, appliance_name: name, appliance_type: type, rated_power_w: ratedPowerW }),
      }),
    getHouse: () => json<House>("/api/house"),
    listAppliances: () => json<ApplianceProfile[]>("/api/appliances"),
    getTelemetry: () => json<ApplianceRuntime[]>("/api/telemetry"),
    getPredictions: (h) => json<Prediction[]>(`/api/predictions?horizon=${h}`),
    getControlLoop: () => json<ControlLoopState[]>("/api/control-loop"),
    getAlerts: () => json<AlertItem[]>("/api/alerts"),
    getHistory: (range = "30d") =>
      json<ReturnType<EnergyDataSource["getHistory"]> extends Promise<infer T> ? T : never>(
        `/api/history?range=${range}`,
      ),
    sendControl: (input) =>
      json<{ ok: boolean }>("/api/control", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    checkHealth: () =>
      json<{ status: string; models_loaded: Record<string, number> }>("/api/health"),
  };
}
