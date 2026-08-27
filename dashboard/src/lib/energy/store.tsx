import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { APPLIANCES, APPLIANCE_MAP } from "./appliances";
import { createHttpDataSource, type EnergyDataSource } from "./api";
import {
  controlLoop,
  dailyHistory,
  predict,
  seedEnergyToday,
  seedHistory,
  simulateTick,
  targetPowerW,
} from "./simulation";
import type {
  ActivityEvent,
  AlertItem,
  ApplianceId,
  ApplianceRuntime,
  ControlLoopState,
  ControlMode,
  EventSeverity,
  Prediction,
  Settings,
  SystemSnapshot,
} from "./types";

const HISTORY_POINTS = 90;
const MAX_EVENTS = 60;

export const DEFAULT_SETTINGS: Settings = {
  tariffPerKwh: 0.18,
  currency: "$",
  refreshMs: 2000,
  autopilot: true,
  safetyInterlocks: true,
  ecoTargetPct: 15,
  budgetKwhPerDay: 3.2,
  notifications: true,
  reduceMotion: false,
  apiBaseUrl: "http://localhost:5000",
  useLiveApi: false,
};

interface EngineState {
  ready: boolean;
  now: number;
  tick: number;
  runtimes: Record<ApplianceId, ApplianceRuntime>;
  events: ActivityEvent[];
  alerts: AlertItem[];
  loops: Record<ApplianceId, ControlLoopState>;
  faults: Partial<Record<ApplianceId, boolean>>;
  baselineKwh: number;
}

interface EnergyContextValue extends EngineState {
  settings: Settings;
  snapshot: SystemSnapshot;
  predictions: Record<ApplianceId, Prediction>;
  horizonMinutes: number;
  connected: boolean;
  setHorizonMinutes: (m: number) => void;
  updateSettings: (patch: Partial<Settings>) => void;
  setPower: (id: ApplianceId, on: boolean) => void;
  setMode: (id: ApplianceId, mode: ControlMode) => void;
  setTarget: (id: ApplianceId, watts: number) => void;
  acknowledgeAlert: (id: string) => void;
  clearAlerts: () => void;
  injectFault: (id: ApplianceId) => void;
  resetDemo: () => void;
  history: ReturnType<typeof dailyHistory>;
}

const EnergyContext = createContext<EnergyContextValue | null>(null);

function makeEvent(
  t: number,
  severity: EventSeverity,
  title: string,
  detail: string,
  source: ActivityEvent["source"],
  appliance?: ApplianceId,
): ActivityEvent {
  return {
    id: `${t}-${title}-${Math.random().toString(36).slice(2, 7)}`,
    t,
    severity,
    title,
    detail,
    source,
    appliance,
  };
}

function initialState(now: number, settings: Settings): EngineState {
  const runtimes = {} as Record<ApplianceId, ApplianceRuntime>;
  for (const p of APPLIANCES) {
    const status: ApplianceRuntime["status"] =
      p.id === "fridge" ? "on" : p.id === "kitchen_lights" ? "on" : p.id === "laptop" ? "on" : "on";
    const mode: ControlMode = p.id === "office_fan" ? "eco" : "maintain";
    const history = seedHistory(p, status, mode, now, HISTORY_POINTS, settings.refreshMs);
    const last = history[history.length - 1];
    runtimes[p.id] = {
      id: p.id,
      status,
      mode,
      powerW: last.powerW,
      targetPowerW: targetPowerW(p, mode, status),
      energyTodayKwh: seedEnergyToday(p.id, now),
      temperatureC: last.temperatureC,
      anomalyScore: 0.05,
      risk: "normal",
      online: true,
      signalPct: 72 + ((p.ratedPowerW * 7) % 25),
      batteryPct: p.id === "office_fan" ? 84 : p.id === "kitchen_lights" ? 91 : undefined,
      lastSeen: now,
      history,
    };
  }

  const loops = {} as Record<ApplianceId, ControlLoopState>;
  for (const p of APPLIANCES) loops[p.id] = controlLoop(runtimes[p.id], 1, settings.safetyInterlocks);

  const events: ActivityEvent[] = [
    makeEvent(now - 4000, "info", "Simulation started", "Demo telemetry engine online.", "system"),
    makeEvent(
      now - 20000,
      "success",
      "Policy applied",
      "Office Fan switched to Eco mode by the optimizer.",
      "policy",
      "office_fan",
    ),
    makeEvent(
      now - 60000,
      "info",
      "Model loaded",
      "4 trained appliance models loaded (demo weights).",
      "system",
    ),
  ];

  return {
    ready: true,
    now,
    tick: Math.floor(now / settings.refreshMs),
    runtimes,
    events,
    alerts: [],
    loops,
    faults: {},
    baselineKwh: 0,
  };
}

