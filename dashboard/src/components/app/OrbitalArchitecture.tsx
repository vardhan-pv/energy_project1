import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Cpu,
  Database,
  Filter,
  Layers,
  Brain,
  TrendingUp,
  Workflow,
  Zap,
  ThumbsUp,
  Award,
  Sparkles,
  Play,
  Pause,
  RotateCw,
  CheckCircle2,
  Activity,
  Server,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface PipelineStep {
  step: string;
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  badge: string;
  description: string;
  details: string[];
  hardwareNote?: string;
}

export const ARCHITECTURE_STEPS: PipelineStep[] = [
  {
    step: "01",
    title: "Data Collection",
    subtitle: "Dual Telemetry Ingestion",
    icon: Cpu,
    badge: "Layer 1",
    description: "High-frequency telemetry sampling from physical ESP32 + PZEM-004T sensors and UK-DALE benchmark logs.",
    details: [
      "Physical ESP32 DevKit V1 Microcontroller Node (DEV-638C71FE)",
      "PZEM-004T V3 AC Meter (Voltage 230V, Current 0-100A, Power W, Energy kWh)",
      "DHT22 Environmental Sensor (Ambient Temp °C & Humidity %)",
      "HC-SR501 PIR Motion & LDR Light Intensity Sensors",
      "HTTPS Telemetry Ingestion via POST /api/telemetry (Every 3-5s)",
      "UK-DALE Benchmark Dataset Baseline Support",
    ],
    hardwareNote: "ESP32 Node → PZEM-004T UART → HTTPS POST Payload",
  },
  {
    step: "02",
    title: "Database Ingestion",
    subtitle: "Dual Relational Engine",
    icon: Database,
    badge: "Layer 2",
    description: "Structures high-frequency time-series telemetry into dual PostgreSQL/SQLite database schema.",
    details: [
      "Render Production PostgreSQL & Local SQLite (ceos_database.db)",
      "Schema: timestamp, appliance_id, voltage, current, power_w, energy_kwh",
      "Environmental: temperature_c, humidity_pct, status, mode, anomaly_score",
      "Auto-healing device secret & appliance profile synchronization",
      "Indexed time-series queries for zero-latency real-time retrieval",
    ],
    hardwareNote: "DB Manager → Connection Pool → Schema Migration Engine",
  },
  {
    step: "03",
    title: "Data Cleaning",
    subtitle: "Sanitization & Integrity",
    icon: Filter,
    badge: "Layer 3",
    description: "Filters sensor noise, handles missing fields, and enforces physical electrical boundary conditions.",
    details: [
      "Zero missing-value validation across 23.8M+ raw records",
      "Sensor outlier screening (Voltage 180-260V, Current 0-15A)",
      "Power factor normalization & noise spike removal",
      "Timestamp alignment and duplicate record deduplication",
      "Creation of sanitized appliance_energy_clean runtime state",
    ],
    hardwareNote: "Range Filters: V ∈ [180, 260], I ∈ [0, 15], PF ∈ [0, 1]",
  },
  {
    step: "04",
    title: "Feature Engineering",
    subtitle: "Multi-Scale Extraction",
    icon: Layers,
    badge: "Layer 4",
    description: "Transforms raw electrical & environmental readings into domain-specific cognitive feature vectors.",
    details: [
      "Active power, reactive power, power factor, duty cycle calculations",
      "Temporal context: Hour of day, Day of week, Weekend flag",
      "Rolling statistics: 5m, 15m, 60m Moving Averages & Variances",
      "Peak load variance & load stability indicators",
      "Harmonic distortion & duty cycle frequency analysis",
    ],
    hardwareNote: "NILM Feature Pipeline → Rolling Window Buffer",
  },
  {
    step: "05",
    title: "Behavior Modeling",
    subtitle: "Cognitive Fingerprinting",
    icon: Brain,
    badge: "Layer 5",
    description: "Computes user occupancy habits, routine predictability, and appliance temporal signatures.",
    details: [
      "UBD — User Behavior Descriptor: Quantifies occupancy habits",
      "ATF — Appliance Temporal Fingerprint: Unique power draw curve",
      "ERI — Energy Routine Index (0-100): Routine predictability score",
      "DSC — Demand Stability / Change: Dynamic load shift indicator",
      "CDI — Comfort / Device Interaction: User comfort impact score",
    ],
    hardwareNote: "PIR Sensor Input → Occupancy Predictor Matrix",
  },
  {
    step: "06",
    title: "Demand Prediction",
    subtitle: "ML Load Forecasting",
    icon: TrendingUp,
    badge: "Layer 6",
    description: "Predicts upcoming energy consumption trajectories and peak load occurrences.",
    details: [
      "Pre-trained XGBoost & Random Forest regression models",
      "Appliance Accuracy: Fridge (R²=0.997), Fan (R²=0.979), Lights (R²=0.963)",
      "Forecast Horizon: 30-minute expected power draw curves",
      "Isolation Forest anomaly detection scoring (0.00 - 1.00)",
      "Risk level classification (Normal, Watch, Critical Risk)",
    ],
    hardwareNote: "Inference Engine → Predicted Power W Output",
  },
  {
    step: "07",
    title: "RL Optimization",
    subtitle: "Multi-Objective Q-Learning",
    icon: Workflow,
    badge: "Layer 7",
    description: "Evaluates systemic energy cost vs user comfort to derive optimal control policies.",
    details: [
      "State Space: Current load, predicted load, ERI/CDI, tariff, temp",
      "Action Space: Keep ON, Turn OFF, Delay Operation, Reduce/Shift Load",
      "Multi-Objective Reward: R = R_energy + R_comfort + R_safety + R_peak",
      "Safety Interlocks: Prevents switching off critical loads (Fridge)",
      "Peak tariff shaving & daily energy budget constraint enforcement",
    ],
    hardwareNote: "Q-Table Evaluator → Optimal Action Candidate",
  },
  {
    step: "08",
    title: "Action & Control",
    subtitle: "Closed-Loop Execution",
    icon: Zap,
    badge: "Layer 8",
    description: "Dispatches hardware relay commands and target setpoints back to physical controllers.",
    details: [
      "Decision Core: Autonomous Action vs Manual Recommendation",
      "Hardware Relay Control: Active LOW signal to ESP32 GPIOs (16,17,18,19)",
      "Real-Time Payload Command: ON, OFF, DIM, MAINTAIN",
      "Target Power Setpoint trimming during peak tariff windows",
      "Sub-100ms API response latency to telemetry HTTP POSTs",
    ],
    hardwareNote: "Flask JSON Payload → ESP32 Relay Switch (ON/OFF/DIM)",
  },
  {
    step: "09",
    title: "User Feedback Loop",
    subtitle: "Human-in-the-Loop",
    icon: ThumbsUp,
    badge: "Layer 9",
    description: "Captures user manual overrides and UI preferences to calibrate comfort boundaries.",
    details: [
      "User override tracking on dashboard Control Center",
      "Accept / Reject / Modify recommendation interactions",
      "Feedback stored in database for reward weight calibration",
      "User preference weight adjustment in RL reward function",
      "Comfort violation logging when manual overrides occur",
    ],
    hardwareNote: "React UI Click → POST /api/appliances → Weight Penalty",
  },
  {
    step: "10",
    title: "Self-Evaluation",
    subtitle: "Performance Verification",
    icon: Award,
    badge: "Layer 10",
    description: "Compares predicted vs actual energy savings to measure optimization efficacy.",
    details: [
      "Continuous verification: Evaluates if optimizer decisions succeeded",
      "Compares: Predicted Energy (kWh) vs Measured Energy (kWh)",
      "Quantifies: Energy Savings %, Prediction Error (MAE/RMSE)",
      "Evaluates: Comfort impact score & User acceptance rate",
      "Anomaly detection: Identifies unpredicted spikes or device faults",
    ],
    hardwareNote: "Verification Matrix: Measured Savings = 13.30% (PASS)",
  },
  {
    step: "11",
    title: "Model Update & Evolution",
    subtitle: "Continuous Learning",
    icon: Sparkles,
    badge: "Layer 11",
    description: "Feeds new telemetry and feedback back into models for continuous self-evolution.",
    details: [
      "Continuous Learning Loop: New Data + Feedback + Performance",
      "Automatic ML predictor weight updating upon concept drift",
      "RL policy fine-tuning based on accumulated experience buffer",
      "Self-Evolution Engine: Generates evolution verification reports",
      "Autonomous system optimization over days, weeks, and months",
    ],
    hardwareNote: "Model Re-trainer → Updated Weights → (Loop Back to Layer 1)",
  },
];

