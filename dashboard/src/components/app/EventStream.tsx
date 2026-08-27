import { Activity } from "lucide-react";
import { APPLIANCE_MAP } from "@/lib/energy/appliances";
import { fmtRelative } from "@/lib/energy/format";
import { useEnergy } from "@/lib/energy/store";
import { cn } from "@/lib/utils";
import type { EventSeverity } from "@/lib/energy/types";

const TONE: Record<EventSeverity, string> = {
  info: "bg-info",
  success: "bg-success",
  warning: "bg-warning",
  critical: "bg-destructive",
};

export function EventStream({ limit = 12, title = "Live activity" }: { limit?: number; title?: string }) {
  const { events, now } = useEnergy();
  const list = events.slice(0, limit);

  return (
    <section className="panel flex flex-col p-5" aria-label={title}>
      <div className="mb-3 flex items-center gap-2">
        <Activity className="size-4" aria-hidden="true" />
        <h2 className="font-semibold">{title}</h2>
        <span className="ml-auto text-xs text-muted-foreground">Updates automatically</span>
      </div>
      {list.length === 0 ? (
        <p className="py-8 text-center text-sm text-muted-foreground">
          Nothing has happened yet. Events appear here as they occur.
        </p>
      ) : (
        <ol className="flex flex-col gap-3" aria-live="polite">
          {list.map((e) => (
            <li key={e.id} className="flex gap-3">
              <span className={cn("mt-1.5 size-2 shrink-0 rounded-full", TONE[e.severity])} aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <p className="text-sm font-medium">{e.title}</p>
                  {e.appliance ? (
                    <span className="text-xs text-muted-foreground">{APPLIANCE_MAP[e.appliance].name}</span>
                  ) : null}
                  <span className="ml-auto text-xs text-muted-foreground">{fmtRelative(e.t, now)}</span>
                </div>
                <p className="text-xs text-muted-foreground">{e.detail}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
