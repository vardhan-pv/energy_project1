import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { PageHeader } from "@/components/app/primitives";
import { EventStream } from "@/components/app/EventStream";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History | Cognitive Energy Dashboard" }
    ]
  }),
  component: HistoryPage,
});

function HistoryPage() {
  return (
    <>
      <PageHeader
        title="Event History"
        description="Comprehensive audit logs of system decisions, optimizer nudges, and safety interlocks."
      />
      <EventStream limit={50} title="Complete Activity Stream" />
    </>
  );
}
