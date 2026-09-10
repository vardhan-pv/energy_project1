import { createFileRoute } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Cpu, Database, Radio, RefreshCw, ShieldCheck, Wifi, Zap } from "lucide-react";
import { toast } from "sonner";
import { EmptyState, LoadingPanel, PageHeader } from "@/components/app/primitives";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/devices")({
  head: () => ({
    meta: [
      { title: "IoT Devices & Pinout Status | Cognitive Energy Dashboard" },
      { name: "description", content: "ESP32 DevKit V1 main microcontroller node, sensor pinout configuration, and connection health." },
    ],
  }),
  component: DevicesPage,
});

export function DevicesPage() {
  const { ready, runtimes, snapshot, settings, house } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="IoT Devices & Pinout Status" description="Connecting to ESP32 node..." />
        <LoadingPanel />
      </>
    );
  }

  const activeHardwareRt = Object.values(runtimes).find((r) => r.isHardware);

  return (
    <>
      <PageHeader
        title="IoT Device Hardware Architecture"
        description={
          settings.useLiveApi && house
            ? `Connection health for ${house.name} (${house.id}).`
            : "Operating in Simulation mode. Review physical ESP32 node configuration and pinout specs below."
        }
      />

      {/* Primary Hardware Node Card */}
      <section className="panel p-6 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="grid size-11 place-items-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
              <Cpu className="size-6" />
            </div>
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2">
                IREOS ESP32 Main Node
                <Badge
                  className={
                    snapshot.isHardwareLive
                      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                      : "bg-warning/15 text-warning border-warning/30"
                  }
                >
                  {snapshot.isHardwareLive ? "ONLINE (Authenticated)" : "OFFLINE / SIMULATION"}
                </Badge>
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Main Physical Microcontroller · Dual-Core Xtensa LX6 · Wi-Fi + HTTPS
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
            <span className="bg-muted px-2.5 py-1 rounded border">
              Device Type: ESP32 DevKit V1
            </span>
            <span className="bg-muted px-2.5 py-1 rounded border">
              Device ID: {activeHardwareRt?.id || "DEV-638C71FE"}
            </span>
          </div>
        </div>

        {/* Device Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground uppercase text-[11px] block">Authentication</span>
            <span className="font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5 block flex items-center gap-1">
              <ShieldCheck className="size-3.5" />
              {snapshot.isHardwareLive ? "Authenticated (Configured)" : "Configured"}
            </span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground uppercase text-[11px] block">Power Supply</span>
            <span className="font-semibold text-foreground mt-0.5 block">
              AC Mains (PZEM-004T)
            </span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground uppercase text-[11px] block">Signal Quality</span>
            <span className="font-semibold text-foreground mt-0.5 block font-mono">
              Not available (Mains)
            </span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground uppercase text-[11px] block">Last Telemetry</span>
            <span className="font-semibold text-foreground mt-0.5 block font-mono">
              {snapshot.t ? new Date(snapshot.t).toLocaleTimeString() : "Not available"}
            </span>
          </div>
        </div>

        {/* Connected Sensors & GPIO Pinout Specifications */}
        <div className="space-y-3 border-t pt-4">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Zap className="size-4 text-primary" />
            Connected Physical Sensors &amp; GPIO Pinouts
          </h3>

          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4 text-xs">
            <PinoutCard
              name="DHT22 Sensor"
              purpose="Ambient Temp & Humidity"
              pins="DATA → GPIO4 · VCC → 3.3V/5V · GND"
              status="Active"
            />
            <PinoutCard
              name="PZEM-004T V3"
              purpose="AC Load Measurement"
              pins="TX → GPIO16 (RX2) · RX → GPIO17 (TX2)"
              status="Active"
            />
            <PinoutCard
              name="5V Relay Module"
              purpose="Active LOW Control (LOW=ON)"
              pins="IN → GPIO26 · VCC → 5V · GND"
              status="Active"
            />
            <PinoutCard
              name="16x2 I2C LCD"
              purpose="Local Telemetry Display"
              pins="SDA → GPIO21 · SCL → GPIO22 (0x27)"
              status="Active"
            />
          </div>
        </div>

        {/* Security Policy Reminder */}
        <div className="rounded-lg bg-surface p-3 text-xs text-muted-foreground flex items-center gap-2 border border-border">
          <ShieldCheck className="size-4 text-emerald-500 shrink-0" />
          <span>
            Security Policy Enforced: Device secrets, database connection strings, JWT tokens, and Wi-Fi passwords are never displayed or logged in frontend UI components.
          </span>
        </div>
      </section>
    </>
  );
}

function PinoutCard({
  name,
  purpose,
  pins,
  status,
}: {
  name: string;
  purpose: string;
  pins: string;
  status: string;
}) {
  return (
    <div className="panel p-3.5 space-y-1.5 border">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-foreground text-xs">{name}</span>
        <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.5 rounded">
          {status}
        </span>
      </div>
      <p className="text-[11px] text-muted-foreground">{purpose}</p>
      <p className="text-[10px] font-mono text-primary bg-primary/5 p-1.5 rounded border border-primary/10 truncate">
        {pins}
      </p>
    </div>
  );
}
