import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [show, setShow] = useState(true);
  const [phase, setPhase] = useState<"runway" | "takeoff">("runway");

  useEffect(() => {
    const t1 = setTimeout(() => setPhase("takeoff"), 400);
    const t2 = setTimeout(() => setShow(false), 1600);
    const t3 = setTimeout(onComplete, 2000);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [onComplete]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-[9999] bg-background flex flex-col items-center justify-center overflow-hidden"
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4, ease: [0.2, 0, 0, 1] }}
        >
          {/* Radial gradient background */}
          <div className="absolute inset-0" style={{
            background: 'radial-gradient(ellipse at 50% 60%, hsl(338 100% 18% / 0.08) 0%, transparent 60%)',
          }} />

          {/* Grid overlay */}
          <div className="absolute inset-0 opacity-[0.03]" style={{
            backgroundImage: `linear-gradient(hsl(var(--secondary)) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--secondary)) 1px, transparent 1px)`,
            backgroundSize: '40px 40px',
          }} />

          {/* Runway line */}
          <div className="absolute w-full" style={{ top: '58%' }}>
            <motion.div
              className="h-[1px] mx-auto"
              style={{ background: 'linear-gradient(90deg, transparent, hsl(var(--border)), transparent)' }}
              initial={{ width: 0 }}
              animate={{ width: '80%' }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
            {/* Runway dashes */}
            <div className="flex justify-center gap-6 mt-2">
              {Array.from({ length: 16 }).map((_, i) => (
                <motion.div
                  key={i}
                  className="w-4 h-[1px] bg-secondary/20"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 + i * 0.02 }}
                />
              ))}
            </div>
          </div>

          {/* Plane */}
          <motion.div
            className="absolute text-3xl"
            style={{ top: 'calc(58% - 20px)' }}
            initial={{ left: "15%", rotate: 0, scale: 1 }}
            animate={phase === "takeoff" ? {
              left: "115%",
              rotate: -20,
              y: -120,
              scale: 0.7,
            } : { left: "15%", rotate: 0 }}
            transition={{
              duration: 1.1,
              ease: [0.45, 0, 0.15, 1],
            }}
          >
            ✈️
          </motion.div>

          {/* Brand */}
          <motion.div
            className="relative z-10 text-center"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="flex items-center justify-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary flex items-center justify-center glow-primary">
                <span className="text-primary-foreground text-sm font-bold">T</span>
              </div>
              <h1 className="text-3xl font-bold tracking-[-0.03em] text-foreground">TIYARA</h1>
            </div>
            <motion.div
              className="flex items-center justify-center gap-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <p className="font-mono-tech text-[10px] text-muted-foreground tracking-[0.25em]">SYSTEMS ONLINE</p>
            </motion.div>
          </motion.div>

          {/* Bottom system info */}
          <motion.div
            className="absolute bottom-8 flex items-center gap-6 font-mono-tech text-[10px] text-muted-foreground/50 tracking-widest"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <span>v2.4.1</span>
            <span>•</span>
            <span>AEROSPACE MAINTENANCE</span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
