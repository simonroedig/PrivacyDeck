import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { Feature, FEATURE_META, NetworkTrustState, CalendarEvent, StudyLogEntry, EXPOSURE_FEATURE_IDS } from "@/context/PrivacyContext";
import { getPrivacyAdvice } from "@/lib/openaiService";

const DEBOUNCE_MS = 1400;
const REFRESH_COOLDOWN_MS = 6000;

const FALLBACK: Record<string, string> = {
  high: "Your privacy shield is holding strong — you're locked down tight!",
  medium: "A few gaps in your defences. Scanning your settings now...",
  low: "Your privacy needs some work. Let me check what's most urgent...",
};

function fallback(score: number) {
  return score >= 75 ? FALLBACK.high : score >= 45 ? FALLBACK.medium : FALLBACK.low;
}

function stateKey(features: Feature[], score: number, networkTrust?: NetworkTrustState | null, userName?: string | null) {
  const f = features.map((f) => `${f.id}:${f.active}`).join(",");
  const n = networkTrust ? `${networkTrust.trustStatus}:${networkTrust.currentNetwork}` : "none";
  return `${score}|${f}|${n}|${userName ?? ""}`;
}

/** Derive habitual risk patterns and score trend from recent study logs. */
function deriveUserPattern(
  logs: StudyLogEntry[]
): { habitualRisks: string[]; scoreTrend: "improving" | "declining" | "stable" } | null {
  if (logs.length < 3) return null;

  const recent = logs.slice(-20);

  // Features left in a risky state in ≥60% of their appearances
  const counts: Record<string, { risky: number; total: number; name: string }> = {};
  recent.forEach((entry) => {
    if (!counts[entry.featureId]) counts[entry.featureId] = { risky: 0, total: 0, name: entry.featureName };
    counts[entry.featureId].total++;
    const isExposure = EXPOSURE_FEATURE_IDS.includes(entry.featureId);
    if (isExposure ? entry.after : !entry.after) counts[entry.featureId].risky++;
  });
  const habitualRisks = Object.values(counts)
    .filter((c) => c.total >= 2 && c.risky / c.total >= 0.6)
    .map((c) => c.name);

  // Score trend: compare first half vs second half of last 10 entries
  const sample = logs.slice(-10).map((e) => e.scoreAfter);
  const half = Math.floor(sample.length / 2);
  const firstAvg = sample.slice(0, half).reduce((a, b) => a + b, 0) / (half || 1);
  const secondAvg = sample.slice(half).reduce((a, b) => a + b, 0) / ((sample.length - half) || 1);
  const scoreTrend: "improving" | "declining" | "stable" =
    secondAvg - firstAvg >= 5 ? "improving" : firstAvg - secondAvg >= 5 ? "declining" : "stable";

  return { habitualRisks, scoreTrend };
}

/** Detect the feature that was most recently toggled (within last 3 s). */
function detectRecentToggle(
  features: Feature[],
  prevRef: React.MutableRefObject<Map<string, boolean>>
): { name: string; nowSafe: boolean } | null {
  const prev = prevRef.current;
  let best: { name: string; nowSafe: boolean; ts: number } | null = null;

  features.forEach((f) => {
    const meta = FEATURE_META[f.id];
    if (!meta || meta.type === "monitor") return;
    const wasActive = prev.get(f.id);
    if (wasActive === undefined || wasActive === f.active) return;

    const msSince = Date.now() - f.lastToggled.getTime();
    if (msSince > 3000) return;

    const nowSafe = meta.type === "exposure" ? !f.active : f.active;
    if (!best || msSince < best.ts) {
      best = { name: f.name, nowSafe, ts: msSince };
    }
  });

  // Update prev map
  features.forEach((f) => prev.set(f.id, f.active));

  return best ? { name: best.name, nowSafe: best.nowSafe } : null;
}

export interface AdvisorState {
  message: string;
  isLoading: boolean;
  canRefresh: boolean;
  refresh: () => void;
}

