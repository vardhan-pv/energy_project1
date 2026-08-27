import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Radio } from "lucide-react";
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
import { LoadingPanel, PageHeader, RiskBadge, StatCard, StatusDot } from "@/components/app/primitives";
import { APPLIANCES, APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtClock, fmtKwh, fmtTemp, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId } from "@/lib/energy/types";

export const Route = createFileRoute("/live")({
  head: () => ({
    meta: [
      { title: "Live Monitoring | Cognitive Energy Dashboard" },
      {
        name: "description",
        content: "Watch power, energy, temperature and status update in real time for every appliance.",
      },
      { property: "og:title", content: "Live Monitoring | Cognitive Energy Dashboard" },
      { property: "og:description", content: "Real-time simulated telemetry for four home appliances." },
    ],
  }),
  component: LivePage,
});

const WINDOWS = [
  { value: "30", label: "Last 1 minute" },
  { value: "60", label: "Last 2 minutes" },
  { value: "90", label: "Last 3 minutes" },
];

function LivePage() {
  const { ready, runtimes, snapshot, settings } = useEnergy();
  const [selected, setSelected] = useState<ApplianceId | "all">("all");
  const [win, setWin] = useState("60");

  if (!ready) {
    return (
      <>
        <PageHeader title="Live Monitoring" description="Real-time readings from every appliance." />
        <LoadingPanel />
      </>
    );
  }

  const points = Number(win);
  const shown = selected === "all" ? APPLIANCES.map((a) => a.id) : [selected];
  const base = runtimes.laptop.history.slice(-points);
  const combined = base.map((s, i) => {
    const row: Record<string, number> = { t: s.t };
    for (const id of APPLIANCES.map((a) => a.id)) {
      row[id] = runtimes[id].history.slice(-points)[i]?.powerW ?? 0;
    }
    return row;
  });

  return (
    <>
      <PageHeader
        title="Live Monitoring"
        description="Readings refresh every few seconds. Pick an appliance or a time window to focus."
        actions={
          <>
            <Select value={selected} onValueChange={(v) => setSelected(v as ApplianceId | "all")}>
              <SelectTrigger className="w-48" aria-label="Filter by appliance">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All appliances</SelectItem>
                {APPLIANCES.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
          </>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total load" value={fmtW(snapshot.totalPowerW, 1)} unitHint="Right now" icon={Radio} />
        <StatCard label="Energy today" value={fmtKwh(snapshot.energyTodayKwh)} unitHint="Since midnight" />
        <StatCard
          label="Refresh rate"
          value={`${(settings.refreshMs / 1000).toFixed(1)}s`}
          unitHint="Change it in Settings"
        />
        <StatCard label="Last update" value={fmtClock(snapshot.t)} unitHint="Local time" tone="info" />
      </section>

      <section className="panel p-5">
        <h2 className="mb-4 font-semibold">Power over time</h2>
        <MultiLineChart
          data={combined}
          series={shown.map((id, i) => ({
            key: id,
            label: APPLIANCE_MAP[id].name,
            color: `var(--color-chart-${(i % 4) + 1})`,
          }))}
          height={320}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {shown.map((id) => {
          const rt = runtimes[id];
          const profile = APPLIANCE_MAP[id];
          return (
            <div key={id} className="panel p-5">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <StatusDot state={rt.online ? rt.status : "offline"} />
                  <h3 className="font-semibold">{profile.name}</h3>
                  <Badge variant="outline" className="capitalize">
                    {rt.mode}
                  </Badge>
                </div>
                <RiskBadge risk={rt.risk} />
              </div>
              <dl className="mb-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                <Cell label="Power" value={fmtW(rt.powerW, 1)} />
                <Cell label="Energy today" value={fmtKwh(rt.energyTodayKwh)} />
                <Cell label="Temperature" value={fmtTemp(rt.temperatureC)} />
                <Cell label="Est. cost" value={`${settings.currency}${(rt.energyTodayKwh * settings.tariffPerKwh).toFixed(2)}`} />
              </dl>
              <PowerAreaChart data={rt.history.slice(-points)} height={150} />
            </div>
          );
        })}
      </section>

      <div className="flex justify-end">
        <Button variant="outline" onClick={() => setSelected("all")}>
          Reset filters
        </Button>
      </div>

      <EventStream limit={14} title="Live event stream" />
    </>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] tracking-wide text-muted-foreground uppercase">{label}</dt>
      <dd className="num font-semibold">{value}</dd>
    </div>
  );
}
