import {
  usePrivacy,
  Feature,
  FEATURE_META,
  EXPOSURE_FEATURE_IDS,
  PROTECTION_FEATURE_IDS,
} from "@/context/PrivacyContext";
import { useAvatar } from "@/context/AvatarContext";
import { motion, AnimatePresence, useAnimation } from "framer-motion";
import { useState, useMemo, forwardRef, useCallback, useEffect, useRef } from "react";
import {
  ShieldCheck, ShieldAlert, ShieldOff,
  Zap, Loader2, Check, Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { FeatureIcon } from "@/components/FeatureIcon";
import { PrivacyAvatar } from "@/components/PrivacyAvatar";
import { AvatarCustomizer } from "@/components/AvatarCustomizer";
import { Switch } from "@/components/ui/switch";
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription,
} from "@/components/ui/sheet";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "@/components/ui/tooltip";
import { PrivacyAdvisorBubble } from "@/components/PrivacyAdvisorBubble";
import { usePrivacyAdvisor } from "@/hooks/usePrivacyAdvisor";

// ─── Feature groupings ────────────────────────────────────────────────────────
const FEATURE_GROUPS = [
  {
    id: "sensors",
    label: "Sensors",
    features: ["camera-control", "camera-preview", "mic-control", "audio-meter"],
  },
  {
    id: "connectivity",
    label: "Connectivity",
    features: ["network", "gps", "usb-lock"],
  },
  {
    id: "system",
    label: "System & Data",
    features: ["clipboard", "presentation", "browser-clean"],
  },
];

// ─── Privacy score arc ────────────────────────────────────────────────────────
function PrivacyScore({ score }: { score: number }) {
  const r = 34;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  const color = score >= 75 ? "#10B981" : score >= 45 ? "#F59E0B" : "#EF4444";
  const label = score >= 75 ? "Secure" : score >= 45 ? "At Risk" : "Exposed";

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-[82px] h-[82px]">
        <svg width="82" height="82" viewBox="0 0 82 82">
          <circle cx="41" cy="41" r={r} fill="none" stroke="currentColor"
            strokeWidth="4.5" className="text-muted/25" />
          <motion.circle
            cx="41" cy="41" r={r}
            fill="none" stroke={color}
            strokeWidth="4.5" strokeLinecap="round"
            strokeDasharray={`${dash} ${circ - dash}`}
            strokeDashoffset={circ / 4}
            style={{ filter: `drop-shadow(0 0 6px ${color}55)` }}
            initial={false}
            animate={{ strokeDasharray: `${dash} ${circ - dash}` }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-[15px] font-bold tabular-nums" style={{ color }}>{score}%</span>
        </div>
      </div>
      <span className="text-[10px] font-semibold tracking-widest uppercase" style={{ color }}>{label}</span>
    </div>
  );
}

