import { createContext, useContext } from "react";

import type { HealthStatus } from "../hooks/useHealthStatus";

export type Toast = { id: string; message: string };

export type AppContextValue = {
  health: HealthStatus;
  online: boolean;
  toasts: Toast[];
  pushToast: (message: string) => void;
  dismissToast: (id: string) => void;
};

export const AppContext = createContext<AppContextValue | null>(null);

export function useAppContext(): AppContextValue {
  const value = useContext(AppContext);
  if (value === null) {
    throw new Error("useAppContext must be used inside AppProviders.");
  }
  return value;
}
