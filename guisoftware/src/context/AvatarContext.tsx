import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

export interface AvatarConfig {
  bodyShape: "compact" | "tall" | "floating";
  colorScheme: string;
  primaryColor: string;
  accentColor: string;
  faceStyle: "friendly" | "professional" | "expressive";
  accessories: string[];
  name: string;
  animationStyle: "reactive" | "lively";
}

export const COLOR_PRESETS: Record<string, { primary: string; accent: string; label: string }> = {
  shieldBlue: { primary: "#2563EB", accent: "#1E3A5F", label: "Shield Blue" },
  stealthBlack: { primary: "#1F2937", accent: "#9CA3AF", label: "Stealth Black" },
  ghostWhite: { primary: "#F9FAFB", accent: "#D1D5DB", label: "Ghost White" },
  hackerGreen: { primary: "#065F46", accent: "#34D399", label: "Hacker Green" },
  sunsetRed: { primary: "#991B1B", accent: "#FCA5A5", label: "Sunset Red" },
  lavender: { primary: "#6D28D9", accent: "#C4B5FD", label: "Lavender" },
  sand: { primary: "#92400E", accent: "#FDE68A", label: "Sand" },
  custom: { primary: "#2563EB", accent: "#1E3A5F", label: "Custom" },
};

export const DEFAULT_CONFIG: AvatarConfig = {
  bodyShape: "compact",
  colorScheme: "shieldBlue",
  primaryColor: "#2563EB",
  accentColor: "#1E3A5F",
  faceStyle: "friendly",
  accessories: [],
  name: "JamesBot",
  animationStyle: "reactive",
};

interface AvatarState {
  config: AvatarConfig;
  updateConfig: (partial: Partial<AvatarConfig>) => void;
  replaceConfig: (next: AvatarConfig) => void;
  saveConfig: () => void;
  resetConfig: () => void;
  dirty: boolean;
}

const AvatarContext = createContext<AvatarState | null>(null);

const STORAGE_KEY = "privacydeck-avatar";

function loadConfig(): AvatarConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_CONFIG, ...JSON.parse(raw) };
  } catch {}
  return { ...DEFAULT_CONFIG };
}

export const useAvatar = () => {
  const ctx = useContext(AvatarContext);
  if (!ctx) throw new Error("useAvatar must be used within AvatarProvider");
  return ctx;
};

export const AvatarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [saved, setSaved] = useState<AvatarConfig>(loadConfig);
  const [config, setConfig] = useState<AvatarConfig>(loadConfig);
  const [dirty, setDirty] = useState(false);

  const updateConfig = useCallback((partial: Partial<AvatarConfig>) => {
    setConfig(prev => {
      const next = { ...prev, ...partial };
      setDirty(JSON.stringify(next) !== JSON.stringify(saved));
      return next;
    });
  }, [saved]);

  const saveConfig = useCallback(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    setSaved({ ...config });
    setDirty(false);
  }, [config]);

  const replaceConfig = useCallback((next: AvatarConfig) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setConfig({ ...next });
    setSaved({ ...next });
    setDirty(false);
  }, []);

  const resetConfig = useCallback(() => {
    setConfig({ ...DEFAULT_CONFIG });
    setDirty(JSON.stringify(DEFAULT_CONFIG) !== JSON.stringify(saved));
  }, [saved]);

  return (
    <AvatarContext.Provider value={{ config, updateConfig, replaceConfig, saveConfig, resetConfig, dirty }}>
      {children}
    </AvatarContext.Provider>
  );
};
