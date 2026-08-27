import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { PageHeader } from "@/components/app/primitives";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { BellRing, ShieldAlert, CheckCircle } from "lucide-react";

export const Route = createFileRoute("/alerts")({
  head: () => ({
    meta: [
      { title: "Alerts & Safety | Cognitive Energy Dashboard" }
    ]
  }),
  component: AlertsPage,
});

function AlertsPage() {
  const { alerts, acknowledgeAlert, clearAlerts } = useEnergy();
  const activeAlerts = alerts.filter(a => !a.acknowledged);

  return (
    <>
      <PageHeader
        title="Alerts & Safety"
        description="Monitor system abnormalities, safety overrides, and appliance warnings."
        actions={
          alerts.length > 0 && (
            <Button variant="outline" onClick={clearAlerts}>
              Clear all
            </Button>
          )
        }
      />

      {alerts.length === 0 ? (
        <div className="panel flex flex-col items-center justify-center py-12 text-center">
          <CheckCircle className="size-12 text-success mb-3" />
          <h3 className="font-semibold text-lg">System status nominal</h3>
          <p className="text-sm text-muted-foreground mt-1">No alerts or safety violations detected.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {alerts.map((a) => (
            <div key={a.id} className="panel p-4 flex flex-wrap items-center justify-between gap-3 border-l-4 border-l-destructive">
              <div className="flex items-start gap-3">
                <ShieldAlert className="size-5 text-destructive mt-0.5" />
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold">{a.title}</span>
                    <Badge variant="destructive" className="capitalize">{a.severity}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">{a.detail}</p>
                </div>
              </div>
              {!a.acknowledged && (
                <Button size="sm" onClick={() => acknowledgeAlert(a.id)}>
                  Acknowledge
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
