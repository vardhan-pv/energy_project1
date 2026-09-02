import { createFileRoute } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Cpu, RefreshCw, Wifi } from "lucide-react";
import { toast } from "sonner";
import { LoadingPanel, PageHeader } from "@/components/app/primitives";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/devices")({
  head: () => ({
    meta: [
      { title: "Device / IoT Status | Cognitive Energy Dashboard" }
    ]
  }),
  component: DevicesPage,
});

function DevicesPage() {
  const { ready, runtimes, appliances, injectFault, settings, house } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Device & IoT Status" description="Verify hardware links and connection health." />
        <LoadingPanel />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Device & IoT Status"
        description={
          settings.useLiveApi && house
            ? `Live connection health for ${house.name} (${house.id}).`
            : "Verify virtual hardware links, simulator signal levels, and battery parameters."
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        {appliances.map((a) => {
          const rt = runtimes[a.id];
          if (!rt) return null;
          return (
            <div key={a.id} className="panel p-5 flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <Cpu className="size-5 text-primary" />
                  <h3 className="font-semibold">{a.name}</h3>
                </div>
                <Badge variant={rt.online ? "default" : "destructive"}>
                  {rt.online ? "CONNECTED" : "OFFLINE"}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Signal Strength</span>
                  <p className="font-medium mt-0.5 flex items-center gap-1.5">
                    <Wifi className="size-4 text-success" /> {rt.signalPct ?? 100}%
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Battery Status</span>
                  <p className="font-medium mt-0.5">
                    {rt.batteryPct !== undefined ? `${rt.batteryPct}%` : "Mains Power"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Last Telemetry</span>
                  <p className="font-medium mt-0.5 text-xs">
                    {rt.lastSeen ? new Date(rt.lastSeen).toLocaleTimeString() : "N/A"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-muted-foreground uppercase">Data Source</span>
                  <p className="font-medium mt-0.5 text-xs text-success">
                    {settings.useLiveApi ? "Flask API (UK-DALE Replay)" : "Active (Simulator)"}
                  </p>
                </div>
              </div>

              <div className="mt-2 flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    injectFault(a.id);
                    toast.warning(`Toggled abnormality test on ${a.name}`);
                  }}
                >
                  <RefreshCw className="size-3.5 mr-1" />
                  Simulate Anomaly
                </Button>
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
