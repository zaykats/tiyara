import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch, setTokens, setUser } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff, ArrowLeft } from "lucide-react";

const roles = [
  { value: "technician", label: "Technician" },
  { value: "engineer", label: "Engineer" },
  { value: "supervisor", label: "Supervisor" },
];

function passwordStrength(p: string): { score: number; label: string; color: string } {
  let s = 0;
  if (p.length >= 8) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9]/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  if (p.length >= 12) s++;
  if (s <= 1) return { score: s, label: "Weak", color: "bg-destructive" };
  if (s <= 3) return { score: s, label: "Medium", color: "bg-warning" };
  return { score: s, label: "Strong", color: "bg-success" };
}

export default function SignUpPage() {
  const navigate = useNavigate();
  const { setUserState } = useAuth();
  const { toast } = useToast();
  const [form, setForm] = useState({ full_name: "", role: "technician", company: "", email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const strength = passwordStrength(form.password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);
    try {
      const res = await apiFetch("/auth/signup", {
        method: "POST",
        body: JSON.stringify(form),
      });
      if (res.status === 201) {
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        setUserState(data.user);
        toast({ title: "Welcome to Tiyara", description: "Account created successfully" });
        navigate("/dashboard");
      } else if (res.status === 409) {
        setErrors({ email: "Email already registered." });
      } else if (res.status === 422) {
        const data = await res.json();
        const fieldErrors: Record<string, string> = {};
        data.detail?.forEach((d: any) => {
          const field = d.loc?.[d.loc.length - 1];
          if (field) fieldErrors[field] = d.msg;
        });
        setErrors(fieldErrors);
      }
    } catch {} finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center overflow-hidden py-8">

      {/* ── Full-screen video background ── */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
        src="/auth.mp4"
      />

      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/60" />
      {/* Subtle vignette */}
      <div className="absolute inset-0" style={{
        background: 'radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.55) 100%)',
      }} />

      {/* Back link */}
      <Link
        to="/"
        className="absolute top-6 left-6 z-20 inline-flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      {/* ── Form card ── */}
      <motion.div
        className="relative z-10 w-full max-w-sm mx-4"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="bg-background/80 backdrop-blur-md border border-border p-8 rounded-xl shadow-2xl">
          {/* Brand */}
          <div className="flex items-center gap-2.5 mb-7">
            <div className="w-8 h-8 bg-primary flex items-center justify-center glow-primary">
              <span className="text-primary-foreground text-[10px] font-bold">T</span>
            </div>
            <span className="font-bold text-base text-foreground tracking-[-0.02em]">TIYARA</span>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground mb-1">Create account</h1>
            <p className="text-sm text-muted-foreground">Set up your Tiyara profile</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="label-tech">FULL NAME</label>
                <input className="input-field" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                {errors.full_name && <p className="text-destructive text-xs mt-1">{errors.full_name}</p>}
              </div>

              <div>
                <label className="label-tech">ROLE</label>
                <select className="input-field" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  {roles.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
                </select>
              </div>

              <div>
                <label className="label-tech">COMPANY</label>
                <input className="input-field" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} required />
                {errors.company && <p className="text-destructive text-xs mt-1">{errors.company}</p>}
              </div>
            </div>

            <div>
              <label className="label-tech">EMAIL</label>
              <input className="input-field" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              {errors.email && <p className="text-destructive text-xs mt-1">{errors.email}</p>}
            </div>

            <div>
              <label className="label-tech">PASSWORD</label>
              <div className="relative">
                <input className="input-field pr-12" type={showPw ? "text" : "password"} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {form.password && (
                <div className="mt-2.5">
                  <div className="flex gap-1">
                    {[1,2,3,4,5].map((i) => (
                      <div key={i} className={`h-[3px] flex-1 ${i <= strength.score ? strength.color : 'bg-border'} transition-colors duration-300`} />
                    ))}
                  </div>
                  <p className="text-[10px] font-mono-tech text-muted-foreground mt-1.5 tracking-widest">{strength.label.toUpperCase()}</p>
                </div>
              )}
              {errors.password && <p className="text-destructive text-xs mt-1">{errors.password}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-aerospace w-full text-sm flex items-center justify-center gap-2 mt-2">
              {loading ? <span className="animate-spin w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full" /> : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-6">
            Already have an account?{" "}
            <Link to="/signin" className="text-foreground hover:text-primary transition-colors font-medium">Sign In</Link>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
