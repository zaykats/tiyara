import { LayoutDashboard, MessageSquare, Settings, Upload, LogOut, Plane } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
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
  const collapsed = state === "collapsed";

  const mainItems = [
    { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
    { title: "My Sessions", url: "/dashboard", icon: MessageSquare },
    { title: "Settings", url: "/dashboard", icon: Settings },
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
                <p className="font-mono-tech text-[8px] text-muted-foreground/50 tracking-[0.15em]">MAINTENANCE</p>
              </div>
            )}
          </div>
        </div>

        <SidebarGroup>
          <SidebarGroupLabel className="font-mono-tech text-[10px] tracking-[0.15em] text-muted-foreground/40 px-4 mb-1">
            {!collapsed && "NAVIGATION"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-sidebar-accent transition-all min-h-[44px] mx-1"
                      activeClassName="bg-sidebar-accent text-foreground border-l-2 border-primary"
                    >
                      <item.icon className="h-4 w-4 shrink-0" />
                      {!collapsed && <span>{item.title}</span>}
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
                      {!collapsed && <span>Upload AMM</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              )}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="p-2 border-t border-sidebar-border">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-muted-foreground hover:text-destructive transition-colors w-full min-h-[44px] mx-1"
        >
          <LogOut className="h-4 w-4 shrink-0" />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </SidebarFooter>
    </Sidebar>
  );
}
