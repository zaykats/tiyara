import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch, setTokens, setUser } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useLang } from "@/contexts/LanguageContext";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff, ArrowLeft } from "lucide-react";

function passwordStrength(p: string): { score: number; labelKey: string; color: string } {
  let s = 0;
  if (p.length >= 8) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9]/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  if (p.length >= 12) s++;
  if (s <= 1) return { score: s, labelKey: "pw_weak", color: "bg-destructive" };
  if (s <= 3) return { score: s, labelKey: "pw_medium", color: "bg-warning" };
  return { score: s, labelKey: "pw_strong", color: "bg-success" };
}

export default function SignUpPage() {
  const navigate = useNavigate();
  const { setUserState } = useAuth();
  const { toast } = useToast();
  const { t } = useLang();
  const [form, setForm] = useState({ full_name: "", role: "technician", company: "", email: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const strength = passwordStrength(form.password);

  const roles = [
    { value: "technician", labelKey: "role_technician" },
    { value: "engineer", labelKey: "role_engineer" },
    { value: "supervisor", labelKey: "role_supervisor" },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoading(true);
    try {
      const res = await apiFetch("/auth/signup", { method: "POST", body: JSON.stringify(form) });
      if (res.status === 201) {
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        setUserState(data.user);
        toast({ title: t("welcome_toast"), description: t("account_created") });
        navigate("/dashboard");
      } else if (res.status === 409) {
        setErrors({ email: t("email_taken") });
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
    <div className="min-h-screen bg-background flex relative overflow-hidden">
      {/* Left decorative panel */}
      <div className="hidden lg:flex flex-col justify-between w-[45%] relative p-12" style={{
        background: 'linear-gradient(135deg, hsl(338 100% 18% / 0.08) 0%, hsl(240 7% 5%) 100%)',
      }}>
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(hsl(var(--secondary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--secondary)) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }} />
        <div className="relative z-10">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-4 h-4" /> {t("back")}
          </Link>
        </div>
        <div className="relative z-10">
          <div className="flex items-center gap-2.5 mb-6">
            <div className="w-9 h-9 bg-primary flex items-center justify-center glow-primary">
              <span className="text-primary-foreground text-xs font-bold">T</span>
            </div>
            <span className="font-bold text-lg text-foreground">TIYARA</span>
          </div>
          <h2 className="text-2xl font-bold text-foreground leading-tight mb-3">{t("join_next")}</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">{t("join_sub")}</p>
        </div>
        <div className="relative z-10 font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em]">
          {t("secure")}
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-8">
        <motion.div
          className="w-full max-w-sm"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="lg:hidden mb-6">
            <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
              <ArrowLeft className="w-4 h-4" /> {t("back")}
            </Link>
          </div>

          <div className="mb-6">
            <h1 className="text-2xl font-bold text-foreground mb-1">{t("create_account")}</h1>
            <p className="text-sm text-muted-foreground">{t("setup_profile")}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="label-tech">{t("full_name")}</label>
                <input className="input-field" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                {errors.full_name && <p className="text-destructive text-xs mt-1">{errors.full_name}</p>}
              </div>
              <div>
                <label className="label-tech">{t("role")}</label>
                <select className="input-field" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  {roles.map((r) => <option key={r.value} value={r.value}>{t(r.labelKey)}</option>)}
                </select>
              </div>
              <div>
                <label className="label-tech">{t("company")}</label>
                <input className="input-field" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} required />
                {errors.company && <p className="text-destructive text-xs mt-1">{errors.company}</p>}
              </div>
            </div>

            <div>
              <label className="label-tech">{t("email")}</label>
              <input className="input-field" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              {errors.email && <p className="text-destructive text-xs mt-1">{errors.email}</p>}
            </div>

            <div>
              <label className="label-tech">{t("password")}</label>
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
                  <p className="text-[10px] font-mono-tech text-muted-foreground mt-1.5 tracking-widest">{t(strength.labelKey)}</p>
                </div>
              )}
              {errors.password && <p className="text-destructive text-xs mt-1">{errors.password}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-aerospace w-full text-sm flex items-center justify-center gap-2 mt-2">
              {loading ? <span className="animate-spin w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full" /> : t("create_account_btn")}
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-8">
            {t("already_account")}{" "}
            <Link to="/signin" className="text-foreground hover:text-primary transition-colors font-medium">{t("sign_in")}</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
