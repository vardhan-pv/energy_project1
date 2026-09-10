import { createFileRoute, Link } from "@tanstack/react-router";
import { Activity, BadgeDollarSign, Gauge, Leaf, ShieldCheck, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApplianceCard } from "@/components/app/ApplianceCard";
import { EventStream } from "@/components/app/EventStream";
import { MultiLineChart } from "@/components/app/charts";
import { LoadingPanel, PageHeader, StatCard } from "@/components/app/primitives";
import { APPLIANCES } from "@/lib/energy/appliances";
import { fmtKwh, fmtMoney, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Home Energy Overview | Cognitive Energy Dashboard" },
      {
        name: "description",
        content:
          "See your home's live power use, today's energy and cost, savings and safety status in one simple view.",
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
  const { ready, snapshot, runtimes, settings, history, house, appliances } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader
          title={house ? house.name : "Overview"}
          description={house ? `${house.location} · ID: ${house.id} · Data Status: PENDING` : "Your home's energy at a glance."}
        />
        <LoadingPanel />
      </>
    );
  }

  const firstAppId = appliances[0]?.id;
  const baseHistory = firstAppId && runtimes[firstAppId] ? runtimes[firstAppId].history.slice(-45) : [];
  const combined = baseHistory.map((s, i) => {
    const row: Record<string, number> = { t: s.t };
    for (const a of appliances) {
      row[a.id] = runtimes[a.id]?.history.slice(-45)[i]?.powerW ?? 0;
    }
    return row;
  });

  const budgetPct = (snapshot.energyTodayKwh / settings.budgetKwhPerDay) * 100;
  const yesterday = history[history.length - 2]?.total ?? 0;

  return (
    <>
      <PageHeader
        title={settings.useLiveApi && house ? house.name : "Good to see you"}
        description={
          settings.useLiveApi && house
            ? `${house.location} · ${house.id} · Status: ${house.status}`
            : "Everything below updates live from the built-in simulator. No hardware is physically connected."
        }
        actions={
          <>
            <Button asChild variant="outline">
              <Link to="/predictions">See predictions</Link>
            </Button>
            <Button asChild>
              <Link to="/control">Control appliances</Link>
            </Button>
          </>
        }
      />

      <section aria-label="Key numbers" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total load now"
          value={fmtW(snapshot.totalPowerW, 1)}
          unitHint={settings.useLiveApi ? "Monitored AC load" : `${appliances.length} appliances combined`}
          icon={Zap}
          hint="How much electricity your home is drawing right this second."
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
          hint="Estimated cost based on the tariff set in Settings."
        />
        <StatCard
          label="Saved by the optimizer"
          value={fmtKwh(snapshot.savingsKwh)}
          unitHint={`About ${snapshot.savingsPct}% less than doing nothing`}
          icon={Leaf}
          tone="success"
          hint="Estimated energy avoided by the self-learning control policy."
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="panel p-5 lg:col-span-2">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-semibold">Live household load</h2>
              <p className="text-xs text-muted-foreground">Power per appliance over the last few minutes</p>
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
        </div>

        <div className="flex flex-col gap-4">
          <div className="panel flex flex-col gap-4 p-5">
            <h2 className="font-semibold">Comfort &amp; safety</h2>
            <StatusRow
              label="Comfort"
              value={snapshot.comfort}
              tone={snapshot.comfort === "optimal" ? "success" : snapshot.comfort === "acceptable" ? "warning" : "danger"}
              detail={
                snapshot.ambientTempC !== undefined
                  ? `Temp: ${snapshot.ambientTempC.toFixed(1)}°C${snapshot.ambientHumidityPct !== undefined ? ` · Humidity: ${snapshot.ambientHumidityPct.toFixed(1)}%` : ""}`
                  : "Not available (no ambient temp/humidity sensor data received)"
              }
            />
            <StatusRow
              label="Safety"
              value={snapshot.safety}
              tone={snapshot.safety === "safe" ? "success" : snapshot.safety === "guarded" ? "warning" : "danger"}
              detail={settings.safetyInterlocks ? "Interlocks are switched on." : "Interlocks are switched off in Settings."}
            />
            <StatusRow
              label="Yesterday"
              value={fmtKwh(yesterday)}
              tone={yesterday > snapshot.energyTodayKwh ? "success" : "warning"}
              detail="Total electricity used the previous day."
            />
            <div className="mt-auto flex items-center gap-2 rounded-lg bg-surface p-3 text-xs text-muted-foreground">
              <ShieldCheck className="size-4 shrink-0 text-success" aria-hidden="true" />
              The system will never switch off critical appliances, and it asks before any disruptive action.
            </div>
          </div>

          <div className="panel flex flex-col gap-3 p-5">
            <div className="flex items-center justify-between border-b pb-2">
              <h2 className="font-semibold text-sm">Real-Time Hardware Telemetry</h2>
              <span className="text-[11px] font-mono text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                {settings.useLiveApi && snapshot.isHardwareLive ? "LIVE ESP32" : "OFFLINE / SIMULATION"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded border p-2">
                <span className="text-muted-foreground">🌡 Temperature</span>
                <p className="font-semibold num text-sm mt-0.5">
                  {snapshot.ambientTempC !== undefined ? `${snapshot.ambientTempC.toFixed(1)} °C` : "Not available"}
                </p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">💧 Humidity</span>
                <p className="font-semibold num text-sm mt-0.5">
                  {snapshot.ambientHumidityPct !== undefined ? `${snapshot.ambientHumidityPct.toFixed(1)} %` : "Not available"}
                </p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">⚡ Voltage</span>
                <p className="font-semibold num text-sm mt-0.5">
                  {snapshot.voltageV !== undefined ? `${snapshot.voltageV.toFixed(1)} V` : "Not available"}
                </p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">🔌 Current</span>
                <p className="font-semibold num text-sm mt-0.5">
                  {snapshot.currentA !== undefined ? `${snapshot.currentA.toFixed(2)} A` : "Not available"}
                </p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">⚡ Power</span>
                <p className="font-semibold num text-sm mt-0.5">{fmtW(snapshot.totalPowerW, 2)}</p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">📊 Energy</span>
                <p className="font-semibold num text-sm mt-0.5">{fmtKwh(snapshot.energyTodayKwh)}</p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">∿ Frequency</span>
                <p className="font-semibold text-sm mt-0.5 text-muted-foreground">Not available</p>
              </div>
              <div className="rounded border p-2">
                <span className="text-muted-foreground">PF (Power Factor)</span>
                <p className="font-semibold text-sm mt-0.5 text-muted-foreground">Not available</p>
              </div>
            </div>

            <div className="border-t pt-2 mt-1 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Relay Status</span>
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                  {Object.values(runtimes).find(r => r.isHardware)?.status === "off" ? "OFF (Open)" : "ON (Closed)"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Device Status</span>
                <span className="font-semibold">
                  {snapshot.isHardwareLive ? "ONLINE (Authenticated)" : "Simulation Mode"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Device ID</span>
                <span className="font-mono">{(Object.values(runtimes).find(r => r.isHardware) as any)?.device_id || (snapshot.isHardwareLive ? "DEV-638C71FE" : "Not available")}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Appliance ID</span>
                <span className="font-mono">{snapshot.primaryApplianceId || "APP-79290D01"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Last Telemetry</span>
                <span className="font-mono">{snapshot.t ? new Date(snapshot.t).toLocaleTimeString() : "Not available"}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section aria-label="Appliances" className="grid gap-4 xl:grid-cols-2">
        {appliances.map((a) => (
          <ApplianceCard key={a.id} id={a.id} />
        ))}
      </section>

      <EventStream />
    </>
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
