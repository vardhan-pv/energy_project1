/**
 * ---------------------------------------------------------------------------
 * HTTP / Flask Backend Connection
 * ---------------------------------------------------------------------------
 * The dashboard can run on a deterministic client-side simulator (default) or
 * connect to the Python Flask API (`api_server.py`) for real model-driven data.
 *
 * To connect:
 *   1. Start the Flask server: `python api_server.py`
 *   2. Open Settings → enable "Use Live API" (persisted in localStorage)
 *   3. The store automatically switches from simulation to polling the API.
 */
import type {
  AlertItem,
  ApplianceId,
  ApplianceProfile,
  ApplianceRuntime,
  ControlLoopState,
  ControlMode,
  Prediction,
} from "./types";

export const ENDPOINTS = {
  appliances: "GET /api/appliances",
  telemetry: "GET /api/telemetry?window=5m",
  predictions: "GET /api/predictions?horizon=30",
  control: "POST /api/control  { appliance_id, action, mode, target_w }",
  controlLoop: "GET /api/control-loop",
  alerts: "GET /api/alerts",
  history: "GET /api/history?range=7d",
  health: "GET /api/health",
  stream: "WS  /ws/telemetry (optional, falls back to polling)",
} as const;

export interface EnergyDataSource {
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

/** Thin HTTP implementation, ready for the Flask backend. */
export function createHttpDataSource(baseUrl: string): EnergyDataSource {
  const url = (p: string) => `${baseUrl.replace(/\/$/, "")}${p}`;
  const json = async <T>(p: string, init?: RequestInit): Promise<T> => {
    const res = await fetch(url(p), {
      headers: { "content-type": "application/json" },
      ...init,
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return (await res.json()) as T;
  };

  return {
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
