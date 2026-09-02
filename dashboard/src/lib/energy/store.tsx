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
import { createHttpDataSource, type EnergyDataSource, type UserProfile } from "./api";
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
  ApplianceProfile,
  ApplianceRuntime,
  ControlLoopState,
  ControlMode,
  EventSeverity,
  House,
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
  apiBaseUrl: "https://energy-project1.onrender.com",
  useLiveApi: true,
};

const DEFAULT_SIMULATED_HOUSE: House = {
  id: "HOUSE_SIMULATED",
  name: "Simulated Home",
  location: "Local Simulation",
  status: "ONLINE",
  dataStatus: "AVAILABLE",
};

interface EngineState {
  ready: boolean;
  now: number;
  tick: number;
  house: House | null;
  appliances: ApplianceProfile[];
  runtimes: Record<string, ApplianceRuntime>;
  events: ActivityEvent[];
  alerts: AlertItem[];
  loops: Record<string, ControlLoopState>;
  faults: Partial<Record<string, boolean>>;
  baselineKwh: number;
}

interface EnergyContextValue extends EngineState {
  house: House | null;
  appliances: ApplianceProfile[];
  settings: Settings;
  snapshot: SystemSnapshot;
  predictions: Record<string, Prediction>;
  horizonMinutes: number;
  connected: boolean;
  user: UserProfile | null;
  token: string | null;
  loginUser: (identifier: string, pass: string) => Promise<UserProfile>;
  registerUser: (name: string, email: string, pass: string) => Promise<UserProfile>;
  logoutUser: () => void;
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
  const runtimes = {} as Record<string, ApplianceRuntime>;
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

  const loops = {} as Record<string, ControlLoopState>;
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
    house: DEFAULT_SIMULATED_HOUSE,
    appliances: APPLIANCES,
    runtimes,
    events,
    alerts: [],
    loops,
    faults: {},
    baselineKwh: 0,
  };
}

function initialLivePendingState(): EngineState {
  return {
    ready: false,
    now: Date.now(),
    tick: 0,
    house: null,
    appliances: [],
    runtimes: {},
    events: [
      makeEvent(Date.now(), "info", "Connecting to Live API", "Fetching house metadata and live telemetry...", "system"),
    ],
    alerts: [],
    loops: {},
    faults: {},
    baselineKwh: 0,
  };
}

