import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/app/primitives";
import { DailyBarChart } from "@/components/app/charts";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Energy Analytics | Cognitive Energy Dashboard" },
      { name: "description", content: "Historical appliance energy stack bars and optimization savings statistics." }
    ]
  }),
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const { history } = useEnergy();

  return (
    <>
      <PageHeader
        title="Energy Analytics"
        description="Review historical metrics, savings distributions, and stacked energy loads per day."
      />
      <div className="panel p-5">
        <h2 className="mb-4 font-semibold">Daily Load Distribution (Last 30 Days)</h2>
        <DailyBarChart data={history} height={400} />
      </div>
    </>
  );
}
