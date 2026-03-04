import {
  Camera, Video, Volume2, Mic, ClipboardList, Lock, Globe, Monitor, MapPin, Trash2, LucideIcon
} from "lucide-react";
import { cn } from "@/lib/utils";

const iconMap: Record<string, LucideIcon> = {
  Camera, Video, Volume2, Mic, ClipboardList, Lock, Globe, Monitor, MapPin, Trash2,
};

interface FeatureIconProps {
  name: string;
  className?: string;
}

export const FeatureIcon = ({ name, className }: FeatureIconProps) => {
  const Icon = iconMap[name];
  if (!Icon) return null;
  return <Icon className={cn("w-4 h-4", className)} />;
};
