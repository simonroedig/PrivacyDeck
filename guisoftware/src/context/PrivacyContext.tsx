import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useWebSocket, type WSMessage } from "@/hooks/useWebSocket";
import { type AvatarConfig } from "@/context/AvatarContext";
import { toast } from "@/hooks/use-toast";

export interface Feature {
  id: string;
  name: string;
  icon: string;
  description: string;
  active: boolean;
  lastToggled: Date;
}

// ─── Feature classification ────────────────────────────────────────────────────
// exposure  : active=true  → sensor is ON  → privacy RISK  (camera recording, mic live)
// protection: active=true  → guard is ON   → privacy SAFE  (network isolated, GPS off)
// monitor   : purely informational, no privacy score impact
export type FeatureType = "exposure" | "protection" | "monitor";
export type FeatureRisk = "critical" | "high" | "medium" | "low" | "none";

export interface FeatureMeta {
  type: FeatureType;
  risk: FeatureRisk;        // severity of the "unsafe" state
  activeLabel: string;      // badge text when active=true
  inactiveLabel: string;    // badge text when active=false
  activeIsRisk: boolean;    // true = active is the risky state (exposure features)
  riskDescription: string;  // shown on card when in risky state
  safeDescription: string;  // shown on card when in safe state
}

export const FEATURE_META: Record<string, FeatureMeta> = {
  "camera-control": {
    type: "exposure",
    risk: "critical",
    activeLabel: "EXPOSED",
    inactiveLabel: "BLOCKED",
    activeIsRisk: true,
    riskDescription: "Camera is live — you may be recorded",
    safeDescription: "Camera hardware blocked",
  },
  "mic-control": {
    type: "exposure",
    risk: "critical",
    activeLabel: "LISTENING",
    inactiveLabel: "MUTED",
    activeIsRisk: true,
    riskDescription: "Microphone is active — audio being captured",
    safeDescription: "Microphone muted at hardware level",
  },
  "camera-preview": {
    type: "monitor",
    risk: "none",
    activeLabel: "PREVIEW",
    inactiveLabel: "OFF",
    activeIsRisk: false,
    riskDescription: "",
    safeDescription: "Live camera view on PrivacyDeck display",
  },
  "audio-meter": {
    type: "monitor",
    risk: "none",
    activeLabel: "METERING",
    inactiveLabel: "OFF",
    activeIsRisk: false,
    riskDescription: "",
    safeDescription: "Real-time audio level monitoring",
  },
  "network": {
    type: "protection",
    risk: "high",
    activeLabel: "ISOLATED",
    inactiveLabel: "OPEN",
    activeIsRisk: false,
    riskDescription: "Wi-Fi is active — network traffic unfiltered",
    safeDescription: "Wi-Fi killed — network isolated",
  },
  "gps": {
    type: "protection",
    risk: "high",
    activeLabel: "DISABLED",
    inactiveLabel: "TRACKING",
    activeIsRisk: false,
    riskDescription: "Location services are exposing your position",
    safeDescription: "GPS & location services disabled",
  },
  "usb-lock": {
    type: "protection",
    risk: "medium",
    activeLabel: "LOCKED",
    inactiveLabel: "UNLOCKED",
    activeIsRisk: false,
    riskDescription: "Unknown USB devices can connect freely",
    safeDescription: "Unauthorized USB devices blocked",
  },
  "clipboard": {
    type: "protection",
    risk: "medium",
    activeLabel: "PROTECTED",
    inactiveLabel: "UNPROTECTED",
    activeIsRisk: false,
    riskDescription: "Clipboard contents may leak between apps",
    safeDescription: "Clipboard auto-wipe active",
  },
  "presentation": {
    type: "protection",
    risk: "low",
    activeLabel: "ACTIVE",
    inactiveLabel: "OFF",
    activeIsRisk: false,
    riskDescription: "Screen content visible to bystanders",
    safeDescription: "Notifications & sensitive content hidden",
  },
  "browser-clean": {
    type: "protection",
    risk: "low",
    activeLabel: "CLEANING",
    inactiveLabel: "OFF",
    activeIsRisk: false,
    riskDescription: "Browser data accumulating",
    safeDescription: "Cookies, cache & history being cleared",
  },
};

// IDs used for the privacy score calculation
export const EXPOSURE_FEATURE_IDS = ["camera-control", "mic-control"];
export const PROTECTION_FEATURE_IDS = [
  "network", "gps", "usb-lock", "clipboard", "presentation", "browser-clean",
];

