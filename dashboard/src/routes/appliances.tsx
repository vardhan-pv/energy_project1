import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ApplianceCard } from "@/components/app/ApplianceCard";
import { EmptyState, LoadingPanel, PageHeader } from "@/components/app/primitives";
import { APPLIANCES } from "@/lib/energy/appliances";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/appliances")({
  head: () => ({
    meta: [
      { title: "Appliances | Cognitive Energy Dashboard" },
      { name: "description", content: "Your four connected demo appliances with live power, cost and status." },
      { property: "og:title", content: "Appliances | Cognitive Energy Dashboard" },
      { property: "og:description", content: "Laptop, Kitchen Lights, Office Fan and Fridge at a glance." },
    ],
  }),
  component: AppliancesPage,
});

const ROOMS = ["All rooms", "Study", "Kitchen"];

function AppliancesPage() {
  const { ready, runtimes } = useEnergy();
  const [room, setRoom] = useState("All rooms");
  const [onlyRunning, setOnlyRunning] = useState(false);

  if (!ready) {
    return (
      <>
        <PageHeader title="Appliances" description="Your connected demo appliances." />
        <LoadingPanel />
      </>
    );
  }

  const list = APPLIANCES.filter((a) => (room === "All rooms" ? true : a.room === room)).filter((a) =>
    onlyRunning ? runtimes[a.id].status === "on" : true,
  );

  return (
    <>
      <PageHeader
        title="Appliances"
        description="Four trained appliance models are connected in this demo. Tap Control on any card to change how it runs."
        actions={
          <>
            {ROOMS.map((r) => (
              <Button key={r} size="sm" variant={room === r ? "default" : "outline"} onClick={() => setRoom(r)}>
                {r}
              </Button>
            ))}
            <Button
              size="sm"
              variant={onlyRunning ? "default" : "outline"}
              aria-pressed={onlyRunning}
              onClick={() => setOnlyRunning((v) => !v)}
            >
              Running only
            </Button>
          </>
        }
      />

      {list.length === 0 ? (
        <EmptyState
          title="No appliances match these filters"
          detail="Try choosing another room or turning off the 'Running only' filter."
        />
      ) : (
        <section className="grid gap-4 xl:grid-cols-2">
          {list.map((a) => (
            <ApplianceCard key={a.id} id={a.id} />
          ))}
        </section>
      )}
    </>
  );
}
