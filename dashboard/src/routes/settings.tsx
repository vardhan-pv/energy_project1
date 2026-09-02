import { useState, useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { createHttpDataSource } from "@/lib/energy/api";
import { PageHeader } from "@/components/app/primitives";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { User, Home, Shield, Save } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings & Profile | Energy Dashboard" }
    ]
  }),
  component: SettingsPage,
});

function SettingsPage() {
  const { settings, updateSettings, user, token, house } = useEnergy();

  // Profile form state
  const [userName, setUserName] = useState(user?.name || "");
  const [userEmail, setUserEmail] = useState(user?.email || "");
  const [savingProfile, setSavingProfile] = useState(false);

  // House form state
  const [hName, setHName] = useState(house?.name || "Rama Nilaya");
  const [hLoc, setHLoc] = useState(house?.location || "Bengaluru, Karnataka, India");
  const [savingHouse, setSavingHouse] = useState(false);

  useEffect(() => {
    if (user) {
      setUserName(user.name);
      setUserEmail(user.email);
    }
  }, [user]);

  useEffect(() => {
    if (house) {
      setHName(house.name);
      setHLoc(house.location);
    }
  }, [house]);

  const saveConfig = (key: keyof typeof settings, val: any) => {
    updateSettings({ [key]: val });
    toast.success("Settings updated");
  };

  const handleSaveProfile = async () => {
    if (!userName || !userEmail) {
      toast.error("Name and email are required");
      return;
    }
    setSavingProfile(true);
    try {
      const ds = createHttpDataSource(settings.apiBaseUrl, () => token);
      const res = await ds.updateProfile(userName, userEmail);
      if (res.ok) {
        toast.success("User profile updated in real-time!");
        if (typeof window !== "undefined") {
          window.localStorage.setItem("ceos.user", JSON.stringify(res.user));
        }
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleSaveHouse = async () => {
    if (!hName) {
      toast.error("House name is required");
      return;
    }
    setSavingHouse(true);
    try {
      const ds = createHttpDataSource(settings.apiBaseUrl, () => token);
      const houseId = house?.id || (house as any)?.house_id || "HSE-87B7EB2B";
      const res = await ds.updateHouse(houseId, hName, hLoc);
      if (res.ok) {
        toast.success("House details updated in real-time!");
      }
    } catch (err: any) {
      toast.error(err.message || "Failed to update house details");
    } finally {
      setSavingHouse(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Settings & User Profile"
        description="Manage your account profile, digital house parameters, optimization bounds, and backend configuration."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-4xl">
        {/* Profile Settings */}
        <div className="panel p-6 flex flex-col gap-4">
          <h2 className="font-semibold text-lg border-b pb-2 flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            User Account Profile
          </h2>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">User ID (Server Assigned)</label>
            <Input
              value={user?.user_id || "USR-DEMO01"}
              disabled
              className="mt-1 font-mono text-sm bg-muted font-bold text-primary"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">Full Name</label>
            <Input
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="e.g. Vardhan Reddy"
              className="mt-1"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
            <Input
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              placeholder="user@example.com"
              className="mt-1"
            />
          </div>

          <Button onClick={handleSaveProfile} disabled={savingProfile || !token} className="mt-2 gap-2">
            <Save className="h-4 w-4" />
            {savingProfile ? "Saving Profile..." : "Save Profile Details"}
          </Button>
        </div>

        {/* House Settings */}
        <div className="panel p-6 flex flex-col gap-4">
          <h2 className="font-semibold text-lg border-b pb-2 flex items-center gap-2">
            <Home className="h-5 w-5 text-emerald-500" />
            Digital House Details
          </h2>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">House ID</label>
            <Input
              value={house?.id || (house as any)?.house_id || "HSE-87B7EB2B"}
              disabled
              className="mt-1 font-mono text-sm bg-muted font-bold text-emerald-500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">House Name</label>
            <Input
              value={hName}
              onChange={(e) => setHName(e.target.value)}
              placeholder="e.g. Rama Nilaya"
              className="mt-1"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-muted-foreground uppercase">Location</label>
            <Input
              value={hLoc}
              onChange={(e) => setHLoc(e.target.value)}
              placeholder="e.g. Bengaluru, Karnataka, India"
              className="mt-1"
            />
          </div>

          <Button onClick={handleSaveHouse} disabled={savingHouse || !token} variant="secondary" className="mt-2 gap-2">
            <Save className="h-4 w-4" />
            {savingHouse ? "Saving House..." : "Save House Details"}
          </Button>
        </div>
      </div>

      <div className="panel p-6 flex flex-col gap-6 max-w-4xl mt-6">
        <h2 className="font-semibold text-lg border-b pb-2">Optimization & Backend Bounds</h2>

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
            placeholder="https://energy-project1.onrender.com"
            className="mt-1 font-mono text-sm"
          />
        </div>
      </div>
    </>
  );
}
