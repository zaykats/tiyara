import { useAuth } from "@/contexts/AuthContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import { User, Building2, Mail, Shield } from "lucide-react";

const ROLE_COLORS: Record<string, string> = {
  technician: "text-warning border-warning/30 bg-warning/5",
  engineer: "text-secondary border-secondary/30 bg-secondary/5",
  supervisor: "text-success border-success/30 bg-success/5",
};

const ROLE_PERMISSIONS: Record<string, string[]> = {
  technician: ["Create sessions", "Chat with AI", "Upload maintenance Excel"],
  engineer: ["Create sessions", "Chat with AI", "Upload maintenance Excel", "Ingest AMM documents"],
  supervisor: ["Create sessions", "Chat with AI", "Upload maintenance Excel", "Ingest AMM documents", "Full access"],
};

export default function SettingsPage() {
  const { user } = useAuth();
  const roleColor = ROLE_COLORS[user?.role || "technician"];
  const permissions = ROLE_PERMISSIONS[user?.role || "technician"] || [];

  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 max-w-2xl animate-fade-in">
        <h1 className="text-2xl font-bold text-foreground mb-1">Settings</h1>
        <p className="text-sm text-muted-foreground mb-8">Your account information</p>

        {/* Account card */}
        <div className="surface-panel p-6 space-y-5 mb-6">
          <p className="font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em]">ACCOUNT</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-muted flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4 text-muted-foreground/50" />
              </div>
              <div>
                <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">FULL NAME</p>
                <p className="text-sm text-foreground font-medium">{user?.full_name}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-muted flex items-center justify-center shrink-0 mt-0.5">
                <Mail className="w-4 h-4 text-muted-foreground/50" />
              </div>
              <div>
                <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">EMAIL</p>
                <p className="text-sm text-foreground">{user?.email}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-muted flex items-center justify-center shrink-0 mt-0.5">
                <Building2 className="w-4 h-4 text-muted-foreground/50" />
              </div>
              <div>
                <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">COMPANY</p>
                <p className="text-sm text-foreground">{user?.company}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-muted flex items-center justify-center shrink-0 mt-0.5">
                <Shield className="w-4 h-4 text-muted-foreground/50" />
              </div>
              <div>
                <p className="text-[10px] font-mono-tech text-muted-foreground/50 tracking-wider mb-0.5">ROLE</p>
                <span className={`inline-flex items-center px-2.5 py-1 text-[11px] font-mono-tech tracking-wider border ${roleColor}`}>
                  {user?.role?.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Permissions */}
        <div className="surface-panel p-6">
          <p className="font-mono-tech text-[10px] text-muted-foreground/40 tracking-[0.15em] mb-4">PERMISSIONS</p>
          <div className="space-y-2">
            {permissions.map((p) => (
              <div key={p} className="flex items-center gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-success" />
                <span className="text-sm text-muted-foreground">{p}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
