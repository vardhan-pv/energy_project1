import { Fan, Laptop, Lightbulb, Refrigerator, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { ApplianceProfile, RiskLevel } from "@/lib/energy/types";

const ICONS: Record<ApplianceProfile["icon"], LucideIcon> = {
  laptop: Laptop,
  lightbulb: Lightbulb,
  fan: Fan,
  refrigerator: Refrigerator,
};

export function ApplianceIcon({
  icon,
  className,
}: {
  icon: ApplianceProfile["icon"];
  className?: string;
}) {
  const Icon = ICONS[icon];
  return <Icon className={cn("size-5", className)} aria-hidden="true" />;
}

export function StatusDot({ state }: { state: "on" | "off" | "standby" | "offline" }) {
  const tone =
    state === "on"
      ? "bg-success text-success"
      : state === "standby"
        ? "bg-warning text-warning"
        : state === "offline"
          ? "bg-destructive text-destructive"
          : "bg-muted-foreground/50 text-muted-foreground";
  return (
    <span className="inline-flex items-center" aria-hidden="true">
      <span className={cn("size-2 rounded-full", tone, state === "on" && "live-dot")} />
    </span>
  );
}

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  const map: Record<RiskLevel, { label: string; className: string; hint: string }> = {
    normal: {
      label: "Normal",
      className: "border-success/30 bg-success/10 text-success",
      hint: "Usage matches what the model expects.",
    },
    watch: {
      label: "Watch",
      className: "border-warning/40 bg-warning/15 text-warning",
      hint: "A little higher than usual — worth keeping an eye on.",
    },
    risk: {
      label: "Attention",
      className: "border-destructive/30 bg-destructive/10 text-destructive",
      hint: "Well outside the learned pattern. Check the appliance.",
    },
  };
  const cfg = map[risk];
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant="outline" className={cn("font-medium", cfg.className)} tabIndex={0}>
          {cfg.label}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>{cfg.hint}</TooltipContent>
    </Tooltip>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}

export function StatCard({
  label,
  value,
  unitHint,
  icon: Icon,
  tone = "neutral",
  hint,
}: {
  label: string;
  value: string;
  unitHint?: string;
  icon?: LucideIcon;
  tone?: "neutral" | "success" | "warning" | "danger" | "info";
  hint?: string;
}) {
  const toneClass = {
    neutral: "text-foreground",
    success: "text-success",
    warning: "text-warning",
    danger: "text-destructive",
    info: "text-info",
  }[tone];

  return (
    <div className="panel p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium tracking-wide text-muted-foreground uppercase">
          {label}
          {hint ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  aria-label={`About ${label}`}
                  className="grid size-4 place-items-center rounded-full border border-border text-[10px] text-muted-foreground"
                >
                  ?
                </button>
              </TooltipTrigger>
              <TooltipContent className="max-w-56">{hint}</TooltipContent>
            </Tooltip>
          ) : null}
        </div>
        {Icon ? <Icon className={cn("size-4", toneClass)} aria-hidden="true" /> : null}
      </div>
      <p className={cn("num mt-3 text-2xl font-semibold sm:text-3xl", toneClass)}>{value}</p>
      {unitHint ? <p className="mt-1 text-xs text-muted-foreground">{unitHint}</p> : null}
    </div>
  );
}

export function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="panel grid place-items-center gap-1 p-10 text-center">
      <p className="font-medium">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}

export function LoadingPanel({ label = "Connecting to the demo telemetry engine…" }: { label?: string }) {
  return (
    <div className="panel grid place-items-center gap-3 p-12 text-center" role="status" aria-live="polite">
      <span className="size-6 animate-spin rounded-full border-2 border-border border-t-foreground" />
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}