export function usePrivacyAdvisor(
  features: Feature[],
  score: number,
  networkTrust?: NetworkTrustState | null,
  calendarEvents?: CalendarEvent[],
  userName?: string | null,
  studyLogs?: StudyLogEntry[]
): AdvisorState {
  const [message, setMessage] = useState(() => fallback(score));
  const [isLoading, setIsLoading] = useState(false);
  const [canRefresh, setCanRefresh] = useState(true);

  const userPattern = useMemo(() => deriveUserPattern(studyLogs ?? []), [studyLogs]);

  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestKeyRef = useRef("");
  const lastRefreshRef = useRef(0);
  const isMounted = useRef(true);
  const prevStatesRef = useRef<Map<string, boolean>>(new Map());
  // Stable snapshot of recent toggle across renders
  const recentToggleRef = useRef<{ name: string; nowSafe: boolean } | null>(null);

  useEffect(() => { isMounted.current = true; return () => { isMounted.current = false; }; }, []);

  // Next event within the next 2 hours
  const nextEvent = useMemo(() => {
    if (!calendarEvents?.length) return null;
    const now = Date.now();
    const twoHours = now + 2 * 60 * 60 * 1000;
    return (
      [...calendarEvents]
        .filter((e) => {
          const start = new Date(e.start).getTime();
          return start >= now && start <= twoHours;
        })
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())[0] ?? null
    );
  }, [calendarEvents]);

  const fetchAdvice = useCallback(
    async (
      featureSnap: Feature[],
      scoreSnap: number,
      recentToggle: { name: string; nowSafe: boolean } | null,
      networkSnap?: NetworkTrustState | null,
      eventSnap?: (typeof nextEvent),
      userNameSnap?: string | null,
      userPatternSnap?: ReturnType<typeof deriveUserPattern>,
    ) => {
      const key = stateKey(featureSnap, scoreSnap, networkSnap, userNameSnap);
      latestKeyRef.current = key;
      setIsLoading(true);

      try {
        const msg = await getPrivacyAdvice({
          features: featureSnap,
          score: scoreSnap,
          recentToggle,
          networkTrust: networkSnap,
          nextEvent: eventSnap,
          userName: userNameSnap,
          userPattern: userPatternSnap,
        });
        if (isMounted.current && latestKeyRef.current === key) setMessage(msg);
      } catch {
        if (isMounted.current && latestKeyRef.current === key) setMessage(fallback(scoreSnap));
      } finally {
        if (isMounted.current && latestKeyRef.current === key) setIsLoading(false);
      }
    },
    []
  );

  // Initial fetch on mount
  useEffect(() => {
    features.forEach((f) => prevStatesRef.current.set(f.id, f.active));
    fetchAdvice(features, score, null, networkTrust, nextEvent, userName, userPattern);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Debounced re-fetch when state changes
  useEffect(() => {
    const key = stateKey(features, score, networkTrust);
    if (key === latestKeyRef.current) return;

    const recentToggle = detectRecentToggle(features, prevStatesRef);
    recentToggleRef.current = recentToggle;

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      fetchAdvice(features, score, recentToggleRef.current, networkTrust, nextEvent, userName, userPattern);
    }, DEBOUNCE_MS);

    return () => { if (debounceTimer.current) clearTimeout(debounceTimer.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [features, score, networkTrust, nextEvent, userName, userPattern]);

  const refresh = useCallback(() => {
    const now = Date.now();
    if (now - lastRefreshRef.current < REFRESH_COOLDOWN_MS) return;
    lastRefreshRef.current = now;
    setCanRefresh(false);
    setTimeout(() => { if (isMounted.current) setCanRefresh(true); }, REFRESH_COOLDOWN_MS);

    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    latestKeyRef.current = ""; // force re-fetch
    fetchAdvice(features, score, null, networkTrust, nextEvent, userName, userPattern);
  }, [features, score, networkTrust, nextEvent, userName, userPattern, fetchAdvice]);

  return { message, isLoading, canRefresh, refresh };
}
