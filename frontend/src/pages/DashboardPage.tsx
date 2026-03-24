import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { SkeletonCard } from "@/components/SkeletonCard";
import { Plus, Activity, CheckCircle, Clock, ArrowUpRight, Plane } from "lucide-react";

interface Session {
  id: string;
  engine_type: string;
  problem_description: string;
  status: string;
  created_at: string;
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { dot: string; text: string; bg: string }> = {
    active: { dot: "status-dot-active", text: "text-warning", bg: "bg-warning/8 border-warning/20" },
    resolved: { dot: "status-dot-resolved", text: "text-success", bg: "bg-success/8 border-success/20" },
    closed: { dot: "bg-secondary", text: "text-secondary", bg: "bg-secondary/8 border-secondary/20" },
  };
  const c = config[status] || config.closed;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-mono-tech tracking-widest border ${c.bg} ${c.text}`}>
      <span className={`status-dot ${c.dot}`} />
      {status.toUpperCase()}
    </span>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch("/sessions").then(async (res) => {
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    }).finally(() => setLoading(false));
  }, []);

  const total = sessions.length;
  const resolved = sessions.filter((s) => s.status === "resolved").length;
  const active = sessions.filter((s) => s.status === "active").length;

  const stats = [
    { label: "TOTAL", value: total, icon: Activity, color: "text-foreground" },
    { label: "RESOLVED", value: resolved, icon: CheckCircle, color: "text-success" },
    { label: "ACTIVE", value: active, icon: Clock, color: "text-warning" },
  ];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-6xl animate-fade-in">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground leading-tight">
              {getGreeting()}, {user?.full_name?.split(" ")[0]}
            </h1>
            <p className="text-xs font-mono-tech text-muted-foreground/60 tracking-[0.15em] mt-1">
              {user?.role?.toUpperCase()} • {user?.company}
            </p>
          </div>
          <motion.button
            onClick={() => navigate("/new-diagnosis")}
            className="btn-aerospace text-sm flex items-center gap-2"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Plus className="w-4 h-4" /> New Diagnosis
          </motion.button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              className="surface-panel p-4 md:p-5"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
            >
              <div className="flex items-center justify-between mb-3">
                <s.icon className={`w-4 h-4 ${s.color} opacity-60`} />
                <span className="font-mono-tech text-[9px] text-muted-foreground/40 tracking-[0.15em]">{s.label}</span>
              </div>
              <p className={`text-3xl font-bold ${s.color} tabular-nums`}>{s.value}</p>
            </motion.div>
          ))}
        </div>

        {/* Sessions */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-mono-tech text-[10px] text-muted-foreground/60 tracking-[0.15em]">RECENT SESSIONS</h2>
            <span className="font-mono-tech text-[10px] text-muted-foreground/40">{total} TOTAL</span>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map((i) => <SkeletonCard key={i} />)}
            </div>
          ) : sessions.length === 0 ? (
            <motion.div
              className="surface-panel p-12 text-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <Plane className="w-10 h-10 text-muted-foreground/20 mx-auto mb-4" />
              <p className="text-muted-foreground mb-1">No sessions yet</p>
              <p className="text-xs text-muted-foreground/60 mb-6">Start your first diagnosis to begin</p>
              <button onClick={() => navigate("/new-diagnosis")} className="btn-aerospace text-sm inline-flex items-center gap-2">
                <Plus className="w-4 h-4" /> Start Diagnosis
              </button>
            </motion.div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session, i) => (
                <motion.button
                  key={session.id}
                  onClick={() => navigate(`/chat/${session.id}`)}
                  className="surface-panel p-4 w-full text-left group"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2.5 mb-1.5">
                        <span className="font-mono-tech text-sm text-foreground">{session.engine_type}</span>
                        <StatusBadge status={session.status} />
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{session.problem_description}</p>
                    </div>
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="font-mono-tech text-[10px] text-muted-foreground/50 hidden sm:inline">
                        {new Date(session.created_at).toLocaleDateString()}
                      </span>
                      <ArrowUpRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-foreground transition-colors" />
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
