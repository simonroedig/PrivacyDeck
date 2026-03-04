import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PrivacyProvider } from "@/context/PrivacyContext";
import { AvatarProvider } from "@/context/AvatarContext";
import { AppLayout } from "@/components/AppLayout";
import Overview from "@/pages/Overview";
import Configuration from "@/pages/Configuration";
import AvatarPage from "@/pages/AvatarPage";
import SettingsPage from "@/pages/SettingsPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <PrivacyProvider>
        <AvatarProvider>
          <BrowserRouter>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Overview />} />
                <Route path="/avatar" element={<AvatarPage />} />
                <Route path="/configuration" element={<Configuration />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFound />} />
              </Routes>
            </AppLayout>
          </BrowserRouter>
        </AvatarProvider>
      </PrivacyProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
