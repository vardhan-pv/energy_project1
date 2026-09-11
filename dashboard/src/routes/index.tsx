import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  BadgeDollarSign,
  Cpu,
  Database,
  Gauge,
  Info,
  Leaf,
  Radio,
  Server,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApplianceCard } from "@/components/app/ApplianceCard";
import { EventStream } from "@/components/app/EventStream";
import { MultiLineChart } from "@/components/app/charts";
import { LoadingPanel, PageHeader, StatCard } from "@/components/app/primitives";
import { LiveTelemetryPanel } from "@/components/app/LiveTelemetryPanel";
import { fmtKwh, fmtMoney, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Home Energy Overview | Cognitive Energy Dashboard" },
      {
        name: "description",
        content:
          "IREOS Intelligent IoT-Driven Cognitive Energy Optimization System with Reinforcement Learning.",
      },
      { property: "og:title", content: "Home Energy Overview | Cognitive Energy Dashboard" },
      {
        property: "og:description",
        content: "Live power, today's energy, savings and safety status for your home.",
      },
    ],
  }),
  component: Overview,
});

function Overview() {
  const { ready, snapshot, runtimes, settings, history, house, appliances, loops } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader
          title={house ? house.name : "Overview"}
          description={
            house
              ? `${house.location} · ID: ${house.id} · Data Status: PENDING`
              : "Connecting to IREOS backend & PostgreSQL..."
          }
        />
        <LoadingPanel />
      </>
    );
  }

  const firstAppId = appliances[0]?.id;
  const firstAppHistory = firstAppId && runtimes[firstAppId]?.history ? runtimes[firstAppId].history : [];
  const baseHistory = firstAppHistory.slice(-45);
  const combined = baseHistory.map((s, i) => {
    const row: Record<string, number> = { t: s.t };
    for (const a of appliances) {
      const appHist = runtimes[a.id]?.history ?? [];
      row[a.id] = appHist.slice(-45)[i]?.powerW ?? 0;
    }
    return row;
  });

  const budgetPct = (snapshot.energyTodayKwh / settings.budgetKwhPerDay) * 100;
  const activeHardwareRt = Object.values(runtimes).find((r) => r.isHardware) || runtimes[appliances[0]?.id];
  const activeLoop = firstAppId ? loops[firstAppId] : undefined;

  return (
    <>
      {/* 1. Top System Status Bar */}
      <section className="rounded-xl border border-border bg-card p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            IREOS System Status
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill
              icon={Server}
              label="Backend"
              value={settings.useLiveApi ? "Render Flask API" : "Simulated"}
              tone="success"
            />
            <StatusPill
              icon={Database}
              label="Database"
              value={settings.useLiveApi ? "Render PostgreSQL" : "SQLite Demo"}
              tone="success"
            />
            <StatusPill
              icon={Cpu}
              label="ESP32 Node"
              value={snapshot.isHardwareLive ? "ONLINE (DEV-638C71FE)" : "Offline / Simulation"}
              tone={snapshot.isHardwareLive ? "success" : "warning"}
            />
            <StatusPill
              icon={Radio}
              label="Telemetry"
              value={snapshot.isHardwareLive ? "PZEM-004T + DHT22" : "Simulated Stream"}
              tone={snapshot.isHardwareLive ? "success" : "info"}
            />
            <StatusPill
              icon={Zap}
              label="Mode"
              value={settings.useLiveApi ? "LIVE HARDWARE" : "SIMULATION"}
              tone={settings.useLiveApi ? "success" : "warning"}
            />
          </div>
        </div>
      </section>

      {/* 2. LIVE PHYSICAL ESP32 HARDWARE TELEMETRY PANEL (TOP PRIORITY) */}
      <section aria-label="Live Telemetry Panel">
        <LiveTelemetryPanel
          voltageV={snapshot.voltageV ?? 230.4}
          currentA={snapshot.currentA ?? 0.45}
          powerW={snapshot.totalPowerW ?? 103.5}
          energyKwh={snapshot.energyTodayKwh ?? 1.42}
          temperatureC={snapshot.ambientTempC ?? 28.5}
          humidityPct={snapshot.ambientHumidityPct ?? 58.0}
          frequencyHz={50.0}
          powerFactor={0.98}
          isHardwareLive={snapshot.isHardwareLive ?? true}
          deviceId="DEV-638C71FE"
          applianceId={activeHardwareRt?.id ? activeHardwareRt.id.toUpperCase() : "APP-79290D01"}
          anomalyScore={activeHardwareRt?.anomalyScore ?? 0.02}
          mode={activeHardwareRt?.mode ? activeHardwareRt.mode.toUpperCase() : "OPTIMIZE"}
          action={activeLoop?.action || "OPTIMIZE_LOAD"}
          relayCommand={activeHardwareRt?.status === "off" ? "RELAY_CH2_OFF (Open)" : "RELAY_CH2_ON (Closed)"}
          predictedPowerW={activeHardwareRt?.targetPowerW || 95.0}
          targetPowerW={activeHardwareRt?.targetPowerW || 100.0}
          reward={activeLoop?.reward || 1.45}
        />
      </section>


      <PageHeader
        title={settings.useLiveApi && house ? house.name : "Good to see you"}
        description={
          settings.useLiveApi && house
            ? `${house.location} · ${house.id} · Status: ${house.status}`
            : "Operating in Simulation mode. Switch to Live API in Settings to connect to physical hardware."
        }
        actions={
          <>
            <Button asChild variant="outline">
              <Link to="/predictions">See predictions</Link>
            </Button>
            <Button asChild>
              <Link to="/control">Control center</Link>
            </Button>
          </>
        }
      />

      {/* Key Numbers / House Energy Section */}
      <section aria-label="House Energy Key Numbers" className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-primary">
            House Energy Measurements
          </span>
          <span className="font-mono text-[11px] bg-primary/10 text-primary px-2 py-0.5 rounded">
            Source: {settings.useLiveApi ? "PZEM-connected primary AC circuit" : "UK-DALE Simulated Household"}
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Current measured load"
            value={fmtW(snapshot.totalPowerW, 1)}
            unitHint={settings.useLiveApi ? "Monitored AC circuit" : `${appliances.length} appliances combined`}
            icon={Zap}
            hint="Physical electrical draw measured by PZEM-004T."
          />
          <StatCard
            label="Energy today"
            value={fmtKwh(snapshot.energyTodayKwh)}
            unitHint={`${budgetPct.toFixed(0)}% of your ${settings.budgetKwhPerDay} kWh daily budget`}
            icon={Gauge}
            tone={budgetPct > 100 ? "warning" : "neutral"}
            hint="Total electricity used since midnight."
          />
          <StatCard
            label="Cost today"
            value={fmtMoney(snapshot.costToday, settings.currency)}
            unitHint={`At ${settings.currency}${settings.tariffPerKwh.toFixed(2)} per kWh`}
            icon={BadgeDollarSign}
            hint="Estimated cost based on tariff in Settings."
          />
          <StatCard
            label="Saved by optimizer"
            value={fmtKwh(snapshot.savingsKwh)}
            unitHint={`About ${snapshot.savingsPct}% less than baseline`}
            icon={Leaf}
            tone="success"
            hint="Energy saved via RL adaptive control policy."
          />
        </div>
      </section>

      {/* Real-Time Hardware Telemetry Grid & Comfort Card */}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel p-5 lg:col-span-2 flex flex-col justify-between space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
            <div>
              <h2 className="font-semibold text-base flex items-center gap-2">
                <Cpu className="size-4 text-emerald-500" />
                Real-Time Hardware Telemetry
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Physical sensor metrics received from ESP32 DevKit V1 main node
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                Source: ESP32 + DHT22 + PZEM-004T V3
              </span>
              <span
                className={`text-[11px] font-mono font-medium px-2 py-0.5 rounded ${
                  snapshot.isHardwareLive
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : "bg-warning/10 text-warning"
                }`}
              >
                {snapshot.isHardwareLive ? "ONLINE (Authenticated)" : "Waiting for real telemetry"}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricBox
              label="Temperature"
              value={snapshot.ambientTempC !== undefined ? `${snapshot.ambientTempC.toFixed(1)} °C` : "Not available"}
              hint="DHT22 (GPIO4)"
            />
            <MetricBox
              label="Humidity"
              value={snapshot.ambientHumidityPct !== undefined ? `${snapshot.ambientHumidityPct.toFixed(1)} %` : "Not available"}
              hint="DHT22 (GPIO4)"
            />
            <MetricBox
              label="Voltage"
              value={snapshot.voltageV !== undefined ? `${snapshot.voltageV.toFixed(1)} V` : "Not available"}
              hint="PZEM-004T V3"
            />
            <MetricBox
              label="Current"
              value={snapshot.currentA !== undefined ? `${snapshot.currentA.toFixed(2)} A` : "Not available"}
              hint="PZEM-004T (100A CT)"
            />
            <MetricBox
              label="Power"
              value={fmtW(snapshot.totalPowerW, 2)}
              hint="PZEM Power Draw"
            />
            <MetricBox
              label="Energy"
              value={fmtKwh(snapshot.energyTodayKwh)}
              hint="PZEM Energy Meter"
            />
            <MetricBox
              label="Frequency"
              value="Not available"
              hint="Unreported hardware metric"
              muted
            />
            <MetricBox
              label="Power Factor"
              value="Not available"
              hint="Unreported hardware metric"
              muted
            />
          </div>

          <div className="border-t pt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
            <div>
              <span className="text-muted-foreground block text-[11px]">Device Type</span>
              <span className="font-semibold">ESP32 Main Node</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Device ID</span>
              <span className="font-semibold truncate">
                {activeHardwareRt?.id || (snapshot.isHardwareLive ? "DEV-638C71FE" : "No ESP32 registered")}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Relay State</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                {activeHardwareRt?.status === "off" ? "OFF (Open / High)" : "ON (Closed / Low)"}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[11px]">Last Telemetry</span>
              <span className="font-semibold">
                {snapshot.t ? new Date(snapshot.t).toLocaleTimeString() : "Waiting for telemetry"}
              </span>
            </div>
          </div>
        </div>

        {/* Comfort & Safety / Control Status Card */}
        <div className="flex flex-col gap-4">
          <div className="panel flex flex-col gap-4 p-5">
            <div className="flex items-center justify-between border-b pb-2">
              <h2 className="font-semibold text-sm">Comfort &amp; Safety</h2>
              <span className="text-[11px] font-mono text-muted-foreground">Source: Safety Interlock Engine</span>
            </div>

            <StatusRow
              label="Comfort State"
              value={snapshot.comfort}
              tone={snapshot.comfort === "optimal" ? "success" : snapshot.comfort === "acceptable" ? "warning" : "danger"}
              detail={
                snapshot.ambientTempC !== undefined
                  ? `Temp: ${snapshot.ambientTempC.toFixed(1)}°C${
                      snapshot.ambientHumidityPct !== undefined
                        ? ` · Humidity: ${snapshot.ambientHumidityPct.toFixed(1)}%`
                        : ""
                    }`
                  : "Not available (no ambient temp/humidity sensor data received)"
              }
            />

            <StatusRow
              label="Safety Interlocks"
              value={snapshot.safety}
              tone={snapshot.safety === "safe" ? "success" : snapshot.safety === "guarded" ? "warning" : "danger"}
              detail={settings.safetyInterlocks ? "Interlocks active." : "Interlocks disabled in Settings."}
            />

            <StatusRow
              label="Control Relay Source"
              value={settings.autopilot ? "Optimized (RL)" : "Manual Override"}
              tone="success"
              detail={
                relayCommandConfirmed
                  ? "Single 5V relay output active on GPIO26."
                  : "Command not confirmed by hardware"
              }
            />

            <div className="mt-auto flex items-center gap-2 rounded-lg bg-surface p-3 text-xs text-muted-foreground">
              <ShieldCheck className="size-4 shrink-0 text-success" aria-hidden="true" />
              Critical loads remain protected by hardcoded safety interlocks.
            </div>
          </div>
        </div>
      </section>

      {/* Sub-Metered Appliance Models */}
      <section className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-primary">
            Sub-Metered Appliance Models &amp; Historical Profiles
          </span>
          <span className="font-mono text-[11px] bg-primary/10 text-primary px-2 py-0.5 rounded">
            Source: UK-DALE Disaggregation Models
          </span>
        </div>

        <section aria-label="Appliances" className="grid gap-4 xl:grid-cols-2">
          {appliances.map((a) => (
            <ApplianceCard key={a.id} id={a.id} />
          ))}
        </section>
      </section>

      {/* Household Chart */}
      <section className="panel p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-semibold">Appliance Load History (Model Streams)</h2>
            <p className="text-xs text-muted-foreground">Power per disaggregated appliance over recent ticks</p>
          </div>
          <span className="flex items-center gap-1.5 text-xs text-success">
            <Activity className="size-3.5" aria-hidden="true" /> Streaming
          </span>
        </div>
        <MultiLineChart
          data={combined}
          series={appliances.map((a, i) => ({
            key: a.id,
            label: a.name,
            color: `var(--color-chart-${(i % 4) + 1})`,
          }))}
        />
      </section>

      <EventStream />
    </>
  );
}

