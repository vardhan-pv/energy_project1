import { createFileRoute } from "@tanstack/react-router";
import { ArrowRight, Brain, Clock, Cpu, LineChart, Sliders } from "lucide-react";
import { useEnergy } from "@/lib/energy/store";
import { PredictionCard } from "@/components/app/PredictionCard";
import { LoadingPanel, PageHeader } from "@/components/app/primitives";

export const Route = createFileRoute("/predictions")({
  head: () => ({
    meta: [
      { title: "Predictions | Cognitive Energy Dashboard" },
      { name: "description", content: "Forecasted power curves and expectation models for appliances." },
    ],
  }),
  component: PredictionsPage,
});

export function PredictionsPage() {
  const { ready, appliances, house } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Predictions & Forecasts" description="Machine learning expectation models predict upcoming draw windows." />
        <LoadingPanel />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="ML Predictions &amp; Power Forecasting"
        description="Forecasting models predict expected usage bands over 30-minute horizons based on learned UK-DALE routine signatures."
      />

      {/* Workflow Diagram */}
      <section className="panel p-5 space-y-3">
        <div className="flex items-center justify-between border-b pb-2">
          <h2 className="font-semibold text-sm flex items-center gap-2">
            <LineChart className="size-4 text-emerald-500" />
            Predictive Machine Learning Workflow
          </h2>
          <span className="font-mono text-[11px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded">
            Source: UK-DALE Disaggregation Models
          </span>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-center pt-2">
          <WorkflowStep label="Historical Data" sub="UK-DALE Dataset" icon={Clock} color="bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30" />
          <ArrowRight className="size-4 text-muted-foreground shrink-0" />
          <WorkflowStep label="Feature Eng" sub="ATF Lag Signals" icon={Cpu} color="bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30" />
          <ArrowRight className="size-4 text-muted-foreground shrink-0" />
          <WorkflowStep label="ML Prediction" sub="Power Horizon" icon={LineChart} color="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30" />
          <ArrowRight className="size-4 text-muted-foreground shrink-0" />
          <WorkflowStep label="Cognitive State" sub="ERI / CDI / UBD" icon={Brain} color="bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/30" />
          <ArrowRight className="size-4 text-muted-foreground shrink-0" />
          <WorkflowStep label="RL Optimization" sub="Action Selection" icon={Sliders} color="bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30" />
        </div>
      </section>

      {/* Prediction Cards */}
      <div className="grid gap-4 xl:grid-cols-2">
        {appliances.map((a) => (
          <PredictionCard key={a.id} id={a.id} />
        ))}
      </div>
    </>
  );
}

function WorkflowStep({
  label,
  sub,
  icon: Icon,
  color,
}: {
  label: string;
  sub: string;
  icon: any;
  color: string;
}) {
  return (
    <div className={`flex-1 min-w-[120px] p-2.5 rounded-lg border flex flex-col items-center gap-1 ${color}`}>
      <Icon className="size-4" />
      <span className="font-semibold text-xs">{label}</span>
      <span className="text-[10px] opacity-80">{sub}</span>
    </div>
  );
}
