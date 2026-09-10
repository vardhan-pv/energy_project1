import { createFileRoute } from "@tanstack/react-router";
import { BellRing, CheckCircle, ShieldAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/app/primitives";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/alerts")({
  head: () => ({
    meta: [
      { title: "Alerts & Safety | Cognitive Energy Dashboard" },
      { name: "description", content: "Real-time backend safety alerts, interlocks, and abnormality events." },
    ],
  }),
  component: AlertsPage,
});

export function AlertsPage() {
  const { alerts, acknowledgeAlert, clearAlerts } = useEnergy();
  const unreadCount = alerts.filter((a) => !a.acknowledged).length;

  return (
    <>
      <PageHeader
        title="Alerts &amp; Safety Events"
        description="Monitor backend safety overrides, load anomalies, and physical interlocks."
        actions={
          alerts.length > 0 ? (
            <Button variant="outline" size="sm" onClick={clearAlerts}>
              Clear all alerts
            </Button>
          ) : null
        }
      />

      <div className="flex items-center justify-between border-b pb-2 text-xs text-muted-foreground">
        <span className="font-semibold uppercase tracking-wider text-[11px] text-primary">
          Real-Time Safety &amp; Interlock Monitor
        </span>
        <span className="font-mono text-[11px] bg-primary/10 text-primary px-2 py-0.5 rounded">
          Source: Backend Safety Interlock System
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="panel flex flex-col items-center justify-center py-16 text-center space-y-3">
          <div className="grid size-14 place-items-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="size-8" />
          </div>
          <div>
            <h3 className="font-semibold text-base text-foreground">No active alerts</h3>
            <p className="text-xs text-muted-foreground mt-1 max-w-sm">
              All safety interlocks nominal. System is operating safely with zero power anomalies or parameter breaches.
            </p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {alerts.map((a) => (
            <div
              key={a.id}
              className={`panel p-4 flex flex-wrap items-center justify-between gap-3 border-l-4 ${
                a.severity === "critical"
                  ? "border-l-destructive"
                  : a.severity === "warning"
                  ? "border-l-amber-500"
                  : "border-l-primary"
              }`}
            >
              <div className="flex items-start gap-3">
                <ShieldAlert className="size-5 text-destructive mt-0.5 shrink-0" />
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm">{a.title}</span>
                    <Badge variant={a.severity === "critical" ? "destructive" : "outline"} className="capitalize text-xs">
                      {a.severity}
                    </Badge>
                    <span className="text-[11px] font-mono text-muted-foreground">
                      {new Date(a.t).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{a.detail}</p>
                </div>
              </div>
              {!a.acknowledged ? (
                <Button size="sm" variant="outline" onClick={() => acknowledgeAlert(a.id)}>
                  Acknowledge
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
