import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Cpu, Database, Network, ShieldCheck, Zap, RefreshCw, Activity, Layers, Sliders } from "lucide-react";
import { PageHeader } from "@/components/app/primitives";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/architecture")({
  head: () => ({
    meta: [
      { title: "System Architecture | Cognitive Energy Dashboard" },
      { name: "description", content: "End-to-end closed-loop pipeline architecture of the IREOS Cognitive Energy Optimization System." },
    ],
  }),
  component: ArchitecturePage,
});

export function ArchitecturePage() {
  return (
    <>
      <PageHeader
        title="IREOS System Architecture"
        description="End-to-end IoT, Machine Learning, Reinforcement Learning, and Self-Evolution closed-loop architecture."
        actions={
          <Button asChild variant="outline">
            <Link to="/analytics">View Cognitive Analytics</Link>
          </Button>
        }
      />

      <section className="panel p-6">
        <div className="flex items-center justify-between border-b pb-4 mb-6">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Network className="size-5 text-primary" />
              Closed-Loop System Flow & Pipeline
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Continuous multi-stage telemetry ingestion, cognitive feature engineering, RL optimization, and hardware execution.
            </p>
          </div>
          <span className="text-xs font-mono bg-primary/10 text-primary px-3 py-1 rounded-full font-medium">
            Phase 17 — Closed-Loop Real-Time Control
          </span>
        </div>

        {/* Closed Loop Steps Diagram */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StepCard
            step="01"
            title="SENSE & INGEST"
            icon={Cpu}
            source="ESP32 IoT Node"
            color="border-cyan-500/40 text-cyan-600 dark:text-cyan-400"
            items={[
              "PZEM-004T V3 (Voltage, Current, Power, Energy)",
              "DHT22 (Temperature & Ambient Humidity)",
              "16x2 I2C LCD Local Status Display (0x27)",
              "HTTPS Ingestion via POST /api/telemetry",
            ]}
          />
          <StepCard
            step="02"
            title="ANALYZE & COMPUTE"
            icon={Layers}
            source="IREOS Analytical Engine"
            color="border-indigo-500/40 text-indigo-600 dark:text-indigo-400"
            items={[
              "ATF: Adaptive Temporal Features",
              "ERI: Energy Routine Index",
              "DSC: Demand Stability / Change Analysis",
              "CDI: Cognitive Demand Intelligence Score",
              "UBD: Usage Behavior Dynamics",
            ]}
          />
          <StepCard
            step="03"
            title="PREDICT & OPTIMIZE"
            icon={Activity}
            source="RL Policy Core"
            color="border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
            items={[
              "UK-DALE Trained Disaggregation Models",
              "Multi-Agent Q-Learning / PPO Policy",
              "Rewards: Energy, Peak & Stability Bonuses",
              "Safety Interlocks & Anomaly Shielding",
            ]}
          />
          <StepCard
            step="04"
            title="CONTROL & EVOLVE"
            icon={RefreshCw}
            source="Hardware Feedback Loop"
            color="border-amber-500/40 text-amber-600 dark:text-amber-400"
            items={[
              "Relay Command Generation (GPIO26 Active LOW)",
              "Render PostgreSQL Storage & History Logs",
              "Continuous Self-Evaluation Engine",
              "Autonomous Self-Evolution Loop",
            ]}
          />
        </div>

        {/* Detailed Flow Visualizer */}
        <div className="mt-8 rounded-xl border border-border/80 bg-surface/50 p-6">
          <h3 className="font-semibold text-sm mb-4 flex items-center gap-2">
            <Sliders className="size-4 text-primary" />
            Complete Pipeline Vector Flow
          </h3>
          <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-mono text-center">
            <Pill text="UK-DALE Dataset" bg="bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Data Cleaning" bg="bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Feature Eng (ATF)" bg="bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Cognitive State (ERI/CDI/UBD)" bg="bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="ML Prediction" bg="bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="RL Optimization" bg="bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Decision Core" bg="bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="ESP32 Controller" bg="bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="PZEM / DHT22 / Relay" bg="bg-cyan-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="PostgreSQL DB" bg="bg-cyan-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Dashboard UI" bg="bg-primary/10 border-primary/30 text-primary" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="Self-Evolution" bg="bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400" />
          </div>
        </div>
      </section>

      {/* Hardware Node Specifications */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="panel p-5 space-y-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Cpu className="size-4 text-cyan-500" />
            Physical Hardware Node Pinout
          </h3>
          <ul className="text-xs space-y-2 text-muted-foreground">
            <li className="flex justify-between border-b pb-1">
              <span>ESP32 Main Microcontroller</span>
              <span className="font-mono text-foreground font-medium">ESP32 DevKit V1</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>DHT22 Temp & Humidity Sensor</span>
              <span className="font-mono text-foreground font-medium">GPIO4</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>PZEM-004T V3 AC Power Meter</span>
              <span className="font-mono text-foreground font-medium">TX: GPIO16 / RX: GPIO17</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>5V Opto-Isolated Relay Module</span>
              <span className="font-mono text-foreground font-medium">GPIO26 (Active LOW)</span>
            </li>
            <li className="flex justify-between">
              <span>16x2 I2C LCD Display</span>
              <span className="font-mono text-foreground font-medium">SDA: GPIO21 / SCL: GPIO22 (0x27)</span>
            </li>
          </ul>
        </div>

        <div className="panel p-5 space-y-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Database className="size-4 text-emerald-500" />
            Backend Infrastructure & Storage
          </h3>
          <ul className="text-xs space-y-2 text-muted-foreground">
            <li className="flex justify-between border-b pb-1">
              <span>Production Backend Service</span>
              <span className="font-mono text-foreground font-medium">Python 3.11 / Flask on Render</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Production Database</span>
              <span className="font-mono text-foreground font-medium">PostgreSQL on Render</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Primary AC Circuit Measurement</span>
              <span className="font-mono text-foreground font-medium">Single PZEM-004T Channel</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Sub-Metered Models</span>
              <span className="font-mono text-foreground font-medium">4 Disaggregated Appliance Profiles</span>
            </li>
            <li className="flex justify-between">
              <span>Security Policy</span>
              <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">Secrets & Credentials Redacted</span>
            </li>
          </ul>
        </div>
      </section>
    </>
  );
}

function StepCard({
  step,
  title,
  source,
  icon: Icon,
  color,
  items,
}: {
  step: string;
  title: string;
  source: string;
  icon: any;
  color: string;
  items: string[];
}) {
  return (
    <div className={`panel p-4 border ${color} flex flex-col justify-between`}>
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-xs font-bold opacity-75">{step}</span>
          <Icon className="size-4" />
        </div>
        <h4 className="font-semibold text-sm mb-1">{title}</h4>
        <p className="text-[11px] font-mono text-muted-foreground mb-3">{source}</p>
        <ul className="text-xs space-y-1.5 text-muted-foreground">
          {items.map((it, i) => (
            <li key={i} className="flex items-start gap-1.5">
              <span className="text-primary">•</span>
              <span>{it}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Pill({ text, bg }: { text: string; bg: string }) {
  return (
    <span className={`px-2.5 py-1 rounded-md border font-mono font-medium ${bg}`}>
      {text}
    </span>
  );
}
