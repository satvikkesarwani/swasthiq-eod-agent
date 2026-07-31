import { useMemo, useState, type ReactNode } from "react";
import { Outlet } from "react-router";

import { AppContext, type AppContextValue, type Toast } from "./AppContext";
import { useHealthStatus } from "../hooks/useHealthStatus";
import { useOnlineStatus } from "../hooks/useOnlineStatus";

export function AppProviders({ children }: { children?: ReactNode }) {
  const health = useHealthStatus();
  const online = useOnlineStatus();
  const [toasts, setToasts] = useState<Toast[]>([]);

  const value = useMemo<AppContextValue>(() => ({
    health,
    online,
    toasts,
    pushToast(message) {
      const id = `${Date.now()}-${message}`;
      setToasts((current) => [...current, { id, message }]);
    },
    dismissToast(id) {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    },
  }), [health, online, toasts]);

  return (
    <AppContext.Provider value={value}>
      {children ?? <Outlet />}
    </AppContext.Provider>
  );
}
