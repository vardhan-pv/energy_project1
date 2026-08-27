import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { PageHeader } from "@/components/app/primitives";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings | Cognitive Energy Dashboard" }
    ]
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { settings, updateSettings } = useEnergy();

  const saveConfig = (key: keyof typeof settings, val: any) => {
    updateSettings({ [key]: val });
    toast.success("Settings updated");
  };

  return (
    <>
      <PageHeader
        title="Settings & Config"
        description="Configure parameters for tariff, daily budget bounds, safety triggers, and backend details."
      />

      <div className="panel p-6 flex flex-col gap-6 max-w-2xl">
        <h2 className="font-semibold text-lg border-b pb-2">Optimization Bounds</h2>

        <div className="flex items-center justify-between gap-4">
          <div>
            <span className="font-medium text-sm">Autopilot Optimization</span>
            <p className="text-xs text-muted-foreground">Allow the ML models to automatically trim and modulate loads.</p>
          </div>
          <Switch
            checked={settings.autopilot}
            onCheckedChange={(v) => saveConfig("autopilot", v)}
          />
        </div>

        <div className="flex items-center justify-between gap-4">
          <div>
            <span className="font-medium text-sm">Safety Interlocks</span>
            <p className="text-xs text-muted-foreground">Block appliance operation or boosting during unsafe draw events.</p>
          </div>
          <Switch
            checked={settings.safetyInterlocks}
            onCheckedChange={(v) => saveConfig("safetyInterlocks", v)}
          />
        </div>

        <div className="grid grid-cols-2 gap-4 pt-2">
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">Daily Budget Limit (kWh)</label>
            <Input
              type="number"
              step="0.1"
              value={settings.budgetKwhPerDay}
              onChange={(e) => saveConfig("budgetKwhPerDay", parseFloat(e.target.value))}
              className="mt-1"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">Tariff rate per kWh ($)</label>
            <Input
              type="number"
              step="0.01"
              value={settings.tariffPerKwh}
              onChange={(e) => saveConfig("tariffPerKwh", parseFloat(e.target.value))}
              className="mt-1"
            />
          </div>
        </div>

        <h2 className="font-semibold text-lg border-b pb-2 mt-4">Data Source</h2>

        <div className="flex items-center justify-between gap-4">
          <div>
            <span className="font-medium text-sm">Use Live API</span>
            <p className="text-xs text-muted-foreground">Connect directly to a Python ML telemetry backend.</p>
          </div>
          <Switch
            checked={settings.useLiveApi}
            onCheckedChange={(v) => saveConfig("useLiveApi", v)}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase">API Base URL</label>
          <Input
            value={settings.apiBaseUrl}
            onChange={(e) => saveConfig("apiBaseUrl", e.target.value)}
            placeholder="http://localhost:5000"
            className="mt-1"
          />
        </div>
      </div>
    </>
  );
}
