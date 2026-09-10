import { Link } from "@tanstack/react-router";
import { Info, Thermometer, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtKwh, fmtMoney, fmtTemp, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId } from "@/lib/energy/types";
import { ApplianceIcon, RiskBadge, StatusDot } from "./primitives";
import { PowerAreaChart } from "./charts";

// Known IREOS Cognitive Analysis scores calculated for the four appliance profiles
const COGNITIVE_SCORES: Record<
  ApplianceId,
  { eri: number; eriLabel: string; cdi: number; cdiLabel: string; ubd: number; ubdLabel: string }
> = {
  fridge: {
    eri: 95.5711,
    eriLabel: "Highly Regular",
    cdi: 79.8768,
    cdiLabel: "High Intelligence",
    ubd: 73.0265,
    ubdLabel: "Consistent High",
  },
  kitchen_lights: {
    eri: 70.0012,
    eriLabel: "Regular",
    cdi: 60.6319,
    cdiLabel: "Moderate",
    ubd: 51.2491,
    ubdLabel: "Moderately Dynamic",
  },
  laptop: {
    eri: 81.9876,
    eriLabel: "Highly Regular",
    cdi: 78.3,
    cdiLabel: "High Intelligence",
    ubd: 78.2374,
    ubdLabel: "Consistent High",
  },
  office_fan: {
    eri: 79.7021,
    eriLabel: "Regular",
    cdi: 61.7271,
    cdiLabel: "Moderate",
    ubd: 51.0365,
    ubdLabel: "Moderately Dynamic",
  },
};

export function ApplianceCard({ id, compact = false }: { id: ApplianceId; compact?: boolean }) {
  const { runtimes, appliances, settings } = useEnergy();
  const rt = runtimes[id];
  const profile = appliances.find((a) => a.id === id) ?? APPLIANCE_MAP[id];
  if (!rt || !profile) return null;

  const loadPct = Math.min(100, (rt.powerW / profile.maxPowerW) * 100);
  const cost = rt.energyTodayKwh * settings.tariffPerKwh;
  const scores = COGNITIVE_SCORES[id] || {
    eri: 75.0,
    eriLabel: "Regular",
    cdi: 65.0,
    cdiLabel: "Moderate",
    ubd: 60.0,
    ubdLabel: "Consistent",
  };

  return (
    <article className="panel flex flex-col justify-between gap-4 p-5 transition-shadow hover:shadow-[var(--shadow-lift)]">
      <div className="flex items-start justify-between gap-3 border-b pb-3">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground">
            <ApplianceIcon icon={profile.icon} />
          </div>
          <div>
            <h3 className="leading-tight font-semibold text-sm sm:text-base">{profile?.name ?? "Appliance"}</h3>
            <p className="text-xs text-muted-foreground">{profile?.room ?? "Main Room"} · Rated {profile?.ratedPowerW ?? 100} W</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {settings.useLiveApi ? (
            rt.isHardware ? (
              <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1.5 text-xs">
                <StatusDot state="on" />
                LIVE ESP32
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 text-[11px] text-muted-foreground">
                <Info className="size-3" />
                Sub-metered Model
              </Badge>
            )
          ) : (
            <>
              <RiskBadge risk={rt.risk} />
              <Badge variant="outline" className="gap-1.5 capitalize text-xs">
                <StatusDot state={rt.online ? rt.status : "offline"} />
                {rt.status}
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Distinction: Model vs Hardware */}
      {settings.useLiveApi && !rt.isHardware ? (
        <div className="rounded-lg bg-muted/40 p-2.5 text-xs border border-border/50">
          <div className="flex items-center justify-between font-mono text-[11px] text-muted-foreground mb-1">
            <span>PHYSICAL TELEMETRY</span>
            <span className="text-amber-600 dark:text-amber-400 font-semibold">Not independently measured</span>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Measured via primary PZEM AC circuit. Power values below reflect UK-DALE disaggregation model predictions.
          </p>
        </div>
      ) : null}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          label="Model Power"
          value={settings.useLiveApi && !rt.isHardware ? `${(profile?.ratedPowerW ?? 100).toFixed(0)} W (rated)` : fmtW(rt.powerW, 1)}
        />
        <Metric
          label="Voltage"
          value={rt.voltageV !== undefined ? `${rt.voltageV.toFixed(1)} V` : "Not available"}
        />
        <Metric
          label="Current"
          value={rt.currentA !== undefined ? `${rt.currentA.toFixed(2)} A` : "Not available"}
        />
        <Metric
          label="Energy Today"
          value={fmtKwh(rt.energyTodayKwh)}
        />
      </div>

      {/* Cognitive Intelligence Summary Pill */}
      <div className="rounded-lg border bg-surface p-2.5 text-xs">
        <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground mb-1.5">
          <span>COGNITIVE MODEL SCORES</span>
          <Link to="/analytics" className="text-primary hover:underline">
            View Analytics →
          </Link>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center text-[11px]">
          <div className="bg-background rounded p-1 border">
            <span className="text-muted-foreground block">ERI</span>
            <span className="font-semibold num">{scores.eri.toFixed(1)}</span>
          </div>
          <div className="bg-background rounded p-1 border">
            <span className="text-muted-foreground block">CDI</span>
            <span className="font-semibold num">{scores.cdi.toFixed(1)}</span>
          </div>
          <div className="bg-background rounded p-1 border">
            <span className="text-muted-foreground block">UBD</span>
            <span className="font-semibold num">{scores.ubd.toFixed(1)}</span>
          </div>
        </div>
      </div>

      <div>
        <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Zap className="size-3" aria-hidden="true" /> Model load vs. maximum
          </span>
          <span className="num">{loadPct.toFixed(0)}%</span>
        </div>
        <Progress value={loadPct} aria-label={`${profile.name} load`} />
      </div>

      {!compact ? (
        <div className="-mx-1">
          <PowerAreaChart data={(rt.history ?? []).slice(-45)} height={110} />
        </div>
      ) : null}

      <div className="flex items-center justify-between text-xs border-t pt-2">
        <span className="text-muted-foreground">
          Target {fmtW(rt.targetPowerW)} · mode <span className="capitalize font-semibold">{rt.mode}</span>
        </span>
        <Link to="/control" className="font-medium text-primary hover:underline">
          Control Center
        </Link>
      </div>
    </article>
  );
}

function Metric({
  label,
  value,
  capitalize,
}: {
  label: string;
  value: string;
  capitalize?: boolean;
}) {
  return (
    <div>
      <p className="text-[11px] tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className={`num mt-0.5 font-semibold text-xs sm:text-sm ${capitalize ? "capitalize" : ""}`}>{value}</p>
    </div>
  );
}
