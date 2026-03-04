import { useLocation, useNavigate } from "react-router-dom";
import { Shield, LayoutDashboard, User, SlidersHorizontal, Settings } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { usePrivacy, EXPOSURE_FEATURE_IDS, PROTECTION_FEATURE_IDS } from "@/context/PrivacyContext";
import { useAvatar } from "@/context/AvatarContext";
import { PrivacyAvatar } from "@/components/PrivacyAvatar";
import { useMemo } from "react";

const navItems = [
  { label: "Overview", path: "/", icon: LayoutDashboard },
  { label: "My Avatar", path: "/avatar", icon: User },
  { label: "Configuration", path: "/configuration", icon: SlidersHorizontal },
  { label: "Settings", path: "/settings", icon: Settings },
];

interface AppSidebarProps {
  onNavigate?: () => void;
}

export const AppSidebar = ({ onNavigate }: AppSidebarProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { features, connected } = usePrivacy();
  const { config } = useAvatar();

  const score = useMemo(() => {
    const exposuresActive = EXPOSURE_FEATURE_IDS.filter(
      id => features.find(f => f.id === id)?.active
    ).length;
    const protectionsActive = PROTECTION_FEATURE_IDS.filter(
      id => features.find(f => f.id === id)?.active
    ).length;
    const exposureScore =
      ((EXPOSURE_FEATURE_IDS.length - exposuresActive) / EXPOSURE_FEATURE_IDS.length) * 40;
    const protectionScore =
      (protectionsActive / PROTECTION_FEATURE_IDS.length) * 60;
    return Math.round(exposureScore + protectionScore);
  }, [features]);

  const scoreColor = score >= 80 ? "#10B981" : score >= 50 ? "#F59E0B" : "#EF4444";

  const handleNav = (path: string) => {
    navigate(path);
    onNavigate?.();
  };

  return (
    <aside className="w-[220px] bg-sidebar-nav shrink-0 flex flex-col text-sidebar-nav-foreground">
      {/* Logo */}
      <div className="px-5 pt-5 pb-4 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-primary/20 flex items-center justify-center">
          <Shield className="w-4 h-4 text-primary" />
        </div>
        <span className="font-bold text-[13px] tracking-tight text-sidebar-nav-foreground">PrivacyDeck</span>
      </div>

      {/* Avatar + score card */}
      <div className="px-3 pb-4">
        <button
          onClick={() => handleNav("/avatar")}
          className="w-full flex items-center gap-3 px-3 py-3 rounded-2xl hover:bg-sidebar-nav-muted/60 transition-all group border border-sidebar-nav-border/50"
        >
          <PrivacyAvatar size={34} />
          <div className="flex-1 min-w-0 text-left">
            <div className="text-[12px] font-semibold text-sidebar-nav-foreground truncate">
              {config.name || "PrivacyBot"}
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <div className="text-[10px] font-bold tabular-nums" style={{ color: scoreColor }}>
                {score}%
              </div>
              <div className="flex-1 h-[3px] rounded-full bg-sidebar-nav-muted overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: scoreColor }}
                  initial={false}
                  animate={{ width: `${score}%` }}
                  transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
                />
              </div>
            </div>
          </div>
        </button>
      </div>

      {/* Connection indicator */}
      <div className="px-5 mb-3 flex items-center gap-2">
        <div className={cn("w-[6px] h-[6px] rounded-full", connected ? "bg-success animate-pulse" : "bg-destructive/70")} />
        <span className="text-[10px] font-medium text-sidebar-nav-foreground/40 tracking-wide">
          {connected ? "Device connected" : "Not connected"}
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-0.5">
        {navItems.map(item => {
          const active = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => handleNav(item.path)}
              className={cn(
                "relative w-full flex items-center gap-2.5 px-3 py-[9px] rounded-xl text-[13px] transition-colors duration-150",
                active
                  ? "text-sidebar-nav-active font-semibold"
                  : "text-sidebar-nav-foreground/60 hover:bg-sidebar-nav-muted/40 hover:text-sidebar-nav-foreground/90",
              )}
            >
              {active && (
                <motion.div
                  layoutId="nav-active-bg"
                  className="absolute inset-0 bg-sidebar-nav-active/15 rounded-xl"
                  transition={{ type: "spring", bounce: 0.15, duration: 0.4 }}
                />
              )}
              <item.icon className={cn("relative z-10 w-[16px] h-[16px] shrink-0", active && "text-sidebar-nav-active")} />
              <span className="relative z-10">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-sidebar-nav-border/30">
        <p className="text-[9px] font-medium text-sidebar-nav-foreground/20 text-center tracking-widest uppercase">
          PrivacyDeck v1.0
        </p>
      </div>
    </aside>
  );
};
