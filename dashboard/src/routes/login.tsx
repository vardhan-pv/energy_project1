import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEnergy } from "@/lib/energy/store";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { LogIn, UserPlus, ShieldCheck, Zap } from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [{ title: "User Login & Registration | Energy Intelligence" }],
  }),
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const { loginUser, registerUser, settings } = useEnergy();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [loading, setLoading] = useState(false);

  // Login state
  const [loginId, setLoginId] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register state
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginId || !loginPassword) {
      toast.error("Please enter User ID or Email and password");
      return;
    }
    setLoading(true);
    try {
      const u = await loginUser(loginId, loginPassword);
      toast.success(`Welcome back, ${u.name}! (${u.user_id})`);
      navigate({ to: "/setup" });
    } catch (err: any) {
      toast.error(err.message || "Login failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName || !regEmail || !regPassword) {
      toast.error("Please fill in all registration fields");
      return;
    }
    setLoading(true);
    try {
      const u = await registerUser(regName, regEmail, regPassword);
      toast.success(`Account created! Your User ID is ${u.user_id}`);
      navigate({ to: "/setup" });
    } catch (err: any) {
      toast.error(err.message || "Registration failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background relative overflow-hidden">
      {/* Subtle glow background */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md panel p-8 flex flex-col gap-6 relative z-10 shadow-2xl border border-border/80">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
            <Zap className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-bold text-xl tracking-tight">Energy Intelligence</h1>
            <p className="text-xs text-muted-foreground">Multi-User Energy Control System</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="grid grid-cols-2 bg-muted p-1 rounded-lg text-xs font-semibold">
          <button
            onClick={() => setMode("login")}
            className={`py-2 rounded-md transition-all ${
              mode === "login" ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode("register")}
            className={`py-2 rounded-md transition-all ${
              mode === "register" ? "bg-background shadow text-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Create Account
          </button>
        </div>

        {mode === "login" ? (
          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">User ID or Email</label>
              <Input
                placeholder="e.g. USR-A82F91 or user@example.com"
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                className="mt-1 font-mono text-sm"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Password</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                className="mt-1"
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full mt-2 gap-2">
              <LogIn className="h-4 w-4" />
              {loading ? "Authenticating..." : "Sign In to Dashboard"}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="flex flex-col gap-4">
            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Full Name</label>
              <Input
                placeholder="e.g. Ravi Kumar"
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
              <Input
                type="email"
                placeholder="ravi@example.com"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-muted-foreground uppercase">Create Password</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                className="mt-1"
              />
            </div>

            <Button type="submit" disabled={loading} className="w-full mt-2 gap-2">
              <UserPlus className="h-4 w-4" />
              {loading ? "Generating User ID..." : "Register & Begin Installation"}
            </Button>
          </form>
        )}

        <div className="border-t pt-4 text-center">
          <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
            JWT Encrypted • Server-Assigned Random User IDs
          </p>
        </div>
      </div>
    </div>
  );
}
