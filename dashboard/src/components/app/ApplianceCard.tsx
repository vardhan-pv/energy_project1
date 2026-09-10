import { Link } from "@tanstack/react-router";
import { Thermometer, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtKwh, fmtMoney, fmtTemp, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId } from "@/lib/energy/types";
import { ApplianceIcon, RiskBadge, StatusDot } from "./primitives";
import { PowerAreaChart } from "./charts";

export function ApplianceCard({ id, compact = false }: { id: ApplianceId; compact?: boolean }) {
  const { runtimes, appliances, settings } = useEnergy();
  const rt = runtimes[id];
  const profile = appliances.find((a) => a.id === id) ?? APPLIANCE_MAP[id];
  if (!rt || !profile) return null;

  const loadPct = Math.min(100, (rt.powerW / profile.maxPowerW) * 100);
  const cost = rt.energyTodayKwh * settings.tariffPerKwh;

  return (
    <article className="panel flex flex-col gap-4 p-5 transition-shadow hover:shadow-[var(--shadow-lift)]">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground">
            <ApplianceIcon icon={profile.icon} />
          </div>
          <div>
            <h3 className="leading-tight font-semibold">{profile.name}</h3>
            <p className="text-xs text-muted-foreground">{profile.room}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {settings.useLiveApi ? (
            rt.isHardware ? (
              <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 gap-1.5">
                <StatusDot state="on" />
                LIVE ESP32
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1.5 text-muted-foreground">
                <StatusDot state="offline" />
                Unmeasured
              </Badge>
            )
          ) : (
            <>
              <RiskBadge risk={rt.risk} />
              <Badge variant="outline" className="gap-1.5 capitalize">
                <StatusDot state={rt.online ? rt.status : "offline"} />
                {rt.status}
              </Badge>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="Power now" value={settings.useLiveApi && !rt.isHardware ? "0.0 W" : fmtW(rt.powerW, 1)} />
        <Metric
          label={rt.voltageV ? "Voltage" : "Today"}
          value={rt.voltageV ? `${rt.voltageV.toFixed(1)} V` : fmtKwh(rt.energyTodayKwh)}
        />
        <Metric
          label={rt.currentA !== undefined ? "Current" : "Cost today"}
          value={rt.currentA !== undefined ? `${rt.currentA.toFixed(2)} A` : fmtMoney(cost, settings.currency)}
        />
        <Metric
          label={rt.humidityPct ? "Humidity" : profile.hasTemperature ? "Temperature" : "Mode"}
          value={
            rt.humidityPct
              ? `${rt.humidityPct.toFixed(0)}%`
              : profile.hasTemperature
              ? fmtTemp(rt.temperatureC)
              : rt.mode
          }
          capitalize={!profile.hasTemperature && !rt.humidityPct}
        />
      </div>

      <div>
        <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Zap className="size-3" aria-hidden="true" /> Load vs. maximum
          </span>
          <span className="num">{loadPct.toFixed(0)}%</span>
        </div>
        <Progress value={loadPct} aria-label={`${profile.name} load`} />
      </div>

      {!compact ? (
        <div className="-mx-1">
          <PowerAreaChart data={rt.history.slice(-45)} height={120} />
        </div>
      ) : null}

      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">
          Target {fmtW(rt.targetPowerW)} · mode <span className="capitalize">{rt.mode}</span>
        </span>
        <Link to="/control" className="font-medium underline underline-offset-4 hover:no-underline">
          Control
        </Link>
      </div>

      {profile.hasTemperature ? (
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Thermometer className="size-3" aria-hidden="true" />
          {profile.description}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground">{profile.description}</p>
      )}
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
      <p className={`num mt-0.5 font-semibold ${capitalize ? "capitalize" : ""}`}>{value}</p>
    </div>
  );
}