function loadSettings(): Settings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  try {
    const raw = window.localStorage.getItem("ceos.settings");
    return raw ? { ...DEFAULT_SETTINGS, ...(JSON.parse(raw) as Partial<Settings>) } : DEFAULT_SETTINGS;
  } catch {
    return DEFAULT_SETTINGS;
  }
}

// ---------------------------------------------------------------------------
// Live API poller – fetches real data from the Flask backend
// ---------------------------------------------------------------------------
async function pollLiveApi(
  ds: EnergyDataSource,
  horizonMinutes: number,
  prev: EngineState | null,
  settings: Settings,
): Promise<Partial<EngineState> | null> {
  try {
    const [telemetry, controlLoopData, alertsData] = await Promise.all([
      ds.getTelemetry(),
      ds.getControlLoop(),
      ds.getAlerts(),
    ]);

    const now = Date.now();
    const runtimes = {} as Record<ApplianceId, ApplianceRuntime>;
    const loops = {} as Record<ApplianceId, ControlLoopState>;

    for (const rt of telemetry) {
      const id = rt.id as ApplianceId;
      // Merge history: keep previous history and append new sample
      const prevHistory = prev?.runtimes?.[id]?.history ?? [];
      const sample = {
        t: now,
        powerW: rt.powerW,
        energyKwh: rt.energyTodayKwh,
        temperatureC: rt.temperatureC,
        status: rt.status,
      };
      const history = [...prevHistory, sample].slice(-HISTORY_POINTS);
      runtimes[id] = { ...rt, history, lastSeen: now };
    }

    for (const cl of controlLoopData) {
      loops[cl.id as ApplianceId] = cl;
    }

    // Build events from alerts
    const newEvents: ActivityEvent[] = [];
    if (alertsData.length > 0) {
      const existingIds = new Set((prev?.events ?? []).map((e) => e.id));
      for (const alert of alertsData.slice(0, 5)) {
        const evId = `api-${alert.id}`;
        if (!existingIds.has(evId)) {
          newEvents.push({
            id: evId,
            t: alert.t,
            severity: alert.severity === "critical" ? "critical" : "warning",
            title: alert.title,
            detail: alert.detail,
            source: "safety",
            appliance: alert.appliance,
          });
        }
      }
    }

    const tick = (prev?.tick ?? 0) + 1;

    // Add periodic telemetry event
    if (tick % 10 === 0) {
      const total = Object.values(runtimes).reduce((s, r) => s + r.powerW, 0);
      newEvents.push(
        makeEvent(
          now,
          "info",
          "Telemetry snapshot",
          `Household load ${total.toFixed(0)} W (live API data from trained models).`,
          "sensor",
        ),
      );
    }

    return {
      ready: true,
      now,
      tick,
      runtimes,
      events: [...newEvents, ...(prev?.events ?? [])].slice(0, MAX_EVENTS),
      alerts: alertsData,
      loops,
      faults: prev?.faults ?? {},
      baselineKwh: prev?.baselineKwh ?? 0,
    };
  } catch (err) {
    console.error("[live-api] Poll failed:", err);
    return null;
  }
}

