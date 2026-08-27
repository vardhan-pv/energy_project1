import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { APPLIANCES } from "@/lib/energy/appliances";
import { PredictionCard } from "@/components/app/PredictionCard";
import { PageHeader } from "@/components/app/primitives";

export const Route = createFileRoute("/predictions")({
  head: () => ({
    meta: [
      { title: "Predictions | Cognitive Energy Dashboard" },
      { name: "description", content: "Forecasted power curves and expectation models for appliances." }
    ]
  }),
  component: PredictionsPage,
});

function PredictionsPage() {
  const { ready } = useEnergy();

  return (
    <>
      <PageHeader
        title="Predictions & Forecasts"
        description="Machine learning expectation models predict upcoming draw windows and compute confidence metrics."
      />
      <div className="grid gap-4 xl:grid-cols-2">
        {APPLIANCES.map((a) => (
          <PredictionCard key={a.id} id={a.id} />
        ))}
      </div>
    </>
  );
}
