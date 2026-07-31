import { Upload, X } from "lucide-react";
import { useId, useRef, useState } from "react";

import { formatFileSize } from "../../../lib/formatters";
import { Button } from "../../../components/primitives/Button";
import { IconButton } from "../../../components/primitives/IconButton";
import { Badge } from "../../../components/primitives/Badge";
import { classNames } from "../../../lib/classNames";
import { BILLING_FILE_LIMIT_LABEL } from "../constants";
import type { BillingFileError, ParsedBillingFile } from "../types";
import styles from "./ImportWorkflow.module.css";

type BillingLogDropzoneProps = {
  parsedFile: ParsedBillingFile | null;
  error: BillingFileError | null;
  reading: boolean;
  onFilesSelected: (files: FileList | File[]) => void;
  onRemove: () => void;
};

export function BillingLogDropzone({ parsedFile, error, reading, onFilesSelected, onRemove }: BillingLogDropzoneProps) {
  const inputId = useId();
  const helperId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const chooseFile = () => {
    inputRef.current?.click();
  };

  return (
    <div>
      <label htmlFor={inputId} className="sr-only">Billing log JSON file</label>
      <input
        ref={inputRef}
        id={inputId}
        className={styles.hiddenInput}
        type="file"
        accept=".json,application/json"
        aria-describedby={helperId}
        onChange={(event) => {
          if (event.target.files) {
            onFilesSelected(event.target.files);
          }
          event.currentTarget.value = "";
        }}
      />
      <div
        className={classNames(styles.dropzone, dragActive && styles.dropzoneActive)}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragActive(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragActive(false);
          onFilesSelected(event.dataTransfer.files);
        }}
      >
        <div>
          <Upload size={26} aria-hidden="true" />
          <p><strong>{dragActive ? "Release to check this JSON file" : "Drag and drop a JSON billing log here"}</strong></p>
          <p id={helperId} className={styles.hint}>
            Browser checks only file type, size and JSON array structure. Billing rows are validated securely by the billing service after submission.
          </p>
          <div className={styles.actions}>
            <Button type="button" variant="primary" onClick={chooseFile} loading={reading}>
              {reading ? "Reading file" : "Choose JSON file"}
            </Button>
          </div>
        </div>
      </div>

      {error && <p className={styles.error} role="alert">{error.message}</p>}

      {parsedFile && (
        <div className={styles.fileCard} aria-label="Selected billing log">
          <div className={styles.actions}>
            <div>
              <span className={styles.fileName} title={parsedFile.fileName}>{parsedFile.fileName}</span>
              <p className={styles.hint}>JSON structure is readable. Billing rows will be validated by the backend.</p>
            </div>
            <IconButton label="Remove selected file" onClick={onRemove}>
              <X size={18} aria-hidden="true" />
            </IconButton>
          </div>
          <div className={styles.metaGrid}>
            <div><span>File size</span><strong>{formatFileSize(parsedFile.fileSizeBytes)}</strong></div>
            <div><span>Rows found</span><strong>{parsedFile.rowCount}</strong></div>
            <div><span>Frontend limit</span><strong>{BILLING_FILE_LIMIT_LABEL}</strong></div>
            <div><span>Day type</span><strong>{parsedFile.isEmpty ? <Badge>Empty clinic day</Badge> : "Activity file"}</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}
