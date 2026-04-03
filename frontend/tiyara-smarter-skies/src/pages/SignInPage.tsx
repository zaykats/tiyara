import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch, setTokens, setUser } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useLang } from "@/contexts/LanguageContext";
import { useToast } from "@/hooks/use-toast";
import { Eye, EyeOff, ArrowLeft } from "lucide-react";

export default function SignInPage() {
  const navigate = useNavigate();
  const { setUserState } = useAuth();
  const { toast } = useToast();
  const { t } = useLang();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch("/auth/signin", { method: "POST", body: JSON.stringify(form) });
      if (res.status === 200) {
        const data = await res.json();
        setTokens(data.access_token, data.refresh_token);
        setUser(data.user);
        setUserState(data.user);
        navigate("/dashboard");
      } else if (res.status === 401) {
        setError(t("invalid_credentials"));
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
          <h2 className="text-2xl font-bold text-foreground leading-tight mb-3">{t("precision_diag")}</h2>
          <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">{t("precision_sub")}</p>
        </div>
        <div className="relative z-10 font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em]">
          {t("secure")}
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 flex items-center justify-center px-6">
        <motion.div
          className="w-full max-w-sm"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="lg:hidden mb-8">
            <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6">
              <ArrowLeft className="w-4 h-4" /> {t("back")}
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-foreground mb-1">{t("welcome_back")}</h1>
            <p className="text-sm text-muted-foreground">{t("sign_in_account")}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <motion.div
                className="border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
              >
                {error}
              </motion.div>
            )}
            <div>
              <label className="label-tech">{t("email")}</label>
              <input className="input-field" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            </div>
            <div>
              <label className="label-tech">{t("password")}</label>
              <div className="relative">
                <input className="input-field pr-12" type={showPw ? "text" : "password"} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1">
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-aerospace w-full text-sm flex items-center justify-center gap-2">
              {loading ? <span className="animate-spin w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full" /> : t("sign_in")}
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground mt-8">
            {t("no_account")}{" "}
            <Link to="/signup" className="text-foreground hover:text-primary transition-colors font-medium">{t("sign_up")}</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
