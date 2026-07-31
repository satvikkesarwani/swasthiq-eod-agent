import { validateBillingFile } from "./validation";
import type { BillingFileError, ParsedBillingFile } from "./types";
import { logDiagnostic } from "../../lib/diagnostics";
import { parseStrictJson } from "./jsonSafety";

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

async function readFileText(file: File): Promise<string> {
  const decoder = new TextDecoder("utf-8", { fatal: true });
  if (typeof file.arrayBuffer === "function") {
    return decoder.decode(await file.arrayBuffer());
  }
  if (typeof FileReader !== "undefined") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.addEventListener("load", () => {
        const result = reader.result;
        try {
          resolve(result instanceof ArrayBuffer ? decoder.decode(result) : "");
        } catch (error) {
          reject(error instanceof Error ? error : new Error("File decode failed."));
        }
      });
      reader.addEventListener("error", () => reject(reader.error ?? new Error("File read failed.")));
      reader.readAsArrayBuffer(file);
    });
  }
  return decoder.decode(await new Response(file).arrayBuffer());
}

export async function parseBillingLogFile(file: File): Promise<ParsedBillingFile> {
  logDiagnostic("info", "import.parser", "Parse file start", {
    fileName: file.name,
    fileSizeBytes: file.size,
    fileType: file.type,
  });
  const validation = validateBillingFile(file);
  if (validation !== null) {
    logDiagnostic("warn", "import.parser", "File validation failed", {
      fileName: file.name,
      code: validation.code,
      message: validation.message,
    });
    throw new BillingFileParseError(validation);
  }

  let text: string;
  try {
    text = await readFileText(file);
  } catch (error) {
    logDiagnostic("error", "import.parser", "File read failed", { fileName: file.name, error });
    throw new BillingFileParseError(fileError("FILE_READ_FAILED", "The selected file could not be read. Choose the file again and retry."));
  }

  const readableText = text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
  if (readableText.length === 0) {
    logDiagnostic("warn", "import.parser", "File empty", { fileName: file.name });
    throw new BillingFileParseError(fileError("EMPTY_FILE", "The selected file is empty. Choose a JSON array billing log."));
  }

  let parsed: unknown;
  try {
    parsed = parseStrictJson(readableText);
  } catch (error) {
    logDiagnostic("warn", "import.parser", "JSON parse failed", { fileName: file.name, error });
    throw new BillingFileParseError(fileError("INVALID_JSON", "The selected file is not valid JSON."));
  }

  if (!Array.isArray(parsed)) {
    logDiagnostic("warn", "import.parser", "JSON root rejected", {
      fileName: file.name,
      rootType: typeof parsed,
    });
    throw new BillingFileParseError(fileError("ROOT_NOT_ARRAY", "The JSON root must be an array of billing records."));
  }

  logDiagnostic("info", "import.parser", "Parse file success", {
    fileName: file.name,
    fileSizeBytes: file.size,
    rowCount: parsed.length,
    isEmpty: parsed.length === 0,
  });
  return {
    fileName: file.name,
    fileSizeBytes: file.size,
    records: parsed,
    rowCount: parsed.length,
    isEmpty: parsed.length === 0,
  };
}
