import { useParams } from "react-router";

import { hasValidReportParams } from "../app/routes";

export type ReportRouteParams = {
  clinicId?: string | undefined;
  businessDate?: string | undefined;
  isValid: boolean;
};

export function useReportRouteParams(): ReportRouteParams {
  const params = useParams();
  return {
    clinicId: params.clinicId,
    businessDate: params.businessDate,
    isValid: hasValidReportParams(params),
  };
}
