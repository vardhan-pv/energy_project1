import { useState } from "react";
import { Lock, ShieldCheck, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtW } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import type { ApplianceId, ControlMode } from "@/lib/energy/types";
import { cn } from "@/lib/utils";
import { ApplianceIcon, StatusDot } from "./primitives";

const MODES: { value: ControlMode; label: string; help: string }[] = [
  { value: "eco", label: "Eco", help: "Lowest sensible power. Best for saving money." },
  { value: "reduce", label: "Reduce", help: "Trim power a little below normal." },
  { value: "maintain", label: "Maintain", help: "Keep the appliance where it is." },
  { value: "increase", label: "Boost", help: "Allow more power for extra comfort." },
];

export function ControlCard({ id }: { id: ApplianceId }) {
  const { runtimes, loops, setPower, setMode, setTarget, settings } = useEnergy();
  const rt = runtimes[id];
  const loop = loops[id];
  const profile = APPLIANCE_MAP[id];
  const [confirm, setConfirm] = useState<null | { title: string; body: string; run: () => void }>(null);

  if (!rt) return null;
  const blocked = settings.safetyInterlocks && loop?.safetyStatus === "blocked";

  const askPower = (on: boolean) => {
    if (profile.criticalAlwaysOn && !on) {
      toast.error(`${profile.name} must stay on`, {
        description: "Safety interlock protects food from spoiling.",
      });
      return;
    }
    if (!on) {
      setConfirm({
        title: `Turn off ${profile.name}?`,
        body: "This stops the appliance immediately. You can turn it back on at any time.",
        run: () => {
          setPower(id, false);
          toast.success(`${profile.name} turned off`);
        },
      });
      return;
    }
    setPower(id, true);
    toast.success(`${profile.name} turned on`);
  };

  const applyMode = (mode: ControlMode) => {
    if (blocked && mode === "increase") {
      toast.error("Blocked by safety interlock", {
        description: "Boost is unavailable while this appliance is flagged for attention.",
      });
      return;
    }
    if (mode === "increase") {
      setConfirm({
        title: `Boost ${profile.name}?`,
        body: "Boost raises power use above normal and will increase today's cost.",
        run: () => {
          setMode(id, mode);
          toast.success(`${profile.name} set to Boost`);
        },
      });
      return;
    }
    setMode(id, mode);
    toast.success(`${profile.name} set to ${MODES.find((m) => m.value === mode)?.label}`);
  };

  return (
    <article className="panel flex flex-col gap-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-lg bg-secondary text-secondary-foreground">
            <ApplianceIcon icon={profile.icon} />
          </div>
          <div>
            <h3 className="font-semibold">{profile.name}</h3>
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <StatusDot state={rt.status} />
              <span className="capitalize">{rt.status}</span> · now {fmtW(rt.powerW, 1)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {profile.criticalAlwaysOn ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Badge variant="outline" tabIndex={0} className="gap-1">
                  <Lock className="size-3" aria-hidden="true" /> Always on
                </Badge>
              </TooltipTrigger>
              <TooltipContent>Safety interlock: the fridge cannot be switched off here.</TooltipContent>
            </Tooltip>
          ) : null}
          <div className="flex items-center gap-2">
            <label htmlFor={`pw-${id}`} className="text-sm text-muted-foreground">
              Power
            </label>
            <Switch
              id={`pw-${id}`}
              checked={rt.status !== "off"}
              disabled={profile.criticalAlwaysOn}
              onCheckedChange={askPower}
              aria-label={`Turn ${profile.name} ${rt.status === "off" ? "on" : "off"}`}
            />
          </div>
        </div>
      </div>

      <div>
        <p className="mb-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">Mode</p>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4" role="group" aria-label={`${profile.name} mode`}>
          {MODES.map((m) => (
            <Tooltip key={m.value}>
              <TooltipTrigger asChild>
                <Button
                  variant={rt.mode === m.value ? "default" : "outline"}
                  size="sm"
                  disabled={rt.status === "off"}
                  aria-pressed={rt.mode === m.value}
                  onClick={() => applyMode(m.value)}
                >
                  {m.label}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{m.help}</TooltipContent>
            </Tooltip>
          ))}
        </div>
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <label htmlFor={`tgt-${id}`} className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Target power
          </label>
          <span className="num text-sm font-semibold">{fmtW(rt.targetPowerW)}</span>
        </div>
        <Slider
          id={`tgt-${id}`}
          value={[rt.targetPowerW]}
          min={profile.minPowerW}
          max={profile.maxPowerW}
          step={1}
          disabled={rt.status === "off"}
          onValueChange={(v) => setTarget(id, v[0])}
          aria-label={`${profile.name} target power in watts`}
        />
        <p className="mt-1.5 text-xs text-muted-foreground">
          Allowed range {profile.minPowerW}–{profile.maxPowerW} W. The controller keeps the appliance near this value.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2 rounded-lg bg-surface p-3 text-xs">
        {blocked ? (
          <ShieldAlert className="size-4 text-destructive" aria-hidden="true" />
        ) : (
          <ShieldCheck className="size-4 text-success" aria-hidden="true" />
        )}
        <span className={cn("font-medium", blocked ? "text-destructive" : "text-success")}>
          {blocked ? "Safety interlock engaged" : "Safe to control"}
        </span>
        <span className="text-muted-foreground">
          Feedback: measured {fmtW(loop?.measuredPowerW ?? 0, 1)} · error{" "}
          {(loop?.powerErrorW ?? 0).toFixed(1)} W · {loop?.controlSuccess ? "on target" : "correcting"}
        </span>
      </div>

      <AlertDialog open={!!confirm} onOpenChange={(o) => !o && setConfirm(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{confirm?.title}</AlertDialogTitle>
            <AlertDialogDescription>{confirm?.body}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                confirm?.run();
                setConfirm(null);
              }}
            >
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </article>
  );
}
