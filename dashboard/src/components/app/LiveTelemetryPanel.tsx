import React from "react";
import { motion } from "framer-motion";
import {
  Zap,
  Activity,
  Cpu,
  Radio,
  Thermometer,
  Droplets,
  Gauge,
  ShieldAlert,
  ShieldCheck,
  Workflow,
  Sparkles,
  Server,
  ArrowRight,
  TrendingUp,
  Award,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface TelemetryPanelProps {
  voltageV?: number;
  currentA?: number;
  powerW?: number;
  energyKwh?: number;
  temperatureC?: number;
  humidityPct?: number;
  frequencyHz?: number;
  powerFactor?: number;
  isHardwareLive?: boolean;
  deviceId?: string;
  applianceId?: string;
  anomalyScore?: number;
  mode?: "MAINTAIN" | "OPTIMIZE" | "EMERGENCY" | string;
  action?: string;
  relayCommand?: string;
  predictedPowerW?: number;
  targetPowerW?: number;
  reward?: number;
}

export function LiveTelemetryPanel({
  voltageV = 230.4,
  currentA = 0.45,
  powerW = 103.5,
  energyKwh = 1.42,
  temperatureC = 28.5,
  humidityPct = 58,
  frequencyHz = 50.0,
  powerFactor = 0.98,
  isHardwareLive = true,
  deviceId = "DEV-638C71FE",
  applianceId = "APP-79290D01",
  anomalyScore = 0.02,
  mode = "OPTIMIZE",
  action = "OPTIMIZE_LOAD",
  relayCommand = "RELAY_CH2_DIM",
  predictedPowerW = 95.0,
  targetPowerW = 100.0,
  reward = 1.45,
}: TelemetryPanelProps) {
  // Mode tone mapping
  const modeUpper = (mode || "OPTIMIZE").toUpperCase();
  let modeBadgeBg = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-emerald-500/10";
  let modeGlow = "shadow-emerald-500/20 border-emerald-500/30";

  if (modeUpper.includes("EMERGENCY") || modeUpper.includes("RISK")) {
    modeBadgeBg = "bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-rose-500/10";
    modeGlow = "shadow-rose-500/20 border-rose-500/30";
  } else if (modeUpper.includes("MAINTAIN") || modeUpper.includes("HOLD")) {
    modeBadgeBg = "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 shadow-cyan-500/10";
    modeGlow = "shadow-cyan-500/20 border-cyan-500/30";
  }

  // Anomaly status
  const isAnomalyHigh = (anomalyScore || 0) > 0.4;

  return (
    <div className="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/90 p-6 backdrop-blur-2xl shadow-2xl space-y-6">
      {/* Ambient Radial Gradient Background */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(6,182,212,0.1)_0%,transparent_60%)] pointer-events-none" />

      {/* Header Bar: Status & Hardware Details */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-500/20">
            <Radio className="h-5 w-5 animate-pulse" />
            {isHardwareLive && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
              </span>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-extrabold text-slate-100 tracking-tight">
                Live Physical ESP32 Hardware Telemetry
              </h2>
              <Badge className={modeBadgeBg}>
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping mr-1.5" />
                CLOSED-LOOP MODE: {modeUpper}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-mono mt-0.5">
              <span className="flex items-center gap-1 text-slate-300">
                <Cpu className="h-3.5 w-3.5 text-cyan-400" /> Node:{" "}
                <strong className="text-cyan-300 font-bold">{deviceId}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-slate-300">
                <Zap className="h-3.5 w-3.5 text-amber-400" /> Appliance:{" "}
                <strong className="text-amber-300 font-bold">{applianceId}</strong>
              </span>
              <span>•</span>
              <span className="text-emerald-400 flex items-center gap-1 font-semibold">
                <Server className="h-3.5 w-3.5" /> Render HTTPS API Live
              </span>
            </div>
          </div>
        </div>

        {/* Closed Loop Status Badge */}
        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 px-3.5 py-2 rounded-xl text-xs font-mono">
          <div className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-slate-400">Loop Cadence:</span>
          <span className="text-emerald-400 font-bold">3–5s Telemetry Cycle</span>
        </div>
      </div>

      {/* 8 Big Real-Time Telemetry Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 relative z-10">
        {/* 1. Voltage */}
        <MetricTile
          icon={Gauge}
          label="Line Voltage"
          value={`${voltageV.toFixed(1)}`}
          unit="V"
          subtext="AC 220V–240V Nominal"
          accentColor="text-cyan-400"
          borderColor="border-cyan-500/30"
          bgGlow="bg-cyan-500/5"
        />

        {/* 2. Current */}
        <MetricTile
          icon={Activity}
          label="Line Current"
          value={`${currentA.toFixed(2)}`}
          unit="A"
          subtext="PZEM CT Clamp Active"
          accentColor="text-blue-400"
          borderColor="border-blue-500/30"
          bgGlow="bg-blue-500/5"
        />

        {/* 3. Active Power */}
        <MetricTile
          icon={Zap}
          label="Active Power"
          value={`${powerW.toFixed(1)}`}
          unit="W"
          subtext="Real-time Load Draw"
          accentColor="text-amber-400"
          borderColor="border-amber-500/30"
          bgGlow="bg-amber-500/5"
          highlight
        />

        {/* 4. Energy Today */}
        <MetricTile
          icon={TrendingUp}
          label="Cumulative Energy"
          value={`${energyKwh.toFixed(2)}`}
          unit="kWh"
          subtext="Recorded Today"
          accentColor="text-emerald-400"
          borderColor="border-emerald-500/30"
          bgGlow="bg-emerald-500/5"
        />

        {/* 5. Temperature */}
        <MetricTile
          icon={Thermometer}
          label="Ambient Temp"
          value={`${temperatureC.toFixed(1)}`}
          unit="°C"
          subtext="DHT22 Sensor Reading"
          accentColor="text-rose-400"
          borderColor="border-rose-500/30"
          bgGlow="bg-rose-500/5"
        />

        {/* 6. Humidity */}
        <MetricTile
          icon={Droplets}
          label="Ambient Humidity"
          value={`${humidityPct.toFixed(0)}`}
          unit="%"
          subtext="Relative Humidity"
          accentColor="text-teal-400"
          borderColor="border-teal-500/30"
          bgGlow="bg-teal-500/5"
        />

        {/* 7. Frequency */}
        <MetricTile
          icon={Radio}
          label="Grid Frequency"
          value={`${frequencyHz.toFixed(1)}`}
          unit="Hz"
          subtext="AC Utility Grid"
          accentColor="text-indigo-400"
          borderColor="border-indigo-500/30"
          bgGlow="bg-indigo-500/5"
        />

        {/* 8. Power Factor */}
        <MetricTile
          icon={Award}
          label="Power Factor"
          value={`${powerFactor.toFixed(2)}`}
          unit="PF"
          subtext="Phase Efficiency"
          accentColor="text-purple-400"
          borderColor="border-purple-500/30"
          bgGlow="bg-purple-500/5"
        />
      </div>

      {/* Closed-Loop Cognitive Decision Pipeline Ribbon */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-4 relative z-10 backdrop-blur-xl">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 border-b border-slate-800/80 pb-2.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-300">
            <Workflow className="h-4 w-4 text-cyan-400" />
            Closed-Loop Real-Time Control State Matrix
          </div>
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Anomaly Score:</span>
            <span
              className={`font-bold px-2 py-0.5 rounded-md border ${
                isAnomalyHigh
                  ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                  : "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
              }`}
            >
              {anomalyScore.toFixed(3)}
            </span>
          </div>
        </div>

        {/* 5-Step Continuous Closed-Loop State Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs font-mono">
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-2.5 text-cyan-300">
            <div className="text-[10px] text-cyan-400/80 uppercase">1. Sense</div>
            <div className="font-bold text-slate-100 text-xs mt-0.5">PZEM + DHT22</div>
            <div className="text-[9px] text-cyan-400 truncate">{powerW.toFixed(0)}W | {temperatureC.toFixed(0)}°C</div>
          </div>

          <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-2.5 text-indigo-300">
            <div className="text-[10px] text-indigo-400/80 uppercase">2. Analyze</div>
            <div className="font-bold text-slate-100 text-xs mt-0.5">NILM Classifier</div>
            <div className="text-[9px] text-indigo-400 truncate">Status: Active</div>
          </div>

          <div className="rounded-xl border border-purple-500/30 bg-purple-500/10 p-2.5 text-purple-300">
            <div className="text-[10px] text-purple-400/80 uppercase">3. Predict</div>
            <div className="font-bold text-slate-100 text-xs mt-0.5">XGBoost Engine</div>
            <div className="text-[9px] text-purple-400 truncate">Target: {predictedPowerW.toFixed(0)}W</div>
          </div>

          <div className="rounded-xl border border-teal-500/30 bg-teal-500/10 p-2.5 text-teal-300">
            <div className="text-[10px] text-teal-400/80 uppercase">4. Optimize</div>
            <div className="font-bold text-slate-100 text-xs mt-0.5">Adaptive RL Agent</div>
            <div className="text-[9px] text-teal-400 truncate">Reward: +{reward.toFixed(2)}</div>
          </div>

          <div className="col-span-2 sm:col-span-1 rounded-xl border border-amber-500/40 bg-amber-500/10 p-2.5 text-amber-300 shadow-md shadow-amber-500/10">
            <div className="text-[10px] text-amber-400/80 uppercase font-bold">5. Act / Control</div>
            <div className="font-bold text-amber-200 text-xs mt-0.5 truncate">{relayCommand}</div>
            <div className="text-[9px] text-amber-400 truncate">Action: {action}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricTileProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  unit: string;
  subtext: string;
  accentColor: string;
  borderColor: string;
  bgGlow: string;
  highlight?: boolean;
}

function MetricTile({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  accentColor,
  borderColor,
  bgGlow,
  highlight = false,
}: MetricTileProps) {
  return (
    <div
      className={`rounded-2xl border ${borderColor} ${bgGlow} p-4 backdrop-blur-xl relative overflow-hidden transition-all duration-300 hover:scale-[1.02] shadow-lg`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-slate-400 truncate">{label}</span>
        <Icon className={`h-4 w-4 ${accentColor}`} />
      </div>

      <div className="flex items-baseline gap-1 my-1">
        <span className={`text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-100 font-mono`}>
          {value}
        </span>
        <span className={`text-xs font-bold font-mono ${accentColor}`}>{unit}</span>
      </div>

      <p className="text-[10px] text-slate-400 font-mono truncate">{subtext}</p>
    </div>
  );
}
