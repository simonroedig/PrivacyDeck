import { useAvatar, COLOR_PRESETS, DEFAULT_CONFIG, AvatarConfig } from "@/context/AvatarContext";
import { usePrivacy } from "@/context/PrivacyContext";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { MonitorSmartphone, Download } from "lucide-react";
import { useEffect, useRef } from "react";

const ACCESSORY_LIST = [
  { id: "topHat", label: "Top Hat" },
  { id: "sunglasses", label: "Sunglasses" },
  { id: "scarf", label: "Scarf" },
  { id: "starBadge", label: "Star Badge" },
  { id: "antenna", label: "Large Antenna" },
  { id: "key", label: "Key" },
];

const BODY_SHAPES: { id: AvatarConfig["bodyShape"]; label: string; desc: string }[] = [
  { id: "compact", label: "Compact", desc: "Short & round" },
  { id: "tall", label: "Tall", desc: "Slim & elongated" },
  { id: "floating", label: "Floating", desc: "Hovers in place" },
];

const FACE_STYLES: { id: AvatarConfig["faceStyle"]; label: string; desc: string }[] = [
  { id: "friendly", label: "Friendly", desc: "Round eyes, warm smile" },
  { id: "professional", label: "Professional", desc: "Visor eyes, neutral" },
  { id: "expressive", label: "Expressive", desc: "Animated eyebrows" },
];

interface Props {
  compact?: boolean;
}

