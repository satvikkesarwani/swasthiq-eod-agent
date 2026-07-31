import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";

import type { ClinicDayDetail } from "../../../api/types";
import { formatPaise } from "../../../lib/formatters";
import { mapHourlyRevenue } from "../presentation";
import styles from "../analytics.module.css";

function RevenueTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0]?.payload as ReturnType<typeof mapHourlyRevenue>[number] | undefined;
  if (!point) {
    return null;
  }
  return (
    <div className={styles.tooltip}>
      <p>{point.rangeLabel}</p>
      <strong>{formatPaise(point.revenuePaise)}</strong>
      {point.isPeak && <p className={styles.muted}>Backend peak hour</p>}
    </div>
  );
}

export function RevenueByHourChart({ report }: { report: ClinicDayDetail }) {
  const points = mapHourlyRevenue(report);
  if (points.length === 0) {
    return (
      <div className={styles.emptyChart} role="status">
        <div>
          <strong>No hourly revenue buckets</strong>
          <p className={styles.muted}>The backend did not return sales-hour analytics for this report.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.chartWrap} role="img" aria-label="Backend revenue by hour">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={points} margin={{ top: 12, right: 12, bottom: 8, left: 0 }}>
          <XAxis dataKey="displayLabel" tick={{ fill: "rgba(232, 241, 255, 0.72)", fontSize: 12 }} tickLine={false} axisLine={false} />
          <YAxis tickFormatter={(value) => formatPaise(Number(value))} tick={{ fill: "rgba(232, 241, 255, 0.72)", fontSize: 12 }} tickLine={false} axisLine={false} width={72} />
          <Tooltip content={(props) => <RevenueTooltip {...props} />} cursor={{ fill: "rgba(99, 216, 215, 0.08)" }} isAnimationActive={false} />
          <Bar dataKey="revenuePaise" name="Revenue" radius={[6, 6, 0, 0]} isAnimationActive={false}>
            {points.map((point) => (
              <Cell key={point.hourKey} fill={point.isPeak ? "var(--color-yellow)" : "var(--color-teal)"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
