import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Activity, Cpu, Database, Radio, ShieldCheck, Wifi, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EventStream } from "@/components/app/EventStream";
import { MultiLineChart, PowerAreaChart } from "@/components/app/charts";
import { EmptyState, LoadingPanel, PageHeader, StatCard, StatusDot } from "@/components/app/primitives";
import { fmtClock, fmtKwh, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/live")({
  head: () => ({
    meta: [
      { title: "Live Hardware Telemetry | Cognitive Energy Dashboard" },
      {
        name: "description",
        content: "Real-time ESP32 DevKit V1 hardware telemetry panel: Voltage, Current, Power, Energy, Temperature, and Humidity.",
      },
    ],
  }),
  component: LivePage,
});

const WINDOWS = [
  { value: "30", label: "Last 1 minute" },
  { value: "60", label: "Last 2 minutes" },
  { value: "90", label: "Last 3 minutes" },
];

export function LivePage() {
  const { ready, runtimes, snapshot, settings, house, appliances } = useEnergy();
  const [win, setWin] = useState("60");

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Live Hardware Telemetry" description="Connecting to ESP32 node..." />
        <LoadingPanel />
      </>
    );
  }

  const points = Number(win);
  const firstAppId = appliances[0]?.id;
  const firstAppHistory = firstAppId && runtimes[firstAppId]?.history ? runtimes[firstAppId].history : [];
  const base = firstAppHistory.slice(-points);
  const combined = base.map((s, i) => {
    const row: Record<string, number> = { t: s.t };
    for (const id of appliances.map((a) => a.id)) {
      const appHist = runtimes[id]?.history ?? [];
      row[id] = appHist.slice(-points)[i]?.powerW ?? 0;
    }
    return row;
  });

  const activeHardwareRt = Object.values(runtimes).find((r) => r.isHardware);

  return (
    <>
      <PageHeader
        title="Live Hardware Telemetry Stream"
        description="Direct sensor measurements received from ESP32 DevKit V1 via PZEM-004T V3 and DHT22."
        actions={
          <Select value={win} onValueChange={setWin}>
            <SelectTrigger className="w-40" aria-label="Time window">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {WINDOWS.map((w) => (
                <SelectItem key={w.value} value={w.value}>
                  {w.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        }
      />

      {/* Main ESP32 Live Telemetry Panel */}
      <section className="panel p-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Cpu className="size-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold flex items-center gap-2">
                IREOS ESP32 Main Node
                <span
                  className={`text-[11px] font-mono font-medium px-2 py-0.5 rounded ${
                    snapshot.isHardwareLive
                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                      : "bg-warning/15 text-warning border border-warning/30"
                  }`}
                >
                  {snapshot.isHardwareLive ? "ONLINE (Authenticated)" : "Simulation / Waiting for Telemetry"}
                </span>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Physical IoT Node · PZEM-004T V3 + DHT22 + 5V Relay + 16x2 I2C LCD
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs font-mono">
            <div className="flex items-center gap-1.5 bg-muted px-3 py-1.5 rounded-lg border">
              <Wifi className="size-3.5 text-cyan-500" />
              <span>Network: Wi-Fi / Render API</span>
            </div>
            <div className="flex items-center gap-1.5 bg-muted px-3 py-1.5 rounded-lg border">
              <ShieldCheck className="size-3.5 text-emerald-500" />
              <span>Auth: {snapshot.isHardwareLive ? "Authenticated" : "Unauthenticated"}</span>
            </div>
          </div>
        </div>

        {!snapshot.isHardwareLive && settings.useLiveApi ? (
          <EmptyState
            title="Waiting for real ESP32 telemetry..."
            detail="The backend is running in production Live API mode. Once your physical ESP32 sends a POST payload to /api/telemetry, real hardware metrics will populate below automatically."
          />
        ) : null}

        {/* Real Sensor Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <SensorBox
            label="Ambient Temperature"
            value={snapshot.ambientTempC !== undefined ? `${snapshot.ambientTempC.toFixed(1)} °C` : "Not available"}
            sensor="DHT22 Sensor (GPIO4)"
          />
          <SensorBox
            label="Ambient Humidity"
            value={snapshot.ambientHumidityPct !== undefined ? `${snapshot.ambientHumidityPct.toFixed(1)} %` : "Not available"}
            sensor="DHT22 Sensor (GPIO4)"
          />
          <SensorBox
            label="AC Voltage"
            value={snapshot.voltageV !== undefined ? `${snapshot.voltageV.toFixed(1)} V` : "Not available"}
            sensor="PZEM-004T V3 (TX16/RX17)"
          />
          <SensorBox
            label="AC Current"
            value={snapshot.currentA !== undefined ? `${snapshot.currentA.toFixed(2)} A` : "Not available"}
            sensor="PZEM 100A Split-Core CT"
          />
          <SensorBox
            label="AC Power Draw"
            value={fmtW(snapshot.totalPowerW, 2)}
            sensor="PZEM Real-Time Power"
          />
          <SensorBox
            label="Energy Accumulation"
            value={fmtKwh(snapshot.energyTodayKwh)}
            sensor="PZEM Energy Register"
          />
          <SensorBox
            label="Line Frequency"
            value="Not available"
            sensor="Unreported hardware metric"
            muted
          />
          <SensorBox
            label="Power Factor (PF)"
            value="Not available"
            sensor="Unreported hardware metric"
            muted
          />
        </div>

        {/* Hardware Status Footer */}
        <div className="border-t pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div>
            <span className="text-muted-foreground block text-[11px]">Relay Hardware Output</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400">
              {activeHardwareRt?.status === "off" ? "OFF (Open / HIGH)" : "ON (Closed / LOW)"}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Device ID</span>
            <span className="font-semibold">{activeHardwareRt?.id || "DEV-638C71FE"}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Primary Appliance ID</span>
            <span className="font-semibold">{snapshot.primaryApplianceId || "APP-79290D01"}</span>
          </div>
          <div>
            <span className="text-muted-foreground block text-[11px]">Last Telemetry Arrival</span>
            <span className="font-semibold">
              {snapshot.t ? new Date(snapshot.t).toLocaleTimeString() : "Waiting for telemetry"}
            </span>
          </div>
        </div>
      </section>

      {/* Chart Panel */}
      <section className="panel p-5 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="font-semibold text-sm">Disaggregated Appliance Load History (Model Streams)</h2>
          <span className="font-mono text-[11px] text-muted-foreground">Source: Disaggregation Models</span>
        </div>
        <MultiLineChart
          data={combined}
          series={appliances.map((a, i) => ({
            key: a.id,
            label: a.name,
            color: `var(--color-chart-${(i % 4) + 1})`,
          }))}
          height={280}
        />
      </section>

      <EventStream limit={14} title="Live hardware event log" />
    </>
  );
}

function SensorBox({
  label,
  value,
  sensor,
  muted,
}: {
  label: string;
  value: string;
  sensor: string;
  muted?: boolean;
}) {
  return (
    <div className={`rounded-xl border p-3.5 ${muted ? "bg-muted/20 border-muted/40" : "bg-card"}`}>
      <span className="text-xs text-muted-foreground block font-medium">{label}</span>
      <p className={`font-semibold num text-lg mt-1 ${muted ? "text-muted-foreground" : "text-foreground"}`}>
        {value}
      </p>
      <span className="text-[11px] text-muted-foreground block mt-1.5 font-mono">{sensor}</span>
    </div>
  );
}
