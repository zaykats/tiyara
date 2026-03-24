import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { Navigate } from "react-router-dom";
import { ArrowRight, Shield, Cpu, Wrench, Plane, Radio, ChevronRight } from "lucide-react";

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
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* ── Full-screen video background ── */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute inset-0 w-full h-full object-cover"
        src="/hero-bg.mp4"
      />
      {/* Dark overlay to keep text legible */}
      <div className="absolute inset-0 bg-black/65" />
      {/* Preserve the original ambient tint on top of the video */}
      <div className="absolute inset-0" style={{
        background: 'radial-gradient(ellipse at 30% 20%, hsl(338 100% 18% / 0.12) 0%, transparent 55%), radial-gradient(ellipse at 70% 80%, hsl(185 100% 50% / 0.05) 0%, transparent 55%)',
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
          <Link to="/signin" className="btn-ghost text-sm flex items-center px-5">
            Sign In
          </Link>
          <Link to="/signup" className="btn-aerospace text-sm flex items-center gap-1.5">
            Get Started <ChevronRight className="w-3.5 h-3.5" />
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
            AVIATION MAINTENANCE AI PLATFORM
          </span>
        </motion.div>

        <motion.h1
          variants={fadeUp}
          className="text-4xl md:text-6xl lg:text-[4.5rem] font-bold text-foreground leading-[1.05] text-balance max-w-4xl"
        >
          Smarter Maintenance.
          <br />
          <span className="relative">
            <span className="text-primary">Safer Skies.</span>
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
          AI-powered diagnostics for aircraft technicians. Analyze fault patterns,
          consult maintenance manuals, and resolve issues faster.
        </motion.p>

        <motion.div
          variants={fadeUp}
          className="flex flex-col sm:flex-row gap-3 mt-10"
        >
          <Link to="/signup" className="btn-aerospace text-[15px] flex items-center gap-2.5 justify-center px-8">
            Start Diagnosis <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/signin" className="btn-ghost text-[15px] flex items-center gap-2 justify-center px-8">
            <Plane className="w-4 h-4" /> Sign In
          </Link>
        </motion.div>

        {/* Stats strip */}
        <motion.div
          variants={fadeUp}
          className="flex items-center gap-8 md:gap-12 mt-16 font-mono-tech text-xs"
        >
          {[
            { value: "500+", label: "ENGINES SUPPORTED" },
            { value: "99.7%", label: "UPTIME" },
            { value: "24/7", label: "AI AVAILABLE" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-lg font-bold text-foreground tabular-nums">{s.value}</p>
              <p className="text-muted-foreground/60 tracking-[0.12em] mt-0.5">{s.label}</p>
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
          <p className="font-mono-tech text-[10px] text-muted-foreground/60 tracking-[0.2em] mb-6 text-center">CAPABILITIES</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                icon: Cpu,
                title: "AI Diagnostics",
                desc: "Pattern analysis powered by maintenance history and AMM documents. Identifies recurring faults and risk patterns.",
                accent: "primary",
              },
              {
                icon: Shield,
                title: "Guided Procedures",
                desc: "Step-by-step maintenance instructions with AMM references, safety warnings, and compliance checks.",
                accent: "accent",
              },
              {
                icon: Wrench,
                title: "Fleet Coverage",
                desc: "Full support for CFM56, LEAP, V2500, PW1100G, Trent, GE90, GEnx and more engine families.",
                accent: "secondary",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="group surface-panel p-6 relative overflow-hidden"
              >
                {/* Top accent line */}
                <div className={`absolute top-0 left-0 right-0 h-[1px] bg-${f.accent}/30 group-hover:bg-${f.accent}/60 transition-colors`} />
                <div className={`w-10 h-10 flex items-center justify-center border border-border mb-4 group-hover:border-${f.accent}/30 transition-colors`}>
                  <f.icon className="w-5 h-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                </div>
                <h3 className="font-semibold text-foreground mb-2 text-sm">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
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
            <span className="font-mono-tech text-[10px] text-muted-foreground/50 tracking-widest">ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
