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
  ShieldCheck,
  Server,
  ArrowRight,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface PipelineStep {
  step: string;
  title: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  glowColor: string;
  accentHex: string;
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
    color: "border-cyan-500/40 bg-cyan-500/10 text-cyan-400",
    glowColor: "rgba(6, 182, 212, 0.6)",
    accentHex: "#06b6d4",
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
    color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-400",
    glowColor: "rgba(99, 102, 241, 0.6)",
    accentHex: "#6366f1",
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
    color: "border-blue-500/40 bg-blue-500/10 text-blue-400",
    glowColor: "rgba(59, 130, 246, 0.6)",
    accentHex: "#3b82f6",
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
    color: "border-purple-500/40 bg-purple-500/10 text-purple-400",
    glowColor: "rgba(168, 85, 247, 0.6)",
    accentHex: "#a855f7",
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
    color: "border-fuchsia-500/40 bg-fuchsia-500/10 text-fuchsia-400",
    glowColor: "rgba(217, 70, 239, 0.6)",
    accentHex: "#d946ef",
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
    color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
    glowColor: "rgba(16, 185, 129, 0.6)",
    accentHex: "#10b981",
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
    color: "border-teal-500/40 bg-teal-500/10 text-teal-600 dark:text-teal-400",
    glowColor: "rgba(20, 184, 166, 0.6)",
    accentHex: "#14b8a6",
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
    color: "border-amber-500/40 bg-amber-500/10 text-amber-400",
    glowColor: "rgba(245, 158, 11, 0.6)",
    accentHex: "#f59e0b",
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
    color: "border-orange-500/40 bg-orange-500/10 text-orange-400",
    glowColor: "rgba(249, 115, 22, 0.6)",
    accentHex: "#f97316",
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
    color: "border-rose-500/40 bg-rose-500/10 text-rose-400",
    glowColor: "rgba(244, 63, 94, 0.6)",
    accentHex: "#f43f5e",
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
    color: "border-emerald-400/40 bg-emerald-500/10 text-emerald-400",
    glowColor: "rgba(52, 211, 153, 0.6)",
    accentHex: "#34d399",
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
  const [rotationSpeed, setRotationSpeed] = useState(2500); // 2.5 seconds per step

  const activeIndex = externalActiveIndex !== undefined ? externalActiveIndex : internalActiveIndex;
  const activeStep = ARCHITECTURE_STEPS[activeIndex];

  // Auto-rotate cycle
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

  // Polar layout geometry constants
  const totalSteps = ARCHITECTURE_STEPS.length;
  const radius = 310; // SVG radius
  const cx = 400; // SVG center X
  const cy = 400; // SVG center Y

  // Compute node coordinates
  const stepNodes = ARCHITECTURE_STEPS.map((stepItem, idx) => {
    const angleRad = -Math.PI / 2 + (idx * 2 * Math.PI) / totalSteps;
    const x = cx + radius * Math.cos(angleRad);
    const y = cy + radius * Math.sin(angleRad);
    return { ...stepItem, idx, x, y, angleRad };
  });

  const activeNode = stepNodes[activeIndex];

  return (
    <div className="relative w-full overflow-hidden rounded-3xl border border-cyan-500/20 bg-slate-950/80 p-4 sm:p-8 backdrop-blur-xl shadow-2xl shadow-cyan-950/30">
      {/* Background Neon Grid & Glow */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.12)_0%,transparent_70%)] pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10 border-b border-cyan-500/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-500/20">
            <Activity className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-lg text-slate-100 tracking-wide">
                IREOS Closed-Loop Engine
              </h3>
              <Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30 animate-pulse text-[10px] uppercase font-mono">
                Real-Time Loop Active
              </Badge>
            </div>
            <p className="text-xs text-slate-400">
              11-Layer Continuous Autonomous Cognitive Optimization Cycle
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/90 border border-slate-800 rounded-xl p-1.5 backdrop-blur-md">
          <Button
            size="sm"
            variant={isAutoRotating ? "default" : "ghost"}
            className={
              isAutoRotating
                ? "bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs shadow-md shadow-cyan-600/30"
                : "text-slate-400 hover:text-slate-200 text-xs"
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
            className="border-slate-800 text-slate-300 hover:bg-slate-800 text-xs"
            onClick={() => handleStepClick((activeIndex + 1) % totalSteps)}
          >
            <RotateCw className="h-3.5 w-3.5 mr-1.5 text-cyan-400" /> Next Layer
          </Button>
        </div>
      </div>

      {/* Main Orbital Layout & Detail Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
        {/* Left / Top: SVG Interactive Orbital Ring (Hero Element) */}
        <div className="lg:col-span-7 flex flex-col items-center justify-center relative min-h-[520px] sm:min-h-[600px] w-full">
          <div className="relative w-full max-w-[580px] aspect-square flex items-center justify-center">
            <svg
              viewBox="0 0 800 800"
              className="w-full h-full drop-shadow-[0_0_25px_rgba(6,182,212,0.15)] overflow-visible"
            >
              <defs>
                {/* Orbital Path Glow Filter */}
                <filter id="orbital-glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="8" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                {/* Ring Gradients */}
                <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
                  <stop offset="33%" stopColor="#3b82f6" stopOpacity="0.8" />
                  <stop offset="66%" stopColor="#a855f7" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.8" />
                </linearGradient>

                <linearGradient id="activeBeam" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#06b6d4" stopOpacity="1" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="1" />
                </linearGradient>
              </defs>

              {/* Background Outer Soft Ring */}
              <circle
                cx={cx}
                cy={cy}
                r={radius + 35}
                fill="none"
                stroke="rgba(255,255,255,0.03)"
                strokeWidth="1"
                strokeDasharray="4 8"
              />

              {/* Main Glowing Orbital Track Ring */}
              <circle
                cx={cx}
                cy={cy}
                r={radius}
                fill="none"
                stroke="url(#ringGradient)"
                strokeWidth="3"
                strokeOpacity="0.35"
                filter="url(#orbital-glow)"
              />

              {/* Flowing Laser Particle Ring Animation */}
              <motion.circle
                cx={cx}
                cy={cy}
                r={radius}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray="25 120"
                animate={{ strokeDashoffset: [0, -1450] }}
                transition={{
                  repeat: Infinity,
                  duration: 12,
                  ease: "linear",
                }}
                filter="url(#orbital-glow)"
              />

              {/* Active Step Ray Beam from Center to Active Node */}
              <motion.line
                x1={cx}
                y1={cy}
                x2={activeNode.x}
                y2={activeNode.y}
                stroke={activeNode.accentHex}
                strokeWidth="2"
                strokeDasharray="4 4"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0.3, 0.8, 0.3] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />

              {/* Connecting Spoke Lines for all nodes */}
              {stepNodes.map((node) => (
                <line
                  key={`spoke-${node.step}`}
                  x1={cx}
                  y1={cy}
                  x2={node.x}
                  y2={node.y}
                  stroke="rgba(255,255,255,0.04)"
                  strokeWidth="1"
                />
              ))}

              {/* Step Nodes SVG Overlay */}
              {stepNodes.map((node) => {
                const isActive = node.idx === activeIndex;
                const IconComp = node.icon;

                return (
                  <g
                    key={node.step}
                    className="cursor-pointer transition-transform duration-300 hover:scale-110"
                    onClick={() => handleStepClick(node.idx)}
                  >
                    {/* Active Pulsing Ring Emitter */}
                    {isActive && (
                      <motion.circle
                        cx={node.x}
                        cy={node.y}
                        r="38"
                        fill="none"
                        stroke={node.accentHex}
                        strokeWidth="2"
                        initial={{ scale: 0.8, opacity: 1 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
                      />
                    )}

                    {/* Node Outer Circle */}
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isActive ? "28" : "22"}
                      fill={isActive ? "#0f172a" : "#020617"}
                      stroke={isActive ? node.accentHex : "rgba(255,255,255,0.15)"}
                      strokeWidth={isActive ? "3" : "1.5"}
                      className="transition-all duration-300"
                      filter={isActive ? "url(#orbital-glow)" : undefined}
                    />

                    {/* Node Number Badge */}
                    <circle
                      cx={node.x + (isActive ? 18 : 14)}
                      cy={node.y - (isActive ? 18 : 14)}
                      r="10"
                      fill={isActive ? node.accentHex : "#1e293b"}
                    />
                    <text
                      x={node.x + (isActive ? 18 : 14)}
                      y={node.y - (isActive ? 14 : 10)}
                      textAnchor="middle"
                      fill={isActive ? "#020617" : "#94a3b8"}
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

            {/* Render HTML Icons & Labels on top of SVG nodes for crisp rendering */}
            {stepNodes.map((node) => {
              const isActive = node.idx === activeIndex;
              const IconComp = node.icon;
              // Map SVG coordinates to percentage inside container
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
                        ? "h-14 w-14 shadow-xl border-2"
                        : "h-11 w-11 hover:scale-110 border border-slate-700 bg-slate-900/90 text-slate-400 group-hover:text-slate-100"
                    }`}
                    style={{
                      borderColor: isActive ? node.accentHex : undefined,
                      backgroundColor: isActive ? "#0f172a" : undefined,
                      color: isActive ? node.accentHex : undefined,
                      boxShadow: isActive ? `0 0 25px ${node.glowColor}` : undefined,
                    }}
                  >
                    <IconComp className={isActive ? "h-6 w-6 animate-pulse" : "h-4 w-4"} />
                  </div>

                  {/* Title Label below node */}
                  <span
                    className={`mt-1.5 text-[10px] font-semibold tracking-tight whitespace-nowrap px-1.5 py-0.5 rounded-full transition-all ${
                      isActive
                        ? "bg-slate-900/90 text-cyan-300 border border-cyan-500/40 shadow-sm"
                        : "text-slate-400 group-hover:text-slate-200 bg-slate-950/60"
                    }`}
                  >
                    {node.title}
                  </span>
                </div>
              );
            })}

            {/* Central Hero Core View (Inside Circle) */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 rounded-full bg-slate-950/90 border border-cyan-500/30 backdrop-blur-xl flex flex-col items-center justify-center text-center p-3 shadow-2xl shadow-cyan-950/80 z-20 pointer-events-none">
              <motion.div
                key={`core-icon-${activeStep.step}`}
                initial={{ scale: 0.7, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="flex h-12 w-12 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 mb-1"
              >
                {React.createElement(activeStep.icon, { className: "h-6 w-6" })}
              </motion.div>

              <div className="text-[10px] font-mono tracking-widest text-cyan-400 uppercase font-bold">
                STEP {activeStep.step} / 11
              </div>

              <div className="font-bold text-sm text-slate-100 leading-tight my-0.5 line-clamp-1 px-1">
                {activeStep.title}
              </div>

              <div className="text-[9px] text-slate-400 font-mono flex items-center justify-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />
                CLOSED-LOOP ACTIVE
              </div>
            </div>
          </div>
        </div>

        {/* Right / Bottom: Selected Step Interactive Glassmorphism Detail Card */}
        <div className="lg:col-span-5 w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeStep.step}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
              className="rounded-2xl border border-slate-800 bg-slate-900/90 p-6 backdrop-blur-xl shadow-xl relative overflow-hidden"
              style={{
                boxShadow: `0 0 30px ${activeStep.glowColor.replace("0.6", "0.15")}`,
              }}
            >
              {/* Header Accent Beam */}
              <div
                className="absolute top-0 left-0 right-0 h-1"
                style={{ backgroundColor: activeStep.accentHex }}
              />

              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className="flex h-12 w-12 items-center justify-center rounded-2xl border"
                    style={{
                      borderColor: activeStep.accentHex,
                      backgroundColor: `${activeStep.accentHex}15`,
                      color: activeStep.accentHex,
                    }}
                  >
                    {React.createElement(activeStep.icon, { className: "h-6 w-6" })}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider">
                        LAYER {activeStep.step} OF 11
                      </span>
                      <Badge variant="outline" className="text-[10px] border-slate-700 text-slate-300">
                        {activeStep.badge}
                      </Badge>
                    </div>
                    <h4 className="text-xl font-bold text-slate-100 tracking-tight">
                      {activeStep.title}
                    </h4>
                  </div>
                </div>
              </div>

              <p className="text-xs font-medium text-slate-300 mb-4 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80 leading-relaxed">
                {activeStep.description}
              </p>

              {/* Hardware / Protocol Note Pill */}
              {activeStep.hardwareNote && (
                <div className="mb-4 flex items-center gap-2 text-[11px] font-mono text-cyan-300 bg-cyan-950/40 border border-cyan-500/20 px-3 py-2 rounded-lg">
                  <Server className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                  <span className="truncate">{activeStep.hardwareNote}</span>
                </div>
              )}

              {/* Implementation Bullet Points */}
              <div className="space-y-2 mb-6">
                <h5 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Info className="h-3.5 w-3.5 text-slate-400" /> Key Pipeline Implementation
                </h5>
                <ul className="space-y-2">
                  {activeStep.details.map((detail, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/40"
                    >
                      <CheckCircle2
                        className="h-4 w-4 shrink-0 mt-0.5"
                        style={{ color: activeStep.accentHex }}
                      />
                      <span className="leading-snug">{detail}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Quick Navigation Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
                <button
                  onClick={() =>
                    handleStepClick((activeIndex - 1 + totalSteps) % totalSteps)
                  }
                  className="text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 font-mono"
                >
                  ← Step {((activeIndex - 1 + totalSteps) % totalSteps) + 1}
                </button>
                <span className="text-slate-500 font-mono">
                  {activeIndex + 1} / 11
                </span>
                <button
                  onClick={() => handleStepClick((activeIndex + 1) % totalSteps)}
                  className="text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1 font-mono font-semibold"
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
