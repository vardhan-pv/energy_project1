import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ApplianceCard } from "@/components/app/ApplianceCard";
import { EmptyState, LoadingPanel, PageHeader } from "@/components/app/primitives";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/appliances")({
  head: () => ({
    meta: [
      { title: "Appliances | Cognitive Energy Dashboard" },
      { name: "description", content: "Connected appliance profiles, UK-DALE disaggregation models and physical AC circuit monitoring." },
      { property: "og:title", content: "Appliances | Cognitive Energy Dashboard" },
      { property: "og:description", content: "Laptop, Kitchen Lights, Office Fan and Fridge profiles." },
    ],
  }),
  component: AppliancesPage,
});

export function AppliancesPage() {
  const { ready, runtimes, appliances, house, settings } = useEnergy();
  const [room, setRoom] = useState("All rooms");
  const [onlyRunning, setOnlyRunning] = useState(false);

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Appliances" description="Loading connected appliance profiles..." />
        <LoadingPanel />
      </>
    );
  }

  const rooms = ["All rooms", ...Array.from(new Set(appliances.map((a) => a.room)))];

  const list = appliances
    .filter((a) => (room === "All rooms" ? true : a.room === room))
    .filter((a) => (onlyRunning ? runtimes[a.id]?.status === "on" : true));

  return (
    <>
      <PageHeader
        title="Appliance Models &amp; Sub-Metering"
        description={
          settings.useLiveApi
            ? "Physical electrical load is measured via the primary PZEM-004T AC circuit. Individual appliance curves represent disaggregated UK-DALE model predictions."
            : `${appliances.length} simulated appliance models are connected.`
        }
        actions={
          <>
            {rooms.map((r) => (
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

      {appliances.length === 0 ? (
        <EmptyState
          title="No appliances configured"
          detail="Your production database currently contains no registered appliances. Register an appliance via the backend API or enable simulation mode."
        />
      ) : list.length === 0 ? (
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
