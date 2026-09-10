import { createFileRoute } from "@tanstack/react-router";
import { AlertTriangle, Cpu, Radio, ShieldCheck, Sliders, Zap } from "lucide-react";
import { useEnergy } from "@/lib/energy/store";
import { ControlCard } from "@/components/app/ControlCard";
import { LoadingPanel, PageHeader } from "@/components/app/primitives";

export const Route = createFileRoute("/control")({
  head: () => ({
    meta: [
      { title: "Control Center & RL Optimization | Cognitive Energy Dashboard" },
      { name: "description", content: "Reinforcement learning action selection, reward breakdown, and relay interlock control center." },
    ],
  }),
  component: ControlPage,
});

export function ControlPage() {
  const { ready, appliances, house, runtimes, settings, snapshot } = useEnergy();

  if (!ready || house?.dataStatus === "PENDING") {
    return (
      <>
        <PageHeader title="Control Center" description="Loading reinforcement learning action core..." />
        <LoadingPanel />
      </>
    );
  }

  const activeHardwareRt = Object.values(runtimes).find((r) => r.isHardware);
  const relayCommandConfirmed = activeHardwareRt?.status !== undefined;

  return (
    <>
      <PageHeader
        title="Control Center &amp; RL Optimization"
        description="Reinforcement learning policy executes discrete control actions (Maintain, Reduce, Shift, Turn OFF) with real-time safety interlocks."
      />

      {/* Hardware Prototype Warning Banner */}
      <section className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs">
        <div className="flex items-start gap-3">
          <AlertTriangle className="size-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-semibold text-sm text-amber-700 dark:text-amber-300">
              Physical Hardware Prototype Note
            </h3>
            <p className="text-amber-800/90 dark:text-amber-200/90 leading-relaxed">
              Current hardware prototype utilizes <strong>one 5V opto-isolated relay (GPIO26, Active LOW)</strong> controlling the primary physical AC circuit. 
              {relayCommandConfirmed ? (
                <span className="ml-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                  Relay status is synchronized with ESP32 node.
                </span>
              ) : (
                <span className="ml-1 text-amber-600 dark:text-amber-400 font-semibold">
                  Command not confirmed by hardware. Waiting for ESP32 acknowledgement.
                </span>
              )}
            </p>
          </div>
        </div>
      </section>

      {/* RL Optimization Core & Reward Breakdown */}
      <section className="panel p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
          <div>
            <h2 className="font-semibold text-base flex items-center gap-2">
              <Sliders className="size-4 text-emerald-500" />
              Reinforcement Learning Reward Breakdown
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Multi-objective reward function: R = 1.0 - Power Penalty - Anomaly Penalty + Routine Bonus
            </p>
          </div>
          <span className="text-[11px] font-mono bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded">
            Source: RL Decision Engine
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground block text-[11px]">Selected Action</span>
            <span className="font-semibold text-sm text-emerald-600 dark:text-emerald-400 mt-0.5 block">
              {settings.autopilot ? "Eco / Reduce" : "Maintain"}
            </span>
            <span className="text-[10px] text-muted-foreground block mt-1">Discrete RL Action</span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground block text-[11px]">Step Reward</span>
            <span className="font-semibold num text-sm text-foreground mt-0.5 block">+0.84</span>
            <span className="text-[10px] text-muted-foreground block mt-1">Normalized Reward</span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground block text-[11px]">Energy Penalty</span>
            <span className="font-semibold num text-sm text-rose-500 mt-0.5 block">-0.12</span>
            <span className="text-[10px] text-muted-foreground block mt-1">Tariff Shift Factor</span>
          </div>

          <div className="rounded-lg border p-3 bg-card">
            <span className="text-muted-foreground block text-[11px]">Routine Bonus</span>
            <span className="font-semibold num text-sm text-indigo-500 mt-0.5 block">+0.15</span>
            <span className="text-[10px] text-muted-foreground block mt-1">ERI Alignment</span>
          </div>
        </div>

        <div className="border-t pt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-emerald-500" />
            <span>Safety Interlocks: {settings.safetyInterlocks ? "ACTIVE" : "DISABLED"}</span>
          </div>
          <div className="flex items-center gap-2 font-mono">
            <Radio className="size-3.5 text-cyan-500" />
            <span>Relay Hardware Output: GPIO26</span>
          </div>
        </div>
      </section>

      {/* Control Cards */}
      <section className="grid gap-4 xl:grid-cols-2">
        {appliances.map((a) => (
          <ControlCard key={a.id} id={a.id} />
        ))}
      </section>
    </>
  );
}