export function EnergyProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [horizonMinutes, setHorizonMinutes] = useState(30);
  const [state, setState] = useState<EngineState | null>(null);
  const [apiConnected, setApiConnected] = useState(false);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  // Boot on the client only: keeps SSR output stable and avoids hydration drift.
  useEffect(() => {
    const s = loadSettings();
    setSettings(s);
    setState(initialState(Date.now(), s));
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("ceos.settings", JSON.stringify(settings));
  }, [settings]);

  // ---- Live API polling loop -----------------------------------------------
  useEffect(() => {
    if (!state?.ready || !settings.useLiveApi) {
      setApiConnected(false);
      return;
    }

    const ds = createHttpDataSource(settings.apiBaseUrl);
    let cancelled = false;

    // Initial connection event
    setState((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        events: [
          makeEvent(Date.now(), "success", "Live API connected", `Polling ${settings.apiBaseUrl} for real model data.`, "system"),
          ...prev.events,
        ].slice(0, MAX_EVENTS),
      };
    });

    const poll = async () => {
      if (cancelled) return;
      const result = await pollLiveApi(ds, horizonMinutes, state, settingsRef.current);
      if (cancelled) return;
      if (result) {
        setState((prev) => (prev ? { ...prev, ...result } : prev));
        setApiConnected(true);
      } else {
        setApiConnected(false);
        // Push a warning event
        setState((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            events: [
              makeEvent(Date.now(), "warning", "API connection lost", "Could not reach the Flask backend. Retrying…", "system"),
              ...prev.events,
            ].slice(0, MAX_EVENTS),
          };
        });
      }
    };

    // First poll immediately
    poll();
    const interval = window.setInterval(poll, settings.refreshMs);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [state?.ready, settings.useLiveApi, settings.apiBaseUrl, settings.refreshMs]);

  // ---- Simulation loop (only when NOT using live API) -----------------------
  useEffect(() => {
    if (!state?.ready || settings.useLiveApi) return;
    const interval = window.setInterval(() => {
      setState((prev) => {
        if (!prev) return prev;
        const cfg = settingsRef.current;
        const now = Date.now();
        const tick = prev.tick + 1;
        const runtimes = { ...prev.runtimes };
        const loops = { ...prev.loops };
        const newEvents: ActivityEvent[] = [];
        const newAlerts: AlertItem[] = [];

        for (const profile of APPLIANCES) {
          const prevRt = prev.runtimes[profile.id];
          const faultActive = !!prev.faults[profile.id];
          const r = simulateTick({
            profile,
            status: prevRt.status,
            mode: prevRt.mode,
            t: now,
            tick,
            faultActive,
          });
          const dtH = cfg.refreshMs / 3600000;
          const energyTodayKwh = prevRt.energyTodayKwh + (r.powerW * dtH) / 1000;
          const sample = {
            t: now,
            powerW: r.powerW,
            energyKwh: Math.round(energyTodayKwh * 10000) / 10000,
            temperatureC: r.temperatureC,
            status: prevRt.status,
          };
          const history = [...prevRt.history, sample].slice(-HISTORY_POINTS);
          const next: ApplianceRuntime = {
            ...prevRt,
            powerW: r.powerW,
            targetPowerW: r.targetW,
            temperatureC: r.temperatureC,
            energyTodayKwh: Math.round(energyTodayKwh * 100000) / 100000,
            anomalyScore: r.anomalyScore,
            risk: r.risk,
            lastSeen: now,
            history,
          };
          runtimes[profile.id] = next;
          loops[profile.id] = controlLoop(next, prev.loops[profile.id].iterations + 1, cfg.safetyInterlocks);

          if (prevRt.risk !== "risk" && r.risk === "risk") {
            newAlerts.push({
              id: `${now}-${profile.id}`,
              t: now,
              appliance: profile.id,
              severity: "critical",
              title: `${profile.name}: unusual power draw`,
              detail: `Measured ${r.powerW.toFixed(0)} W against an expected ${r.targetW} W. Safety interlock ${
                cfg.safetyInterlocks ? "engaged" : "disabled"
              }.`,
              acknowledged: false,
            });
            newEvents.push(
              makeEvent(
                now,
                "critical",
                `${profile.name} anomaly detected`,
                "Draw is far above the learned pattern.",
                "safety",
                profile.id,
              ),
            );
          }
          if (cfg.autopilot && tick % 15 === 0 && prevRt.status === "on" && r.risk === "watch") {
            newEvents.push(
              makeEvent(
                now,
                "info",
                `Optimizer nudged ${profile.name}`,
                "Target power trimmed to stay inside the daily budget.",
                "policy",
                profile.id,
              ),
            );
          }
        }

        if (tick % 10 === 0) {
          const total = APPLIANCES.reduce((s, p) => s + runtimes[p.id].powerW, 0);
          newEvents.push(
            makeEvent(
              now,
              "info",
              "Telemetry snapshot",
              `Household load ${total.toFixed(0)} W across 4 appliances.`,
              "sensor",
            ),
          );
        }

        return {
          ...prev,
          now,
          tick,
          runtimes,
          loops,
          events: [...newEvents, ...prev.events].slice(0, MAX_EVENTS),
          alerts: [...newAlerts, ...prev.alerts].slice(0, 40),
        };
      });
    }, settings.refreshMs);
    return () => window.clearInterval(interval);
  }, [state?.ready, settings.refreshMs, settings.useLiveApi]);

  const pushEvent = useCallback(
    (severity: EventSeverity, title: string, detail: string, source: ActivityEvent["source"], id?: ApplianceId) => {
      setState((prev) =>
        prev
          ? { ...prev, events: [makeEvent(Date.now(), severity, title, detail, source, id), ...prev.events].slice(0, MAX_EVENTS) }
          : prev,
      );
    },
    [],
  );

  // ---- Control actions (work for both simulated and live API) ---------------
  const liveControl = useCallback(
    async (input: { id: ApplianceId; action: string; on?: boolean; mode?: ControlMode; targetW?: number }) => {
      if (!settingsRef.current.useLiveApi) return;
      try {
        const ds = createHttpDataSource(settingsRef.current.apiBaseUrl);
        await ds.sendControl(input as Parameters<typeof ds.sendControl>[0]);
      } catch (err) {
        console.error("[live-api] Control command failed:", err);
      }
    },
    [],
  );

  const setPower = useCallback(
    (id: ApplianceId, on: boolean) => {
      const profile = APPLIANCE_MAP[id];
      if (!on && profile.criticalAlwaysOn) {
        pushEvent("warning", `${profile.name} cannot be switched off`, "Safety interlock: this appliance must stay powered.", "safety", id);
        return;
      }
      setState((prev) => {
        if (!prev) return prev;
        const rt = prev.runtimes[id];
        const status: ApplianceRuntime["status"] = on ? "on" : "off";
        return {
          ...prev,
          runtimes: {
            ...prev.runtimes,
            [id]: { ...rt, status, powerW: on ? rt.powerW : 0, targetPowerW: targetPowerW(profile, rt.mode, status) },
          },
        };
      });
      pushEvent(on ? "success" : "info", `${profile.name} turned ${on ? "on" : "off"}`, "Command accepted by the controller.", "user", id);
      liveControl({ id, action: "power", on });
    },
    [pushEvent, liveControl],
  );

  const setMode = useCallback(
    (id: ApplianceId, mode: ControlMode) => {
      const profile = APPLIANCE_MAP[id];
      setState((prev) => {
        if (!prev) return prev;
        const rt = prev.runtimes[id];
        return {
          ...prev,
          runtimes: { ...prev.runtimes, [id]: { ...rt, mode, targetPowerW: targetPowerW(profile, mode, rt.status) } },
        };
      });
      pushEvent("success", `${profile.name} set to ${mode}`, "Control policy updated and applied.", "user", id);
      liveControl({ id, action: "mode", mode });
    },
    [pushEvent, liveControl],
  );

  const setTarget = useCallback(
    (id: ApplianceId, watts: number) => {
      setState((prev) => {
        if (!prev) return prev;
        const rt = prev.runtimes[id];
        return { ...prev, runtimes: { ...prev.runtimes, [id]: { ...rt, targetPowerW: Math.round(watts) } } };
      });
      liveControl({ id, action: "target", targetW: Math.round(watts) });
    },
    [liveControl],
  );

  const acknowledgeAlert = useCallback((alertId: string) => {
    setState((prev) =>
      prev ? { ...prev, alerts: prev.alerts.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a)) } : prev,
    );
  }, []);

  const clearAlerts = useCallback(() => {
    setState((prev) => (prev ? { ...prev, alerts: [] } : prev));
  }, []);

  const injectFault = useCallback(
    (id: ApplianceId) => {
      setState((prev) => (prev ? { ...prev, faults: { ...prev.faults, [id]: !prev.faults[id] } } : prev));
      pushEvent("warning", `Demo fault toggled on ${APPLIANCE_MAP[id].name}`, "Simulated abnormal draw for testing alerts.", "system", id);
    },
    [pushEvent],
  );

  const resetDemo = useCallback(() => {
    setState(initialState(Date.now(), settingsRef.current));
  }, []);

  const updateSettings = useCallback((patch: Partial<Settings>) => {
    setSettings((s) => ({ ...s, ...patch }));
  }, []);

  // ---- Predictions (simulation mode uses local predict, live mode polls API)
  const [livePredictions, setLivePredictions] = useState<Record<ApplianceId, Prediction> | null>(null);

  useEffect(() => {
    if (!state?.ready || !settings.useLiveApi) {
      setLivePredictions(null);
      return;
    }
    const ds = createHttpDataSource(settings.apiBaseUrl);
    let cancelled = false;

    const fetchPredictions = async () => {
      try {
        const preds = await ds.getPredictions(horizonMinutes);
        if (cancelled) return;
        const map = {} as Record<ApplianceId, Prediction>;
        for (const p of preds) map[p.id as ApplianceId] = p;
        setLivePredictions(map);
      } catch (err) {
        console.error("[live-api] Predictions fetch failed:", err);
      }
    };

    fetchPredictions();
    const interval = window.setInterval(fetchPredictions, 6000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [state?.ready, settings.useLiveApi, settings.apiBaseUrl, horizonMinutes]);

  const simPredictions = useMemo(() => {
    const out = {} as Record<ApplianceId, Prediction>;
    if (!state) return out;
    for (const p of APPLIANCES) out[p.id] = predict(state.runtimes[p.id], horizonMinutes, state.now);
    return out;
    // Recompute a few times a minute rather than every tick.
  }, [state?.tick ? Math.floor(state.tick / 3) : 0, horizonMinutes, state?.runtimes]);

  const predictions = livePredictions ?? simPredictions;

  // ---- Live history (polls API) or simulated --------------------------------
  const [liveHistory, setLiveHistory] = useState<ReturnType<typeof dailyHistory> | null>(null);

  useEffect(() => {
    if (!state?.ready || !settings.useLiveApi) {
      setLiveHistory(null);
      return;
    }
    const ds = createHttpDataSource(settings.apiBaseUrl);
    let cancelled = false;

    const fetchHistory = async () => {
      try {
        const data = await ds.getHistory("30d");
        if (cancelled) return;
        setLiveHistory(data as ReturnType<typeof dailyHistory>);
      } catch (err) {
        console.error("[live-api] History fetch failed:", err);
      }
    };

    fetchHistory();
    // History doesn't change often, refresh every 60 seconds
    const interval = window.setInterval(fetchHistory, 60000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [state?.ready, settings.useLiveApi, settings.apiBaseUrl]);

  const simHistory = useMemo(() => dailyHistory(30, state?.now ?? Date.now()), [state?.ready]);
  const history = liveHistory ?? simHistory;

  const snapshot: SystemSnapshot = useMemo(() => {
    if (!state) {
      return {
        t: 0,
        totalPowerW: 0,
        energyTodayKwh: 0,
        savingsKwh: 0,
        savingsPct: 0,
        costToday: 0,
        comfort: "optimal",
        safety: "safe",
      };
    }
    const totalPowerW = APPLIANCES.reduce((s, p) => s + state.runtimes[p.id].powerW, 0);
    const energyTodayKwh = APPLIANCES.reduce((s, p) => s + state.runtimes[p.id].energyTodayKwh, 0);
    const savingsKwh = energyTodayKwh * (settings.ecoTargetPct / 100) * (settings.autopilot ? 1 : 0.35);
    const risky = APPLIANCES.some((p) => state.runtimes[p.id].risk === "risk");
    const watch = APPLIANCES.some((p) => state.runtimes[p.id].risk === "watch");
    return {
      t: state.now,
      totalPowerW: Math.round(totalPowerW * 10) / 10,
      energyTodayKwh: Math.round(energyTodayKwh * 1000) / 1000,
      savingsKwh: Math.round(savingsKwh * 1000) / 1000,
      savingsPct: Math.round((settings.ecoTargetPct * (settings.autopilot ? 1 : 0.35)) * 10) / 10,
      costToday: energyTodayKwh * settings.tariffPerKwh,
      comfort: risky ? "attention" : watch ? "acceptable" : "optimal",
      safety: risky && settings.safetyInterlocks ? "blocked" : watch ? "guarded" : "safe",
    };
  }, [state, settings]);

  const value: EnergyContextValue = {
    ready: !!state?.ready,
    now: state?.now ?? 0,
    tick: state?.tick ?? 0,
    runtimes: state?.runtimes ?? ({} as Record<ApplianceId, ApplianceRuntime>),
    events: state?.events ?? [],
    alerts: state?.alerts ?? [],
    loops: state?.loops ?? ({} as Record<ApplianceId, ControlLoopState>),
    faults: state?.faults ?? {},
    baselineKwh: state?.baselineKwh ?? 0,
    settings,
    snapshot,
    predictions,
    horizonMinutes,
    connected: settings.useLiveApi ? apiConnected : !!state?.ready,
    setHorizonMinutes,
    updateSettings,
    setPower,
    setMode,
    setTarget,
    acknowledgeAlert,
    clearAlerts,
    injectFault,
    resetDemo,
    history,
  };

  return <EnergyContext.Provider value={value}>{children}</EnergyContext.Provider>;
}

export function useEnergy() {
  const ctx = useContext(EnergyContext);
  if (!ctx) throw new Error("useEnergy must be used inside <EnergyProvider>");
  return ctx;
}
