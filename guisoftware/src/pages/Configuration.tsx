import { usePrivacy } from "@/context/PrivacyContext";
import { useState } from "react";
import { Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";
import { FeatureIcon } from "@/components/FeatureIcon";
import { DeviceMockup } from "@/components/DeviceMockup";
import { PrivacyAvatar, FEATURE_BODY_PART } from "@/components/PrivacyAvatar";

const BUTTON_COLORS = [
  "hsl(82, 85%, 40%)",
  "hsl(142, 71%, 45%)",
  "hsl(48, 96%, 53%)",
  "hsl(25, 95%, 53%)",
];

const BODY_PART_LABELS: Record<string, string> = {
  eyes: "Eyes (Camera)",
  ears: "Ears (Audio)",
  mouth: "Mouth (Mic)",
  arms: "Arms (USB)",
  torso: "Torso (Network)",
  feet: "Feet (GPS)",
  head: "Head (Presentation)",
  antenna: "Antenna (Browser)",
  hands: "Hands (Clipboard)",
};

export default function Configuration() {
  const { features, connected, buttonMapping, setButtonMapping } = usePrivacy();
  const { toast } = useToast();
  const [localMapping, setLocalMapping] = useState(buttonMapping);
  const [hoveredPart, setHoveredPart] = useState<string | null>(null);

  const handleSave = () => {
    setButtonMapping(localMapping);
    toast({
      title: "Configuration saved",
      description: "Synced to your PrivacyDeck device.",
    });
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-primary/10 flex items-center justify-center">
          <Settings2 className="w-7 h-7 text-primary" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-foreground mb-1">Configuration</h1>
        <p className="text-[13px] text-muted-foreground max-w-md mx-auto">
          Map features to your device’s physical buttons.
        </p>
      </div>

      {/* Device Mockup */}
      <DeviceMockup />

      {/* Two-column: buttons + avatar preview */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
        {/* Button mapping — 3 cols */}
        <div className="md:col-span-3 bg-card rounded-2xl border border-border p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-foreground mb-1">Quick-Action Buttons</h2>
          <p className="text-xs text-muted-foreground mb-5">
            Assign a feature to each button
          </p>
          <div className="space-y-3">
            {localMapping.map((featureId, idx) => {
              const mappedFeature = features.find(f => f.id === featureId);
              const bodyPart = FEATURE_BODY_PART[featureId] || null;
              return (
                <div
                  key={idx}
                  className="flex items-center gap-4 bg-muted/40 rounded-xl px-4 py-3 transition-all hover:bg-muted/60 cursor-default"
                  onMouseEnter={() => setHoveredPart(bodyPart)}
                  onMouseLeave={() => setHoveredPart(null)}
                >
                  <div
                    className="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-sm font-bold text-card shadow-sm"
                    style={{ backgroundColor: BUTTON_COLORS[idx] }}
                  >
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 mb-1">
                      <label className="text-xs text-muted-foreground font-medium">Button {idx + 1}</label>
                      {bodyPart && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                          → {BODY_PART_LABELS[bodyPart] || bodyPart}
                        </span>
                      )}
                    </div>
                    <select
                      value={featureId}
                      onChange={e => {
                        const next = [...localMapping];
                        next[idx] = e.target.value;
                        setLocalMapping(next);
                        setHoveredPart(FEATURE_BODY_PART[e.target.value] || null);
                      }}
                      className="w-full bg-card border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-shadow"
                    >
                      {features.map(f => (
                        <option key={f.id} value={f.id}>{f.name}</option>
                      ))}
                    </select>
                  </div>
                  {mappedFeature && (
                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                      <FeatureIcon name={mappedFeature.icon} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Avatar preview — 2 cols */}
        <div className="md:col-span-2 bg-card rounded-2xl border border-border p-5 flex flex-col items-center justify-center shadow-sm">
          <p className="text-xs text-muted-foreground mb-4 text-center">
            Hover a button to see which body part it controls
          </p>
          <PrivacyAvatar
            size={120}
            highlightedPart={hoveredPart}
            showButtonNumbers
          />
          {hoveredPart && (
            <div className="mt-3 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-semibold animate-fade-in">
              {BODY_PART_LABELS[hoveredPart] || hoveredPart}
            </div>
          )}
          {!hoveredPart && (
            <div className="mt-3 px-3 py-1.5 rounded-full bg-muted text-muted-foreground text-xs">
              All buttons shown
            </div>
          )}
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={!connected}
        className={cn(
          "w-full py-3.5 bg-primary text-primary-foreground rounded-2xl font-semibold text-[13px] transition-all",
          connected ? "hover:opacity-90 active:scale-[0.99] shadow-sm" : "opacity-50 cursor-not-allowed",
        )}
      >
        Save Configuration
      </button>
      {!connected && (
        <p className="text-xs text-muted-foreground text-center mt-2">Connect your device to save changes</p>
      )}
    </div>
  );
}
