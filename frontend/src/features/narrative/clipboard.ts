import { logDiagnostic } from "../../lib/diagnostics";

export async function copyTextToClipboard(text: string): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "true");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);
    if (!copied) {
      throw new Error("Copy command was rejected.");
    }
  } catch (error) {
    logDiagnostic("warn", "narrative.clipboard", "Clipboard copy failed", {
      error,
      textLength: text.length,
    });
    throw error;
  }
}
