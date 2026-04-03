import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { useAuth } from "@/contexts/AuthContext";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-14 flex items-center justify-between border-b border-border px-4 md:px-6 shrink-0">
            <div className="flex items-center gap-3">
              <SidebarTrigger className="text-muted-foreground hover:text-foreground transition-colors" />
              <div className="hidden sm:flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-success" style={{ boxShadow: '0 0 6px hsl(var(--success) / 0.5)' }} />
                <span className="font-mono-tech text-[10px] text-muted-foreground/60 tracking-[0.15em]">SYSTEM ACTIVE</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono-tech text-[10px] text-muted-foreground/50 tracking-[0.12em] hidden md:inline">
                {user?.company?.toUpperCase()}
              </span>
              <div className="w-7 h-7 bg-muted flex items-center justify-center text-xs font-bold text-foreground">
                {user?.full_name?.[0]?.toUpperCase() || "U"}
              </div>
            </div>
          </header>
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