export const AvatarCustomizer = ({ compact }: Props) => {
  const { config, updateConfig, replaceConfig, saveConfig, resetConfig, dirty } = useAvatar();

  const { connected, sendAvatarConfig, daemonAvatarConfig } = usePrivacy();

  const lastAppliedRemoteRef = useRef<string | null>(null);

  const toggleAccessory = (id: string) => {
    const next = config.accessories.includes(id)
      ? config.accessories.filter(a => a !== id)
      : [...config.accessories, id];
    updateConfig({ accessories: next });
  };

  const handleSave = () => {
    saveConfig();
    if (connected) {
      sendAvatarConfig(config);
      lastAppliedRemoteRef.current = JSON.stringify(config);
      toast({ title: "Avatar saved", description: "Saved locally and synced to device." });
    } else {
      toast({ title: "Avatar saved", description: "Your customization has been saved." });
    }
  };

  const handleLoadFromDevice = () => {
    if (daemonAvatarConfig) {
      replaceConfig(daemonAvatarConfig);
      lastAppliedRemoteRef.current = JSON.stringify(daemonAvatarConfig);

      toast({ title: "Loaded from device", description: "Avatar config synced from daemon." });
    }
  };


  useEffect(() => {
    if (!daemonAvatarConfig) return;
    const remote = JSON.stringify(daemonAvatarConfig);

    // Do not clobber in-progress local edits.
    if (dirty) return;

    // Apply remote config only once per distinct daemon payload.
    if (lastAppliedRemoteRef.current === remote) return;

    const local = JSON.stringify(config);
    if (local !== remote) {
      replaceConfig(daemonAvatarConfig);
    }
    lastAppliedRemoteRef.current = remote;
  }, [config, daemonAvatarConfig, dirty, replaceConfig]);

  const handleColorPreset = (key: string) => {
    if (key === "custom") {
      updateConfig({ colorScheme: "custom" });
    } else {
      const preset = COLOR_PRESETS[key];
      updateConfig({ colorScheme: key, primaryColor: preset.primary, accentColor: preset.accent });
    }
  };

  return (
    <div className={cn("flex flex-col", compact ? "gap-2" : "gap-0")}>
      <Accordion type="multiple" defaultValue={["body", "color", "face", "accessories", "name", "animation"]} className="w-full">
        {/* Body Shape */}
        <AccordionItem value="body">
          <AccordionTrigger className="text-sm font-semibold">Body Shape</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-3 gap-2">
              {BODY_SHAPES.map(s => (
                <button
                  key={s.id}
                  onClick={() => updateConfig({ bodyShape: s.id })}
                  className={cn(
                    "rounded-xl border-2 p-3 text-center transition-all",
                    config.bodyShape === s.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <div className="text-xs font-semibold text-foreground">{s.label}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">{s.desc}</div>
                </button>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Color */}
        <AccordionItem value="color">
          <AccordionTrigger className="text-sm font-semibold">Color Scheme</AccordionTrigger>
          <AccordionContent>
            <div className="flex flex-wrap gap-2 mb-3">
              {Object.entries(COLOR_PRESETS).map(([key, val]) => (
                <button
                  key={key}
                  onClick={() => handleColorPreset(key)}
                  title={val.label}
                  className={cn(
                    "w-8 h-8 rounded-full border-2 transition-all flex items-center justify-center",
                    config.colorScheme === key ? "border-primary ring-2 ring-primary/30" : "border-border"
                  )}
                >
                  {key === "custom" ? (
                    <span className="text-[9px] font-bold text-muted-foreground">+</span>
                  ) : (
                    <div className="w-5 h-5 rounded-full" style={{ background: `linear-gradient(135deg, ${val.primary} 50%, ${val.accent} 50%)` }} />
                  )}
                </button>
              ))}
            </div>
            {config.colorScheme === "custom" && (
              <div className="flex gap-3">
                <label className="flex-1">
                  <span className="text-xs text-muted-foreground">Primary</span>
                  <input
                    type="color"
                    value={config.primaryColor}
                    onChange={e => updateConfig({ primaryColor: e.target.value })}
                    className="w-full h-8 rounded border border-border cursor-pointer"
                  />
                </label>
                <label className="flex-1">
                  <span className="text-xs text-muted-foreground">Accent</span>
                  <input
                    type="color"
                    value={config.accentColor}
                    onChange={e => updateConfig({ accentColor: e.target.value })}
                    className="w-full h-8 rounded border border-border cursor-pointer"
                  />
                </label>
              </div>
            )}
          </AccordionContent>
        </AccordionItem>

        {/* Face */}
        <AccordionItem value="face">
          <AccordionTrigger className="text-sm font-semibold">Face Style</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-3 gap-2">
              {FACE_STYLES.map(s => (
                <button
                  key={s.id}
                  onClick={() => updateConfig({ faceStyle: s.id })}
                  className={cn(
                    "rounded-xl border-2 p-3 text-center transition-all",
                    config.faceStyle === s.id
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <div className="text-xs font-semibold text-foreground">{s.label}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">{s.desc}</div>
                </button>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Accessories */}
        <AccordionItem value="accessories">
          <AccordionTrigger className="text-sm font-semibold">Accessories</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2.5">
              {ACCESSORY_LIST.map(a => (
                <div key={a.id} className="flex items-center justify-between">
                  <span className="text-sm text-foreground">{a.label}</span>
                  <Switch
                    checked={config.accessories.includes(a.id)}
                    onCheckedChange={() => toggleAccessory(a.id)}
                  />
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Name */}
        <AccordionItem value="name">
          <AccordionTrigger className="text-sm font-semibold">Name</AccordionTrigger>
          <AccordionContent>
            <div className="space-y-1">
              <Input
                value={config.name}
                maxLength={12}
                onChange={e => updateConfig({ name: e.target.value })}
                placeholder="Name your avatar"
              />
              <span className="text-[10px] text-muted-foreground">{config.name.length}/12 characters</span>
            </div>
          </AccordionContent>
        </AccordionItem>

        {/* Animation */}
        <AccordionItem value="animation">
          <AccordionTrigger className="text-sm font-semibold">Animation Style</AccordionTrigger>
          <AccordionContent>
            <div className="grid grid-cols-2 gap-2">
              {(["reactive", "lively"] as const).map(style => (
                <button
                  key={style}
                  onClick={() => updateConfig({ animationStyle: style })}
                  className={cn(
                    "rounded-xl border-2 p-3 text-center transition-all",
                    config.animationStyle === style
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-muted-foreground/30"
                  )}
                >
                  <div className="text-xs font-semibold text-foreground capitalize">{style}</div>
                  <div className="text-[10px] text-muted-foreground mt-0.5">
                    {style === "reactive" ? "Animates on changes" : "Subtle idle motion"}
                  </div>
                </button>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      {/* Footer */}
      <div className={cn("flex flex-col gap-2 pt-4", compact ? "" : "sticky bottom-0 bg-background pb-2 border-t border-border mt-2")}>
        <div className="flex items-center gap-3">
          <Button onClick={handleSave} className="flex-1">
            <MonitorSmartphone className="w-3.5 h-3.5 mr-1.5" />
            {connected ? "Save & Sync to Device" : "Save Avatar"}
          </Button>
          <button onClick={resetConfig} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
            Reset
          </button>
        </div>
        {connected && daemonAvatarConfig && (
          <button
            onClick={handleLoadFromDevice}
            className="flex items-center justify-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors py-1"
          >
            <Download className="w-3 h-3" />
            Load from Device
          </button>
        )}
      </div>
    </div>
  );
};
