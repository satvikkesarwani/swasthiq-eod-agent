import { useEffect, useRef, useState } from "react";

import { API_OK_EVENT } from "../api/client";
import { getHealth } from "../api/endpoints";
import { logDiagnostic } from "../lib/diagnostics";
import { useOnlineStatus } from "./useOnlineStatus";

export type HealthState = "checking" | "healthy" | "degraded" | "unavailable";

export type HealthStatus = {
  state: HealthState;
  label: string;
  checkedAt: Date | null;
};

const CHECK_INTERVAL_MS = 60_000;
const RECOVERY_RETRY_MS = 3_000;

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
  const failures = useRef(0);

  useEffect(() => {
    if (!online) {
      logDiagnostic("warn", "health", "Browser reported offline");
      setStatus({ state: "unavailable", label: "Offline", checkedAt: new Date() });
      return undefined;
    }

    const controller = new AbortController();
    let retry: number | undefined;
    const check = async () => {
      if (inFlight.current) {
        return;
      }
      inFlight.current = true;
      try {
        logDiagnostic("debug", "health", "Health check start");
        const response = await getHealth(controller.signal);
        const nextState: HealthState = response.status === "ok" || response.status === "healthy" ? "healthy" : "degraded";
        failures.current = 0;
        logDiagnostic("info", "health", "Health check success", {
          backendStatus: response.status,
          database: response.database,
          nextState,
        });
        setStatus({ state: nextState, label: labelFor(nextState), checkedAt: new Date() });
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          failures.current += 1;
          const nextState: HealthState = failures.current >= 2 ? "unavailable" : "checking";
          logDiagnostic("warn", "health", "Health check failed", {
            failures: failures.current,
            nextState,
            error,
          });
          setStatus({ state: nextState, label: labelFor(nextState), checkedAt: new Date() });
          retry = window.setTimeout(() => {
            void check();
          }, RECOVERY_RETRY_MS);
        }
      } finally {
        inFlight.current = false;
      }
    };

    void check();
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        void check();
      }
    };
    const onOnline = () => {
      void check();
    };
    const onApiOk = () => {
      failures.current = 0;
      logDiagnostic("info", "health", "Backend marked healthy from successful API call");
      setStatus({ state: "healthy", label: labelFor("healthy"), checkedAt: new Date() });
    };
    const interval = window.setInterval(() => {
      void check();
    }, CHECK_INTERVAL_MS);
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    window.addEventListener(API_OK_EVENT, onApiOk);

    return () => {
      controller.abort();
      if (retry !== undefined) {
        window.clearTimeout(retry);
      }
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
      window.removeEventListener(API_OK_EVENT, onApiOk);
    };
  }, [online]);

  return status;
}
