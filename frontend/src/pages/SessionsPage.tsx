import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { DashboardLayout } from "@/components/DashboardLayout";
import { SkeletonCard } from "@/components/SkeletonCard";
import { Plus, ArrowUpRight, Plane } from "lucide-react";

interface Session {
  id: string;
  engine_type: string;
  problem_description: string;
  status: string;
  created_at: string;
  created_by?: string;
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

export default function SessionsPage() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "active" | "resolved">("all");

  useEffect(() => {
    apiFetch("/sessions").then(async (res) => {
      if (res.ok) setSessions(await res.json());
    }).finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? sessions : sessions.filter((s) => s.status === filter);

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-4xl animate-fade-in">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-foreground mb-1">Sessions</h1>
            <p className="text-sm text-muted-foreground">All your maintenance diagnosis sessions</p>
          </div>
          <motion.button
            onClick={() => navigate("/new-diagnosis")}
            className="btn-aerospace text-sm flex items-center gap-2"
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
          >
            <Plus className="w-4 h-4" /> New Diagnosis
          </motion.button>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 mb-6">
          {(["all", "active", "resolved"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 text-[11px] font-mono-tech tracking-wider transition-colors border ${
                filter === f
                  ? "border-primary/40 text-foreground bg-primary/5"
                  : "border-border text-muted-foreground/50 hover:text-foreground"
              }`}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-3">{[1,2,3].map((i) => <SkeletonCard key={i} />)}</div>
        ) : filtered.length === 0 ? (
          <div className="surface-panel p-12 text-center">
            <Plane className="w-10 h-10 text-muted-foreground/20 mx-auto mb-4" />
            <p className="text-muted-foreground mb-1">No sessions found</p>
            <button onClick={() => navigate("/new-diagnosis")} className="btn-aerospace text-sm inline-flex items-center gap-2 mt-4">
              <Plus className="w-4 h-4" /> Start Diagnosis
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map((session, i) => (
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
                    {session.created_by && (
                      <p className="text-[10px] font-mono-tech text-muted-foreground/40 mt-1">BY {session.created_by.toUpperCase()}</p>
                    )}
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
    </DashboardLayout>
  );
}