// ─── Persisted user settings ────────────────────────────────────────────────
export interface DashboardSettings {
  wsUrl: string;
  theme: "system" | "light" | "dark";
  notifications: boolean;
  autoLock: boolean;
  autoLockDelay: string;
  startOnBoot: boolean;
  demoMode: boolean;
  avatarRemoveAutoLock: boolean;
  privacyScoreThreshold: string;
  localStudyMode: boolean;
  localStudyDataCollection: boolean;
  calendarPrivacyMode: "minimal" | "standard";
}

const DEFAULT_SETTINGS: DashboardSettings = {
  wsUrl: "ws://localhost:50556",
  theme: "system",
  notifications: true,
  autoLock: true,
  autoLockDelay: "5",
  startOnBoot: false,
  demoMode: false,
  avatarRemoveAutoLock: true,
  privacyScoreThreshold: "70",
  localStudyMode: false,
  localStudyDataCollection: false,
  calendarPrivacyMode: "minimal",
};

const SETTINGS_KEY = "privacydeck-settings";

function loadSettings(): DashboardSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
  } catch {}
  return { ...DEFAULT_SETTINGS };
}

function saveSettings(settings: DashboardSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}


export interface StudyLogEntry {
  id: string;
  timestamp: string;
  featureId: string;
  featureName: string;
  before: boolean;
  after: boolean;
  source: "dashboard" | "daemon";
  scoreBefore: number;
  scoreAfter: number;
}

export interface CalendarStatus {
  provider: "google" | "microsoft";
  connected: boolean;
  lastSync: string | null;
  error: string | null;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  isPrivate: boolean;
}

export interface CalendarRecommendation {
  profile: string;
  reason: string;
  impact: number;
}

export interface NetworkTrustState {
  currentNetwork: string;
  trustStatus: "trusted" | "caution" | "untrusted";
  trustScore: number;
  reasons: string[];
}

interface PrivacyState {
  features: Feature[];
  connected: boolean;
  lastSynced: Date | null;
  connecting: boolean;
  connectionError: string | null;
  buttonMapping: string[];
  settings: DashboardSettings;
  daemonDemoMode: boolean;
  daemonAvatarConfig: AvatarConfig | null;
  toggleFeature: (id: string) => void;
  connect: () => void;
  disconnect: () => void;
  setButtonMapping: (mapping: string[]) => void;
  updateSettings: (partial: Partial<DashboardSettings>) => void;
  sendAvatarConfig: (config: AvatarConfig) => void;
  studyLogs: StudyLogEntry[];
  clearStudyLogs: () => void;
  exportStudyLogs: () => string;
  calendarStatus: CalendarStatus;
  calendarEvents: CalendarEvent[];
  calendarRecommendation: CalendarRecommendation | null;
  connectGoogleCalendar: () => void;
  disconnectGoogleCalendar: () => void;
  refreshCalendar: () => void;
  networkTrust: NetworkTrustState;
}

const STUDY_LOG_KEY = "privacydeck-local-study-logs";

const GOOGLE_TOKEN_KEY = "privacydeck-google-token";
const GOOGLE_AUTH_PENDING_KEY = "privacydeck-google-auth-pending";
const GOOGLE_AUTH_STATE_KEY = "privacydeck-google-auth-state";
const GOOGLE_SCOPES = ["openid", "profile", "email", "https://www.googleapis.com/auth/calendar.readonly"];
const GOOGLE_CLIENT_ID_STORAGE_KEY = "privacydeck-google-client-id";
const GOOGLE_CLIENT_ID = (import.meta.env.VITE_GOOGLE_CLIENT_ID || import.meta.env.VITE_GMAIL_CLIENT_ID) as string | undefined;
const GOOGLE_REDIRECT_URI = import.meta.env.VITE_GOOGLE_REDIRECT_URI as string | undefined;

interface GoogleToken {
  accessToken: string;
  expiresAt: number;
}

function persistGoogleAuthValue(key: string, value: string) {
  try {
    sessionStorage.setItem(key, value);
  } catch {
    void 0; // ignore storage restrictions
  }
  try {
    localStorage.setItem(key, value);
  } catch {
    void 0; // ignore storage restrictions
  }
}

