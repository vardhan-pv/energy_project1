import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { APPLIANCES } from "@/lib/energy/appliances";
import { ControlCard } from "@/components/app/ControlCard";
import { LoadingPanel, PageHeader } from "@/components/app/primitives";

export const Route = createFileRoute("/control")({
  head: () => ({
    meta: [
      { title: "Intelligent Control | Cognitive Energy Dashboard" },
      { name: "description", content: "Switch modes, set target power, and monitor closed-loop interlock state." }
    ]
  }),
  component: ControlPage,
});

function ControlPage() {
  const { ready, appliances, house } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Intelligent Control" description="Configure appliance modes and target levels." />
        <LoadingPanel />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Intelligent Control"
        description="Configure appliance modes, adjust target levels, and watch the closed-loop controller maintain safety bounds."
      />
      <div className="grid gap-4 xl:grid-cols-2">
        {appliances.map((a) => (
          <ControlCard key={a.id} id={a.id} />
        ))}
      </div>
    </>
  );
}
