import { validateBillingFile } from "./validation";
import type { BillingFileError, ParsedBillingFile } from "./types";

export class BillingFileParseError extends Error {
  readonly code: BillingFileError["code"];

  constructor(error: BillingFileError) {
    super(error.message);
    this.name = "BillingFileParseError";
    this.code = error.code;
  }
}

function fileError(code: BillingFileError["code"], message: string): BillingFileError {
  return { code, message };
}

function readFileText(file: File): Promise<string> {
  if (typeof file.text === "function") {
    return file.text();
  }
  if (typeof FileReader !== "undefined") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        const result = reader.result;
        resolve(typeof result === "string" ? result : "");
      });
      reader.addEventListener("error", () => reject(reader.error ?? new Error("File read failed.")));
      reader.readAsText(file);
    });
  }
  return new Response(file).text();
}

export async function parseBillingLogFile(file: File): Promise<ParsedBillingFile> {
  const validation = validateBillingFile(file);
  if (validation !== null) {
    throw new BillingFileParseError(validation);
  }

  let text: string;
  try {
    text = await readFileText(file);
  } catch {
    throw new BillingFileParseError(fileError("FILE_READ_FAILED", "The selected file could not be read. Choose the file again and retry."));
  }

  const readableText = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  if (readableText.length === 0) {
    throw new BillingFileParseError(fileError("EMPTY_FILE", "The selected file is empty. Choose a JSON array billing log."));
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(readableText) as unknown;
  } catch {
    throw new BillingFileParseError(fileError("INVALID_JSON", "The selected file is not valid JSON."));
  }

  if (!Array.isArray(parsed)) {
    throw new BillingFileParseError(fileError("ROOT_NOT_ARRAY", "The JSON root must be an array of billing records."));
  }

  return {
    fileName: file.name,
    fileSizeBytes: file.size,
    records: parsed,
    rowCount: parsed.length,
    isEmpty: parsed.length === 0,
  };
}
