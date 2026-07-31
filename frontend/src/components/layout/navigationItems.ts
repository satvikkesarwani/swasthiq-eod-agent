import { BarChart3, FileText, GitCompareArrows, ListChecks, type LucideIcon } from "lucide-react";

export type NavigationItem = {
  label: string;
  icon: LucideIcon;
  section: "reports" | "report-detail";
};

export const navigationItems: NavigationItem[] = [
  { label: "Reports", icon: ListChecks, section: "reports" },
  { label: "Reconcile", icon: GitCompareArrows, section: "report-detail" },
  { label: "Analytics", icon: BarChart3, section: "report-detail" },
  { label: "Narrative", icon: FileText, section: "report-detail" },
];