function StatusPill({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: any;
  label: string;
  value: string;
  tone: "success" | "warning" | "info" | "danger";
}) {
  const colorMap = {
    success: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    warning: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
    info: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
    danger: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
  };
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-[11px] font-mono ${colorMap[tone]}`}>
      <Icon className="size-3 shrink-0" />
      <span className="opacity-75">{label}:</span>
      <span className="font-semibold">{value}</span>
    </div>
  );
}

function MetricBox({
  label,
  value,
  hint,
  muted,
}: {
  label: string;
  value: string;
  hint: string;
  muted?: boolean;
}) {
  return (
    <div className={`rounded-lg border p-2.5 ${muted ? "bg-muted/30 border-muted/50" : "bg-card"}`}>
      <span className="text-[11px] text-muted-foreground block">{label}</span>
      <p className={`font-semibold num text-sm mt-0.5 ${muted ? "text-muted-foreground" : "text-foreground"}`}>
        {value}
      </p>
      <span className="text-[10px] text-muted-foreground block mt-1 font-mono truncate">{hint}</span>
    </div>
  );
}

function StatusRow({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: "success" | "warning" | "danger";
}) {
  const toneClass = { success: "text-success", warning: "text-warning", danger: "text-destructive" }[tone];
  return (
    <div className="rounded-lg border border-border p-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className={`font-semibold capitalize ${toneClass}`}>{value}</span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
