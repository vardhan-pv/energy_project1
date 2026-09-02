import { Brain, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtKwh, fmtMoney, fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId } from "@/lib/energy/types";
import { ForecastChart } from "./charts";
import { ApplianceIcon, RiskBadge } from "./primitives";

export function PredictionCard({ id }: { id: ApplianceId }) {
  const { predictions, runtimes, settings, appliances } = useEnergy();
  const p = predictions[id];
  const rt = runtimes[id];
  const profile = appliances.find((a) => a.id === id) ?? APPLIANCE_MAP[id];
  if (!p || !rt || !profile) return null;

  const delta = p.nextPowerW - rt.powerW;
  const cost = p.expectedUsageKwh * settings.tariffPerKwh;

  return (
    <article className="panel flex flex-col gap-4 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground">
            <ApplianceIcon icon={profile.icon} />
          </div>
          <div>
            <h3 className="font-semibold">{profile.name}</h3>
            <p className="text-xs text-muted-foreground">
              {profile.model.name} · {profile.model.version}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <RiskBadge risk={p.risk} />
          <Badge variant="outline" className="gap-1">
            <Brain className="size-3" aria-hidden="true" />
            {settings.useLiveApi ? "Live model" : "Simulation"}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Field
          label="Next power"
          value={fmtW(p.nextPowerW, 1)}
          sub={`${delta >= 0 ? "+" : ""}${delta.toFixed(1)} W vs now`}
          hint="Average power the model expects over the horizon."
        />
        <Field
          label="Expected usage"
          value={fmtKwh(p.expectedUsageKwh, 3)}
          sub={`≈ ${fmtMoney(cost, settings.currency)}`}
          hint="Energy likely to be used across the prediction horizon."
        />
        <Field label="Horizon" value={`${p.horizonMinutes} min`} sub="Forecast window" hint="How far ahead the model is looking." />
        <Field label="Confidence" value={`${p.confidencePct}%`} sub="Model certainty" hint="How sure the trained demo model is about this forecast." />
      </div>

      <div>
        <Progress value={p.confidencePct} aria-label={`${profile.name} prediction confidence`} />
      </div>

      <ForecastChart data={p.curve} height={170} />

      <p className="flex items-start gap-2 text-xs text-muted-foreground">
        <TrendingUp className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
        {p.riskNote}{" "}
        {settings.useLiveApi
          ? `Trained on ${profile.model.trainedOn}.`
          : `Trained on ${profile.model.trainedOn} (offline simulation).`}
      </p>
    </article>
  );
}

function Field({ label, value, sub, hint }: { label: string; value: string; sub: string; hint: string }) {
  return (
    <div>
      <Tooltip>
        <TooltipTrigger asChild>
          <p tabIndex={0} className="text-[11px] tracking-wide text-muted-foreground uppercase">
            {label}
          </p>
        </TooltipTrigger>
        <TooltipContent className="max-w-56">{hint}</TooltipContent>
      </Tooltip>
      <p className="num mt-0.5 text-lg font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}
