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
  const { ready, snapshot, runtimes, settings, history } = useEnergy();

  if (!ready) {
    return (
      <>
        <PageHeader title="Overview" description="Your home's energy at a glance." />
        <LoadingPanel />
      </>
    );
  }

  const combined = runtimes.laptop.history.slice(-45).map((s, i) => ({
    t: s.t,
    laptop: s.powerW,
    kitchen_lights: runtimes.kitchen_lights.history.slice(-45)[i]?.powerW ?? 0,
    office_fan: runtimes.office_fan.history.slice(-45)[i]?.powerW ?? 0,
    fridge: runtimes.fridge.history.slice(-45)[i]?.powerW ?? 0,
  }));

  const budgetPct = (snapshot.energyTodayKwh / settings.budgetKwhPerDay) * 100;
  const yesterday = history[history.length - 2]?.total ?? 0;

  return (
    <>
      <PageHeader
        title="Good to see you"
        description={
          settings.useLiveApi
            ? "Live data from trained ML models. Connected to the Flask API backend."
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
          unitHint="All four appliances combined"
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
            series={[
              { key: "fridge", label: "Fridge", color: "var(--color-chart-1)" },
              { key: "laptop", label: "Laptop", color: "var(--color-chart-2)" },
              { key: "office_fan", label: "Office Fan", color: "var(--color-chart-3)" },
              { key: "kitchen_lights", label: "Kitchen Lights", color: "var(--color-chart-4)" },
            ]}
          />
        </div>

        <div className="panel flex flex-col gap-4 p-5">
          <h2 className="font-semibold">Comfort &amp; safety</h2>
          <StatusRow
            label="Comfort"
            value={snapshot.comfort}
            tone={snapshot.comfort === "optimal" ? "success" : snapshot.comfort === "acceptable" ? "warning" : "danger"}
            detail="Based on room temperature and fan behaviour."
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
            The system will never switch off the fridge, and it asks before any disruptive action.
          </div>
        </div>
      </section>

      <section aria-label="Appliances" className="grid gap-4 xl:grid-cols-2">
        {APPLIANCES.map((a) => (
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
