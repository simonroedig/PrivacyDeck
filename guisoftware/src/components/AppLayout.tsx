import { MacOSChrome } from "@/components/MacOSChrome";
import { AppSidebar } from "@/components/AppSidebar";
import { ConnectionModal } from "@/components/ConnectionModal";
import { useIsMobile } from "@/hooks/use-mobile";
import { useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Menu } from "lucide-react";
import { useState } from "react";

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout = ({ children }: AppLayoutProps) => {
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="h-screen flex flex-col overflow-hidden rounded-xl border border-chrome-border shadow-2xl bg-background">
      <MacOSChrome onMenuToggle={isMobile ? () => setSidebarOpen(!sidebarOpen) : undefined} />
      <div className="flex flex-1 overflow-hidden relative">
        {/* Sidebar — always visible on desktop, overlay on mobile */}
        {isMobile ? (
          <>
            {sidebarOpen && (
              <div className="absolute inset-0 z-40 flex">
                <AppSidebar onNavigate={() => setSidebarOpen(false)} />
                <div
                  className="flex-1 bg-foreground/20 backdrop-blur-sm"
                  onClick={() => setSidebarOpen(false)}
                />
              </div>
            )}
          </>
        ) : (
          <AppSidebar />
        )}
        <main className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={location.pathname}
              className="px-4 py-6 sm:px-6 md:px-8"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.18, ease: [0.4, 0, 0.2, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
      <ConnectionModal />
    </div>
  );
};
