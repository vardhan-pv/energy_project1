import React from "react";
import {
  Zap,
  Activity,
  Cpu,
  Radio,
  Thermometer,
  Droplets,
  Gauge,
  Workflow,
  Server,
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
  mode?: string;
  action?: string;
  relayCommand?: string;
  predictedPowerW?: number;
  targetPowerW?: number;
  reward?: number;
}

export function LiveTelemetryPanel({
  voltageV,
  currentA,
  powerW,
  energyKwh,
  temperatureC,
  humidityPct,
  frequencyHz,
  powerFactor,
  isHardwareLive = false,
  deviceId = "DEV-638C71FE",
  applianceId = "APP-79290D01",
  anomalyScore,
  mode = "MAINTAIN",
  action = "MAINTAIN_LOAD",
  relayCommand = "HIGH",
  predictedPowerW,
  targetPowerW,
  reward,
}: TelemetryPanelProps) {
  const modeUpper = (mode || "MAINTAIN").toUpperCase();

  return (
    <div className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-black p-6 backdrop-blur-xl shadow-2xl space-y-6 text-white">
      {/* Header Bar: Status & Hardware Details */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-700 text-white shadow-md">
            <Radio className="h-5 w-5" />
            {isHardwareLive && (
              <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white" />
              </span>
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-tight">
                Live Physical ESP32 Hardware Telemetry
              </h2>
              <Badge className="bg-zinc-900 text-white border-zinc-700 font-mono text-[10px] uppercase">
                <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse mr-1.5" />
                CLOSED-LOOP: {modeUpper}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-400 font-mono mt-1">
              <span className="flex items-center gap-1 text-zinc-300">
                <Cpu className="h-3.5 w-3.5 text-zinc-400" /> Node:{" "}
                <strong className="text-white font-bold">{deviceId}</strong>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-zinc-300">
                <Zap className="h-3.5 w-3.5 text-zinc-400" /> Appliance:{" "}
                <strong className="text-white font-bold">{applianceId}</strong>
              </span>
              <span>•</span>
              <span className="text-white flex items-center gap-1 font-semibold">
                <Server className="h-3.5 w-3.5 text-zinc-400" /> Render API Live
              </span>
            </div>
          </div>
        </div>

        {/* Live Loop Status */}
        <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 px-3.5 py-1.5 rounded-lg text-xs font-mono text-zinc-300">
          <div className="h-2 w-2 rounded-full bg-white animate-pulse" />
          <span>Telemetry Stream:</span>
          <span className="text-white font-bold">
            {isHardwareLive ? "LIVE HARDWARE ACTIVE" : "REAL-TIME POLLING"}
          </span>
        </div>
      </div>

      {/* 8 Monochrome Real-Time Telemetry Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        {/* 1. Voltage */}
        <MetricTile
          icon={Gauge}
          label="Line Voltage"
          value={voltageV !== undefined && voltageV !== null ? voltageV.toFixed(1) : "--"}
          unit="V"
          subtext="AC Mains Input"
        />

        {/* 2. Current */}
        <MetricTile
          icon={Activity}
          label="Line Current"
          value={currentA !== undefined && currentA !== null ? currentA.toFixed(2) : "--"}
          unit="A"
          subtext="PZEM CT Clamp Sensor"
        />

        {/* 3. Active Power */}
        <MetricTile
          icon={Zap}
          label="Active Power"
          value={powerW !== undefined && powerW !== null ? powerW.toFixed(1) : "--"}
          unit="W"
          subtext="Real-time Load Draw"
          highlight
        />

        {/* 4. Energy Today */}
        <MetricTile
          icon={Activity}
          label="Cumulative Energy"
          value={energyKwh !== undefined && energyKwh !== null ? energyKwh.toFixed(2) : "--"}
          unit="kWh"
          subtext="Recorded Energy"
        />

        {/* 5. Temperature */}
        <MetricTile
          icon={Thermometer}
          label="Ambient Temp"
          value={temperatureC !== undefined && temperatureC !== null ? temperatureC.toFixed(1) : "--"}
          unit="°C"
          subtext="DHT22 Sensor Reading"
        />

        {/* 6. Humidity */}
        <MetricTile
          icon={Droplets}
          label="Ambient Humidity"
          value={humidityPct !== undefined && humidityPct !== null ? humidityPct.toFixed(0) : "--"}
          unit="%"
          subtext="Relative Humidity"
        />

        {/* 7. Frequency */}
        <MetricTile
          icon={Radio}
          label="Grid Frequency"
          value={frequencyHz !== undefined && frequencyHz !== null ? frequencyHz.toFixed(1) : "--"}
          unit="Hz"
          subtext="AC Utility Grid"
          muted={frequencyHz === undefined}
        />

        {/* 8. Power Factor */}
        <MetricTile
          icon={Award}
          label="Power Factor"
          value={powerFactor !== undefined && powerFactor !== null ? powerFactor.toFixed(2) : "--"}
          unit="PF"
          subtext="Phase Efficiency"
          muted={powerFactor === undefined}
        />
      </div>

      {/* Closed-Loop Real-Time State Matrix */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-4 font-mono">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 border-b border-zinc-800 pb-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white">
            <Workflow className="h-4 w-4 text-white" />
            Closed-Loop Real-Time Control Matrix
          </div>
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span>Anomaly Score:</span>
            <span className="font-bold text-white bg-zinc-900 border border-zinc-700 px-2 py-0.5 rounded">
              {anomalyScore !== undefined && anomalyScore !== null ? anomalyScore.toFixed(3) : "--"}
            </span>
          </div>
        </div>

        {/* 5-Step Monochrome State Pipeline */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-2.5 text-zinc-300">
            <div className="text-[10px] text-zinc-400 uppercase font-semibold">1. Sense</div>
            <div className="font-bold text-white text-xs mt-0.5">PZEM + DHT22</div>
            <div className="text-[9px] text-zinc-400 truncate">
              {powerW !== undefined ? `${powerW.toFixed(0)}W` : "--"} | {temperatureC !== undefined ? `${temperatureC.toFixed(0)}°C` : "--"}
            </div>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-2.5 text-zinc-300">
            <div className="text-[10px] text-zinc-400 uppercase font-semibold">2. Analyze</div>
            <div className="font-bold text-white text-xs mt-0.5">NILM Classifier</div>
            <div className="text-[9px] text-zinc-400 truncate">Status: Active</div>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-2.5 text-zinc-300">
            <div className="text-[10px] text-zinc-400 uppercase font-semibold">3. Predict</div>
            <div className="font-bold text-white text-xs mt-0.5">XGBoost Engine</div>
            <div className="text-[9px] text-zinc-400 truncate">
              Target: {predictedPowerW !== undefined ? `${predictedPowerW.toFixed(0)}W` : "--"}
            </div>
          </div>

          <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-2.5 text-zinc-300">
            <div className="text-[10px] text-zinc-400 uppercase font-semibold">4. Optimize</div>
            <div className="font-bold text-white text-xs mt-0.5">Adaptive RL</div>
            <div className="text-[9px] text-zinc-400 truncate">
              Reward: {reward !== undefined ? `+${reward.toFixed(2)}` : "--"}
            </div>
          </div>

          <div className="col-span-2 sm:col-span-1 rounded-lg border border-white bg-zinc-900 p-2.5 text-white shadow-sm">
            <div className="text-[10px] text-zinc-300 uppercase font-bold">5. Act / Control</div>
            <div className="font-bold text-white text-xs mt-0.5 truncate">{relayCommand}</div>
            <div className="text-[9px] text-zinc-400 truncate">Action: {action}</div>
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
  muted?: boolean;
  highlight?: boolean;
}

function MetricTile({
  icon: Icon,
  label,
  value,
  unit,
  subtext,
  muted = false,
  highlight = false,
}: MetricTileProps) {
  return (
    <div
      className={`rounded-xl border p-4 backdrop-blur-md transition-all duration-200 ${
        highlight
          ? "border-white bg-zinc-900 text-white shadow-lg"
          : muted
          ? "border-zinc-800/60 bg-zinc-950/40 text-zinc-500"
          : "border-zinc-800 bg-zinc-950 text-zinc-200"
      }`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-zinc-400 truncate">{label}</span>
        <Icon className={`h-4 w-4 ${highlight ? "text-white" : "text-zinc-400"}`} />
      </div>

      <div className="flex items-baseline gap-1 my-1">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        <span className="text-xs font-bold font-mono text-zinc-400">{unit}</span>
      </div>

      <p className="text-[10px] text-zinc-400 font-mono truncate">{subtext}</p>
    </div>
  );
}
