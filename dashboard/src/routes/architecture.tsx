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

export const Route = createFileRoute("/architecture")({
  head: () => ({
    meta: [
      { title: "11-Step System Architecture | Cognitive Energy Dashboard" },
      { name: "description", content: "Complete 11-step closed-loop pipeline methodology of the IREOS Cognitive Energy System." },
    ],
  }),
  component: ArchitecturePage,
});

const PIPELINE_STEPS = [
  {
    step: "01",
    title: "Data Collection",
    subtitle: "Dual Ingestion Core",
    icon: Cpu,
    color: "border-cyan-500/40 bg-cyan-500/5 text-cyan-600 dark:text-cyan-400",
    badge: "Layer 1",
    description: "Combines historical UK-DALE benchmark data with real-time physical ESP32 telemetry.",
    details: [
      "UK-DALE Dataset: Laptop, Kitchen Lights, Fridge, Office Fan",
      "Physical ESP32 DevKit V1 Microcontroller Node",
      "PZEM-004T V3 (AC Voltage, Current, Power, Energy)",
      "DHT22 Sensor (Ambient Temperature & Humidity)",
      "16x2 I2C Local Status LCD Display (0x27)",
      "HTTPS Telemetry Ingestion via POST /api/telemetry",
    ],
  },
  {
    step: "02",
    title: "Database Ingestion",
    subtitle: "Unified Relational Schema",
    icon: Database,
    color: "border-indigo-500/40 bg-indigo-500/5 text-indigo-600 dark:text-indigo-400",
    badge: "Layer 2",
    description: "Structures high-frequency time-series sensor data into production PostgreSQL database.",
    details: [
      "Render Production PostgreSQL & Local SQLite Fallback",
      "Schema: timestamp, appliance, voltage, current, power",
      "Environmental: temperature, humidity, status, energy_kwh",
      "Source tagging (UK-DALE vs Live Physical ESP32 Node)",
      "Indexed time-series queries for zero-latency retrieval",
    ],
  },
  {
    step: "03",
    title: "Data Cleaning",
    subtitle: "Sanitization & Integrity",
    icon: Filter,
    color: "border-blue-500/40 bg-blue-500/5 text-blue-600 dark:text-blue-400",
    badge: "Layer 3",
    description: "Filters sensor noise, handles missing fields, and checks for out-of-range readings.",
    details: [
      "Zero missing-value validation across 23.8M+ raw records",
      "Duplicate record detection & timestamp synchronization",
      "Sensor outlier screening (Voltage 180-260V, Current 0-15A)",
      "Noise filtering & invalid status handling (status IN (0,1))",
      "Creation of separate sanitized `appliance_energy_clean` table",
    ],
  },
  {
    step: "04",
    title: "Feature Engineering",
    subtitle: "Multi-Scale Extraction",
    icon: Layers,
    color: "border-purple-500/40 bg-purple-500/5 text-purple-600 dark:text-purple-400",
    badge: "Layer 4",
    description: "Transforms raw power/temperature samples into domain-specific cognitive features.",
    details: [
      "Power, Energy, Runtime, Ambient Temperature & Humidity",
      "Temporal context: Hour of day, Day of week, Weekend flag",
      "Rolling statistics: 5m, 15m, 60m Moving Averages",
      "Peak load detection & Load variability variance",
      "Usage frequency & duty cycle calculations",
    ],
  },
  {
    step: "05",
    title: "Behavior Modeling",
    subtitle: "Cognitive State Engine",
    icon: Brain,
    color: "border-fuchsia-500/40 bg-fuchsia-500/5 text-fuchsia-600 dark:text-fuchsia-400",
    badge: "Layer 5",
    description: "Computes user behavior descriptors and appliance temporal fingerprints.",
    details: [
      "UBD — User Behavior Descriptor: Quantifies occupancy habits",
      "ATF — Appliance Temporal Fingerprint: Unique power draw curve",
      "ERI — Energy Routine Index (0-100): Routine predictability score",
      "DSC — Demand Stability / Change: Dynamic load shift indicator",
      "CDI — Comfort / Device Interaction: User comfort impact score",
    ],
  },
  {
    step: "06",
    title: "Demand Prediction",
    subtitle: "ML Load Forecasting",
    icon: TrendingUp,
    color: "border-emerald-500/40 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400",
    badge: "Layer 6",
    description: "Predicts future load demand and individual appliance power trajectories.",
    details: [
      "Models trained on UK-DALE data & physical telemetry",
      "Random Forest (Fridge R²=0.9976, Fan R²=0.9795, Lights R²=0.9632)",
      "Linear Regression (Laptop R²=0.9547)",
      "Forecast Horizon: 30-minute expected power draw curves",
      "Confidence intervals & risk level flags (Normal, Watch, Risk)",
    ],
  },
  {
    step: "07",
    title: "RL Optimization",
    subtitle: "Multi-Agent Q-Learning / PPO",
    icon: Workflow,
    color: "border-teal-500/40 bg-teal-500/5 text-teal-600 dark:text-teal-400",
    badge: "Layer 7",
    description: "Evaluates system state and selects optimal control policy actions.",
    details: [
      "State Space: Current load, predicted load, ERI/CDI, tariff, temp",
      "Action Space: Keep ON, Turn OFF, Delay Operation, Reduce/Shift Load",
      "Multi-Objective Reward: R = R_energy + R_comfort + R_safety + R_peak",
      "Safety Interlocks: Prevents switching off critical loads (Fridge)",
      "Peak tariff shaving & daily energy budget constraint enforcement",
    ],
  },
  {
    step: "08",
    title: "Action & Recommendation",
    subtitle: "Decision Core Execution",
    icon: Zap,
    color: "border-amber-500/40 bg-amber-500/5 text-amber-600 dark:text-amber-400",
    badge: "Layer 8",
    description: "Executes hardware control commands or generates user recommendations.",
    details: [
      "Decision Core: Chooses Autonomous Action vs User Recommendation",
      "Hardware Relay Control: Active LOW signal to ESP32 GPIO26",
      "Live Command Stream: Power ON/OFF, Mode switch (Eco/Maintain)",
      "Target Power Nudging: Setpoint trimming during peak hours",
      "Real-time UI alert broadcasting via Web sockets / Polling",
    ],
  },
  {
    step: "09",
    title: "User Feedback Loop",
    subtitle: "Human-in-the-Loop",
    icon: ThumbsUp,
    color: "border-orange-500/40 bg-orange-500/5 text-orange-600 dark:text-orange-400",
    badge: "Layer 9",
    description: "Captures user responses (accept, reject, modify) to refine decision policy.",
    details: [
      "User override tracking on dashboard control center",
      "Accept / Reject / Modify recommendation interactions",
      "Feedback stored in PostgreSQL database for reward tuning",
      "User preference weight adjustment in RL reward function",
      "Comfort violation logging when manual overrides occur",
    ],
  },
  {
    step: "10",
    title: "Self-Evaluation",
    subtitle: "Performance Verification",
    icon: Award,
    color: "border-rose-500/40 bg-rose-500/5 text-rose-600 dark:text-rose-400",
    badge: "Layer 10",
    description: "Compares predicted vs actual energy and evaluates decision efficacy.",
    details: [
      "Continuous verification: Did the optimizer decision actually work?",
      "Compare: Predicted Energy (kWh) vs Actual Measured Energy (kWh)",
      "Quantifies: Energy Savings %, Prediction Error (MAE/RMSE)",
      "Evaluates: Comfort impact score & User acceptance rate",
      "Anomaly detection: Identifies unpredicted spikes or device faults",
    ],
  },
  {
    step: "11",
    title: "Model Update & Evolution",
    subtitle: "Continuous Learning",
    icon: Sparkles,
    color: "border-emerald-600/40 bg-emerald-600/5 text-emerald-600 dark:text-emerald-400",
    badge: "Layer 11",
    description: "Feeds new data and feedback back into models for autonomous self-evolution.",
    details: [
      "Continuous Learning Loop: New Data + Feedback + Performance",
      "Automatic ML predictor weight updating upon drift detection",
      "RL policy fine-tuning based on accumulated experience buffer",
      "Self-Evolution Engine: Generates evolution verification reports",
      "Autonomous system optimization over days, weeks, and months",
    ],
  },
];

export function ArchitecturePage() {
  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  return (
    <>
      <PageHeader
        title="IREOS 11-Step System Architecture"
        description="Complete end-to-end closed-loop pipeline: Data Collection, ML Prediction, RL Optimization, User Feedback, and Self-Evolution."
        actions={
          <Button asChild variant="outline">
            <Link to="/analytics">View Cognitive Analytics</Link>
          </Button>
        }
      />

      {/* Closed Loop Overview Header */}
      <section className="panel p-6 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Network className="size-5 text-primary" />
              11-Step Closed-Loop Pipeline Flow
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Click any step below to inspect its exact implementation details, dataset structures, and hardware interactions.
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
