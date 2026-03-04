import { usePrivacy } from "@/context/PrivacyContext";
import { Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

export const ConnectionModal = () => {
  const { connecting } = usePrivacy();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!connecting) {
      setElapsed(0);
      return;
    }
    const interval = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => clearInterval(interval);
  }, [connecting]);

  return (
    <AnimatePresence>
      {connecting && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/30 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="bg-card rounded-3xl shadow-2xl p-8 flex flex-col items-center gap-5 min-w-[300px] border border-border"
          >
            <Loader2 className="w-10 h-10 text-primary animate-spin" />
            <div className="text-center">
              <p className="font-semibold text-foreground">Connecting to PrivacyDeck daemon...</p>
              <p className="text-sm text-muted-foreground mt-1">Please wait</p>
              {elapsed >= 5 && (
                <p className="text-xs text-amber-500 mt-2">
                  Taking longer than expected. Ensure the daemon is running on port 50556.
                </p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
