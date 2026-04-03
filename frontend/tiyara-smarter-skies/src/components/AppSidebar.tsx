import { LayoutDashboard, MessageSquare, Settings, Upload, LogOut, Plane, Globe } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
import { useLang } from "@/contexts/LanguageContext";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";

export function AppSidebar() {
  const { user, logout } = useAuth();
  const { state } = useSidebar();
  const { lang, setLang, t } = useLang();
  const collapsed = state === "collapsed";

  const mainItems = [
    { titleKey: "dashboard", url: "/dashboard", icon: LayoutDashboard },
    { titleKey: "my_sessions", url: "/dashboard", icon: MessageSquare },
    { titleKey: "settings", url: "/dashboard", icon: Settings },
  ];

  const showUpload = user?.role === "engineer" || user?.role === "supervisor";

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarContent className="py-2">
        {/* Brand */}
        <div className={`px-4 py-3 mb-2 ${collapsed ? 'flex justify-center' : ''}`}>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-primary flex items-center justify-center shrink-0 glow-primary">
              <span className="text-primary-foreground text-[10px] font-bold">T</span>
            </div>
            {!collapsed && (
              <div>
                <span className="font-bold text-sm text-foreground tracking-[-0.02em]">TIYARA</span>
                <p className="font-mono-tech text-[8px] text-muted-foreground/50 tracking-[0.15em]">{t("maintenance_label")}</p>
              </div>
            )}
          </div>
        </div>

        <SidebarGroup>
          <SidebarGroupLabel className="font-mono-tech text-[10px] tracking-[0.15em] text-muted-foreground/40 px-4 mb-1">
            {!collapsed && t("navigation")}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainItems.map((item) => (
                <SidebarMenuItem key={item.titleKey}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-all min-h-[44px] mx-1"
                      activeClassName="bg-sidebar-accent text-foreground border-l-2 border-primary"
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      {!collapsed && <span>{t(item.titleKey)}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
              {showUpload && (
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to="/upload-amm"
                      end
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-all min-h-[44px] mx-1"
                      activeClassName="bg-sidebar-accent text-foreground border-l-2 border-primary"
                    >
                      <Upload className="h-4 w-4 shrink-0" />
                      {!collapsed && <span>{t("upload_amm_nav")}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-2 border-t border-sidebar-border space-y-1">
        {/* Language toggle */}
        {!collapsed && (
          <div className="flex items-center gap-2 px-4 py-2">
            <Globe className="w-3.5 h-3.5 text-muted-foreground/40 shrink-0" />
            <span className="font-mono-tech text-[9px] text-muted-foreground/40 tracking-[0.15em] flex-1">{t("language")}</span>
            <div className="flex border border-border overflow-hidden">
              {(["en", "fr"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`px-2.5 py-1 text-[10px] font-mono-tech tracking-wider transition-all ${
                    lang === l
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}
        {collapsed && (
          <button
            onClick={() => setLang(lang === "en" ? "fr" : "en")}
            className="flex items-center justify-center w-full py-2 text-[10px] font-mono-tech text-muted-foreground/50 hover:text-foreground transition-colors"
            title={t("language")}
          >
            <Globe className="w-3.5 h-3.5" />
          </button>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-destructive transition-colors w-full min-h-[44px] mx-1"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>{t("sign_out")}</span>}
        </button>
      </SidebarFooter>
    </Sidebar>
  );
}
