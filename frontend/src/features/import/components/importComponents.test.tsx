import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { describe, expect, it, vi } from "vitest";

import { partialImportResponse } from "../../../test/fixtures";
import { mapImportResult } from "../importMapping";
import { BillingLogDropzone } from "./BillingLogDropzone";
import { ImportPipelineStatus } from "./ImportPipelineStatus";
import { ImportResultPanel } from "./ImportResultPanel";

function renderRouter(element: React.ReactNode) {
  const router = createMemoryRouter([{ path: "/", element }], { initialEntries: ["/"] });
  return render(<RouterProvider router={router} />);
}

describe("import feature components", () => {
  it("supports file selection, remove and drag/drop callbacks", async () => {
    const onFilesSelected = vi.fn();
    const onRemove = vi.fn();
    const parsedFile = { fileName: "billing.json", fileSizeBytes: 2, records: [], rowCount: 0, isEmpty: true };
    const { rerender } = render(
      <BillingLogDropzone parsedFile={null} error={null} reading={false} onFilesSelected={onFilesSelected} onRemove={onRemove} />,
    );
    const file = new File(["[]"], "billing.json", { type: "application/json" });
    await userEvent.upload(screen.getByLabelText("Billing log JSON file"), file);
    expect(onFilesSelected).toHaveBeenCalledTimes(1);
    fireEvent.dragEnter(screen.getByText("Drag and drop a JSON billing log here"));
    expect(screen.getByText("Release to check this JSON file")).toBeVisible();
    fireEvent.drop(screen.getByText("Release to check this JSON file"), { dataTransfer: { files: [file] } });
    expect(onFilesSelected).toHaveBeenCalledTimes(2);

    rerender(<BillingLogDropzone parsedFile={parsedFile} error={{ code: "INVALID_JSON", message: "Invalid" }} reading={false} onFilesSelected={onFilesSelected} onRemove={onRemove} />);
    expect(screen.getByText("billing.json")).toBeVisible();
    expect(screen.getByText("Empty clinic day")).toBeVisible();
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid");
    await userEvent.click(screen.getByRole("button", { name: "Remove selected file" }));
    expect(onRemove).toHaveBeenCalledTimes(1);
  });

  it("renders pipeline and result states", () => {
    renderRouter(
      <div>
        <ImportPipelineStatus status="reading_file" hasFile={false} hasResult={false} rejectedRows={0} />
        <ImportPipelineStatus status="completed_with_errors" hasFile hasResult rejectedRows={2} />
        <ImportResultPanel result={mapImportResult(partialImportResponse)} onReviewIssues={vi.fn()} onImportAnother={vi.fn()} />
      </div>,
    );
    expect(screen.getByText("Reading")).toBeVisible();
    expect(screen.getByText("Report generated with validation issues")).toBeVisible();
    expect(screen.getByRole("link", { name: "Continue to reconciliation" })).toHaveAttribute("href", "/reports/CLN-TST-001/2026-07-31/reconciliation");
  });
});
