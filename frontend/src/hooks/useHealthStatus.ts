import { useEffect, useRef, useState } from "react";

import { getHealth } from "../api/endpoints";
import { useOnlineStatus } from "./useOnlineStatus";

export type HealthState = "checking" | "healthy" | "degraded" | "unavailable";

export type HealthStatus = {
  state: HealthState;
  label: string;
  checkedAt: Date | null;
};

const CHECK_INTERVAL_MS = 60_000;

function labelFor(state: HealthState): string {
  if (state === "healthy") {
    return "Backend online";
  }
  if (state === "degraded") {
    return "Backend degraded";
  }
  if (state === "unavailable") {
    return "Backend unavailable";
  }
  return "Checking backend";
}

export function useHealthStatus(): HealthStatus {
  const online = useOnlineStatus();
  const [status, setStatus] = useState<HealthStatus>(() => ({
    state: online ? "checking" : "unavailable",
    label: online ? labelFor("checking") : "Offline",
    checkedAt: null,
  }));
  const inFlight = useRef(false);

  useEffect(() => {
    if (!online) {
      setStatus({ state: "unavailable", label: "Offline", checkedAt: new Date() });
      return undefined;
    }

    const controller = new AbortController();
    const check = async () => {
      if (inFlight.current) {
        return;
      }
      inFlight.current = true;
      try {
        const response = await getHealth(controller.signal);
        const nextState: HealthState = response.status === "ok" ? "healthy" : "degraded";
        setStatus({ state: nextState, label: labelFor(nextState), checkedAt: new Date() });
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setStatus({ state: "unavailable", label: labelFor("unavailable"), checkedAt: new Date() });
        }
      } finally {
        inFlight.current = false;
      }
    };

    void check();
    const interval = window.setInterval(() => {
      void check();
    }, CHECK_INTERVAL_MS);

    return () => {
      controller.abort();
      window.clearInterval(interval);
    };
  }, [online]);

  return status;
}