function readGoogleAuthValue(key: string): string | null {
  try {
    const sessionValue = sessionStorage.getItem(key);
    if (sessionValue) return sessionValue;
  } catch {
    void 0; // ignore storage restrictions
  }
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function clearGoogleAuthValue(key: string) {
  try {
    sessionStorage.removeItem(key);
  } catch {
    void 0; // ignore storage restrictions
  }
  try {
    localStorage.removeItem(key);
  } catch {
    void 0; // ignore storage restrictions
  }
}

function resolveGoogleClientId(): string | null {
  const envClientId = GOOGLE_CLIENT_ID?.trim();
  if (envClientId) return envClientId;

  const savedClientId = localStorage.getItem(GOOGLE_CLIENT_ID_STORAGE_KEY)?.trim();
  if (savedClientId) return savedClientId;

  const manualClientId = window.prompt(
    "Enter your Google Cloud application (client) ID to connect Gmail. This will be saved locally for future connects."
  )?.trim();

  if (!manualClientId) return null;

  localStorage.setItem(GOOGLE_CLIENT_ID_STORAGE_KEY, manualClientId);
  return manualClientId;
}

function resolveGoogleRedirectUri(): string {
  const configuredUri = GOOGLE_REDIRECT_URI?.trim();
  if (configuredUri) return configuredUri;
  // Default to origin-only callback to avoid path mismatches (e.g. /settings)
  // with Google OAuth redirect URI allowlists.
  return window.location.origin;
}

function loadGoogleToken(): GoogleToken | null {
  try {
    const raw = localStorage.getItem(GOOGLE_TOKEN_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as GoogleToken;
    if (!parsed.accessToken || typeof parsed.expiresAt !== "number") return null;
    if (Date.now() >= parsed.expiresAt) {
      localStorage.removeItem(GOOGLE_TOKEN_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveGoogleToken(token: GoogleToken) {
  localStorage.setItem(GOOGLE_TOKEN_KEY, JSON.stringify(token));
}

function clearGoogleToken() {
  localStorage.removeItem(GOOGLE_TOKEN_KEY);
}

function getWeekWindow() {
  const now = new Date();
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  monday.setHours(0, 0, 0, 0);
  const end = new Date(monday);
  end.setDate(monday.getDate() + 7);
  return { start: monday.toISOString(), end: end.toISOString() };
}

function buildDemoMeetingAtFive(): CalendarEvent {
  const start = new Date();
  start.setSeconds(0, 0);
  start.setHours(17, 0, 0, 0);
  if (start.getTime() <= Date.now()) {
    start.setDate(start.getDate() + 1);
  }
  const end = new Date(start.getTime() + 30 * 60 * 1000);
  return {
    id: `demo-gmail-${start.toISOString()}`,
    title: "Team privacy check-in",
    start: start.toISOString(),
    end: end.toISOString(),
    isPrivate: false,
  };
}

function beginGoogleRedirectAuth() {
  const clientId = resolveGoogleClientId();
  if (!clientId) {
    throw new Error("Missing Google client ID. Set VITE_GOOGLE_CLIENT_ID (or VITE_GMAIL_CLIENT_ID) or provide it when prompted.");
  }

  const state = crypto.randomUUID();

  persistGoogleAuthValue(GOOGLE_AUTH_STATE_KEY, state);
  const redirectUri = resolveGoogleRedirectUri();
  const authUrl = new URL("https://accounts.google.com/o/oauth2/v2/auth");
  authUrl.searchParams.set("client_id", clientId);
  authUrl.searchParams.set("response_type", "code");
  authUrl.searchParams.set("redirect_uri", redirectUri);
  authUrl.searchParams.set("response_mode", "query");
  authUrl.searchParams.set("scope", GOOGLE_SCOPES.join(" "));
  authUrl.searchParams.set("include_granted_scopes", "true");
  authUrl.searchParams.set("access_type", "offline");
  authUrl.searchParams.set("prompt", "select_account");
  authUrl.searchParams.set("state", state);

  persistGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY, "1");
  window.location.assign(authUrl.toString());
}

function consumeGoogleAuthRedirect(): { code: string | null; error: string | null } {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  const error = params.get("error_description") ?? params.get("error");
  const state = params.get("state");
  const expectedState = readGoogleAuthValue(GOOGLE_AUTH_STATE_KEY);

  if (!code && !error) {
    return { code: null, error: null };
  }

  const cleanUrl = `${window.location.origin}${window.location.pathname}`;
  window.history.replaceState({}, document.title, cleanUrl);

  if (error) {
    return { code: null, error: decodeURIComponent(error) };
  }

  if (!state || !expectedState || state !== expectedState) {
    return { code: null, error: "Google sign-in state validation failed. Please try again." };
  }

  return { code, error: null };
}

async function fetchGoogleWeekEvents(accessToken: string): Promise<CalendarEvent[]> {
  const { start, end } = getWeekWindow();
  const query = new URLSearchParams({
    timeMin: start,
    timeMax: end,
    orderBy: "startTime",
    singleEvents: "true",
    maxResults: "50",
    timeZone: "UTC",
  });

  const response = await fetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?${query.toString()}`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Google Calendar API error (${response.status}): ${message}`);
  }

  const payload = await response.json() as { items?: Array<Record<string, unknown>> };
  const events = Array.isArray(payload.items) ? payload.items : [];

  return events.map((evt, index) => {
    const startObj = (evt.start as { dateTime?: string; date?: string } | undefined);
    const endObj = (evt.end as { dateTime?: string; date?: string } | undefined);
    const startRaw = startObj?.dateTime ?? startObj?.date;
    const endRaw = endObj?.dateTime ?? endObj?.date;
    return {
      id: String(evt.id ?? `google-${index}`),
      title: String(evt.summary ?? "Untitled meeting"),
      start: startRaw ? new Date(startRaw).toISOString() : new Date().toISOString(),
      end: endRaw ? new Date(endRaw).toISOString() : new Date().toISOString(),
      isPrivate: (evt as { visibility?: string }).visibility === "private",
    };
  });
}


function computePrivacyScore(features: Feature[]): number {
  const exposuresActive = EXPOSURE_FEATURE_IDS.filter(id => features.find(f => f.id === id)?.active).length;
  const protectionsActive = PROTECTION_FEATURE_IDS.filter(id => features.find(f => f.id === id)?.active).length;
  const exposureScore = ((EXPOSURE_FEATURE_IDS.length - exposuresActive) / EXPOSURE_FEATURE_IDS.length) * 40;
  const protectionScore = (protectionsActive / PROTECTION_FEATURE_IDS.length) * 60;
  return Math.round(exposureScore + protectionScore);
}

function loadStudyLogs(): StudyLogEntry[] {
  try {
    const raw = localStorage.getItem(STUDY_LOG_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

const defaultFeatures: Feature[] = [
  // ── Sensors (exposure — active = risk) ──────────────────────────────────────
  { id: "camera-control",  name: "Camera Control",      icon: "Video",         description: "Enables or disables the system camera hardware.",               active: true,  lastToggled: new Date() },
  { id: "camera-preview",  name: "Camera Preview",      icon: "Camera",        description: "Shows a live camera preview on your PrivacyDeck display.",      active: true,  lastToggled: new Date() },
  { id: "mic-control",     name: "Microphone Control",  icon: "Mic",           description: "Enables or disables the microphone input.",                     active: true,  lastToggled: new Date() },
  { id: "audio-meter",     name: "Audio Meter",         icon: "Volume2",       description: "Displays real-time audio levels from your microphone.",         active: true,  lastToggled: new Date() },
  // ── Connectivity (protection — active = safe) ────────────────────────────────
  { id: "network",         name: "Network Isolation",   icon: "Globe",         description: "Cuts Wi-Fi to isolate network traffic.",                        active: false, lastToggled: new Date() },
  { id: "gps",             name: "Instant Disable GPS", icon: "MapPin",        description: "Disables GPS and location services immediately.",               active: false, lastToggled: new Date() },
  { id: "usb-lock",        name: "USB Safety Lock",     icon: "Lock",          description: "Blocks unauthorized USB devices from connecting.",              active: true,  lastToggled: new Date() },
  // ── System & Data (protection — active = safe) ──────────────────────────────
  { id: "clipboard",       name: "Clipboard Guard",     icon: "ClipboardList", description: "Tracks and wipes clipboard history on demand.",                 active: false, lastToggled: new Date() },
  { id: "presentation",    name: "Presentation Mode",   icon: "Monitor",       description: "Hides notifications and sensitive content during presentations.", active: true, lastToggled: new Date() },
  { id: "browser-clean",   name: "Browser Clean",       icon: "Trash2",        description: "Clears browser cookies, cache, and history.",                  active: true,  lastToggled: new Date() },
];

const PrivacyContext = createContext<PrivacyState | null>(null);

export const usePrivacy = () => {
  const ctx = useContext(PrivacyContext);
  if (!ctx) throw new Error("usePrivacy must be used within PrivacyProvider");
  return ctx;
};

export const PrivacyProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [features, setFeatures] = useState<Feature[]>(defaultFeatures);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);
  const [settings, setSettings] = useState<DashboardSettings>(loadSettings);
  const [buttonMappingLocal, setButtonMappingLocal] = useState<string[]>([
    "camera-control",
    "mic-control",
    "network",
    "gps",
  ]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [daemonDemoMode, setDaemonDemoMode] = useState<boolean>(false);
  const [daemonAvatarConfig, setDaemonAvatarConfig] = useState<AvatarConfig | null>(null);
  const [studyLogs, setStudyLogs] = useState<StudyLogEntry[]>(loadStudyLogs);
  const [calendarStatus, setCalendarStatus] = useState<CalendarStatus>({
    provider: "google",
    connected: false,
    lastSync: null,
    error: null,
  });
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [calendarRecommendation, setCalendarRecommendation] = useState<CalendarRecommendation | null>(null);
  const [networkTrust, setNetworkTrust] = useState<NetworkTrustState>({
    currentNetwork: "Unknown",
    trustStatus: "caution",
    trustScore: 50,
    reasons: ["Waiting for daemon network telemetry."],
  });
  // Track pending toggles to prevent state sync from overwriting optimistic updates
  const pendingTogglesRef = React.useRef<Map<string, number>>(new Map());
  const pendingCalendarConnectRef = React.useRef(false);
  const calendarSourceRef = React.useRef<"daemon" | "google">("daemon");
  const pendingGoogleOAuthRef = React.useRef<{
    resolve: (token: GoogleToken) => void;
    reject: (error: Error) => void;
  } | null>(null);
  const PENDING_TOGGLE_TIMEOUT = 2000; // 2 seconds grace period

  const appendStudyLog = useCallback((entry: Omit<StudyLogEntry, "id" | "timestamp">) => {
    if (!settings.localStudyDataCollection) return;
    setStudyLogs(prev => {
      const next = [
        ...prev,
        {
          ...entry,
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          timestamp: new Date().toISOString(),
        },
      ].slice(-2000);
      localStorage.setItem(STUDY_LOG_KEY, JSON.stringify(next));
      return next;
    });
  }, [settings.localStudyDataCollection]);

  const syncGoogleCalendar = useCallback(async (accessToken: string) => {
    const events = await fetchGoogleWeekEvents(accessToken);
    const nowIso = new Date().toISOString();
    calendarSourceRef.current = "google";
    setCalendarEvents(events);
    setCalendarStatus({
      provider: "google",
      connected: true,
      lastSync: nowIso,
      error: null,
    });

    setCalendarRecommendation(() => {
      if (!events.length) return null;
      const now = Date.now();
      const nextEvent = [...events]
        .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
        .find(evt => new Date(evt.end).getTime() >= now);
      if (!nextEvent) return null;
      const mins = Math.max(0, Math.floor((new Date(nextEvent.start).getTime() - now) / 60000));
      const actions = [];
      if (features.find(f => f.id === "mic-control")?.active) actions.push("mute mic");
      if (features.find(f => f.id === "camera-control")?.active) actions.push("block camera");
      if (!features.find(f => f.id === "presentation")?.active) actions.push("enable presentation mode");
      if (networkTrust.trustStatus !== "trusted" && !features.find(f => f.id === "network")?.active) {
        actions.push("enable network isolation");
      }
      return {
        profile: mins <= 20 ? "Focus Meeting Shield" : "Weekly Privacy Balance",
        reason: `Synced ${events.length} meetings this week. Next starts in ${mins}m. Suggested: ${actions.slice(0, 3).join(", ") || "maintain current protections"}.`,
        impact: 14 + (networkTrust.trustStatus !== "trusted" ? 4 : 0),
      };
    });
  }, [features, networkTrust.trustStatus]);

  const handleMessage = useCallback((msg: WSMessage) => {
    setConnectionError(null);
    const now = Date.now();

    // Helper: check if a feature has a pending toggle (recently toggled locally)
    const hasPendingToggle = (featureId: string) => {
      const toggleTime = pendingTogglesRef.current.get(featureId);
      if (!toggleTime) return false;
      if (now - toggleTime > PENDING_TOGGLE_TIMEOUT) {
        pendingTogglesRef.current.delete(featureId);
        return false;
      }
      return true;
    };

    if (msg.type === "state") {
      const featureStates = msg.features as Record<string, { active: boolean }>;
      setFeatures(prev =>
        prev.map(f => {
          const daemonState = featureStates[f.id];
          // Skip updating features with pending toggles to prevent race conditions
          if (daemonState && !hasPendingToggle(f.id)) {
            return { ...f, active: daemonState.active, lastToggled: new Date() };
          }
          return f;
        }),
      );
      if (msg.buttonMapping) {
        setButtonMappingLocal(msg.buttonMapping as string[]);
      }
      if (typeof msg.demoMode === "boolean") {
        setDaemonDemoMode(msg.demoMode);
      }
      if (msg.avatarConfig && typeof msg.avatarConfig === "object") {
        setDaemonAvatarConfig(msg.avatarConfig as AvatarConfig);
      }
      if (calendarSourceRef.current !== "google") {
        if (msg.calendarStatus && typeof msg.calendarStatus === "object") {
          setCalendarStatus(msg.calendarStatus as CalendarStatus);
        }
        if (Array.isArray(msg.calendarEvents)) {
          setCalendarEvents(msg.calendarEvents as CalendarEvent[]);
        }
        if (msg.calendarRecommendation && typeof msg.calendarRecommendation === "object") {
          setCalendarRecommendation(msg.calendarRecommendation as CalendarRecommendation);
        }
      }
      if (msg.networkTrust && typeof msg.networkTrust === "object") {
        setNetworkTrust(msg.networkTrust as NetworkTrustState);
      }
      setLastSynced(new Date());
    }

    if (calendarSourceRef.current !== "google" && msg.type === "calendar_status" && typeof msg.status === "object") {
      setCalendarStatus(msg.status as CalendarStatus);
      setLastSynced(new Date());
    }

    if (calendarSourceRef.current !== "google" && msg.type === "calendar_events" && Array.isArray(msg.events)) {
      setCalendarEvents(msg.events as CalendarEvent[]);
      setLastSynced(new Date());
    }

    if (calendarSourceRef.current !== "google" && msg.type === "calendar_recommendation" && typeof msg.recommendation === "object") {
      setCalendarRecommendation(msg.recommendation as CalendarRecommendation);
      setLastSynced(new Date());
    }

    if (msg.type === "network_trust" && typeof msg.payload === "object") {
      setNetworkTrust(msg.payload as NetworkTrustState);
      setLastSynced(new Date());
    }

    if (msg.type === "google_token" && pendingGoogleOAuthRef.current) {
      const accessToken = msg.accessToken as string;
      const expiresAt = msg.expiresAt as number;
      if (accessToken) {
        pendingGoogleOAuthRef.current.resolve({ accessToken, expiresAt });
        pendingGoogleOAuthRef.current = null;
      } else {
        pendingGoogleOAuthRef.current.reject(new Error("No access token in daemon response"));
        pendingGoogleOAuthRef.current = null;
      }
    }

    if (msg.type === "ack" && msg.success) {
      const featureId = msg.featureId as string;
      // Clear pending toggle since we got confirmation
      pendingTogglesRef.current.delete(featureId);
      setFeatures(prev => {
        const scoreBefore = computePrivacyScore(prev);
        const next = prev.map(f =>
          f.id === featureId
            ? { ...f, active: msg.active as boolean, lastToggled: new Date() }
            : f,
        );
        const changedFeature = prev.find(f => f.id === featureId);
        if (changedFeature && settings.localStudyDataCollection && changedFeature.active !== (msg.active as boolean)) {
          appendStudyLog({
            featureId,
            featureName: changedFeature.name,
            before: changedFeature.active,
            after: msg.active as boolean,
            source: "daemon",
            scoreBefore,
            scoreAfter: computePrivacyScore(next),
          });
        }
        return next;
      });
      setLastSynced(new Date());
    }

    if (msg.type === "error") {
      // On error, clear pending toggle and revert if needed
      const featureId = msg.featureId as string;
      if (featureId) {
        pendingTogglesRef.current.delete(featureId);
      }
      // Reject a pending Google OAuth exchange if the daemon returns an error
      if (pendingGoogleOAuthRef.current) {
        pendingGoogleOAuthRef.current.reject(new Error(msg.message as string));
        pendingGoogleOAuthRef.current = null;
      }
      setConnectionError(msg.message as string);
    }

    if (msg.type === "feature_update") {
      const featureId = msg.featureId as string;
      // Feature updates from daemon (e.g., Tkinter UI) should apply unless pending
      if (!hasPendingToggle(featureId)) {
        setFeatures(prev => {
          const scoreBefore = computePrivacyScore(prev);
          const next = prev.map(f =>
            f.id === featureId
              ? { ...f, active: msg.active as boolean, lastToggled: new Date() }
              : f,
          );
          const changedFeature = prev.find(f => f.id === featureId);
          if (changedFeature && settings.localStudyDataCollection && changedFeature.active !== (msg.active as boolean)) {
            appendStudyLog({
              featureId,
              featureName: changedFeature.name,
              before: changedFeature.active,
              after: msg.active as boolean,
              source: "daemon",
              scoreBefore,
              scoreAfter: computePrivacyScore(next),
            });
          }
          return next;
        });
      }
      setLastSynced(new Date());
    }
  }, [appendStudyLog, settings.localStudyDataCollection]);

  // Apply theme whenever settings change
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    if (settings.theme === "system") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.classList.add(prefersDark ? "dark" : "light");
    } else {
      root.classList.add(settings.theme);
    }
  }, [settings.theme]);

  const updateSettings = useCallback((partial: Partial<DashboardSettings>) => {
    setSettings(prev => {
      const next = { ...prev, ...partial };
      saveSettings(next);
      return next;
    });
  }, []);

  const { status, connect, disconnect, send } = useWebSocket({
    url: settings.wsUrl,
    onMessage: handleMessage,
  });

  const connected = status === "connected";
  const connecting = status === "connecting";

  const toggleFeature = useCallback(
    (id: string) => {
      // Mark this feature as having a pending toggle to prevent state sync race conditions
      pendingTogglesRef.current.set(id, Date.now());
      
      // Always apply optimistic local update so the UI responds instantly,
      // even when the daemon is not connected (important for demos).
      setFeatures(prev => {
        const scoreBefore = computePrivacyScore(prev);
        const next = prev.map(f =>
          f.id === id
            ? { ...f, active: !f.active, lastToggled: new Date() }
            : f,
        );
        const changedFeature = prev.find(f => f.id === id);
        if (changedFeature && settings.localStudyDataCollection) {
          appendStudyLog({
            featureId: id,
            featureName: changedFeature.name,
            before: changedFeature.active,
            after: !changedFeature.active,
            source: "dashboard",
            scoreBefore,
            scoreAfter: computePrivacyScore(next),
          });
        }
        return next;
      });
      // If the daemon is reachable, also forward the toggle so hardware syncs.
      if (connected) {
        send({ type: "toggle", featureId: id });
      } else {
        // If not connected, clear pending immediately since there's no daemon to confirm
        setTimeout(() => pendingTogglesRef.current.delete(id), 100);
      }
    },
    [appendStudyLog, connected, send, settings.localStudyDataCollection],
  );

  const setButtonMapping = useCallback(
    (mapping: string[]) => {
      setButtonMappingLocal(mapping);
      if (connected) {
        send({ type: "set_button_mapping", mapping });
      }
    },
    [connected, send],
  );

  const sendAvatarConfig = useCallback(
    (config: AvatarConfig) => {
      if (connected) {
        send({ type: "set_avatar_config", config });
      }
    },
    [connected, send],
  );

  const clearStudyLogs = useCallback(() => {
    localStorage.removeItem(STUDY_LOG_KEY);
    setStudyLogs([]);
  }, []);

  const exportStudyLogs = useCallback(() => JSON.stringify(studyLogs, null, 2), [studyLogs]);

  const connectGoogleCalendar = useCallback(() => {
    const demoEvent = buildDemoMeetingAtFive();
    const nowIso = new Date().toISOString();
    calendarSourceRef.current = "google";
    setCalendarEvents([demoEvent]);
    setCalendarStatus({
      provider: "google",
      connected: true,
      lastSync: nowIso,
      error: null,
    });
    setCalendarRecommendation({
      profile: "Meeting Privacy Shield",
      reason: "Demo Gmail sync created a meeting at 5:00 PM. Before it starts: mute mic, block camera, and enable presentation mode.",
      impact: 18,
    });

    if (connected) {
      send({ type: "connect_calendar", provider: "google" });
    }

    toast({
      title: "Gmail demo connected",
      description: "Added a demo meeting at 5:00 PM and generated privacy recommendations.",
    });
  }, [connected, send]);

  const disconnectGoogleCalendar = useCallback(() => {
    clearGoogleToken();
    calendarSourceRef.current = "daemon";
    setCalendarEvents([]);
    setCalendarRecommendation(null);
    setCalendarStatus({ provider: "google", connected: false, lastSync: new Date().toISOString(), error: null });
    if (connected) {
      send({ type: "disconnect_calendar" });
    }
  }, [connected, send]);

  const refreshCalendar = useCallback(() => {
    const token = loadGoogleToken();
    if (token) {
      syncGoogleCalendar(token.accessToken)
        .then(() => toast({ title: "Calendar refreshed", description: "Gmail meetings updated for this week." }))
        .catch((error: unknown) => {
          const message = error instanceof Error ? error.message : "Refresh failed.";
          toast({ title: "Calendar refresh failed", description: message, variant: "destructive" });
        });
      return;
    }

    if (connected) {
      send({ type: "refresh_calendar" });
    }
  }, [connected, send, syncGoogleCalendar]);

  useEffect(() => {
    if (connected && pendingCalendarConnectRef.current) {
      pendingCalendarConnectRef.current = false;
      send({ type: "connect_calendar", provider: "google" });
    }
  }, [connected, send]);

  useEffect(() => {
    const pendingAuth = readGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY) === "1";
    const { code, error } = consumeGoogleAuthRedirect();

    if (error) {
      clearGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY);
      clearGoogleAuthValue(GOOGLE_AUTH_STATE_KEY);
      setCalendarStatus({ provider: "google", connected: false, lastSync: null, error });
      toast({ title: "Google connection failed", description: error, variant: "destructive" });
      return;
    }

    if (code && connected) {
      // Exchange code via daemon
      const tokenPromise = new Promise<GoogleToken>((resolve, reject) => {
        pendingGoogleOAuthRef.current = { resolve, reject };
        const redirectUri = resolveGoogleRedirectUri();
        send({ type: "google_oauth_exchange_code", code, redirect_uri: redirectUri });
        
        // Timeout after 30 seconds
        setTimeout(() => {
          if (pendingGoogleOAuthRef.current) {
            pendingGoogleOAuthRef.current.reject(new Error("Daemon token exchange timeout"));
            pendingGoogleOAuthRef.current = null;
          }
        }, 30000);
      });

      tokenPromise
        .then((token) => {
          saveGoogleToken(token);
          clearGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY);
          clearGoogleAuthValue(GOOGLE_AUTH_STATE_KEY);
              return syncGoogleCalendar(token.accessToken);
        })
        .then(() => toast({ title: "Google connected", description: "Meetings were synced from your Gmail calendar." }))
        .catch((syncError: unknown) => {
          const message = syncError instanceof Error ? syncError.message : "Gmail sync failed.";
          setCalendarStatus({ provider: "google", connected: false, lastSync: null, error: message });
          toast({ title: "Calendar sync failed", description: message, variant: "destructive" });
          clearGoogleToken();
          clearGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY);
          clearGoogleAuthValue(GOOGLE_AUTH_STATE_KEY);
            });
      return;
    }

    if (code && !connected) {
      // Try to connect first, then exchange code
      pendingCalendarConnectRef.current = true;
      connect();
      return;
    }

    if (pendingAuth) {
      clearGoogleAuthValue(GOOGLE_AUTH_PENDING_KEY);
      clearGoogleAuthValue(GOOGLE_AUTH_STATE_KEY);
      setCalendarStatus({
        provider: "google",
        connected: false,
        lastSync: null,
        error: "Google sign-in did not return an authorization code. Please try again.",
      });
    }
  }, [connected, send, syncGoogleCalendar, connect]);

  useEffect(() => {
    const token = loadGoogleToken();
    if (!token) return;
    syncGoogleCalendar(token.accessToken).catch(() => {
      clearGoogleToken();
    });
  }, [syncGoogleCalendar]);

  return (
    <PrivacyContext.Provider
      value={{
        features,
        connected,
        lastSynced,
        connecting,
        connectionError,
        buttonMapping: buttonMappingLocal,
        settings,
        daemonDemoMode,
        daemonAvatarConfig,
        toggleFeature,
        connect,
        disconnect,
        setButtonMapping,
        updateSettings,
        sendAvatarConfig,
        studyLogs,
        clearStudyLogs,
        exportStudyLogs,
        calendarStatus,
        calendarEvents,
        calendarRecommendation,
        connectGoogleCalendar,
        disconnectGoogleCalendar,
        refreshCalendar,
        networkTrust,
      }}
    >
      {children}
    </PrivacyContext.Provider>
  );
};
