import { Outlet } from "react-router";

import { useAppContext } from "../../app/AppContext";
import { OfflineBanner } from "../feedback/OfflineBanner";
import { ToastRegion } from "../feedback/ToastRegion";
import { MobileNavigation } from "./MobileNavigation";
import { NavigationRail } from "./NavigationRail";
import { TopBar } from "./TopBar";
import styles from "./Layout.module.css";

export function AppShell() {
  const { online, toasts } = useAppContext();

  return (
    <div className={styles.shell}>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <TopBar />
      <div className={styles.chrome}>
        <div className={styles.rail}>
          <NavigationRail />
        </div>
        <main id="main-content" className={styles.main}>
          <div className={styles.inner}>
            <OfflineBanner online={online} />
            <Outlet />
          </div>
        </main>
      </div>
      <MobileNavigation />
      <ToastRegion toasts={toasts} />
    </div>
  );
}
