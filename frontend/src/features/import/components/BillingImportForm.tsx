import { RotateCcw } from "lucide-react";
import { useId, useRef, useState, type FormEvent } from "react";

import { Button } from "../../../components/primitives/Button";
import { GlassPanel } from "../../../components/primitives/GlassPanel";
import { InlineError } from "../../../components/feedback/InlineError";
import { StatusPill } from "../../../components/primitives/StatusPill";
import type { ClinicDaySummary } from "../../../api/types";
import { logDiagnostic } from "../../../lib/diagnostics";
import { useBillingFileState } from "../hooks/useBillingFile";
import { useBillingImport } from "../hooks/useBillingImport";
import { normalizeBusinessDateInput, trimOptional } from "../validation";
import { BillingLogDropzone } from "./BillingLogDropzone";
import { ImportResultPanel } from "./ImportResultPanel";
import type { ImportResult } from "../types";
import styles from "./ImportWorkflow.module.css";

type BillingImportFormProps = {
  recentReports: ClinicDaySummary[];
  onPartialResult: (result: ImportResult) => void;
  onReviewIssues: () => void;
};

type FieldErrors = Partial<Record<"clinicId" | "businessDate" | "file" | "confirmReplacement" | "confirmEmpty", string>>;

export function BillingImportForm({ recentReports, onPartialResult, onReviewIssues }: BillingImportFormProps) {
  const clinicIdId = useId();
  const businessDateId = useId();
  const [clinicId, setClinicId] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [clinicLocation, setClinicLocation] = useState("");
  const [businessDate, setBusinessDate] = useState("");
  const [confirmReplacement, setConfirmReplacement] = useState(false);
  const [confirmEmpty, setConfirmEmpty] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const clinicIdRef = useRef<HTMLInputElement>(null);
  const dateRef = useRef<HTMLInputElement>(null);
  const { state, dispatch, selectFiles } = useBillingFileState();
  const { submitImport } = useBillingImport(state, dispatch);

  const trimmedClinicId = clinicId.trim();
  const normalizedBusinessDate = normalizeBusinessDateInput(businessDate);
  const existingReport = normalizedBusinessDate !== null && recentReports.some((report) => report.clinic_id === trimmedClinicId && report.business_date === normalizedBusinessDate);
  const isEmptyDay = state.parsedFile?.isEmpty ?? false;
  const canSubmit = state.status !== "reading_file" && state.status !== "submitting";

  const validate = (): boolean => {
    const errors: FieldErrors = {};
    if (!trimmedClinicId) {
      errors.clinicId = "Clinic ID is required.";
    }
    if (normalizedBusinessDate === null) {
      errors.businessDate = "Business date is required as DD/MM/YYYY or YYYY-MM-DD.";
    }
    if (state.parsedFile === null) {
      errors.file = "Choose a JSON billing log.";
    }
    if (existingReport && !confirmReplacement) {
      errors.confirmReplacement = "Confirm replacement before submitting this clinic day.";
    }
    if (existingReport && isEmptyDay && !confirmEmpty) {
      errors.confirmEmpty = "Confirm empty-day replacement before submitting.";
    }
    setFieldErrors(errors);
    logDiagnostic(Object.keys(errors).length === 0 ? "info" : "warn", "import.form", "Submit validation result", {
      clinicId: trimmedClinicId,
      businessDateInput: businessDate,
      normalizedBusinessDate,
      hasFile: state.parsedFile !== null,
      rowCount: state.parsedFile?.rowCount ?? 0,
      existingReport,
      isEmptyDay,
      errors,
    });
    if (errors.clinicId) {
      clinicIdRef.current?.focus();
      return false;
    }
    if (errors.businessDate) {
      dateRef.current?.focus();
      return false;
    }
    return Object.keys(errors).length === 0;
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    logDiagnostic("info", "import.form", "Submit clicked", {
      clinicId: trimmedClinicId,
      businessDateInput: businessDate,
      normalizedBusinessDate,
      status: state.status,
      hasFile: state.parsedFile !== null,
      rowCount: state.parsedFile?.rowCount ?? 0,
    });
    dispatch({ type: "form_changed" });
    if (!validate()) {
      return;
    }
    const dateForSubmit = normalizeBusinessDateInput(businessDate);
    if (dateForSubmit === null) {
      logDiagnostic("error", "import.form", "Normalized date unexpectedly missing after validation", {
        businessDateInput: businessDate,
      });
      return;
    }
    void submitImport({
      clinicId: trimmedClinicId,
      clinicName: trimOptional(clinicName) ?? "",
      clinicLocation: trimOptional(clinicLocation) ?? "",
      businessDate: dateForSubmit,
    });
  };

  const resetForm = () => {
    const hasData = clinicId || clinicName || clinicLocation || businessDate || state.parsedFile;
    if (hasData && !window.confirm("Reset this import form and remove the selected file?")) {
      return;
    }
    setClinicId("");
    setClinicName("");
    setClinicLocation("");
    setBusinessDate("");
    setConfirmReplacement(false);
    setConfirmEmpty(false);
    setFieldErrors({});
    dispatch({ type: "reset" });
  };

  return (
    <GlassPanel title="Import billing log" description="Select a clinic day and submit the exact JSON array to the billing service.">
      <form className={styles.importForm} onSubmit={onSubmit} aria-busy={state.status === "submitting"}>
        {Object.keys(fieldErrors).length > 0 && (
          <InlineError message="Some import fields need attention before submission." />
        )}
        <div className={styles.formGrid}>
          <div className={styles.field}>
            <label htmlFor={clinicIdId}>Clinic ID</label>
            <input
              ref={clinicIdRef}
              id={clinicIdId}
              value={clinicId}
              autoComplete="organization"
              aria-invalid={Boolean(fieldErrors.clinicId)}
              aria-describedby={fieldErrors.clinicId ? `${clinicIdId}-error` : undefined}
              onChange={(event) => {
                setClinicId(event.target.value);
                setConfirmReplacement(false);
                dispatch({ type: "form_changed" });
              }}
            />
            {fieldErrors.clinicId && <p id={`${clinicIdId}-error`} className={styles.error}>{fieldErrors.clinicId}</p>}
          </div>
          <div className={styles.field}>
            <label htmlFor={businessDateId}>Business date</label>
            <input
              ref={dateRef}
              id={businessDateId}
              type="text"
              value={businessDate}
              inputMode="numeric"
              placeholder="dd/mm/yyyy"
              aria-invalid={Boolean(fieldErrors.businessDate)}
              aria-describedby={fieldErrors.businessDate ? `${businessDateId}-error` : undefined}
              onChange={(event) => {
                setBusinessDate(event.target.value);
                setConfirmReplacement(false);
                setConfirmEmpty(false);
                dispatch({ type: "form_changed" });
              }}
            />
            {fieldErrors.businessDate && <p id={`${businessDateId}-error`} className={styles.error}>{fieldErrors.businessDate}</p>}
          </div>
          <div className={styles.field}>
            <label htmlFor="clinic-name">Clinic name</label>
            <input id="clinic-name" value={clinicName} autoComplete="organization-title" onChange={(event) => setClinicName(event.target.value)} />
          </div>
          <div className={styles.field}>
            <label htmlFor="clinic-location">Clinic location</label>
            <input id="clinic-location" value={clinicLocation} autoComplete="address-level2" onChange={(event) => setClinicLocation(event.target.value)} />
          </div>
        </div>

        <BillingLogDropzone
          parsedFile={state.parsedFile}
          error={state.fileError ?? (fieldErrors.file ? { code: "NO_FILE", message: fieldErrors.file } : null)}
          reading={state.status === "reading_file"}
          onFilesSelected={(files) => {
            setFieldErrors({});
            dispatch({ type: "form_changed" });
            selectFiles(files);
          }}
          onRemove={() => dispatch({ type: "remove_file" })}
        />

        {existingReport && (
          <div className={styles.warning}>
            <StatusPill tone="warning">Existing report</StatusPill>
            <p className={styles.hint}>This clinic day already appears in recent reports. The backend performs an atomic replacement if the submitted data differs.</p>
            <label className={styles.checkbox}>
              <input type="checkbox" checked={confirmReplacement} onChange={(event) => setConfirmReplacement(event.target.checked)} />
              <span>I understand this may replace the stored report for this clinic day.</span>
            </label>
            {fieldErrors.confirmReplacement && <p className={styles.error}>{fieldErrors.confirmReplacement}</p>}
          </div>
        )}

        {existingReport && isEmptyDay && (
          <div className={styles.warning}>
            <StatusPill tone="neutral">Empty clinic day</StatusPill>
            <p className={styles.hint}>This will create or replace the selected clinic day with a no-activity report.</p>
            <label className={styles.checkbox}>
              <input type="checkbox" checked={confirmEmpty} onChange={(event) => setConfirmEmpty(event.target.checked)} />
              <span>I understand this empty day may replace an existing report.</span>
            </label>
            {fieldErrors.confirmEmpty && <p className={styles.error}>{fieldErrors.confirmEmpty}</p>}
          </div>
        )}

        {state.submitError && <InlineError message={state.submitError} />}
        {state.importResult && (
          <ImportResultPanel
            result={state.importResult}
            onReviewIssues={() => {
              onPartialResult(state.importResult as ImportResult);
              onReviewIssues();
            }}
            onImportAnother={resetForm}
          />
        )}

        <div className={styles.actions}>
          <Button type="submit" variant="primary" disabled={!canSubmit} loading={state.status === "submitting"}>
            {state.status === "submitting" ? "Submitting" : existingReport ? "Replace report" : "Validate and generate report"}
          </Button>
          <Button type="button" variant="ghost" icon={<RotateCcw size={16} aria-hidden="true" />} onClick={resetForm}>Reset</Button>
        </div>
      </form>
    </GlassPanel>
  );
}