interface OrbitalProps {
  activeStepIndex?: number;
  onStepSelect?: (index: number) => void;
  autoRotate?: boolean;
}

export function OrbitalArchitecture({
  activeStepIndex: externalActiveIndex,
  onStepSelect,
  autoRotate: initialAutoRotate = true,
}: OrbitalProps) {
  const [internalActiveIndex, setInternalActiveIndex] = useState(0);
  const [isAutoRotating, setIsAutoRotating] = useState(initialAutoRotate);
  const rotationSpeed = 2500;

  const activeIndex = externalActiveIndex !== undefined ? externalActiveIndex : internalActiveIndex;
  const activeStep = ARCHITECTURE_STEPS[activeIndex];

  useEffect(() => {
    if (!isAutoRotating) return;
    const interval = setInterval(() => {
      setInternalActiveIndex((prev) => (prev + 1) % ARCHITECTURE_STEPS.length);
    }, rotationSpeed);
    return () => clearInterval(interval);
  }, [isAutoRotating, rotationSpeed]);

  const handleStepClick = (index: number) => {
    setInternalActiveIndex(index);
    if (onStepSelect) onStepSelect(index);
  };

  const totalSteps = ARCHITECTURE_STEPS.length;
  const radius = 310;
  const cx = 400;
  const cy = 400;

  const stepNodes = ARCHITECTURE_STEPS.map((stepItem, idx) => {
    const angleRad = -Math.PI / 2 + (idx * 2 * Math.PI) / totalSteps;
    const x = cx + radius * Math.cos(angleRad);
    const y = cy + radius * Math.sin(angleRad);
    return { ...stepItem, idx, x, y, angleRad };
  });

  const activeNode = stepNodes[activeIndex];

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-zinc-800 bg-black p-4 sm:p-8 shadow-2xl text-white">
      {/* Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10 border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-700 text-white">
            <Activity className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-lg text-white tracking-wide">
                IREOS Closed-Loop Engine
              </h3>
              <Badge className="bg-zinc-900 text-white border-zinc-700 text-[10px] uppercase font-mono">
                Real-Time Loop Active
              </Badge>
            </div>
            <p className="text-xs text-zinc-400">
              11-Layer Continuous Autonomous Cognitive Optimization Cycle
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-xl p-1.5">
          <Button
            size="sm"
            variant={isAutoRotating ? "default" : "ghost"}
            className={
              isAutoRotating
                ? "bg-white hover:bg-zinc-200 text-black font-semibold text-xs"
                : "text-zinc-400 hover:text-white text-xs"
            }
            onClick={() => setIsAutoRotating(!isAutoRotating)}
          >
            {isAutoRotating ? (
              <>
                <Pause className="h-3.5 w-3.5 mr-1.5" /> Auto Loop ON
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 mr-1.5" /> Resume Loop
              </>
            )}
          </Button>

          <Button
            size="sm"
            variant="outline"
            className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-xs"
            onClick={() => handleStepClick((activeIndex + 1) % totalSteps)}
          >
            <RotateCw className="h-3.5 w-3.5 mr-1.5 text-white" /> Next Layer
          </Button>
        </div>
      </div>

      {/* Main Orbital Layout & Detail Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
        {/* Left: SVG Orbital Ring */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center relative min-h-[520px] sm:min-h-[600px] w-full">
          <div className="relative w-full max-w-[580px] aspect-square flex items-center justify-center">
            <svg
              viewBox="0 0 800 800"
              className="w-full h-full overflow-visible"
            >
              {/* Main Monochrome Track Ring */}
              <circle
                cx={cx}
                cy={cy}
                r={radius}
                fill="none"
                stroke="#52525b"
                strokeWidth="2"
                strokeDasharray="6 6"
              />

              {/* Flowing Laser Particle Ring Animation */}
              <motion.circle
                cx={cx}
                cy={cy}
                r={radius}
                fill="none"
                stroke="#ffffff"
                strokeWidth="3"
                strokeLinecap="round"
                strokeDasharray="30 140"
                animate={{ strokeDashoffset: [0, -1450] }}
                transition={{
                  repeat: Infinity,
                  duration: 10,
                  ease: "linear",
                }}
              />

              {/* Active Step Line Beam */}
              <motion.line
                x1={cx}
                y1={cy}
                x2={activeNode.x}
                y2={activeNode.y}
                stroke="#ffffff"
                strokeWidth="2"
                strokeDasharray="4 4"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.3, 1, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />

              {/* Spoke Lines */}
              {stepNodes.map((node) => (
                <line
                  key={`spoke-${node.step}`}
                  x1={cx}
                  y1={cy}
                  x2={node.x}
                  y2={node.y}
                  stroke="#27272a"
                  strokeWidth="1"
                />
              ))}

              {/* Step Nodes SVG Overlay */}
              {stepNodes.map((node) => {
                const isActive = node.idx === activeIndex;

                return (
                  <g
                    key={node.step}
                    className="cursor-pointer transition-transform duration-300 hover:scale-110"
                    onClick={() => handleStepClick(node.idx)}
                  >
                    {isActive && (
                      <motion.circle
                        cx={node.x}
                        cy={node.y}
                        r="36"
                        fill="none"
                        stroke="#ffffff"
                        strokeWidth="2"
                        initial={{ scale: 0.8, opacity: 1 }}
                        animate={{ scale: 1.4, opacity: 0 }}
                        transition={{ duration: 1.5, repeat: Infinity, ease: "easeOut" }}
                      />
                    )}

                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isActive ? "28" : "22"}
                      fill={isActive ? "#ffffff" : "#09090b"}
                      stroke={isActive ? "#ffffff" : "#3f3f46"}
                      strokeWidth={isActive ? "3" : "1.5"}
                    />

                    <circle
                      cx={node.x + (isActive ? 18 : 14)}
                      cy={node.y - (isActive ? 18 : 14)}
                      r="10"
                      fill={isActive ? "#000000" : "#27272a"}
                    />
                    <text
                      x={node.x + (isActive ? 18 : 14)}
                      y={node.y - (isActive ? 14 : 10)}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="9"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      {node.step}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* HTML Node Icons */}
            {stepNodes.map((node) => {
              const isActive = node.idx === activeIndex;
              const IconComp = node.icon;
              const leftPct = (node.x / 800) * 100;
              const topPct = (node.y / 800) * 100;

              return (
                <div
                  key={`html-node-${node.step}`}
                  style={{
                    position: "absolute",
                    left: `${leftPct}%`,
                    top: `${topPct}%`,
                    transform: "translate(-50%, -50%)",
                  }}
                  className="pointer-events-auto cursor-pointer flex flex-col items-center justify-center group"
                  onClick={() => handleStepClick(node.idx)}
                >
                  <div
                    className={`flex items-center justify-center rounded-full transition-all duration-300 ${
                      isActive
                        ? "h-14 w-14 border-2 border-white bg-white text-black shadow-xl"
                        : "h-11 w-11 hover:scale-110 border border-zinc-800 bg-zinc-950 text-zinc-400 group-hover:text-white"
                    }`}
                  >
                    <IconComp className={isActive ? "h-6 w-6 text-black" : "h-4 w-4"} />
                  </div>

                  <span
                    className={`mt-1.5 text-[10px] font-mono font-semibold tracking-tight whitespace-nowrap px-2 py-0.5 rounded-full transition-all ${
                      isActive
                        ? "bg-white text-black border border-white font-bold"
                        : "text-zinc-400 group-hover:text-white bg-zinc-900 border border-zinc-800"
                    }`}
                  >
                    {node.title}
                  </span>
                </div>
              );
            })}

            {/* Central Hero Core View */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full bg-zinc-950 border border-zinc-800 flex flex-col items-center justify-center text-center p-3 shadow-2xl z-20 pointer-events-none">
              <motion.div
                key={`core-icon-${activeStep.step}`}
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-900 border border-zinc-700 text-white mb-1"
              >
                {React.createElement(activeStep.icon, { className: "h-6 w-6" })}
              </motion.div>

              <div className="text-[10px] font-mono tracking-widest text-zinc-400 uppercase font-bold">
                STEP {activeStep.step} / 11
              </div>

              <div className="font-bold text-sm text-white leading-tight my-0.5 line-clamp-1 px-1">
                {activeStep.title}
              </div>

              <div className="text-[9px] text-zinc-400 font-mono flex items-center justify-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse" />
                CLOSED-LOOP ACTIVE
              </div>
            </div>
          </div>
        </div>

        {/* Right: Selected Step Detail Card */}
        <div className="lg:col-span-5 w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep.step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="rounded-xl border border-zinc-800 bg-zinc-950 p-6 backdrop-blur-xl shadow-xl relative overflow-hidden text-white"
            >
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-zinc-700 bg-zinc-900 text-white">
                    {React.createElement(activeStep.icon, { className: "h-6 w-6" })}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-zinc-400 font-bold uppercase tracking-wider">
                        LAYER {activeStep.step} OF 11
                      </span>
                      <Badge variant="outline" className="text-[10px] border-zinc-800 text-zinc-300">
                        {activeStep.badge}
                      </Badge>
                    </div>
                    <h4 className="text-xl font-bold text-white tracking-tight">
                      {activeStep.title}
                    </h4>
                  </div>
                </div>
              </div>

              <p className="text-xs font-medium text-zinc-300 mb-4 bg-zinc-900 p-3 rounded-lg border border-zinc-800 leading-relaxed">
                {activeStep.description}
              </p>

              {activeStep.hardwareNote && (
                <div className="mb-4 flex items-center gap-2 text-[11px] font-mono text-zinc-300 bg-zinc-900 border border-zinc-800 px-3 py-2 rounded-lg">
                  <Server className="h-3.5 w-3.5 text-zinc-400 shrink-0" />
                  <span className="truncate">{activeStep.hardwareNote}</span>
                </div>
              )}

              <div className="space-y-2 mb-6">
                <h5 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Info className="h-3.5 w-3.5 text-zinc-400" /> Implementation Details
                </h5>
                <ul className="space-y-2">
                  {activeStep.details.map((detail, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 text-xs text-zinc-300 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60"
                    >
                      <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5 text-white" />
                      <span className="leading-snug">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-zinc-800 text-xs">
                <button
                  onClick={() =>
                    handleStepClick((activeIndex - 1 + totalSteps) % totalSteps)
                  }
                  className="text-zinc-400 hover:text-white transition-colors flex items-center gap-1 font-mono"
                >
                  ← Step {((activeIndex - 1 + totalSteps) % totalSteps) + 1}
                </button>
                <span className="text-zinc-500 font-mono">
                  {activeIndex + 1} / 11
                </span>
                <button
                  onClick={() => handleStepClick((activeIndex + 1) % totalSteps)}
                  className="text-white hover:text-zinc-200 transition-colors flex items-center gap-1 font-mono font-semibold"
                >
                  Step {((activeIndex + 1) % totalSteps) + 1} →
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
