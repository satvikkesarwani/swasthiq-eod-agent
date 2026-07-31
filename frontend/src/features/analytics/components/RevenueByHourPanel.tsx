import type { ClinicDayDetail } from "../../../api/types";
import { GlassPanel } from "../../../components/primitives/GlassPanel";
import { RevenueByHourChart } from "./RevenueByHourChart";
import { RevenueByHourTable } from "./RevenueByHourTable";

export function RevenueByHourPanel({ report }: { report: ClinicDayDetail }) {
  return (
    <GlassPanel title="Revenue By Hour" description="Backend supplied billed-sales buckets in UTC.">
      <RevenueByHourChart report={report} />
      <RevenueByHourTable report={report} />
    </GlassPanel>
  );
}
