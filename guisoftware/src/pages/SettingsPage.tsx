import { useState } from "react";
import {
  Shield, Wifi, Bell, Clock, Palette, Info, Zap, FlaskConical, Download, Trash2,
  Calendar,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { usePrivacy } from "@/context/PrivacyContext";

interface SettingRowProps {
  icon: React.ReactNode;
  label: string;
  description?: string;
  children: React.ReactNode;
}

function SettingRow({ icon, label, description, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-3.5 px-5 hover:bg-muted/20 transition-colors">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-primary/8 text-primary flex items-center justify-center shrink-0">
          {icon}
        </div>
        <div>
          <div className="text-[13px] font-medium text-foreground">{label}</div>
          {description && <div className="text-[11px] text-muted-foreground mt-0.5">{description}</div>}
        </div>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="px-5 pt-5 pb-1.5">
      <span className="text-[10px] font-bold tracking-[0.1em] uppercase text-muted-foreground">{label}</span>
    </div>
  );
}

export default function SettingsPage() {
  const {
    connected, connect, disconnect, settings, updateSettings,
    studyLogs, clearStudyLogs, exportStudyLogs,
    calendarStatus, connectGoogleCalendar, disconnectGoogleCalendar, refreshCalendar,
  } = usePrivacy();

  const handleSave = () => {
    toast({
      title: "Settings saved",
      description: "Your preferences have been applied.",
    });
  };

  const AUTO_LOCK_OPTIONS = ["1", "3", "5", "10", "15", "30"];


  const downloadStudyLogs = () => {
    const blob = new Blob([exportStudyLogs()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `privacydeck-local-study-logs-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast({ title: "Local logs exported", description: "Saved as a JSON file on this device." });
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-primary/10 flex items-center justify-center">
          <Shield className="w-7 h-7 text-primary" />
        </div>
        <h1 className="text-xl font-bold text-foreground tracking-tight mb-1">Settings</h1>
        <p className="text-[13px] text-muted-foreground">Manage your preferences</p>
      </div>

      <div className="bg-card rounded-2xl border border-border overflow-hidden mb-5 shadow-sm">
        {/* Privacy Behaviour */}
        <SectionHeader label="Privacy Behaviour" />
        <SettingRow
          icon={<Clock className="w-4 h-4" />}
          label="Auto-Lock Timer"
          description="Inactivity timeout"
        >
          <select
            value={settings.autoLockDelay}
            onChange={e => updateSettings({ autoLockDelay: e.target.value })}
            className="bg-muted border border-border rounded-lg px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          >
            {AUTO_LOCK_OPTIONS.map(v => (
              <option key={v} value={v}>{v} min</option>
            ))}
          </select>
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Shield className="w-4 h-4" />}
          label="Lift-to-Lock"
          description="Lock when avatar is removed"
        >
          <Switch checked={settings.avatarRemoveAutoLock} onCheckedChange={v => updateSettings({ avatarRemoveAutoLock: v })} />
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Zap className="w-4 h-4" />}
          label="Sleep Privacy Lock"
          description="Enable all protections on suspend"
        >
          <Switch checked={settings.autoLock} onCheckedChange={v => updateSettings({ autoLock: v })} />
        </SettingRow>

        {/* Privacy Score */}
        <SectionHeader label="Privacy Score" />
        <SettingRow
          icon={<Shield className="w-4 h-4" />}
          label="Alert Threshold"
          description="Warn below this score"
        >
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="10"
              max="100"
              step="10"
              value={settings.privacyScoreThreshold}
              onChange={e => updateSettings({ privacyScoreThreshold: e.target.value })}
              className="w-24 accent-primary"
            />
            <span className="text-xs font-semibold text-foreground w-8 text-right">{settings.privacyScoreThreshold}%</span>
          </div>
        </SettingRow>

        {/* Appearance */}
        <SectionHeader label="Appearance" />
        <SettingRow
          icon={<Palette className="w-4 h-4" />}
          label="Theme"
        >
          <div className="flex gap-1">
            {(["system", "light", "dark"] as const).map(t => (
              <button
                key={t}
                onClick={() => updateSettings({ theme: t })}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-[11px] font-medium capitalize transition-all",
                  settings.theme === t
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:text-foreground",
                )}
              >
                {t}
              </button>
            ))}
          </div>
        </SettingRow>

        {/* Notifications */}
        <SectionHeader label="Notifications" />
        <SettingRow
          icon={<Bell className="w-4 h-4" />}
          label="Notifications"
          description="Feature state change alerts"
        >
          <Switch checked={settings.notifications} onCheckedChange={v => updateSettings({ notifications: v })} />
        </SettingRow>

        <SectionHeader label="Calendar" />
        <SettingRow
          icon={<Calendar className="w-4 h-4" />}
          label="Google Calendar"
          description={calendarStatus.connected ? "Connected to your Google account" : (calendarStatus.error ?? "Not connected") }
        >
          <div className="flex items-center gap-2">
            {calendarStatus.connected ? (
              <>
                <button onClick={refreshCalendar} className="px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-primary/10 text-primary">Refresh</button>
                <button onClick={disconnectGoogleCalendar} className="px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-destructive/10 text-destructive">Disconnect</button>
              </>
            ) : (
              <button onClick={connectGoogleCalendar} className="px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-primary/10 text-primary">Connect Gmail</button>
            )}
          </div>
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Calendar className="w-4 h-4" />}
          label="Calendar Privacy Display"
          description="Minimal hides event titles, Standard shows event names"
        >
          <div className="flex rounded-lg border border-border p-1 bg-muted/30">
            {["minimal", "standard"].map(mode => (
              <button
                key={mode}
                onClick={() => updateSettings({ calendarPrivacyMode: mode as "minimal" | "standard" })}
                className={cn(
                  "px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors",
                  settings.calendarPrivacyMode === mode
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {mode === "minimal" ? "Minimal" : "Standard"}
              </button>
            ))}
          </div>
        </SettingRow>

        {/* Device Connection */}
        <SectionHeader label="Device Connection" />
        <SettingRow
          icon={<Wifi className="w-4 h-4" />}
          label="WebSocket URL"
        >
          <input
            value={settings.wsUrl}
            onChange={e => updateSettings({ wsUrl: e.target.value })}
            className="w-44 bg-muted border border-border rounded-lg px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring font-mono"
          />
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Wifi className="w-4 h-4" />}
          label="Connection"
          description={connected ? "Connected to daemon" : "Not connected"}
        >
          <button
            onClick={connected ? disconnect : connect}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all",
              connected
                ? "bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground"
                : "bg-success/10 text-success hover:bg-success hover:text-success-foreground",
            )}
          >
            <span className={cn("w-1.5 h-1.5 rounded-full", connected ? "bg-success" : "bg-destructive")} />
            {connected ? "Disconnect" : "Connect"}
          </button>
        </SettingRow>

        {/* Research & Local Data */}
        <SectionHeader label="Research & Local Data" />
        <SettingRow
          icon={<FlaskConical className="w-4 h-4" />}
          label="Study Mode"
          description="Shows extra explanation cues for user studies"
        >
          <Switch checked={settings.localStudyMode} onCheckedChange={v => updateSettings({ localStudyMode: v })} />
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Shield className="w-4 h-4" />}
          label="Local-Only Data Collection"
          description="Stores interaction events only in this browser (never sent to daemon/cloud)"
        >
          <Switch
            checked={settings.localStudyDataCollection}
            onCheckedChange={v => updateSettings({ localStudyDataCollection: v })}
          />
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Info className="w-4 h-4" />}
          label="Collected Events"
          description={`${studyLogs.length} events currently stored locally`}
        >
          <div className="flex items-center gap-1.5">
            <button
              onClick={downloadStudyLogs}
              disabled={!studyLogs.length}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-primary/10 text-primary disabled:opacity-40"
            >
              <Download className="w-3.5 h-3.5" /> Export
            </button>
            <button
              onClick={() => { clearStudyLogs(); toast({ title: "Local logs deleted", description: "All local study events were removed." }); }}
              disabled={!studyLogs.length}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-destructive/10 text-destructive disabled:opacity-40"
            >
              <Trash2 className="w-3.5 h-3.5" /> Clear
            </button>
          </div>
        </SettingRow>


        {/* Advanced */}
        <SectionHeader label="Advanced" />
        <SettingRow
          icon={<Zap className="w-4 h-4" />}
          label="Launch at Login"
        >
          <Switch checked={settings.startOnBoot} onCheckedChange={v => updateSettings({ startOnBoot: v })} />
        </SettingRow>
        <div className="h-px bg-border mx-4" />
        <SettingRow
          icon={<Info className="w-4 h-4" />}
          label="Demo Mode"
          description="Simulate without hardware"
        >
          <Switch checked={settings.demoMode} onCheckedChange={v => updateSettings({ demoMode: v })} />
        </SettingRow>
      </div>

      <button
        onClick={handleSave}
        className="w-full py-3.5 bg-primary text-primary-foreground rounded-2xl font-semibold text-[13px] hover:opacity-90 active:scale-[0.99] transition-all shadow-sm"
      >
        Save Settings
      </button>

      <p className="text-center text-[10px] text-muted-foreground/60 mt-5 tracking-wide">
        PrivacyDeck v1.0 · macOS · © 2026
      </p>
    </div>
  );
}
