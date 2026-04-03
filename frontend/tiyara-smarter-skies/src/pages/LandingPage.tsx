import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { useLang } from "@/contexts/LanguageContext";
import { Navigate } from "react-router-dom";
import { ArrowRight, Shield, Cpu, Wrench, Plane, Radio, ChevronRight, Globe } from "lucide-react";

function TurbineGraphic() {
  return (
    <div className="absolute right-[-10%] top-1/2 -translate-y-1/2 opacity-[0.04] pointer-events-none select-none hidden lg:block">
      <svg width="700" height="700" viewBox="0 0 700 700" className="animate-spin-slow">
        <circle cx="350" cy="350" r="340" stroke="currentColor" strokeWidth="0.5" fill="none" />
        <circle cx="350" cy="350" r="260" stroke="currentColor" strokeWidth="0.5" fill="none" />
        <circle cx="350" cy="350" r="180" stroke="currentColor" strokeWidth="0.5" fill="none" />
        <circle cx="350" cy="350" r="100" stroke="currentColor" strokeWidth="0.8" fill="none" />
        <circle cx="350" cy="350" r="30" stroke="currentColor" strokeWidth="1" fill="currentColor" fillOpacity="0.1" />
        {Array.from({ length: 24 }).map((_, i) => {
          const angle = (i * 15) * Math.PI / 180;
          const x1 = 350 + 35 * Math.cos(angle);
          const y1 = 350 + 35 * Math.sin(angle);
          const x2 = 350 + 330 * Math.cos(angle);
          const y2 = 350 + 330 * Math.sin(angle);
          return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="currentColor" strokeWidth="0.3" />;
        })}
      </svg>
    </div>
  );
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.2, 0, 0, 1] } },
};

export default function LandingPage() {
  const { isAuthenticated } = useAuth();
  const { lang, setLang, t } = useLang();
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <div className="absolute inset-0" style={{
        background: 'radial-gradient(ellipse at 30% 20%, hsl(338 100% 18% / 0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 80%, hsl(185 100% 50% / 0.03) 0%, transparent 50%)',
      }} />
      <div className="absolute inset-0 opacity-[0.025]" style={{
        backgroundImage: `linear-gradient(hsl(var(--secondary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--secondary)) 1px, transparent 1px)`,
        backgroundSize: '80px 80px',
      }} />
      <div className="absolute inset-0 scanline-overlay" />
      <TurbineGraphic />

      {/* Nav */}
      <motion.nav
        className="relative z-10 flex items-center justify-between px-6 md:px-12 lg:px-16 py-5"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 bg-primary flex items-center justify-center glow-primary">
            <span className="text-primary-foreground text-xs font-bold">T</span>
          </div>
          <span className="font-bold text-lg tracking-[-0.02em] text-foreground">TIYARA</span>
          <span className="font-mono-tech text-[9px] text-muted-foreground/50 tracking-widest ml-1 hidden sm:inline">AEROSPACE</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Language toggle */}
          <div className="flex border border-border overflow-hidden mr-1">
            {(["en", "fr"] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLang(l)}
                className={`px-2.5 py-1.5 text-[10px] font-mono-tech tracking-wider transition-all ${
                  lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {l.toUpperCase()}
              </button>
            ))}
          </div>
          <Link to="/signin" className="btn-ghost text-sm flex items-center px-5">
            {t("sign_in")}
          </Link>
          <Link to="/signup" className="btn-aerospace text-sm flex items-center gap-1.5">
            {t("get_started")} <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </motion.nav>

      {/* Hero */}
      <motion.section
        className="relative z-10 flex flex-col items-center justify-center text-center px-6 pt-16 md:pt-28 lg:pt-32 pb-16"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        <motion.div variants={fadeUp} className="mb-5">
          <span className="inline-flex items-center gap-2 px-3 py-1.5 border border-border text-[11px] font-mono-tech text-muted-foreground tracking-[0.15em]">
            <Radio className="w-3 h-3 text-primary" />
            {t("ai_platform")}
          </span>
        </motion.div>

        <motion.h1
          variants={fadeUp}
          className="text-4xl md:text-6xl lg:text-[4.5rem] font-bold text-foreground leading-[1.05] text-balance max-w-4xl"
        >
          {t("tagline1")}
          <br />
          <span className="relative">
            <span className="text-primary">{t("tagline2")}</span>
            <motion.span
              className="absolute -bottom-2 left-0 h-[2px] bg-primary/40"
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ delay: 0.8, duration: 0.6 }}
            />
          </span>
        </motion.h1>

        <motion.p
          variants={fadeUp}
          className="mt-6 text-base md:text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed"
        >
          {t("tagline_sub")}
        </motion.p>

        <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3 mt-10">
          <Link to="/signup" className="btn-aerospace text-[15px] flex items-center gap-2.5 justify-center px-8">
            {t("start_diagnosis")} <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/signin" className="btn-ghost text-[15px] flex items-center gap-2 justify-center px-8">
            <Plane className="w-4 h-4" /> {t("sign_in")}
          </Link>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          variants={fadeUp}
          className="flex items-center gap-8 md:gap-12 mt-16 font-mono-tech text-xs"
        >
          {[
            { value: "500+", labelKey: "engines_supported" },
            { value: "99.7%", labelKey: "uptime" },
            { value: "24/7", labelKey: "ai_available" },
          ].map((s) => (
            <div key={s.labelKey} className="text-center">
              <p className="text-lg font-bold text-foreground tabular-nums">{s.value}</p>
              <p className="text-muted-foreground/60 tracking-[0.12em] mt-0.5">{t(s.labelKey)}</p>
            </div>
          ))}
        </motion.div>
      </motion.section>

      {/* Features */}
      <motion.section
        className="relative z-10 px-6 md:px-12 lg:px-16 pb-24"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.5 }}
      >
        <div className="max-w-5xl mx-auto">
          <p className="font-mono-tech text-[10px] text-muted-foreground/60 tracking-[0.2em] mb-6 text-center">{t("capabilities")}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { icon: Cpu, titleKey: "cap1_title", descKey: "cap1_desc", accent: "primary" },
              { icon: Shield, titleKey: "cap2_title", descKey: "cap2_desc", accent: "accent" },
              { icon: Wrench, titleKey: "cap3_title", descKey: "cap3_desc", accent: "secondary" },
            ].map((f) => (
              <div key={f.titleKey} className="group surface-panel p-6 relative overflow-hidden">
                <div className={`absolute top-0 left-0 right-0 h-[1px] bg-${f.accent}/30 group-hover:bg-${f.accent}/60 transition-colors`} />
                <div className={`w-10 h-10 flex items-center justify-center border border-border mb-4 group-hover:border-${f.accent}/30 transition-colors`}>
                  <f.icon className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <h3 className="font-semibold text-foreground mb-2 text-sm">{t(f.titleKey)}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{t(f.descKey)}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border py-6 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-primary/80 flex items-center justify-center">
              <span className="text-primary-foreground text-[8px] font-bold">T</span>
            </div>
            <span className="font-mono-tech text-[10px] text-muted-foreground/50 tracking-[0.15em]">
              TIYARA AEROSPACE © {new Date().getFullYear()}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="status-dot status-dot-resolved" />
            <span className="font-mono-tech text-[10px] text-muted-foreground/50 tracking-widest">{t("all_systems")}</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
