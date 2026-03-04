import { useState } from "react";
import { PrivacyAvatar } from "@/components/PrivacyAvatar";
import { AvatarCustomizer } from "@/components/AvatarCustomizer";
import { useAvatar } from "@/context/AvatarContext";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const VIEWS = [
  { label: "Front", rotate: 0 },
  { label: "Side", rotate: 90 },
  { label: "Back", rotate: 180 },
];

export default function AvatarPage() {
  const { config } = useAvatar();
  const [viewIdx, setViewIdx] = useState(0);

  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-xl font-bold tracking-tight text-foreground mb-1">My Avatar</h1>
        <p className="text-[13px] text-muted-foreground">Customize your PrivacyDeck robot companion</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
        {/* Preview */}
        <div className="md:col-span-2 flex flex-col items-center">
          <div className="bg-card rounded-2xl border border-border p-6 w-full flex flex-col items-center shadow-sm">
            <div style={{ perspective: "800px" }} className="mb-4">
              <div
                className="transition-transform duration-500"
                style={{ transform: `rotateY(${VIEWS[viewIdx].rotate}deg)` }}
              >
                <PrivacyAvatar size={140} />
              </div>
            </div>

            <div className="flex gap-1.5 mb-4">
              {VIEWS.map((v, i) => (
                <Button
                  key={v.label}
                  variant={viewIdx === i ? "default" : "outline"}
                  size="sm"
                  className="text-xs px-3 h-7"
                  onClick={() => setViewIdx(i)}
                >
                  {v.label}
                </Button>
              ))}
            </div>

            <span className="text-sm font-semibold text-foreground">{config.name || "Unnamed"}</span>
          </div>
        </div>

        {/* Controls */}
        <div className="md:col-span-3">
          <div className="bg-card rounded-2xl border border-border p-5 shadow-sm">
            <AvatarCustomizer />
          </div>
        </div>
      </div>
    </div>
  );
}
