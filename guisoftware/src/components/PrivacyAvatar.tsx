import { useAvatar, AvatarConfig } from "@/context/AvatarContext";
import { usePrivacy, EXPOSURE_FEATURE_IDS, PROTECTION_FEATURE_IDS } from "@/context/PrivacyContext";
import { cn } from "@/lib/utils";
import { useMemo } from "react";

export const FEATURE_BODY_PART: Record<string, string> = {
  "camera-control": "eyes",
  "camera-preview": "eyes",
  "mic-control": "mouth",
  "audio-meter": "ears",
  "usb-lock": "arms",
  "network": "torso",
  "gps": "feet",
  "clipboard": "hands",
  "presentation": "head",
  "browser-clean": "antenna",
};

interface Props {
  size?: number;
  configOverride?: AvatarConfig;
  className?: string;
  showLabels?: boolean;
  highlightedPart?: string | null;
  showButtonNumbers?: boolean;
}

export const PrivacyAvatar = ({
  size = 80,
  configOverride,
  className,
  showLabels = false,
  highlightedPart = null,
  showButtonNumbers = false,
}: Props) => {
  let config: AvatarConfig;
  try {
    const ctx = useAvatar();
    config = configOverride ?? ctx.config;
  } catch {
    config = configOverride ?? {
      bodyShape: "compact",
      colorScheme: "shieldBlue",
      primaryColor: "#2563EB",
      accentColor: "#1E3A5F",
      faceStyle: "friendly",
      accessories: [],
      name: "JamesBot",
      animationStyle: "reactive",
    };
  }

  const { features, buttonMapping } = usePrivacy();

  // Compute same privacy score as Overview for avatar vitality
  const privacyScore = useMemo(() => {
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

  const isDead = privacyScore === 0;
  const isLow = privacyScore > 0 && privacyScore < 30;
  const isMid = privacyScore >= 30 && privacyScore < 70;

  const cameraActive = features.find(f => f.id === "camera-control")?.active ?? false;
  const micActive = features.find(f => f.id === "mic-control")?.active ?? false;
  const audioActive = features.find(f => f.id === "audio-meter")?.active ?? false;
  const usbActive = features.find(f => f.id === "usb-lock")?.active ?? false;
  const networkActive = features.find(f => f.id === "network")?.active ?? false;
  const gpsActive = features.find(f => f.id === "gps")?.active ?? false;

  const { primaryColor, accentColor, bodyShape, faceStyle, accessories } = config;
  const hasSunglasses = accessories.includes("sunglasses");
  const hasTopHat = accessories.includes("topHat");
  const hasScarf = accessories.includes("scarf");
  const hasStarBadge = accessories.includes("starBadge");
  const hasAntenna = accessories.includes("antenna");
  const hasKey = accessories.includes("key");

  const cx = 60;
  const vb = bodyShape === "tall" ? "0 0 120 220" : "0 0 120 180";

  // Glow colors for active features
  // Camera active = RED (danger — being recorded)
  // Mic active    = ORANGE/RED (danger — being listened to)
  // Protections active = GREEN (safe)
  const eyeGlow = cameraActive ? "#EF4444" : highlightedPart === "eyes" ? "#60A5FA" : null;
  const earGlow = (micActive || audioActive) ? "#F97316" : highlightedPart === "ears" ? "#60A5FA" : null;
  const mouthGlow = micActive ? "#EF4444" : highlightedPart === "mouth" ? "#60A5FA" : null;
  // Protections active = GREEN glow (safe state)
  const armGlow = usbActive ? "#10B981" : highlightedPart === "arms" ? "#60A5FA" : null;
  const armGlowFilter = usbActive ? "url(#av-glow-green)" : highlightedPart === "arms" ? "url(#av-glow-blue)" : undefined;
  const torsoGlow = networkActive ? "#10B981" : highlightedPart === "torso" ? "#60A5FA" : null;
  const torsoGlowFilter = networkActive ? "url(#av-glow-green)" : highlightedPart === "torso" ? "url(#av-glow-blue)" : undefined;
  const feetGlow = gpsActive ? "#10B981" : highlightedPart === "feet" ? "#60A5FA" : null;
  const feetGlowFilter = gpsActive ? "url(#av-glow-green)" : highlightedPart === "feet" ? "url(#av-glow-blue)" : undefined;
  const headGlow = highlightedPart === "head" ? "#60A5FA" : null;

  // When camera is active, override display color to red for danger signalling
  const eyeDisplayColor = cameraActive ? "#EF4444" : (eyeGlow || primaryColor);
  const mouthDisplayColor = mouthGlow || primaryColor;

  const height = size * (bodyShape === "tall" ? 1.83 : 1.5);

  // Button number badges
  const BUTTON_COLORS = ["#84CC16", "#22C55E", "#EAB308", "#F97316"];

  // Health bar color based on score
  const healthColor = isDead ? "#EF4444" : isLow ? "#EF4444" : isMid ? "#F59E0B" : "#10B981";
  // Avatar body opacity pulses when dead
  const bodyOpacity = isDead ? 0.35 : isLow ? 0.6 : 1;

  return (
    <div
      className={cn(
        bodyShape === "floating" && "animate-avatar-float",
        config.animationStyle === "lively" && "animate-avatar-breathe",
        className,
      )}
    >
      <svg
        width={size}
        height={height}
        viewBox={vb}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        overflow="visible"
      >
        <defs>
          <filter id="av-glow-green" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-orange" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-red" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-blue" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-purple" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-pink" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="av-glow-cyan" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <radialGradient id="av-bg-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={primaryColor} stopOpacity="0.12" />
            <stop offset="100%" stopColor={primaryColor} stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Ambient background glow */}
        <ellipse
          cx={cx}
          cy={bodyShape === "tall" ? 110 : 90}
          rx="55"
          ry={bodyShape === "tall" ? 100 : 80}
          fill="url(#av-bg-glow)"
          opacity={bodyOpacity}
        />

        {/* ============ HEALTH BAR ============ */}
        {showLabels && (
          <g>
            {/* Health bar background */}
            <rect
              x={cx - 22}
              y={bodyShape === "tall" ? 196 : bodyShape === "compact" ? 152 : 132}
              width="44"
              height="5"
              rx="2.5"
              fill="#1F2937"
              opacity="0.5"
            />
            {/* Health bar fill */}
            <rect
              x={cx - 22}
              y={bodyShape === "tall" ? 196 : bodyShape === "compact" ? 152 : 132}
              width={Math.max(2, (privacyScore / 100) * 44)}
              height="5"
              rx="2.5"
              fill={healthColor}
              opacity="0.9"
            >
              <animate
                attributeName="width"
                from={Math.max(2, (privacyScore / 100) * 44)}
                to={Math.max(2, (privacyScore / 100) * 44)}
                dur="0.5s"
                fill="freeze"
              />
              {isDead && (
                <animate attributeName="opacity" values="0.9;0.3;0.9" dur="1s" repeatCount="indefinite" />
              )}
            </rect>
            {/* Score text */}
            <text
              x={cx}
              y={bodyShape === "tall" ? 208 : bodyShape === "compact" ? 164 : 144}
              textAnchor="middle"
              fontSize="6"
              fontWeight="bold"
              fill={healthColor}
              opacity="0.9"
            >
              {isDead ? "CRITICAL" : `${privacyScore}% HP`}
            </text>
          </g>
        )}

        {/* ============ BODY GROUP — vitality opacity ============ */}
        <g opacity={bodyOpacity} style={{ transition: "opacity 0.5s ease" }}>

        {/* ============ ANTENNA ============ */}
        {hasAntenna ? (
          <g>
            <line x1={cx} y1="8" x2={cx} y2="28" stroke={accentColor} strokeWidth="3" strokeLinecap="round" />
            <circle cx={cx} cy="6" r="5" fill={primaryColor} />
            <circle
              cx={cx}
              cy="6"
              r="2.5"
              fill={eyeDisplayColor}
              opacity="0.8"
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            >
              <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" repeatCount="indefinite" />
            </circle>
          </g>
        ) : (
          <g>
            <line x1={cx} y1="18" x2={cx} y2="28" stroke={accentColor} strokeWidth="2" strokeLinecap="round" />
            <circle cx={cx} cy="16" r="3" fill={primaryColor} />
          </g>
        )}

        {/* Top Hat */}
        {hasTopHat && (
          <g>
            <rect x={cx - 18} y="6" width="36" height="4" rx="2" fill={accentColor} />
            <rect x={cx - 12} y="-12" width="24" height="20" rx="3" fill={accentColor} />
            <rect x={cx - 12} y="-2" width="24" height="3" rx="1" fill={primaryColor} opacity="0.4" />
          </g>
        )}

        {/* ============ HEAD ============ */}
        <ellipse
          cx={cx}
          cy="42"
          rx="28"
          ry="24"
          fill={primaryColor}
          opacity="0.15"
          stroke={headGlow || primaryColor}
          strokeWidth={headGlow ? 2.5 : 2}
          filter={headGlow ? "url(#av-glow-blue)" : undefined}
        />

        {/* ============ EARS ============ */}
        {/* --- Left ear --- */}
        <g>
          {/* Outer ear glow halo when mic active */}
          {earGlow && (
            <ellipse
              cx={cx - 32}
              cy="40"
              rx="11"
              ry="16"
              fill={earGlow}
              opacity="0.25"
              filter="url(#av-glow-orange)"
            >
              <animate attributeName="opacity" values="0.25;0.5;0.25" dur="0.7s" repeatCount="indefinite" />
            </ellipse>
          )}
          <ellipse
            cx={cx - 32}
            cy="40"
            rx="6"
            ry="10"
            fill={earGlow || primaryColor}
            opacity={earGlow ? 0.75 : 0.2}
            stroke={earGlow || primaryColor}
            strokeWidth={earGlow ? 2 : 1.5}
            filter={earGlow ? "url(#av-glow-orange)" : undefined}
          >
            {earGlow && (
              <animate attributeName="opacity" values="0.75;1;0.75" dur="0.7s" repeatCount="indefinite" />
            )}
          </ellipse>
          {/* Inner ear highlight */}
          {earGlow && (
            <ellipse cx={cx - 32} cy="40" rx="2.5" ry="5" fill="white" opacity="0.5" />
          )}
          {/* LED dot on ear */}
          <circle
            cx={cx - 32}
            cy="34"
            r="2"
            fill={earGlow ? earGlow : "#374151"}
            filter={earGlow ? "url(#av-glow-orange)" : undefined}
          >
            {earGlow && (
              <animate attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite" />
            )}
          </circle>
        </g>

        {/* --- Right ear --- */}
        <g>
          {earGlow && (
            <ellipse
              cx={cx + 32}
              cy="40"
              rx="11"
              ry="16"
              fill={earGlow}
              opacity="0.25"
              filter="url(#av-glow-orange)"
            >
              <animate attributeName="opacity" values="0.25;0.5;0.25" dur="0.7s" repeatCount="indefinite" begin="0.1s" />
            </ellipse>
          )}
          <ellipse
            cx={cx + 32}
            cy="40"
            rx="6"
            ry="10"
            fill={earGlow || primaryColor}
            opacity={earGlow ? 0.75 : 0.2}
            stroke={earGlow || primaryColor}
            strokeWidth={earGlow ? 2 : 1.5}
            filter={earGlow ? "url(#av-glow-orange)" : undefined}
          >
            {earGlow && (
              <animate attributeName="opacity" values="0.75;1;0.75" dur="0.7s" repeatCount="indefinite" begin="0.1s" />
            )}
          </ellipse>
          {earGlow && (
            <ellipse cx={cx + 32} cy="40" rx="2.5" ry="5" fill="white" opacity="0.5" />
          )}
          <circle
            cx={cx + 32}
            cy="34"
            r="2"
            fill={earGlow ? earGlow : "#374151"}
            filter={earGlow ? "url(#av-glow-orange)" : undefined}
          >
            {earGlow && (
              <animate attributeName="opacity" values="1;0.3;1" dur="0.6s" repeatCount="indefinite" begin="0.1s" />
            )}
          </circle>
        </g>

        {/* Sound wave arcs when mic active */}
        {(micActive || audioActive) && (
          <>
            <path
              d={`M ${cx - 42} 35 Q ${cx - 47} 40 ${cx - 42} 45`}
              stroke="#F97316"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
            >
              <animate attributeName="opacity" values="0;0.9;0" dur="0.7s" repeatCount="indefinite" />
            </path>
            <path
              d={`M ${cx - 47} 31 Q ${cx - 54} 40 ${cx - 47} 49`}
              stroke="#F97316"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
            >
              <animate attributeName="opacity" values="0;0.7;0" dur="0.7s" repeatCount="indefinite" begin="0.15s" />
            </path>
            <path
              d={`M ${cx + 42} 35 Q ${cx + 47} 40 ${cx + 42} 45`}
              stroke="#F97316"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
            >
              <animate attributeName="opacity" values="0;0.9;0" dur="0.7s" repeatCount="indefinite" />
            </path>
            <path
              d={`M ${cx + 47} 31 Q ${cx + 54} 40 ${cx + 47} 49`}
              stroke="#F97316"
              strokeWidth="1.5"
              fill="none"
              strokeLinecap="round"
            >
              <animate attributeName="opacity" values="0;0.7;0" dur="0.7s" repeatCount="indefinite" begin="0.15s" />
            </path>
          </>
        )}

        {/* ============ FACE / EYES ============ */}
        {hasSunglasses ? (
          <g>
            <rect x={cx - 22} y="33" width="18" height="12" rx="3" fill="#1F2937" stroke={accentColor} strokeWidth="1.5" />
            <rect x={cx + 4} y="33" width="18" height="12" rx="3" fill="#1F2937" stroke={accentColor} strokeWidth="1.5" />
            <line x1={cx - 4} y1="39" x2={cx + 4} y2="39" stroke={accentColor} strokeWidth="1.5" />
            <line x1={cx - 22} y1="36" x2={cx - 32} y2="34" stroke={accentColor} strokeWidth="1" />
            <line x1={cx + 22} y1="36" x2={cx + 32} y2="34" stroke={accentColor} strokeWidth="1" />
            {cameraActive && (
              <>
                <rect
                  x={cx - 23}
                  y="32"
                  width="20"
                  height="14"
                  rx="4"
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="2"
                  filter="url(#av-glow-red)"
                >
                  <animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite" />
                </rect>
                <rect
                  x={cx + 3}
                  y="32"
                  width="20"
                  height="14"
                  rx="4"
                  fill="none"
                  stroke="#EF4444"
                  strokeWidth="2"
                  filter="url(#av-glow-red)"
                >
                  <animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite" />
                </rect>
              </>
            )}
          </g>
        ) : faceStyle === "professional" ? (
          <g>
            <rect x={cx - 20} y="35" width="14" height="8" rx="2" fill="white" stroke={eyeDisplayColor} strokeWidth="1.5" filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <rect x={cx - 16} y="37" width="6" height="4" rx="1" fill={eyeDisplayColor} filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <rect x={cx + 6} y="35" width="14" height="8" rx="2" fill="white" stroke={eyeDisplayColor} strokeWidth="1.5" filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <rect x={cx + 10} y="37" width="6" height="4" rx="1" fill={eyeDisplayColor} filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            {cameraActive && (
              <>
                <rect x={cx - 22} y="33" width="18" height="12" rx="4" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="opacity" values="1;0.1;1" dur="1.4s" repeatCount="indefinite" />
                </rect>
                <rect x={cx + 4} y="33" width="18" height="12" rx="4" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="opacity" values="1;0.1;1" dur="1.4s" repeatCount="indefinite" />
                </rect>
              </>
            )}
          </g>
        ) : faceStyle === "expressive" ? (
          <g>
            <path
              d={`M ${cx - 22} 28 Q ${cx - 14} 24 ${cx - 6} 28`}
              stroke={eyeDisplayColor}
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            />
            <path
              d={`M ${cx + 6} 28 Q ${cx + 14} 24 ${cx + 22} 28`}
              stroke={eyeDisplayColor}
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            />
            {/* Camera active danger rings — expressive style */}
            {cameraActive && (
              <>
                <circle cx={cx - 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="10;22;22" dur="1.4s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.4s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx - 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="10;22;22" dur="1.4s" begin="0.45s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.4s" begin="0.45s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx + 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="10;22;22" dur="1.4s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.4s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx + 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="10;22;22" dur="1.4s" begin="0.45s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.4s" begin="0.45s" repeatCount="indefinite" />
                </circle>
              </>
            )}
            <ellipse cx={cx - 14} cy="40" rx="10" ry="11" fill={cameraActive ? "#10B981" : "white"} fillOpacity={cameraActive ? 0.2 : 1} stroke={eyeDisplayColor} strokeWidth="1.5" filter={eyeGlow ? "url(#av-glow-green)" : undefined}>
              {!cameraActive && <animate attributeName="ry" values="11;1;11" dur="4s" repeatCount="indefinite" begin="2s" />}
            </ellipse>
            <circle cx={cx - 14} cy="40" r={cameraActive ? 6 : 5} fill={eyeDisplayColor} filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <circle cx={cx - 16} cy="38" r="1.5" fill="white" opacity="0.8" />
            <ellipse cx={cx + 14} cy="40" rx="10" ry="11" fill={cameraActive ? "#10B981" : "white"} fillOpacity={cameraActive ? 0.2 : 1} stroke={eyeDisplayColor} strokeWidth="1.5" filter={eyeGlow ? "url(#av-glow-green)" : undefined}>
              {!cameraActive && <animate attributeName="ry" values="11;1;11" dur="4s" repeatCount="indefinite" begin="2s" />}
            </ellipse>
            <circle cx={cx + 14} cy="40" r={cameraActive ? 6 : 5} fill={eyeDisplayColor} filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <circle cx={cx + 12} cy="38" r="1.5" fill="white" opacity="0.8" />
          </g>
        ) : (
          /* ---- Friendly (default) ---- */
          <g>
            {/* Eyebrows */}
            <path d={`M ${cx - 22} 30 Q ${cx - 14} 26 ${cx - 6} 30`} stroke={eyeDisplayColor} strokeWidth="1.5" strokeLinecap="round" fill="none" filter={eyeGlow ? "url(#av-glow-green)" : undefined} />
            <path d={`M ${cx + 6} 30 Q ${cx + 14} 26 ${cx + 22} 30`} stroke={eyeDisplayColor} strokeWidth="1.5" strokeLinecap="round" fill="none" filter={eyeGlow ? "url(#av-glow-green)" : undefined} />

            {/* Pulsing danger rings when camera active — RED = being recorded */}
            {cameraActive && (
              <>
                <circle cx={cx - 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx - 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" begin="0.43s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" begin="0.43s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx - 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="1.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" begin="0.86s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" begin="0.86s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx + 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx + 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="2" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" begin="0.43s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" begin="0.43s" repeatCount="indefinite" />
                </circle>
                <circle cx={cx + 14} cy="40" r="0" fill="none" stroke="#EF4444" strokeWidth="1.5" filter="url(#av-glow-red)">
                  <animate attributeName="r" values="9;24;24" dur="1.3s" begin="0.86s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.9;0;0" dur="1.3s" begin="0.86s" repeatCount="indefinite" />
                </circle>
              </>
            )}

            {/* Eyes */}
            <ellipse
              cx={cx - 14}
              cy="40"
              rx="8"
              ry="9"
              fill={cameraActive ? "#10B981" : "white"}
              fillOpacity={cameraActive ? 0.25 : 1}
              stroke={eyeDisplayColor}
              strokeWidth={cameraActive ? 2 : 1.5}
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            >
              {!cameraActive && (
                <animate attributeName="ry" values="9;1;9" dur="4s" repeatCount="indefinite" begin="2s" />
              )}
            </ellipse>
            <circle
              cx={cx - 14}
              cy="40"
              r={cameraActive ? 5 : 4}
              fill={eyeDisplayColor}
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            />
            <circle cx={cx - 16} cy="38" r="1.2" fill="white" opacity="0.8" />

            <ellipse
              cx={cx + 14}
              cy="40"
              rx="8"
              ry="9"
              fill={cameraActive ? "#10B981" : "white"}
              fillOpacity={cameraActive ? 0.25 : 1}
              stroke={eyeDisplayColor}
              strokeWidth={cameraActive ? 2 : 1.5}
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            >
              {!cameraActive && (
                <animate attributeName="ry" values="9;1;9" dur="4s" repeatCount="indefinite" begin="2s" />
              )}
            </ellipse>
            <circle
              cx={cx + 14}
              cy="40"
              r={cameraActive ? 5 : 4}
              fill={eyeDisplayColor}
              filter={eyeGlow ? "url(#av-glow-green)" : undefined}
            />
            <circle cx={cx + 12} cy="38" r="1.2" fill="white" opacity="0.8" />
          </g>
        )}

        {/* Camera LED indicators above eyes — RED when recording (like real camera LEDs) */}
        <circle
          cx={cx - 14}
          cy="27"
          r="2.5"
          fill={cameraActive ? "#EF4444" : "#374151"}
          filter={cameraActive ? "url(#av-glow-red)" : undefined}
        >
          {cameraActive && (
            <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" />
          )}
        </circle>
        <circle
          cx={cx + 14}
          cy="27"
          r="2.5"
          fill={cameraActive ? "#EF4444" : "#374151"}
          filter={cameraActive ? "url(#av-glow-red)" : undefined}
        >
          {cameraActive && (
            <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite" begin="0.5s" />
          )}
        </circle>

        {/* Nose */}
        <ellipse cx={cx} cy="51" rx="2.5" ry="2" fill={primaryColor} opacity="0.25" />

        {/* ============ MOUTH ============ */}
        {faceStyle === "professional" ? (
          <line
            x1={cx - 8}
            y1="57"
            x2={cx + 8}
            y2="57"
            stroke={mouthDisplayColor}
            strokeWidth="2"
            strokeLinecap="round"
            filter={mouthGlow ? "url(#av-glow-red)" : undefined}
          />
        ) : micActive ? (
          /* Animated talking mouth */
          <g>
            {/* Glow halo behind mouth */}
            <ellipse cx={cx} cy="58" rx="14" ry="7" fill="#EF4444" opacity="0.15" filter="url(#av-glow-red)" />
            {/* Outer lip path */}
            <path
              d={`M ${cx - 11} 54 Q ${cx} 65 ${cx + 11} 54`}
              stroke="#EF4444"
              strokeWidth="2.5"
              strokeLinecap="round"
              fill="#EF444430"
              filter="url(#av-glow-red)"
            >
              <animate
                attributeName="d"
                values={`M ${cx-11} 54 Q ${cx} 65 ${cx+11} 54;M ${cx-11} 55 Q ${cx} 60 ${cx+11} 55;M ${cx-11} 54 Q ${cx} 65 ${cx+11} 54`}
                dur="0.35s"
                repeatCount="indefinite"
              />
            </path>
            {/* Animated sound bars inside */}
            <rect x={cx - 6} y="55" width="2.5" height="4" rx="1" fill="white" opacity="0.7">
              <animate attributeName="height" values="4;7;4;2;4" dur="0.3s" repeatCount="indefinite" />
              <animate attributeName="y" values="55;53;55;57;55" dur="0.3s" repeatCount="indefinite" />
            </rect>
            <rect x={cx - 1.25} y="54" width="2.5" height="6" rx="1" fill="white" opacity="0.7">
              <animate attributeName="height" values="6;2;6;4;6" dur="0.3s" repeatCount="indefinite" begin="0.1s" />
              <animate attributeName="y" values="54;57;54;56;54" dur="0.3s" repeatCount="indefinite" begin="0.1s" />
            </rect>
            <rect x={cx + 3.5} y="55" width="2.5" height="4" rx="1" fill="white" opacity="0.7">
              <animate attributeName="height" values="4;6;4;2;4" dur="0.3s" repeatCount="indefinite" begin="0.2s" />
              <animate attributeName="y" values="55;54;55;57;55" dur="0.3s" repeatCount="indefinite" begin="0.2s" />
            </rect>
          </g>
        ) : (
          <path
            d={cameraActive ? `M ${cx - 9} 57 Q ${cx} 62 ${cx + 9} 57` : `M ${cx - 10} 58 Q ${cx} 52 ${cx + 10} 58`}
            stroke={mouthDisplayColor}
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
          />
        )}

        {/* ============ SCARF ============ */}
        {hasScarf && (
          <g>
            <path d={`M ${cx - 24} 62 Q ${cx} 72 ${cx + 24} 62`} fill={accentColor} opacity="0.8" />
            <path d={`M ${cx + 10} 66 Q ${cx + 14} 78 ${cx + 8} 82`} fill={accentColor} opacity="0.6" stroke={accentColor} strokeWidth="1" />
          </g>
        )}

        {/* Neck */}
        <rect x={cx - 6} y="63" width="12" height="8" rx="3" fill={primaryColor} opacity="0.2" />

        {/* ============ TORSO ============ */}
        {bodyShape === "compact" ? (
          <rect
            x={cx - 28}
            y="70"
            width="56"
            height="50"
            rx="14"
            fill={torsoGlow || primaryColor}
            opacity={torsoGlow ? 0.2 : 0.12}
            stroke={torsoGlow || primaryColor}
            strokeWidth="2"
            filter={torsoGlow ? "url(#av-glow-cyan)" : undefined}
          >
            {torsoGlow && (
              <animate attributeName="opacity" values="0.2;0.08;0.2" dur="2s" repeatCount="indefinite" />
            )}
          </rect>
        ) : bodyShape === "tall" ? (
          <rect
            x={cx - 22}
            y="70"
            width="44"
            height="80"
            rx="10"
            fill={torsoGlow || primaryColor}
            opacity={torsoGlow ? 0.2 : 0.12}
            stroke={torsoGlow || primaryColor}
            strokeWidth="2"
            filter={torsoGlow ? "url(#av-glow-cyan)" : undefined}
          >
            {torsoGlow && (
              <animate attributeName="opacity" values="0.2;0.08;0.2" dur="2s" repeatCount="indefinite" />
            )}
          </rect>
        ) : (
          <rect
            x={cx - 26}
            y="70"
            width="52"
            height="45"
            rx="12"
            fill={torsoGlow || primaryColor}
            opacity={torsoGlow ? 0.2 : 0.12}
            stroke={torsoGlow || primaryColor}
            strokeWidth="2"
            filter={torsoGlow ? "url(#av-glow-cyan)" : undefined}
          >
            {torsoGlow && (
              <animate attributeName="opacity" values="0.2;0.08;0.2" dur="2s" repeatCount="indefinite" />
            )}
          </rect>
        )}

        {/* Star Badge */}
        {hasStarBadge && (
          <g transform={`translate(${cx + 12}, 82)`}>
            <polygon points="0,-7 2,-2 7,-2 3,1 5,6 0,3 -5,6 -3,1 -7,-2 -2,-2" fill="#FBBF24" stroke="#F59E0B" strokeWidth="0.5" />
          </g>
        )}

        {/* ============ ARMS ============ */}
        {bodyShape === "compact" ? (
          <>
            <ellipse
              cx={cx - 34}
              cy="88"
              rx="8"
              ry="18"
              fill={armGlow || primaryColor}
              opacity={armGlow ? 0.3 : 0.1}
              stroke={armGlow || primaryColor}
              strokeWidth="1.5"
              filter={armGlow ? "url(#av-glow-purple)" : undefined}
            >
              {armGlow && (
                <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.4s" repeatCount="indefinite" />
              )}
            </ellipse>
            <ellipse
              cx={cx + 34}
              cy="88"
              rx="8"
              ry="18"
              fill={armGlow || primaryColor}
              opacity={armGlow ? 0.3 : 0.1}
              stroke={armGlow || primaryColor}
              strokeWidth="1.5"
              filter={armGlow ? "url(#av-glow-purple)" : undefined}
            >
              {armGlow && (
                <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.4s" repeatCount="indefinite" begin="0.2s" />
              )}
            </ellipse>
          </>
        ) : bodyShape === "tall" ? (
          <>
            <ellipse cx={cx - 28} cy="100" rx="7" ry="24" fill={armGlow || primaryColor} opacity={armGlow ? 0.3 : 0.1} stroke={armGlow || primaryColor} strokeWidth="1.5" filter={armGlow ? "url(#av-glow-purple)" : undefined} />
            <ellipse cx={cx + 28} cy="100" rx="7" ry="24" fill={armGlow || primaryColor} opacity={armGlow ? 0.3 : 0.1} stroke={armGlow || primaryColor} strokeWidth="1.5" filter={armGlow ? "url(#av-glow-purple)" : undefined} />
          </>
        ) : (
          <>
            <ellipse cx={cx - 32} cy="86" rx="7" ry="16" fill={armGlow || primaryColor} opacity={armGlow ? 0.3 : 0.1} stroke={armGlow || primaryColor} strokeWidth="1.5" filter={armGlow ? "url(#av-glow-purple)" : undefined} />
            <ellipse cx={cx + 32} cy="86" rx="7" ry="16" fill={armGlow || primaryColor} opacity={armGlow ? 0.3 : 0.1} stroke={armGlow || primaryColor} strokeWidth="1.5" filter={armGlow ? "url(#av-glow-purple)" : undefined} />
          </>
        )}

        {/* Key accessory */}
        {hasKey && (
          <g transform={`translate(${cx - 16}, ${bodyShape === "tall" ? 140 : 112})`}>
            <rect x="0" y="0" width="3" height="12" rx="1" fill={accentColor} />
            <circle cx="1.5" cy="-2" r="4" fill="none" stroke={accentColor} strokeWidth="1.5" />
            <rect x="3" y="8" width="4" height="1.5" rx="0.5" fill={accentColor} />
          </g>
        )}

        {/* ============ LEGS / BASE ============ */}
        {bodyShape === "compact" ? (
          <>
            <rect
              x={cx - 14}
              y="118"
              width="12"
              height="22"
              rx="6"
              fill={feetGlow || primaryColor}
              opacity={feetGlow ? 0.3 : 0.1}
              stroke={feetGlow || primaryColor}
              strokeWidth="1.5"
              filter={feetGlow ? "url(#av-glow-pink)" : undefined}
            >
              {feetGlow && (
                <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.4s" repeatCount="indefinite" />
              )}
            </rect>
            <rect
              x={cx + 2}
              y="118"
              width="12"
              height="22"
              rx="6"
              fill={feetGlow || primaryColor}
              opacity={feetGlow ? 0.3 : 0.1}
              stroke={feetGlow || primaryColor}
              strokeWidth="1.5"
              filter={feetGlow ? "url(#av-glow-pink)" : undefined}
            >
              {feetGlow && (
                <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.4s" repeatCount="indefinite" begin="0.2s" />
              )}
            </rect>
            <ellipse cx={cx - 8} cy="142" rx="8" ry="4" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.4 : 0.15} filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
            <ellipse cx={cx + 8} cy="142" rx="8" ry="4" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.4 : 0.15} filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
          </>
        ) : bodyShape === "tall" ? (
          <>
            <rect x={cx - 12} y="148" width="10" height="32" rx="5" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.3 : 0.1} stroke={feetGlow || primaryColor} strokeWidth="1.5" filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
            <rect x={cx + 2} y="148" width="10" height="32" rx="5" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.3 : 0.1} stroke={feetGlow || primaryColor} strokeWidth="1.5" filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
            <ellipse cx={cx - 7} cy="182" rx="8" ry="4" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.4 : 0.15} filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
            <ellipse cx={cx + 7} cy="182" rx="8" ry="4" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.4 : 0.15} filter={feetGlow ? "url(#av-glow-pink)" : undefined} />
          </>
        ) : (
          <g>
            <ellipse cx={cx} cy="120" rx="22" ry="5" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.35 : 0.15} filter={feetGlow ? "url(#av-glow-pink)" : undefined}>
              <animate attributeName="opacity" values={feetGlow ? "0.35;0.15;0.35" : "0.15;0.08;0.15"} dur="2s" repeatCount="indefinite" />
            </ellipse>
            <ellipse cx={cx} cy="122" rx="16" ry="3" fill={feetGlow || primaryColor} opacity={feetGlow ? 0.25 : 0.1} filter={feetGlow ? "url(#av-glow-pink)" : undefined}>
              <animate attributeName="opacity" values={feetGlow ? "0.25;0.1;0.25" : "0.1;0.05;0.1"} dur="2s" repeatCount="indefinite" />
            </ellipse>
          </g>
        )}

        {/* ============ CLOSE BODY GROUP ============ */}
        </g>

        {/* ============ DEAD EYES OVERLAY (0% privacy) ============ */}
        {isDead && !hasSunglasses && (
          <g>
            {/* Desaturated overlay on face */}
            <ellipse cx={cx} cy="42" rx="28" ry="24" fill="#1F2937" opacity="0.15" />
            {/* XX Left eye */}
            <line x1={cx - 20} y1="34" x2={cx - 8} y2="46" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" filter="url(#av-glow-red)">
              <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
            </line>
            <line x1={cx - 8} y1="34" x2={cx - 20} y2="46" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" filter="url(#av-glow-red)">
              <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
            </line>
            {/* XX Right eye */}
            <line x1={cx + 8} y1="34" x2={cx + 20} y2="46" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" filter="url(#av-glow-red)">
              <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
            </line>
            <line x1={cx + 20} y1="34" x2={cx + 8} y2="46" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" filter="url(#av-glow-red)">
              <animate attributeName="opacity" values="1;0.4;1" dur="1.5s" repeatCount="indefinite" />
            </line>
            {/* Flat-line mouth */}
            <line x1={cx - 10} y1="57" x2={cx + 10} y2="57" stroke="#EF4444" strokeWidth="2.5" strokeLinecap="round" filter="url(#av-glow-red)">
              <animate attributeName="opacity" values="1;0.5;1" dur="2s" repeatCount="indefinite" />
            </line>
            {/* Dizzy swirl */}
            <circle cx={cx + 24} cy="28" r="0" fill="none" stroke="#EF4444" strokeWidth="1.5" opacity="0">
              <animate attributeName="r" values="0;8;0" dur="2s" repeatCount="indefinite" />
              <animate attributeName="opacity" values="0;0.6;0" dur="2s" repeatCount="indefinite" />
            </circle>
          </g>
        )}

        {/* ============ LOW HEALTH WARNING (< 30%) ============ */}
        {isLow && !isDead && showLabels && (
          <g>
            <rect x={cx - 22} y={bodyShape === "tall" ? 212 : bodyShape === "compact" ? 168 : 148} width="44" height="10" rx="3" fill="#EF4444" opacity="0.9">
              <animate attributeName="opacity" values="0.9;0.5;0.9" dur="1.2s" repeatCount="indefinite" />
            </rect>
            <text
              x={cx}
              y={bodyShape === "tall" ? 218 : bodyShape === "compact" ? 174 : 154}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="5.5"
              fontWeight="bold"
              fill="white"
            >
              ⚠ LOW HP
            </text>
          </g>
        )}

        {/* ============ BUTTON NUMBER BADGES ============ */}
        {showButtonNumbers &&
          buttonMapping.map((featureId, idx) => {
            const part = FEATURE_BODY_PART[featureId];
            const color = BUTTON_COLORS[idx];
            const offsets = [-10, -4, 4, 10];
            const baseX = cx + offsets[idx] * 1.5;
            let bx = 0, by = 0;
            switch (part) {
              case "eyes": bx = idx < 2 ? cx - 18 : cx + 18; by = 26; break;
              case "ears": bx = idx < 2 ? cx - 44 : cx + 44; by = 36; break;
              case "mouth": bx = baseX; by = 67; break;
              case "arms": bx = idx < 2 ? cx - 42 : cx + 42; by = 82; break;
              case "torso": bx = cx - 12 + idx * 8; by = 83; break;
              case "feet": bx = idx < 2 ? cx - 16 : cx + 16; by = 148; break;
              case "head": bx = cx - 12 + idx * 8; by = 22; break;
              default: bx = cx - 16 + idx * 11; by = 72;
            }
            return (
              <g key={idx} transform={`translate(${bx}, ${by})`}>
                <circle r="5.5" fill={color} stroke="white" strokeWidth="1" opacity="0.9" />
                <text
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="5.5"
                  fontWeight="bold"
                  fill="white"
                >
                  {idx + 1}
                </text>
              </g>
            );
          })}

        {/* ============ STATUS LABEL BADGES ============ */}
        {showLabels && cameraActive && (
          <g>
            {/* Red badge — camera ON = danger */}
            <rect x={cx - 26} y="15" width="52" height="11" rx="3" fill="#EF4444" opacity="0.93" />
            <text x={cx} y="22" textAnchor="middle" dominantBaseline="central" fontSize="6.5" fontWeight="bold" fill="white">
              ⚠ CAM EXPOSED
            </text>
          </g>
        )}
        {showLabels && micActive && (
          <g>
            <rect x={cx - 24} y="63" width="48" height="11" rx="3" fill="#EF4444" opacity="0.92" />
            <text x={cx} y="70" textAnchor="middle" dominantBaseline="central" fontSize="6.5" fontWeight="bold" fill="white">
              ● MIC ACTIVE
            </text>
          </g>
        )}
      </svg>
    </div>
  );
};
