import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface PrivacyAdvisorBubbleProps {
  message: string;
  isLoading: boolean;
  score: number;
  canRefresh?: boolean;
  onRefresh?: () => void;
  onDismiss?: () => void;
  className?: string;
}

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-[3px] h-[14px]">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="w-[5px] h-[5px] rounded-full bg-current"
          animate={{ opacity: [0.3, 1, 0.3], y: [0, -3, 0] }}
          transition={{
            duration: 0.9,
            repeat: Infinity,
            delay: i * 0.18,
            ease: "easeInOut",
          }}
        />
      ))}
    </span>
  );
}

export function PrivacyAdvisorBubble({
  message,
  isLoading,
  score,
  canRefresh = true,
  onRefresh,
  onDismiss,
  className,
}: PrivacyAdvisorBubbleProps) {
  const bubbleColor =
    score >= 75
      ? "from-emerald-500/10 to-emerald-500/5 border-emerald-500/20"
      : score >= 45
      ? "from-amber-500/10 to-amber-500/5 border-amber-500/20"
      : "from-red-500/10 to-red-500/5 border-red-500/20";

  const textColor =
    score >= 75
      ? "text-emerald-700 dark:text-emerald-400"
      : score >= 45
      ? "text-amber-700 dark:text-amber-400"
      : "text-red-700 dark:text-red-400";

  const iconColor =
    score >= 75
      ? "text-emerald-500"
      : score >= 45
      ? "text-amber-500"
      : "text-red-500";

  const tailColor =
    score >= 75
      ? "rgba(16,185,129,0.25)"
      : score >= 45
      ? "rgba(245,158,11,0.25)"
      : "rgba(239,68,68,0.25)";

  return (
    <div className={cn("relative flex items-start gap-2", className)}>
      {/* Left tail pointing toward avatar */}
      <div
        className="shrink-0 mt-3"
        aria-hidden
        style={{
          width: 0,
          height: 0,
          borderTop: "6px solid transparent",
          borderBottom: "6px solid transparent",
          borderRight: `8px solid ${tailColor}`,
        }}
      />

      {/* Bubble */}
      <div
        className={cn(
          "relative flex-1 rounded-2xl rounded-tl-sm border bg-gradient-to-br px-3 py-2.5 shadow-sm",
          bubbleColor
        )}
      >
        {/* Header row: icon + label + refresh + dismiss */}
        <div className="flex items-center gap-1 mb-1">
          <Sparkles className={cn("w-3 h-3 shrink-0", iconColor)} />
          <span className={cn("text-[9px] font-bold uppercase tracking-widest", iconColor)}>
            Privacy Advisor
          </span>

          <div className="ml-auto flex items-center gap-0.5">
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isLoading || !canRefresh}
                className={cn(
                  "p-0.5 rounded-md transition-opacity",
                  isLoading || !canRefresh
                    ? "opacity-30 cursor-not-allowed"
                    : "opacity-50 hover:opacity-100"
                )}
                aria-label="Refresh advice"
              >
                <motion.span
                  animate={isLoading ? { rotate: 360 } : { rotate: 0 }}
                  transition={
                    isLoading
                      ? { duration: 1, repeat: Infinity, ease: "linear" }
                      : { duration: 0 }
                  }
                  className="block"
                >
                  <RefreshCw className={cn("w-3 h-3", iconColor)} />
                </motion.span>
              </button>
            )}

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="p-0.5 rounded-md opacity-40 hover:opacity-80 transition-opacity"
                aria-label="Dismiss advisor"
              >
                <X className={cn("w-3 h-3", iconColor)} />
              </button>
            )}
          </div>
        </div>

        {/* Message body */}
        <div className={cn("text-[12px] font-medium leading-snug min-h-[18px]", textColor)}>
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.span
                key="typing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="flex items-center gap-1.5"
              >
                <TypingDots />
                <span className="text-[11px] font-normal opacity-60">Reflecting on your settings…</span>
              </motion.span>
            ) : (
              <motion.span
                key={message}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.25, ease: "easeOut" }}
                className="block"
              >
                {message}
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