function loadSettings(): Settings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  try {
    const raw = window.localStorage.getItem("ceos.settings");
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<Settings>;
    if (parsed.apiBaseUrl === "http://localhost:5000" || parsed.apiBaseUrl === "http://localhost:5001") {
      parsed.apiBaseUrl = "https://energy-project1.onrender.com";
    }
    return { ...DEFAULT_SETTINGS, ...parsed };
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
    const housePromise = ds.getHouse();
    const appliancesPromise = ds.listAppliances();
    const [houseData, appliancesData, telemetry, controlLoopData, alertsData] = await Promise.all([
      housePromise,
      appliancesPromise,
      ds.getTelemetry(),
      ds.getControlLoop(),
      ds.getAlerts(),
    ]);

    const now = Date.now();
    const runtimes = { ...(prev?.runtimes ?? {}) };
    const loops = { ...(prev?.loops ?? {}) };

    for (const rt of telemetry) {
      const id = rt.id;
      // Merge history: keep previous history and append new sample
      const prevHistory = prev?.runtimes?.[id]?.history ?? [];
      const sample = {
        t: now,
        powerW: rt.powerW ?? 0,
        energyKwh: rt.energyTodayKwh ?? 0,
        temperatureC: rt.temperatureC,
        status: rt.status ?? "off",
      };
      const history = [...prevHistory, sample].slice(-HISTORY_POINTS);
      runtimes[id] = { ...rt, history, lastSeen: now };
    }

    for (const cl of controlLoopData) {
      loops[cl.id] = cl;
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
    if (tick % 10 === 0 && Object.keys(runtimes).length > 0) {
      const total = Object.values(runtimes).reduce((s, r) => s + (r.powerW ?? 0), 0);
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
      house: houseData,
      appliances: appliancesData,
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
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedToken = window.localStorage.getItem("ceos.token");
      const savedUser = window.localStorage.getItem("ceos.user");
      if (savedToken && savedUser) {
        setToken(savedToken);
        try {
          setUser(JSON.parse(savedUser));
        } catch {
          // ignore
        }
      }
    }
  }, []);

  const loginUser = async (identifier: string, pass: string) => {
    let ds = createHttpDataSource(settings.apiBaseUrl);
    try {
      const res = await ds.login(identifier, pass);
      if (res.ok && res.token) {
        setToken(res.token);
        setUser(res.user);
        if (typeof window !== "undefined") {
          window.localStorage.setItem("ceos.token", res.token);
          window.localStorage.setItem("ceos.user", JSON.stringify(res.user));
        }
        return res.user;
      }
    } catch (err) {
      if (settings.apiBaseUrl.includes("onrender.com")) {
        try {
          const altDs = createHttpDataSource("http://localhost:5000");
          const res = await altDs.login(identifier, pass);
          if (res.ok && res.token) {
            updateSettings({ apiBaseUrl: "http://localhost:5000" });
            setToken(res.token);
            setUser(res.user);
            if (typeof window !== "undefined") {
              window.localStorage.setItem("ceos.token", res.token);
              window.localStorage.setItem("ceos.user", JSON.stringify(res.user));
            }
            return res.user;
          }
        } catch {
          // ignore
        }
      }
      throw err;
    }
    throw new Error("Login failed");
  };

  const registerUser = async (name: string, email: string, pass: string) => {
    let ds = createHttpDataSource(settings.apiBaseUrl);
    try {
      const res = await ds.register(name, email, pass);
      if (res.ok && res.token) {
        setToken(res.token);
        setUser(res.user);
        if (typeof window !== "undefined") {
          window.localStorage.setItem("ceos.token", res.token);
          window.localStorage.setItem("ceos.user", JSON.stringify(res.user));
        }
        return res.user;
      }
    } catch (err) {
      if (settings.apiBaseUrl.includes("onrender.com")) {
        try {
          const altDs = createHttpDataSource("http://localhost:5000");
          const res = await altDs.register(name, email, pass);
          if (res.ok && res.token) {
            updateSettings({ apiBaseUrl: "http://localhost:5000" });
            setToken(res.token);
            setUser(res.user);
            if (typeof window !== "undefined") {
              window.localStorage.setItem("ceos.token", res.token);
              window.localStorage.setItem("ceos.user", JSON.stringify(res.user));
            }
            return res.user;
          }
        } catch {
          // ignore
        }
      }
      throw err;
    }
    throw new Error("Registration failed");
  };

  const logoutUser = () => {
    setToken(null);
    setUser(null);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("ceos.token");
      window.localStorage.removeItem("ceos.user");
    }
  };

  // Boot on the client only: keeps SSR output stable and avoids hydration drift.
  useEffect(() => {
    const s = loadSettings();
    setSettings(s);
    if (s.useLiveApi) {
      setState(initialLivePendingState());
    } else {
      setState(initialState(Date.now(), s));
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem("ceos.settings", JSON.stringify(settings));
  }, [settings]);

  // Sync state mode if useLiveApi setting changes
  useEffect(() => {
    if (!state) return;
    if (settings.useLiveApi && state.house?.id === "HOUSE_SIMULATED") {
      setState(initialLivePendingState());
    } else if (!settings.useLiveApi && state.house?.id !== "HOUSE_SIMULATED") {
      setState(initialState(Date.now(), settings));
    }
  }, [settings.useLiveApi]);

  // ---- Live API polling loop -----------------------------------------------
  useEffect(() => {
    if (!settings.useLiveApi) {
      setApiConnected(false);
      return;
    }

    const ds = createHttpDataSource(settings.apiBaseUrl, () => token);
    let cancelled = false;

    const poll = async () => {
      if (cancelled) return;
      let currentDs = ds;
      let result = await pollLiveApi(currentDs, horizonMinutes, state, settingsRef.current);
      
      // Auto fallback between port 5000 and 5001 if primary URL is localhost and failed
      if (!result && settingsRef.current.apiBaseUrl.includes("localhost")) {
        const altUrl = settingsRef.current.apiBaseUrl.includes("5000")
          ? "http://localhost:5001"
          : "http://localhost:5000";
        const altDs = createHttpDataSource(altUrl);
        const altResult = await pollLiveApi(altDs, horizonMinutes, state, settingsRef.current);
        if (altResult) {
          result = altResult;
          updateSettings({ apiBaseUrl: altUrl });
        }
      }

      if (cancelled) return;
      if (result) {
        setState((prev) => {
          if (!prev) return result as EngineState;
          const cleanedEvents = prev.events.filter((e) => e.title !== "API connection lost");
          return {
            ...prev,
            ...result,
            events: [...(result.events ?? []), ...cleanedEvents].slice(0, MAX_EVENTS),
          };
        });
        setApiConnected(true);
      } else {
        setApiConnected(false);
        setState((prev) => {
          if (!prev) return prev;
          // Avoid flooding the stream with duplicate retry warnings
          const hasRecentWarning = prev.events[0]?.title === "API connection lost";
          if (hasRecentWarning) return prev;
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
  }, [settings.useLiveApi, settings.apiBaseUrl, settings.refreshMs]);

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
          if (!prevRt) continue;
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
          loops[profile.id] = controlLoop(next, prev.loops[profile.id]?.iterations ? prev.loops[profile.id].iterations + 1 : 1, cfg.safetyInterlocks);

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
          const total = APPLIANCES.reduce((s, p) => s + (runtimes[p.id]?.powerW ?? 0), 0);
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

  const getApplianceProfile = useCallback(
    (id: string): ApplianceProfile => {
      if (APPLIANCE_MAP[id as ApplianceId]) return APPLIANCE_MAP[id as ApplianceId];
      const found = state?.appliances.find((a) => a.id === id);
      if (found) return found;
      return {
        id: id as ApplianceId,
        name: id,
        room: "Home",
        icon: "laptop",
        ratedPowerW: 50,
        minPowerW: 0,
        maxPowerW: 100,
        criticalAlwaysOn: false,
        hasTemperature: false,
        description: "Appliance",
        model: { name: "Model", version: "v1.0", trainedOn: "Data", accuracyPct: 90 },
      };
    },
    [state?.appliances],
  );

  // ---- Control actions (work for both simulated and live API) ---------------
  const liveControl = useCallback(
    async (input: { id: string; action: string; on?: boolean; mode?: ControlMode; targetW?: number }) => {
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
      const profile = getApplianceProfile(id);
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
            [id]: { ...rt, status, powerW: on ? (rt?.powerW ?? 0) : 0, targetPowerW: targetPowerW(profile, rt?.mode ?? "maintain", status) },
          },
        };
      });
      pushEvent(on ? "success" : "info", `${profile.name} turned ${on ? "on" : "off"}`, "Command accepted by the controller.", "user", id);
      liveControl({ id, action: "power", on });
    },
    [pushEvent, liveControl, getApplianceProfile],
  );

  const setMode = useCallback(
    (id: ApplianceId, mode: ControlMode) => {
      const profile = getApplianceProfile(id);
      setState((prev) => {
        if (!prev) return prev;
        const rt = prev.runtimes[id];
        return {
          ...prev,
          runtimes: { ...prev.runtimes, [id]: { ...rt, mode, targetPowerW: targetPowerW(profile, mode, rt?.status ?? "on") } },
        };
      });
      pushEvent("success", `${profile.name} set to ${mode}`, "Control policy updated and applied.", "user", id);
      liveControl({ id, action: "mode", mode });
    },
    [pushEvent, liveControl, getApplianceProfile],
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
      const profile = getApplianceProfile(id);
      setState((prev) => (prev ? { ...prev, faults: { ...prev.faults, [id]: !prev.faults[id] } } : prev));
      pushEvent("warning", `Demo fault toggled on ${profile.name}`, "Simulated abnormal draw for testing alerts.", "system", id);
    },
    [pushEvent, getApplianceProfile],
  );

  const resetDemo = useCallback(() => {
    if (settingsRef.current.useLiveApi) {
      setState(initialLivePendingState());
    } else {
      setState(initialState(Date.now(), settingsRef.current));
    }
  }, []);

  const updateSettings = useCallback((patch: Partial<Settings>) => {
    setSettings((s) => ({ ...s, ...patch }));
  }, []);

  // ---- Predictions (simulation mode uses local predict, live mode polls API)
  const [livePredictions, setLivePredictions] = useState<Record<string, Prediction> | null>(null);

  useEffect(() => {
    if (!settings.useLiveApi) {
      setLivePredictions(null);
      return;
    }
    const ds = createHttpDataSource(settings.apiBaseUrl);
    let cancelled = false;

    const fetchPredictions = async () => {
      try {
        const preds = await ds.getPredictions(horizonMinutes);
        if (cancelled) return;
        const map = {} as Record<string, Prediction>;
        for (const p of preds) map[p.id] = p;
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
  }, [settings.useLiveApi, settings.apiBaseUrl, horizonMinutes]);

  const simPredictions = useMemo(() => {
    const out = {} as Record<string, Prediction>;
    if (!state) return out;
    const currentAppliances = state.appliances.length > 0 ? state.appliances : APPLIANCES;
    for (const p of currentAppliances) {
      if (state.runtimes[p.id]) {
        out[p.id] = predict(state.runtimes[p.id], horizonMinutes, state.now);
      }
    }
    return out;
  }, [state?.tick ? Math.floor(state.tick / 3) : 0, horizonMinutes, state?.runtimes, state?.appliances]);

  const predictions = livePredictions ?? simPredictions;

  // ---- Live history (polls API) or simulated --------------------------------
  const [liveHistory, setLiveHistory] = useState<ReturnType<typeof dailyHistory> | null>(null);

  useEffect(() => {
    if (!settings.useLiveApi) {
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
    const interval = window.setInterval(fetchHistory, 60000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [settings.useLiveApi, settings.apiBaseUrl]);

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
    const currentAppliances = state.appliances.length > 0 ? state.appliances : APPLIANCES;
    const totalPowerW = currentAppliances.reduce((s, p) => s + (state.runtimes[p.id]?.powerW ?? 0), 0);
    const energyTodayKwh = currentAppliances.reduce((s, p) => s + (state.runtimes[p.id]?.energyTodayKwh ?? 0), 0);
    const savingsKwh = energyTodayKwh * (settings.ecoTargetPct / 100) * (settings.autopilot ? 1 : 0.35);
    const risky = currentAppliances.some((p) => state.runtimes[p.id]?.risk === "risk");
    const watch = currentAppliances.some((p) => state.runtimes[p.id]?.risk === "watch");
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
    house: state?.house ?? null,
    appliances: state?.appliances ?? APPLIANCES,
    runtimes: state?.runtimes ?? ({} as Record<string, ApplianceRuntime>),
    events: state?.events ?? [],
    alerts: state?.alerts ?? [],
    loops: state?.loops ?? ({} as Record<string, ControlLoopState>),
    faults: state?.faults ?? {},
    baselineKwh: state?.baselineKwh ?? 0,
    settings,
    snapshot,
    predictions,
    horizonMinutes,
    connected: settings.useLiveApi ? apiConnected : !!state?.ready,
    user,
    token,
    loginUser,
    registerUser,
    logoutUser,
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
