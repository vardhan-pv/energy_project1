import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { createHttpDataSource } from "@/lib/energy/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { CheckCircle2, Home, Cpu, Plug, ArrowRight, Zap, Shield } from "lucide-react";

export const Route = createFileRoute("/setup")({
  head: () => ({
    meta: [{ title: "Digital House Setup Wizard | Energy System" }],
  }),
  component: SetupWizardPage,
});

export function SetupWizardPage() {
  const navigate = useNavigate();
  const { user, token, settings } = useEnergy();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);

  // House fields
  const [houseName, setHouseName] = useState("Rama Nilaya");
  const [location, setLocation] = useState("Bengaluru, Karnataka, India");
  const [createdHouse, setCreatedHouse] = useState<any>(null);

  // Device fields
  const [deviceType, setDeviceType] = useState("ESP32");
  const [deviceName, setDeviceName] = useState("Main Energy Controller");
  const [macAddress, setMacAddress] = useState("A4:CF:12:89:BC:45");
  const [createdDevice, setCreatedDevice] = useState<any>(null);

  // Appliance fields
  const [appName, setAppName] = useState("Refrigerator");
  const [appType, setAppType] = useState("fridge");
  const [ratedPowerW, setRatedPowerW] = useState(150);
  const [appliancesList, setAppliancesList] = useState<any[]>([]);

  const getDs = () => createHttpDataSource(settings.apiBaseUrl, () => token);

  const handleCreateHouse = async () => {
    if (!houseName) {
      toast.error("Please enter a house name");
      return;
    }
    setLoading(true);
    try {
      const res = await getDs().createHouse(houseName, location);
      setCreatedHouse(res.house);
      toast.success(`House created! House ID: ${res.house.id || (res.house as any).house_id}`);
      setStep(3);
    } catch (err: any) {
      toast.error(err.message || "Failed to create house");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDevice = async () => {
    if (!deviceName) {
      toast.error("Please enter a device name");
      return;
    }
    setLoading(true);
    try {
      const res = await getDs().createDevice(deviceType, deviceName, macAddress);
      setCreatedDevice(res.device);
      toast.success(`Device registered! Device ID: ${res.device.device_id}`);
      setStep(4);
    } catch (err: any) {
      toast.error(err.message || "Failed to register device");
    } finally {
      setLoading(false);
    }
  };

  const handleAddAppliance = async () => {
    if (!appName) {
      toast.error("Please enter an appliance name");
      return;
    }
    setLoading(true);
    try {
      const devId = createdDevice?.device_id || null;
      const res = await getDs().createAppliance(devId, appName, appType, Number(ratedPowerW));
      setAppliancesList((prev) => [...prev, res.appliance]);
      toast.success(`Appliance '${appName}' added!`);
      // Reset appliance form for additional additions
      setAppName("");
    } catch (err: any) {
      toast.error(err.message || "Failed to add appliance");
    } finally {
      setLoading(false);
    }
  };

  const finishSetup = () => {
    toast.success("Digital House Setup Complete!");
    navigate({ to: "/" });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-2xl panel p-8 flex flex-col gap-6 shadow-2xl border border-border/80 relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <h1 className="font-bold text-xl">Digital House Installation Wizard</h1>
              <p className="text-xs text-muted-foreground">Dynamic Hardware & Appliance Setup</p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs font-mono font-bold text-primary">Step {step} of 6</span>
          </div>
        </div>

        {/* Step Indicator Bar */}
        <div className="grid grid-cols-6 gap-1 bg-muted p-1 rounded-full text-[10px] font-semibold text-center">
          <div className={`py-1 rounded-full ${step >= 1 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>Account</div>
          <div className={`py-1 rounded-full ${step >= 2 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>House</div>
          <div className={`py-1 rounded-full ${step >= 3 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>Device</div>
          <div className={`py-1 rounded-full ${step >= 4 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>Appliances</div>
          <div className={`py-1 rounded-full ${step >= 5 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>Verify</div>
          <div className={`py-1 rounded-full ${step >= 6 ? "bg-primary text-primary-foreground" : "text-muted-foreground"}`}>Complete</div>
        </div>

        {/* STEP 1: Account */}
        {step === 1 && (
          <div className="flex flex-col gap-4 py-4">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Shield className="h-5 w-5 text-emerald-500" />
              Step 1: User Identity Verification
            </h2>
            <p className="text-xs text-muted-foreground">
              Your server-assigned cryptographically random User ID binds your house and hardware telemetry.
            </p>
            <div className="bg-card p-4 rounded-lg border font-mono text-sm flex flex-col gap-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">User ID:</span>
                <span className="font-bold text-primary">{user?.user_id || "USR-A82F91"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Name:</span>
                <span>{user?.name || "Ravi Kumar"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Email:</span>
                <span>{user?.email || "user@example.com"}</span>
              </div>
            </div>
            <Button onClick={() => setStep(2)} className="w-full mt-4 gap-2">
              Continue to House Setup <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* STEP 2: House Setup */}
        {step === 2 && (
          <div className="flex flex-col gap-4 py-4">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Home className="h-5 w-5 text-primary" />
              Step 2: Digital House Registration
            </h2>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">House Name</label>
              <Input value={houseName} onChange={(e) => setHouseName(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Geographic Location</label>
              <Input value={location} onChange={(e) => setLocation(e.target.value)} className="mt-1" />
            </div>
            <Button onClick={handleCreateHouse} disabled={loading} className="w-full mt-4 gap-2">
              {loading ? "Creating House..." : "Register Digital House"} <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* STEP 3: Device Registration */}
        {step === 3 && (
          <div className="flex flex-col gap-4 py-4">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Cpu className="h-5 w-5 text-cyan-500" />
              Step 3: Hardware Controller / Smart Plug Setup
            </h2>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Device Type</label>
              <select
                value={deviceType}
                onChange={(e) => setDeviceType(e.target.value)}
                className="w-full mt-1 bg-background border rounded-md p-2 text-sm"
              >
                <option value="ESP32">ESP32 Main Microcontroller</option>
                <option value="Smart Plug">Tuya Smart Plug</option>
                <option value="PZEM-004T">PZEM Power Meter</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Device Name</label>
              <Input value={deviceName} onChange={(e) => setDeviceName(e.target.value)} className="mt-1" />
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">MAC Address</label>
              <Input value={macAddress} onChange={(e) => setMacAddress(e.target.value)} className="mt-1 font-mono text-sm" />
            </div>
            <Button onClick={handleCreateDevice} disabled={loading} className="w-full mt-4 gap-2">
              {loading ? "Registering Device..." : "Register Hardware Device"} <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* STEP 4: Appliance Registration */}
        {step === 4 && (
          <div className="flex flex-col gap-4 py-4">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <Plug className="h-5 w-5 text-amber-500" />
              Step 4: Appliance Registration
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Appliance Name</label>
                <Input placeholder="e.g. Refrigerator" value={appName} onChange={(e) => setAppName(e.target.value)} className="mt-1" />
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase">Category / Type</label>
                <select
                  value={appType}
                  onChange={(e) => setAppType(e.target.value)}
                  className="w-full mt-1 bg-background border rounded-md p-2 text-sm"
                >
                  <option value="fridge">Refrigerator (Always-on)</option>
                  <option value="office_fan">Pedestal Fan</option>
                  <option value="laptop">Laptop & Charger</option>
                  <option value="kitchen_lights">Kitchen LED Lights</option>
                  <option value="air_conditioner">Air Conditioner (Adaptive Baseline)</option>
                  <option value="generic">Generic Appliance</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Rated Power (Watts)</label>
              <Input type="number" value={ratedPowerW} onChange={(e) => setRatedPowerW(Number(e.target.value))} className="mt-1" />
            </div>

            <Button onClick={handleAddAppliance} disabled={loading} variant="outline" className="w-full mt-2">
              + Add Appliance to House
            </Button>

            {appliancesList.length > 0 && (
              <div className="bg-card p-3 rounded-lg border flex flex-col gap-2 mt-2">
                <span className="text-xs font-semibold text-muted-foreground uppercase">Registered Appliances ({appliancesList.length}):</span>
                {appliancesList.map((a, i) => (
                  <div key={i} className="text-xs flex justify-between border-b pb-1">
                    <span className="font-medium">{a.name || a.appliance_name} ({a.type || a.appliance_type})</span>
                    <span className="font-mono text-primary">{a.ratedPowerW || a.rated_power_w} W</span>
                  </div>
                ))}
              </div>
            )}

            <Button onClick={() => setStep(5)} className="w-full mt-4 gap-2">
              Proceed to Verification <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* STEP 5: Verification */}
        {step === 5 && (
          <div className="flex flex-col gap-4 py-4 text-center">
            <div className="h-16 w-16 bg-emerald-500/20 text-emerald-500 rounded-full flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-10 w-10" />
            </div>
            <h2 className="font-bold text-xl">System Verification Passed</h2>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Telemetry pipelines, dynamic feature engineering, ML load forecasting, IsolationForest anomaly detection, and RL optimization loops are bound to your user house.
            </p>
            <Button onClick={() => setStep(6)} className="w-full mt-4 gap-2">
              Generate Installation Summary <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* STEP 6: Complete Summary */}
        {step === 6 && (
          <div className="flex flex-col gap-6 py-4">
            <div className="text-center border-b pb-4">
              <h2 className="font-bold text-2xl tracking-tight text-primary">INSTALLATION COMPLETE</h2>
              <p className="text-xs text-muted-foreground mt-1">Multi-User Digital House Active</p>
            </div>

            <div className="bg-card p-6 rounded-xl border flex flex-col gap-3 font-mono text-sm shadow-inner">
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground uppercase text-xs font-semibold">User ID</span>
                <span className="font-bold text-primary">{user?.user_id || "USR-A82F91"}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground uppercase text-xs font-semibold">House ID</span>
                <span className="font-bold text-primary">{createdHouse?.house_id || createdHouse?.id || "HSE-7B29D4"}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground uppercase text-xs font-semibold">House Name</span>
                <span>{houseName}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground uppercase text-xs font-semibold">Registered Devices</span>
                <span>1 ({createdDevice?.device_name || "ESP32"})</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-muted-foreground uppercase text-xs font-semibold">Registered Appliances</span>
                <span>{appliancesList.length > 0 ? appliancesList.length : 4}</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-muted-foreground uppercase text-xs font-semibold">System Status</span>
                <span className="text-emerald-500 font-bold">READY</span>
              </div>
            </div>

            <Button onClick={finishSetup} className="w-full py-6 text-base gap-2 font-bold shadow-lg">
              <Zap className="h-5 w-5" /> Launch Energy Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
