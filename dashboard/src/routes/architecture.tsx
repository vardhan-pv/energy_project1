import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  Cpu,
  Database,
  Network,
  ShieldCheck,
  Zap,
  RefreshCw,
  Activity,
  Layers,
  Sliders,
  Filter,
  Brain,
  TrendingUp,
  Award,
  CheckCircle2,
  ThumbsUp,
  Sparkles,
  Search,
  Server,
  Workflow,
} from "lucide-react";
import { PageHeader } from "@/components/app/primitives";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OrbitalArchitecture, ARCHITECTURE_STEPS } from "@/components/app/OrbitalArchitecture";

export const Route = createFileRoute("/architecture")({
  head: () => ({
    meta: [
      { title: "11-Step System Architecture | Cognitive Energy Dashboard" },
      { name: "description", content: "Complete 11-step closed-loop pipeline methodology of the IREOS Cognitive Energy System." },
    ],
  }),
  component: ArchitecturePage,
});

const PIPELINE_STEPS = ARCHITECTURE_STEPS;

export function ArchitecturePage() {
  const [selectedStep, setSelectedStep] = useState<number | null>(0);

  return (
    <>
      <PageHeader
        title="IREOS 11-Step Closed-Loop Architecture"
        description="Continuous, self-evolving cognitive energy cycle: Sense → Communicate → Analyze → Predict → Optimize → Control → Measure → Learn → Evolve."
        actions={
          <Button asChild variant="outline">
            <Link to="/analytics">View Cognitive Analytics</Link>
          </Button>
        }
      />

      {/* 1. Hero Continuous Animated Orbital Loop (Circular Closed-Loop System) */}
      <section className="space-y-4">
        <OrbitalArchitecture
          activeStepIndex={selectedStep ?? 0}
          onStepSelect={(idx) => setSelectedStep(idx)}
        />
      </section>

      {/* Closed Loop Overview Header & Grid */}
      <section className="panel p-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Network className="size-5 text-primary" />
              11-Step Layer-by-Layer Inspector
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Click any step below to jump directly to its position on the central closed-loop orbital ring above.
            </p>
          </div>
          <span className="text-xs font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-3 py-1 rounded-full font-semibold border border-emerald-500/20 flex items-center gap-1.5">
            <CheckCircle2 className="size-3.5" />
            Phase 17 — Closed-Loop Control Verified
          </span>
        </div>


        {/* 11 Steps Interactive Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {PIPELINE_STEPS.map((item, idx) => {
            const Icon = item.icon;
            const isSelected = selectedStep === idx;
            return (
              <div
                key={item.step}
                onClick={() => setSelectedStep(isSelected ? null : idx)}
                className={`panel p-4 border cursor-pointer transition-all duration-200 hover:scale-[1.02] ${item.color} ${
                  isSelected ? "ring-2 ring-primary shadow-lg" : ""
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-xs font-bold opacity-80">{item.step}</span>
                  <Badge variant="outline" className="text-[10px] uppercase tracking-wide bg-background/80">
                    {item.badge}
                  </Badge>
                </div>

                <div className="flex items-center gap-2.5 mb-2">
                  <div className="p-1.5 rounded-md bg-background/80 shrink-0">
                    <Icon className="size-4 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm leading-snug">{item.title}</h3>
                    <p className="text-[11px] font-mono opacity-80">{item.subtitle}</p>
                  </div>
                </div>

                <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                  {item.description}
                </p>

                <div className="space-y-1 border-t pt-2.5 text-[11px] text-muted-foreground">
                  {item.details.slice(0, 3).map((detail, dIdx) => (
                    <div key={dIdx} className="flex items-start gap-1.5 truncate">
                      <span className="text-primary font-bold">•</span>
                      <span className="truncate">{detail}</span>
                    </div>
                  ))}
                  {item.details.length > 3 ? (
                    <p className="text-[10px] text-primary font-medium mt-1">
                      +{item.details.length - 3} more details {isSelected ? "▲" : "▼"}
                    </p>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>

        {/* Complete Pipeline Vector Flow */}
        <div className="mt-8 rounded-xl border border-border/80 bg-surface/50 p-6">
          <h3 className="font-semibold text-sm mb-4 flex items-center gap-2">
            <Workflow className="size-4 text-primary" />
            Continuous Vector Flow Diagram (Steps 1 → 11)
          </h3>
          <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-mono text-center">
            <Pill text="1. Data Collection" bg="bg-cyan-500/10 border-cyan-500/30 text-cyan-600 dark:text-cyan-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="2. Database Ingestion" bg="bg-indigo-500/10 border-indigo-500/30 text-indigo-600 dark:text-indigo-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="3. Data Cleaning" bg="bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="4. Feature Eng" bg="bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="5. Behavior Modeling" bg="bg-fuchsia-500/10 border-fuchsia-500/30 text-fuchsia-600 dark:text-fuchsia-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="6. Demand Prediction" bg="bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="7. RL Optimization" bg="bg-teal-500/10 border-teal-500/30 text-teal-600 dark:text-teal-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="8. Action & Exec" bg="bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="9. User Feedback" bg="bg-orange-500/10 border-orange-500/30 text-orange-600 dark:text-orange-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="10. Self-Evaluation" bg="bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400" />
            <ArrowRight className="size-3 text-muted-foreground shrink-0" />
            <Pill text="11. Continuous Evolution ↺" bg="bg-emerald-600/10 border-emerald-600/30 text-emerald-600 dark:text-emerald-400 font-bold" />
          </div>
        </div>
      </section>

      {/* Hardware Node & Database Specs Grid */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="panel p-5 space-y-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Cpu className="size-4 text-cyan-500" />
            Hardware Data Collection Specs (Step 1)
          </h3>
          <ul className="text-xs space-y-2 text-muted-foreground">
            <li className="flex justify-between border-b pb-1">
              <span>Main Microcontroller</span>
              <span className="font-mono text-foreground font-medium">ESP32 DevKit V1 (Dual-Core Xtensa)</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>AC Load Meter</span>
              <span className="font-mono text-foreground font-medium">PZEM-004T V3 (TX: GPIO16 / RX: GPIO17)</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Environmental Sensor</span>
              <span className="font-mono text-foreground font-medium">DHT22 (DATA: GPIO4)</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Opto-Isolated Relay</span>
              <span className="font-mono text-foreground font-medium">GPIO26 (Active LOW, 5V Coils)</span>
            </li>
            <li className="flex justify-between">
              <span>Local Telemetry LCD</span>
              <span className="font-mono text-foreground font-medium">16x2 I2C (SDA: GPIO21 / SCL: GPIO22)</span>
            </li>
          </ul>
        </div>

        <div className="panel p-5 space-y-3">
          <h3 className="font-semibold text-sm flex items-center gap-2">
            <Database className="size-4 text-indigo-500" />
            Database & Data Cleaning Specs (Steps 2 & 3)
          </h3>
          <ul className="text-xs space-y-2 text-muted-foreground">
            <li className="flex justify-between border-b pb-1">
              <span>Production Relational Database</span>
              <span className="font-mono text-foreground font-medium">Render PostgreSQL & Local SQLite</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>UK-DALE Raw Records Processed</span>
              <span className="font-mono text-foreground font-medium">23,834,898 clean records</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Sanitized Data Table</span>
              <span className="font-mono text-foreground font-medium">`appliance_energy_clean`</span>
            </li>
            <li className="flex justify-between border-b pb-1">
              <span>Benchmark Appliances</span>
              <span className="font-mono text-foreground font-medium">Laptop, Lights, Fridge, Fan</span>
            </li>
            <li className="flex justify-between">
              <span>Missing Values & Duplicates</span>
              <span className="font-mono text-emerald-600 dark:text-emerald-400 font-medium">0 Missing / 0 Duplicates</span>
            </li>
          </ul>
        </div>
      </section>
    </>
  );
}

function Pill({ text, bg }: { text: string; bg: string }) {
  return (
    <span className={`px-2.5 py-1 rounded-md border font-mono font-medium ${bg}`}>
      {text}
    </span>
  );
}
