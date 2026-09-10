import { createFileRoute } from "@tanstack/react-router";
import { Brain, Activity, BarChart3, Clock, Layers, ShieldCheck, Zap } from "lucide-react";
import { PageHeader } from "@/components/app/primitives";
import { DailyBarChart } from "@/components/app/charts";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId } from "@/lib/energy/types";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Cognitive Analysis | Cognitive Energy Dashboard" },
      { name: "description", content: "Multi-dimensional analytical metrics: ATF, ERI, DSC, CDI, and UBD cognitive modeling." },
      { property: "og:title", content: "Cognitive Analysis | Cognitive Energy Dashboard" },
    ],
  }),
  component: AnalyticsPage,
});

const COGNITIVE_METRICS = [
  {
    code: "ATF",
    name: "Adaptive Temporal Features",
    icon: Clock,
    color: "border-purple-500/40 text-purple-600 dark:text-purple-400 bg-purple-500/10",
    description: "Extracts cyclical time-of-day, day-of-week, and rolling load lags to capture routine signatures.",
  },
  {
    code: "ERI",
    name: "Energy Routine Index",
    icon: Activity,
    color: "border-blue-500/40 text-blue-600 dark:text-blue-400 bg-blue-500/10",
    description: "Quantifies usage predictability (0–100). Higher scores indicate strict, repeatable routines.",
  },
  {
    code: "DSC",
    name: "Demand Stability & Change",
    icon: Layers,
    color: "border-cyan-500/40 text-cyan-600 dark:text-cyan-400 bg-cyan-500/10",
    description: "Measures sudden power ramp-ups and load variances to isolate steady vs. volatile draws.",
  },
  {
    code: "CDI",
    name: "Cognitive Demand Intelligence",
    icon: Brain,
    color: "border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10",
    description: "Evaluates overall load controllability and optimization responsiveness for RL action selection.",
  },
  {
    code: "UBD",
    name: "Usage Behavior Dynamics",
    icon: BarChart3,
    color: "border-amber-500/40 text-amber-600 dark:text-amber-400 bg-amber-500/10",
    description: "Tracks long-term operational consistency and peak coincidence across household appliances.",
  },
];

const COGNITIVE_DATA: Record<
  ApplianceId,
  {
    name: string;
    eri: number;
    eriLabel: string;
    cdi: number;
    cdiLabel: string;
    ubd: number;
    ubdLabel: string;
    stability: string;
    notes: string;
  }
> = {
  fridge: {
    name: "Fridge",
    eri: 95.5711,
    eriLabel: "Highly Regular",
    cdi: 79.8768,
    cdiLabel: "High Intelligence",
    ubd: 73.0265,
    ubdLabel: "Consistent High",
    stability: "Very High (Duty Cycle)",
    notes: "Strict compressor cycling pattern; ideal candidate for peak shaving.",
  },
  laptop: {
    name: "Laptop",
    eri: 81.9876,
    eriLabel: "Highly Regular",
    cdi: 78.3,
    cdiLabel: "High Intelligence",
    ubd: 78.2374,
    ubdLabel: "Consistent High",
    stability: "High (Workstation)",
    notes: "Predictable weekday office hours; steady charging load.",
  },
  office_fan: {
    name: "Office Fan",
    eri: 79.7021,
    eriLabel: "Regular",
    cdi: 61.7271,
    cdiLabel: "Moderate",
    ubd: 51.0365,
    ubdLabel: "Moderately Dynamic",
    stability: "Moderate",
    notes: "Temperature-dependent activation; suitable for Eco mode reduction.",
  },
  kitchen_lights: {
    name: "Kitchen Lights",
    eri: 70.0012,
    eriLabel: "Regular",
    cdi: 60.6319,
    cdiLabel: "Moderate",
    ubd: 51.2491,
    ubdLabel: "Moderately Dynamic",
    stability: "Moderate (Evening Peak)",
    notes: "Coincides with evening food preparation; routine lighting usage.",
  },
};

export function AnalyticsPage() {
  const { history } = useEnergy();

  return (
    <>
      <PageHeader
        title="Cognitive Energy Analytics"
        description="IREOS multi-dimensional analytical pipeline: ERI, DSC, CDI, and UBD cognitive modeling."
      />

      {/* Analytical Metric Framework Cards */}
      <section className="space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="font-semibold text-sm flex items-center gap-2">
            <Brain className="size-4 text-purple-500" />
            IREOS Cognitive Framework Metrics
          </h2>
          <span className="font-mono text-[11px] bg-purple-500/10 text-purple-600 dark:text-purple-400 px-2 py-0.5 rounded">
            Source: Analytical Model Pipeline
          </span>
        </div>

        <div className="grid gap-3 md:grid-cols-3 lg:grid-cols-5">
          {COGNITIVE_METRICS.map((m) => (
            <div key={m.code} className="panel p-4 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded font-mono font-bold text-xs border ${m.color}`}>
                    {m.code}
                  </span>
                  <m.icon className="size-4 text-muted-foreground" />
                </div>
                <h3 className="font-semibold text-xs text-foreground">{m.name}</h3>
                <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{m.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Appliance Cognitive State Table */}
      <section className="panel p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
          <div>
            <h2 className="font-semibold text-base flex items-center gap-2">
              <Zap className="size-4 text-emerald-500" />
              Appliance Cognitive State &amp; Intelligence Scores
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Calculated routine metrics based on UK-DALE disaggregation modeling
            </p>
          </div>
          <span className="text-[11px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2.5 py-1 rounded">
            Analytical / Model Results (Not Live Hardware Sensors)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b bg-muted/30 text-muted-foreground font-mono">
                <th className="p-3">Appliance</th>
                <th className="p-3">Energy Routine Index (ERI)</th>
                <th className="p-3">Cognitive Intelligence (CDI)</th>
                <th className="p-3">Behavior Dynamics (UBD)</th>
                <th className="p-3">Demand Stability</th>
                <th className="p-3">Optimization Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(COGNITIVE_DATA).map(([id, data]) => (
                <tr key={id} className="hover:bg-muted/20">
                  <td className="p-3 font-semibold text-sm">
                    {data.name}
                    <span className="block text-[11px] font-mono font-normal text-muted-foreground">
                      {id}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="font-mono font-semibold num text-sm block">{data.eri.toFixed(4)}</span>
                    <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                      {data.eriLabel}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="font-mono font-semibold num text-sm block">{data.cdi.toFixed(4)}</span>
                    <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">
                      {data.cdiLabel}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="font-mono font-semibold num text-sm block">{data.ubd.toFixed(4)}</span>
                    <span className="text-[11px] text-purple-600 dark:text-purple-400 font-medium">
                      {data.ubdLabel}
                    </span>
                  </td>
                  <td className="p-3">
                    <span className="font-medium text-foreground">{data.stability}</span>
                  </td>
                  <td className="p-3 text-muted-foreground max-w-xs">{data.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Historical Load Bar Chart */}
      <section className="panel p-5 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="font-semibold text-sm">Historical Daily Load Distribution (30 Days)</h2>
          <span className="font-mono text-[11px] text-muted-foreground">Source: Historical Dataset</span>
        </div>
        <DailyBarChart data={history} height={320} />
      </section>
    </>
  );
}
