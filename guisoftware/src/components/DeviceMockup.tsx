import { usePrivacy } from "@/context/PrivacyContext";
import { FeatureIcon } from "@/components/FeatureIcon";
import { cn } from "@/lib/utils";

export const DeviceMockup = () => {
  const { features } = usePrivacy();
  const displayFeatures = features.slice(0, 8);

  return (
    <div className="mb-8">
      <div className="bg-device rounded-2xl p-8 flex flex-col items-center shadow-lg border border-device-inactive/20">
        {/* Device label */}
        <div className="text-[11px] text-device-inactive font-medium tracking-[0.15em] uppercase mb-5">
          PrivacyDeck Pro
        </div>

        {/* Button grid */}
        <div className="grid grid-cols-4 grid-rows-2 gap-3 mb-4">
          {displayFeatures.map(f => (
            <div
              key={f.id}
              className={cn(
                "w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 border",
                f.active
                  ? "bg-device-active/15 border-device-active/60 text-device-active shadow-[0_0_20px_hsl(221,80%,56%/0.3)]"
                  : "bg-device-inactive/40 border-device-inactive/30 text-device-inactive"
              )}
            >
              <FeatureIcon name={f.icon} className="w-5 h-5" />
            </div>
          ))}
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-[11px] text-device-inactive mt-1">
          <div className="w-[5px] h-[5px] rounded-full bg-device-active animate-pulse" />
          <span>Device Preview</span>
        </div>
      </div>
    </div>
  );
};
