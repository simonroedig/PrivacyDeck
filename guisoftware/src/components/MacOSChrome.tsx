import { Shield, Menu } from "lucide-react";
import { usePrivacy } from "@/context/PrivacyContext";

interface MacOSChromeProps {
  onMenuToggle?: () => void;
}

export const MacOSChrome = ({ onMenuToggle }: MacOSChromeProps) => {
  const { connected, connecting, connect, disconnect, lastSynced, daemonDemoMode } = usePrivacy();

  const formatSynced = () => {
    if (!lastSynced) return "";
    const diff = Math.floor((Date.now() - lastSynced.getTime()) / 1000);
    if (diff < 10) return "just now";
    if (diff < 60) return `${diff}s ago`;
    return `${Math.floor(diff / 60)}m ago`;
  };

  return (
    <div className="flex flex-col shrink-0">
    {daemonDemoMode && (
      <div className="flex items-center justify-center gap-2 px-4 py-1 bg-amber-500/15 border-b border-amber-500/30 text-amber-600 dark:text-amber-400 text-[11px] font-semibold tracking-wide select-none">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
        DEMO MODE — OS calls bypassed, simulating PrivacyDeck
      </div>
    )}
    <div className="h-12 glass border-b border-chrome-border flex items-center px-4 select-none">
      {/* Mobile menu button */}
      {onMenuToggle && (
        <button onClick={onMenuToggle} className="mr-3 p-1.5 rounded-lg hover:bg-muted transition-colors md:hidden">
          <Menu className="w-4 h-4 text-foreground" />
        </button>
      )}

      {/* Traffic lights */}
      <div className="flex items-center gap-[7px] mr-4">
        <div className="w-[11px] h-[11px] rounded-full bg-[#FF5F57] shadow-[inset_0_0_0_0.5px_rgba(0,0,0,0.12)]" />
        <div className="w-[11px] h-[11px] rounded-full bg-[#FEBC2E] shadow-[inset_0_0_0_0.5px_rgba(0,0,0,0.12)]" />
        <div className="w-[11px] h-[11px] rounded-full bg-[#28C840] shadow-[inset_0_0_0_0.5px_rgba(0,0,0,0.12)]" />
      </div>

      {/* App name */}
      <div className="flex items-center gap-1.5 text-[13px] font-medium text-foreground tracking-tight">
        <Shield className="w-3.5 h-3.5 text-primary" />
        <span>PrivacyDeck</span>
      </div>

      <div className="flex-1" />

      {/* Connection status */}
      {connected ? (
        <div className="flex items-center gap-3">
          {lastSynced && (
            <span className="text-[11px] text-muted-foreground hidden sm:block">Synced {formatSynced()}</span>
          )}
          <button
            onClick={disconnect}
            className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-success/10 text-success hover:bg-success/20 transition-colors"
          >
            <span className="w-[5px] h-[5px] rounded-full bg-success animate-pulse" />
            Connected
          </button>
        </div>
      ) : (
        <button
          onClick={connect}
          disabled={connecting}
          className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium bg-destructive/10 text-destructive hover:bg-destructive/20 transition-colors"
        >
          <span className="w-[5px] h-[5px] rounded-full bg-destructive" />
          {connecting ? "Connecting..." : "Connect"}
        </button>
      )}
    </div>
    </div>
  );
};
