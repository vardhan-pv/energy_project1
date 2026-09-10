import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Database, FileText, History as HistoryIcon, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/app/primitives";
import { EventStream } from "@/components/app/EventStream";
import { DailyBarChart } from "@/components/app/charts";
import { useEnergy } from "@/lib/energy/store";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History & Database Logs | Cognitive Energy Dashboard" },
      { name: "description", content: "Separate audit logs for production PostgreSQL telemetry and UK-DALE historical reference datasets." },
    ],
  }),
  component: HistoryPage,
});

export function HistoryPage() {
  const { history, settings } = useEnergy();
  const [tab, setTab] = useState<"pg" | "ukdale">("pg");

  return (
    <>
      <PageHeader
        title="Telemetry History &amp; Audit Logs"
        description="Review historical telemetry logs stored in PostgreSQL alongside reference disaggregation datasets."
        actions={
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={tab === "pg" ? "default" : "outline"}
              onClick={() => setTab("pg")}
            >
              <Database className="size-3.5 mr-1.5 text-emerald-500" />
              Real Telemetry Log (PostgreSQL)
            </Button>
            <Button
              size="sm"
              variant={tab === "ukdale" ? "default" : "outline"}
              onClick={() => setTab("ukdale")}
            >
              <Layers className="size-3.5 mr-1.5 text-indigo-500" />
              UK-DALE Dataset
            </Button>
          </div>
        }
      />

      {tab === "pg" ? (
        <section className="panel p-5 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h2 className="font-semibold text-base flex items-center gap-2">
                <Database className="size-4 text-emerald-500" />
                Production PostgreSQL Telemetry History
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Time-series records stored in the production PostgreSQL <code className="font-mono text-foreground font-semibold">telemetry</code> table on Render
              </p>
            </div>
            <span className="text-[11px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded">
              Source: Render PostgreSQL DB
            </span>
          </div>

          <div className="rounded-lg bg-surface p-3 text-xs text-muted-foreground border">
            <p>
              Telemetry entries are inserted into PostgreSQL upon every valid ESP32 sensor POST request. Records capture timestamp, user_id, house_id, appliance_id, voltage, current, power_w, energy_kwh, temperature, humidity, and anomaly scores.
            </p>
          </div>

          <EventStream limit={50} title="Real-Time Telemetry & System Action Audit Stream" />
        </section>
      ) : (
        <section className="panel p-5 space-y-4">
          <div className="flex items-center justify-between border-b pb-3">
            <div>
              <h2 className="font-semibold text-base flex items-center gap-2">
                <Layers className="size-4 text-indigo-500" />
                UK-DALE Historical Reference Dataset
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                UK Domestic Appliance-Level Electricity dataset (House 1 profile) used for ML training
              </p>
            </div>
            <span className="text-[11px] font-mono bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded">
              Source: UK-DALE Benchmark Dataset
            </span>
          </div>

          <div className="space-y-3">
            <h3 className="font-semibold text-sm">30-Day Historical Load Trend</h3>
            <DailyBarChart data={history} height={320} />
          </div>
        </section>
      )}
    </>
  );
}