// ─── Group header status helper ───────────────────────────────────────────────
function getGroupStatus(groupId: string, groupFeatures: Feature[]) {
  if (groupId === "sensors") {
    const exposures = groupFeatures.filter(
      f => FEATURE_META[f.id]?.type === "exposure" && f.active
    );
    const monitors = groupFeatures.filter(f => FEATURE_META[f.id]?.type === "monitor");
    if (exposures.length === 0) {
      return { label: "All blocked", color: "#10B981" };
    }
    return {
      label: `${exposures.length} exposed · ${monitors.length} monitoring`,
      color: "#EF4444",
    };
  } else {
    const protections = groupFeatures.filter(f => FEATURE_META[f.id]?.type === "protection");
    const active = protections.filter(f => f.active);
    const color =
      active.length === protections.length ? "#10B981"
        : active.length > 0 ? "#F59E0B"
          : "#EF4444";
    return { label: `${active.length}/${protections.length} protected`, color };
  }
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Overview() {
  const {
    features,
    toggleFeature,
    connected,
    settings,
    calendarStatus,
    calendarEvents,
    calendarRecommendation,
    networkTrust,
    studyLogs,
  } = usePrivacy();
  const { config } = useAvatar();
  const [flashId, setFlashId] = useState<string | null>(null);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [togglingId, setTogglingId] = useState<string | null>(null);
  const [lastScoreChange, setLastScoreChange] = useState<string>("No recent score change");
  const prevScoreRef = useRef<number | null>(null);

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

  const allSafe = useMemo(() => {
    const exposuresBlocked = EXPOSURE_FEATURE_IDS.every(
      id => !features.find(f => f.id === id)?.active
    );
    const protectionsOn = PROTECTION_FEATURE_IDS.every(
      id => features.find(f => f.id === id)?.active
    );
    return exposuresBlocked && protectionsOn;
  }, [features]);

  const nextEvent = useMemo(() => {
    const now = Date.now();
    return [...calendarEvents]
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
      .find(evt => new Date(evt.end).getTime() >= now) ?? null;
  }, [calendarEvents]);

  const weekEvents = useMemo(() => {
    const now = new Date();
    const monday = new Date(now);
    monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    monday.setHours(0, 0, 0, 0);
    const sundayEnd = new Date(monday);
    sundayEnd.setDate(monday.getDate() + 7);

    return [...calendarEvents]
      .filter(evt => {
        const start = new Date(evt.start).getTime();
        return start >= monday.getTime() && start < sundayEnd.getTime();
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());
  }, [calendarEvents]);

  const priorityActions = useMemo(() => {
    return features
      .filter(feature => {
        const meta = FEATURE_META[feature.id];
        if (!meta || meta.type === "monitor") return false;
        return meta.type === "exposure" ? feature.active : !feature.active;
      })
      .slice(0, 3)
      .map(feature => {
        const meta = FEATURE_META[feature.id]!;
        const actionLabel = meta.type === "exposure" ? "Block now" : "Enable now";
        const reason = meta.type === "exposure" ? meta.riskDescription : meta.safeDescription;
        return { feature, actionLabel, reason };
      });
  }, [features]);



  useEffect(() => {
    if (prevScoreRef.current === null) {
      prevScoreRef.current = score;
      return;
    }
    if (prevScoreRef.current === score) return;

    const delta = score - prevScoreRef.current;
    const recentlyChanged = [...features]
      .sort((a, b) => b.lastToggled.getTime() - a.lastToggled.getTime())
      .slice(0, 2)
      .map(f => {
        const meta = FEATURE_META[f.id];
        if (!meta) return `${f.name} changed`;
        const safeState = meta.type === "exposure" ? !f.active : meta.type === "protection" ? f.active : f.active;
        const stateLabel = safeState ? "safer" : "riskier";
        return `${f.name} → ${stateLabel}`;
      })
      .join(" · ");

    setLastScoreChange(`${delta > 0 ? "+" : ""}${delta} points (${recentlyChanged || "state changed"})`);
    prevScoreRef.current = score;
  }, [features, score]);


  const handleToggle = useCallback((id: string) => {
    setTogglingId(id);
    toggleFeature(id);
    setFlashId(id);
    setTimeout(() => {
      setFlashId(null);
      setTogglingId(null);
    }, connected ? 400 : 200);
  }, [toggleFeature, connected]);

  const { message: advisorMessage, isLoading: advisorLoading, canRefresh: advisorCanRefresh, refresh: refreshAdvisor } =
    usePrivacyAdvisor(features, score, networkTrust, calendarEvents, config.name || null, studyLogs);

  const [advisorDismissed, setAdvisorDismissed] = useState(false);

  // Avatar bounce animation — fires whenever a feature is toggled
  const avatarControls = useAnimation();
  useEffect(() => {
    if (!flashId) return;
    avatarControls.start({
      scale: [1, 1.13, 0.93, 1.05, 1],
      rotate: [0, -4, 4, -2, 0],
      transition: { duration: 0.45, ease: "easeInOut" },
    });
  }, [flashId, avatarControls]);

  const [instantPrivacyActive, setInstantPrivacyActive] = useState(false);
  const handleInstantPrivacy = useCallback(() => {
    setInstantPrivacyActive(true);
    EXPOSURE_FEATURE_IDS.forEach(id => {
      const f = features.find(f => f.id === id);
      if (f?.active) toggleFeature(id);
    });
    PROTECTION_FEATURE_IDS.forEach(id => {
      const f = features.find(f => f.id === id);
      if (!f?.active) toggleFeature(id);
    });
    setTimeout(() => setInstantPrivacyActive(false), 1200);
  }, [features, toggleFeature]);

  return (
    <TooltipProvider delayDuration={300}>
    <div className="max-w-4xl mx-auto">

      {/* ── Hero strip ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center gap-5 mb-8 bg-card border border-border rounded-2xl p-5 sm:p-6 shadow-sm card-hover relative overflow-hidden">
        {/* Subtle right accent gradient */}
        <div className="absolute right-0 top-0 bottom-0 w-40 bg-gradient-to-l from-primary/[0.04] to-transparent pointer-events-none" />

        {/* Avatar with bounce reaction + score glow */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.button
              animate={avatarControls}
              onClick={() => setSheetOpen(true)}
              className="shrink-0 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded-xl"
              aria-label="Customize avatar"
              style={{
                filter: score >= 75
                  ? "drop-shadow(0 0 10px rgba(16,185,129,0.45))"
                  : score >= 45
                  ? "drop-shadow(0 0 10px rgba(245,158,11,0.40))"
                  : "drop-shadow(0 0 10px rgba(239,68,68,0.45))",
                transition: "filter 0.6s ease",
              }}
            >
              <PrivacyAvatar size={88} showLabels />
            </motion.button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p>Click to customize</p>
          </TooltipContent>
        </Tooltip>

        {/* Info */}
        <div className="flex-1 min-w-0 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start gap-2 mb-3">
            <span className="font-bold text-lg text-foreground tracking-tight">{config.name || "PrivacyBot"}</span>
            {allSafe ? (
              <span className="flex items-center gap-1 text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3" /> Protected
              </span>
            ) : score >= 45 ? (
              <span className="flex items-center gap-1 text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-600 border border-amber-500/20">
                <ShieldAlert className="w-3 h-3" /> At Risk
              </span>
            ) : (
              <span className="flex items-center gap-1 text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-600 border border-red-500/20">
                <ShieldOff className="w-3 h-3" /> Exposed
              </span>
            )}
          </div>

          {/* AI Privacy Advisor speech bubble */}
          <AnimatePresence mode="wait">
            {advisorDismissed ? (
              <motion.button
                key="reopen"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.2 }}
                onClick={() => setAdvisorDismissed(false)}
                className="my-3 flex items-center gap-1 text-[10px] font-semibold text-muted-foreground/60 hover:text-muted-foreground transition-colors"
              >
                <Sparkles className="w-3 h-3" />
                Show advisor
              </motion.button>
            ) : (
              <motion.div
                key="bubble"
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.22 }}
                className="my-3 max-w-sm"
              >
                <PrivacyAdvisorBubble
                  message={advisorMessage}
                  isLoading={advisorLoading}
                  score={score}
                  canRefresh={advisorCanRefresh}
                  onRefresh={refreshAdvisor}
                  onDismiss={() => setAdvisorDismissed(true)}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Instant Privacy button */}
          <Tooltip>
            <TooltipTrigger asChild>
              <motion.button
                onClick={handleInstantPrivacy}
                disabled={allSafe || instantPrivacyActive}
                whileTap={{ scale: 0.96 }}
                className={cn(
                  "inline-flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-semibold transition-all",
                  allSafe
                    ? "bg-emerald-500/10 text-emerald-600 cursor-default"
                    : instantPrivacyActive
                    ? "bg-emerald-500 text-white shadow-sm shadow-emerald-500/30"
                    : "bg-gradient-to-r from-primary to-blue-500 text-white hover:shadow-lg hover:shadow-primary/25 active:shadow-sm"
                )}
              >
                {instantPrivacyActive ? (
                  <Check className="w-3.5 h-3.5" />
                ) : allSafe ? (
                  <ShieldCheck className="w-3.5 h-3.5" />
                ) : (
                  <Zap className="w-3.5 h-3.5" />
                )}
                {instantPrivacyActive ? "Applied!" : allSafe ? "All Secure" : "Instant Privacy"}
              </motion.button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <p>{allSafe ? "All privacy features are active" : "Block all sensors & enable all protections"}</p>
            </TooltipContent>
          </Tooltip>
        </div>

        {/* Score */}
        <div className="shrink-0 relative z-10">
          <PrivacyScore score={score} />
        </div>
      </div>

      {settings.localStudyMode && (
        <div className="mb-5 grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="rounded-2xl border border-border bg-card px-4 py-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Safety Semantics</h3>
            <p className="text-xs text-foreground">Exposure features are safe when OFF. Protection features are safe when ON. Monitor features do not affect score.</p>
          </div>
          <div className="rounded-2xl border border-border bg-card px-4 py-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1">Why score changed</h3>
            <p className="text-xs text-foreground">{lastScoreChange}</p>
            <p className="text-[10px] text-muted-foreground mt-1">Score = 40% exposure safety + 60% protection coverage.</p>
          </div>
        </div>
      )}

      <div className="mb-5 grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-foreground">Google Calendar</h3>
            <span className="text-[11px] font-semibold text-muted-foreground">
              {calendarStatus.connected ? "Connected" : "Disconnected"}
            </span>
          </div>
          {nextEvent ? (
            <>
              <p className="text-xs text-muted-foreground">
                Next: {settings.calendarPrivacyMode === "minimal" ? "Upcoming meeting" : nextEvent.title}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                {new Date(nextEvent.start).toLocaleString()} → {new Date(nextEvent.end).toLocaleTimeString()}
              </p>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">No upcoming events.</p>
          )}
          <div className="mt-3 rounded-xl border border-border bg-muted/20 px-3 py-2">
            <p className="text-[11px] font-semibold text-foreground mb-1">This week</p>
            {weekEvents.length ? (
              <ul className="space-y-1.5">
                {weekEvents.slice(0, 4).map(evt => (
                  <li key={evt.id} className="text-[11px] text-muted-foreground flex items-center justify-between gap-2">
                    <span className="truncate">
                      {settings.calendarPrivacyMode === "minimal" ? "Meeting" : evt.title}
                    </span>
                    <span className="shrink-0">{new Date(evt.start).toLocaleDateString(undefined, { weekday: "short" })}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-muted-foreground">No meetings in this week window.</p>
            )}
          </div>
                    {calendarRecommendation && (
            <div className="mt-3 rounded-xl border border-primary/15 bg-primary/5 px-3 py-2.5 flex items-start gap-2">
              <Sparkles className="w-3.5 h-3.5 text-primary shrink-0 mt-0.5" />
              <p className="text-[11px] text-foreground/80 leading-snug">
                {calendarRecommendation.reason}
              </p>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-border bg-card p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-foreground">Network Trust</h3>
            <span
              className={cn(
                "text-[11px] font-semibold uppercase",
                networkTrust.trustStatus === "trusted"
                  ? "text-emerald-600"
                  : networkTrust.trustStatus === "caution"
                    ? "text-amber-600"
                    : "text-destructive"
              )}
            >
              {networkTrust.trustStatus}
            </span>
          </div>
          <p className="text-xs text-muted-foreground">Current network: {networkTrust.currentNetwork}</p>
          <p className="text-[11px] text-muted-foreground mt-1">Trust score: {networkTrust.trustScore}/100</p>
          <ul className="mt-2 space-y-1">
            {networkTrust.reasons.slice(0, 3).map(reason => (
              <li key={reason} className="text-[11px] text-muted-foreground">• {reason}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mb-5 rounded-2xl border border-border bg-card p-4 sm:p-5">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-foreground">Priority Actions</h3>
          </div>
          <span className="text-[10px] font-medium text-muted-foreground">Fastest route to safer state</span>
        </div>

        {priorityActions.length === 0 ? (
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-2.5 text-xs text-emerald-700 dark:text-emerald-400">
            All high-impact controls are already in safe states.
          </div>
        ) : (
          <div className="space-y-2">
            {priorityActions.map(({ feature, actionLabel, reason }) => (
              <div key={feature.id} className="flex items-center gap-3 rounded-xl border border-border px-3 py-2.5">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-foreground truncate">{feature.name}</div>
                  <p className="text-[11px] text-muted-foreground line-clamp-1">{reason}</p>
                </div>
                <button
                  onClick={() => handleToggle(feature.id)}
                  className="shrink-0 px-3 py-1.5 rounded-lg text-[11px] font-semibold bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground transition-colors"
                >
                  {actionLabel}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Feature groups ─────────────────────────────────────────── */}
      <div className="space-y-6">
        {FEATURE_GROUPS.map(group => {
          const groupFeatures = features.filter(f => group.features.includes(f.id));
          const status = getGroupStatus(group.id, groupFeatures);

          return (
            <div key={group.id}>
              {/* Group header */}
              <div className="flex items-center gap-3 mb-3 px-0.5">
                <h2 className="text-[11px] font-bold text-muted-foreground tracking-[0.1em] uppercase">
                  {group.label}
                </h2>
                <div className="flex-1 h-px bg-border/60" />
                <span
                  className="text-[10px] font-semibold tracking-wide"
                  style={{ color: status.color }}
                >
                  {status.label}
                </span>
              </div>

              {/* Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <AnimatePresence mode="popLayout">
                  {groupFeatures.map(f => (
                    <FeatureCard
                      key={f.id}
                      feature={f}
                      flash={flashId === f.id}
                      toggling={togglingId === f.id}
                      onToggle={() => handleToggle(f.id)}
                    />
                  ))}
                </AnimatePresence>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Avatar customizer sheet ─────────────────────────────────── */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Customize Avatar</SheetTitle>
            <SheetDescription>Personalize your PrivacyDeck companion</SheetDescription>
          </SheetHeader>
          <div className="mt-4">
            <div className="flex justify-center mb-4">
              <PrivacyAvatar size={90} showLabels />
            </div>
            <AvatarCustomizer compact />
          </div>
        </SheetContent>
      </Sheet>
    </div>
    </TooltipProvider>
  );
}

// ─── Feature card ─────────────────────────────────────────────────────────────
const FeatureCard = forwardRef<HTMLDivElement, {
  feature: Feature;
  flash: boolean;
  toggling?: boolean;
  onToggle: () => void;
}>(function FeatureCard({ feature, flash, toggling, onToggle }, ref) {
  const meta = FEATURE_META[feature.id];

  const isRisky =
    meta?.type === "exposure" ? feature.active
      : meta?.type === "protection" ? !feature.active
        : false;
  const isMonitor = meta?.type === "monitor";

  // Left bar + border color
  let barColor: string;
  let borderClass: string;
  if (isMonitor) {
    barColor = feature.active ? "#3B82F6" : "#6B7280";
    borderClass = "border-border";
  } else if (isRisky) {
    barColor = "#EF4444";
    borderClass = "border-red-500/20";
  } else {
    barColor = "#10B981";
    borderClass = "border-emerald-500/15";
  }

  // Status badge
  const statusLabel = feature.active ? (meta?.activeLabel ?? "ON") : (meta?.inactiveLabel ?? "OFF");
  const statusBg = isMonitor
    ? feature.active ? "rgba(59,130,246,0.12)" : "rgba(107,114,128,0.08)"
    : isRisky ? "rgba(239,68,68,0.12)" : "rgba(16,185,129,0.12)";
  const statusColor = isMonitor
    ? feature.active ? "#3B82F6" : "#9CA3AF"
    : isRisky ? "#EF4444" : "#10B981";

  // Description line
  const description = isMonitor
    ? (feature.active ? meta?.safeDescription : "Not active")
    : isRisky
    ? meta?.riskDescription
    : meta?.safeDescription;

  // Switch track color
  const switchClass = cn(
    "shrink-0",
    meta?.type === "exposure"
      ? "data-[state=checked]:bg-destructive"
      : meta?.type === "protection"
      ? "data-[state=checked]:bg-emerald-500"
      : "data-[state=checked]:bg-blue-500",
  );

  return (
    <motion.div
      ref={ref}
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      className={cn(
        "bg-card rounded-2xl border px-4 py-3.5 card-hover relative overflow-hidden",
        borderClass,
        flash && "flash-green",
        toggling && "opacity-75",
      )}
    >
      {/* Left colour bar */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-2xl transition-colors duration-300"
        style={{ backgroundColor: barColor }}
      />

      {/* Content row */}
      <div className="flex items-center gap-3">
        {/* Icon */}
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors"
          style={{ backgroundColor: `${barColor}18`, color: barColor }}
        >
          {toggling ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FeatureIcon name={feature.icon} className="w-4 h-4" />
          )}
        </div>

        {/* Name + description */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-[13px] font-semibold text-foreground leading-tight truncate">{feature.name}</span>
            <span
              className="shrink-0 text-[8px] font-bold px-1.5 py-[2px] rounded-full tracking-widest uppercase"
              style={{ backgroundColor: statusBg, color: statusColor }}
            >
              {statusLabel}
            </span>
          </div>
          {description && (
            <p className="text-[11px] text-muted-foreground leading-snug line-clamp-1">
              {description}
            </p>
          )}
        </div>

        {/* Switch */}
        <Switch
          checked={feature.active}
          onCheckedChange={() => !toggling && onToggle()}
          disabled={toggling}
          className={switchClass}
          aria-label={`Toggle ${feature.name}`}
        />
      </div>
    </motion.div>
  );
});
