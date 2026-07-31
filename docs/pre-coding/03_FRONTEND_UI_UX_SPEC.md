# Step 5 UI/UX Specification — React Production Interface

## 1. Goal

Build the three required screens so their structure, content hierarchy, and layout closely match the assignment mockups while adding only the minimum controls needed to import and operate the report.

The frontend is a presentation client. It must not recompute financial or ranking metrics.

## 2. Routes

```text
/                                      import/latest-report entry
/reports/:clinicId/:date/reconciliation
/reports/:clinicId/:date/analytics
/reports/:clinicId/:date/narrative
```

Unknown report routes show a report-not-found state with an Import Log action.

## 3. Frontend structure

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── clinicDays.ts
│   │   └── narratives.ts
│   ├── components/
│   │   ├── layout/
│   │   ├── common/
│   │   ├── import/
│   │   ├── reconciliation/
│   │   ├── analytics/
│   │   └── narrative/
│   ├── pages/
│   ├── hooks/
│   ├── types/
│   ├── utils/
│   ├── styles/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── vite.config.ts
└── vercel.json
```

## 4. Locked frontend versions and runtime

- Node.js 22 LTS-compatible runtime.
- React 19.
- Vite 8.
- TypeScript strict mode.
- React Router 7.
- Recharts 3.
- ESLint.
- Vitest and React Testing Library.
- Playwright for one end-to-end smoke flow.

## 5. Design tokens

The visual language follows the assignment screenshots: clinical blue/teal accents, light neutral background, white cards, subtle borders, and restrained use of status colors.

```css
:root {
  --color-brand-blue: #0b4a8b;
  --color-brand-blue-strong: #0a3f78;
  --color-brand-teal: #08a8a0;
  --color-page: #f7f9fc;
  --color-surface: #ffffff;
  --color-border: #dfe5ec;
  --color-text: #17212b;
  --color-muted: #6f7b87;
  --color-success: #18864b;
  --color-success-bg: #e9f7ee;
  --color-warning: #9a6500;
  --color-warning-bg: #fff7db;
  --color-danger: #b42318;
  --color-danger-bg: #fff0ee;
  --color-ai: #6d4bc3;
  --color-ai-bg: #f1eaff;
  --radius-card: 12px;
  --shadow-card: 0 1px 2px rgba(16, 24, 40, 0.05);
}
```

No third-party component system is required. Native semantic elements plus focused reusable components will make screenshot matching easier.

## 6. Shared application shell

### Desktop

- Fixed narrow left sidebar.
- Main content centered with a maximum width around 1180 px.
- Header title/subtitle left; date/import controls right.
- Required content begins immediately below the header.

### Sidebar

Navigation items:

1. Reconciliation.
2. Analytics.
3. AI Summary.

Each item has:

- Icon.
- Active indicator.
- `aria-label`.
- Tooltip on desktop.
- Keyboard focus state.

### Mobile

- Sidebar becomes bottom navigation.
- Header actions wrap below title.
- Content is single-column.
- Narrative trace panel moves beneath narrative.

## 7. Import flow

The mockups show report screens, not an upload page. The import workflow will therefore be unobtrusive:

### Entry page `/`

- Product heading.
- Clinic ID field.
- Clinic name and location defaults.
- Business-date field.
- Drag/drop or Select JSON File.
- Validate & Generate Report button.
- Recent reports list when available.

### Header import action

- `Import another log` button opens a modal.
- Re-importing the same clinic/date requires confirmation because it replaces the stored report.

### Client checks

Frontend checks only:

- `.json` file type/name.
- File size under 5 MB.
- Valid JSON syntax.
- Root value is an array.

All business validation remains in the backend.

## 8. Screen 1 — EOD Reconciliation

### Header

- `EOD Reconciliation`.
- Clinic name and location.
- Business date chip/control.

### Metric cards

| Card | Primary field | Supporting text |
|---|---|---|
| Total Billed | `total_billed_paise` | `<accepted_rows> valid visits` |
| Total Collected | `total_collected_paise` | `<collection_rate> collected` |
| Outstanding | `total_outstanding_paise` | `<pending_visit_count> pending visits` |
| Refunds | `total_refunds_paise` | `<refund_visit_count> refunds` |

### Payment-mode table

Rows are always ordered:

```text
Cash
Card
UPI
```

Columns:

```text
Mode | Billed | Collected | Outstanding | Refunds
```

The screenshot has three money columns; including Refunds as a fourth business column is acceptable because the assignment explicitly requires refunds split by payment mode. On narrow layouts the table scrolls horizontally.

### Partial-import banner

When `rejected_rows > 0`:

```text
Report generated from 18 valid rows. 1 row needs attention.
```

Button: `Review issue` / `Review issues`.

### Validation drawer

Fields:

- Row number displayed as one-based for humans.
- Visit ID when available.
- Field.
- Error message.
- No raw row JSON.

## 9. Screen 2 — Analytics

### Revenue chart

- Recharts `BarChart`.
- API supplies 24 hourly buckets.
- UI displays the contiguous range from the first positive hour to the last positive hour; for the supplied normal day this naturally produces 9am–6pm as shown.
- If all values are zero, show the no-sales state instead of meaningless bars.
- Peak bar uses brand blue; others use a pale blue.
- Peak callout contains hour label and exact money value.
- Tooltip shows `UTC` explicitly.

### Medicine rankings

Two independent cards:

1. `Top Medicines — by Quantity`.
2. `Top Medicines — by Revenue`.

Each shows up to five rows, rank number, medicine name, and quantity/money. Do not merge them or sort one using the other's metric.

### Data-quality warning

Possible spelling variants appear in a subtle warning card below rankings. They remain separate in the rankings.

## 10. Screen 3 — AI Narrative Summary

### Narrative panel

Status badge:

- `AI SUGGESTED` when `status=generated`.
- `DETERMINISTIC FALLBACK` when `status=fallback`.

Content:

- Owner-facing summary preserving paragraph breaks.
- Copy Summary button.
- Regenerate button.
- Provider/model metadata in a low-emphasis footer.
- Fallback explanation that does not expose provider error details.

### Traced Figures panel

Each row shows:

- Displayed value.
- Report path.
- Optional category label.

Trace rows come directly from the narrative API response and are not reconstructed client-side.

### Unavailable metrics

Render a note such as:

```text
Profit is not available because cost-price data was not provided.
```

## 11. Page states

### Common states

- Loading skeleton.
- Ready.
- Ready with ingestion errors.
- Empty day.
- Refund-only day.
- Not found.
- Backend unavailable.

### Narrative states

- Not generated: show Generate Summary action.
- Generating: disable actions, show progress copy.
- Generated.
- Fallback.
- Stale: regenerate automatically after report refresh or show Regenerate.
- Failure only when neither generated output nor deterministic fallback is available.

## 12. Formatting rules

- Money is sent as integer paise but formatted in frontend with an integer-safe utility using rupee values and Indian grouping. The frontend does not alter totals.
- Collection rate is displayed as a percentage with at most one decimal.
- Hour labels explicitly say UTC.
- Business dates use `27 Jul 2026` in the UI and ISO dates in URLs/API.
- Drug names remain uppercase to match source/report output.

## 13. Accessibility

- Semantic headings and landmarks.
- All icon-only navigation has accessible names.
- Visible keyboard focus.

## Prompt 6 Implementation Note

Prompt 6 keeps the Prompt 5 dark floating glass-panel interface rather than the earlier light-card palette in this planning document. The Reports route now contains the first end-to-end workflow: clinic/date metadata, accessible JSON dropzone, conservative file-size validation, backend-authoritative import submission, partial-import issue review, recent-report filters, URL-backed pagination, and report-opening links. Final reconciliation KPI cards, analytics charts, and AI narrative controls remain deferred to Prompts 7-9.
- Minimum 4.5:1 contrast for normal text.
- Chart includes a text summary and peak value outside the SVG.
- Status is not communicated using color alone.
- Drawer traps focus and closes with Escape.
- Copy action announces success through an `aria-live` region.

## 14. Frontend data ownership

The frontend must never:

- Recalculate outstanding.
- Recompute collection rate.
- Find the peak hour.
- Re-rank medicines.
- Interpret refunds as negative collections.
- Generate traces from text.

It may only format already returned values and select how they are arranged visually.

## 15. Frontend tests

- App shell renders and active navigation persists route context.
- All four reconciliation cards map to the correct fields.
- Payment rows stay in Cash/Card/UPI order.
- Partial-ingestion banner and drawer render.
- Peak bar/callout maps to API peak hour.
- Two medicine ranking cards remain distinct.
- Empty/refund-only states render correctly.
- Generated and fallback narrative badges differ.
- Copy Summary works.
- Trace panel renders exact server values and paths.
- Mobile navigation and stacked narrative layout are present.
- API errors produce a recoverable UI.

## 16. Step 5 completion gate

- All three required screens match the screenshot structure.
- Shared navigation persists across screens.
- Import flow works without cluttering the required layouts.
- No financial calculation exists in React.
- Desktop, tablet, and mobile layouts work.
- Component tests pass.
- Production build has no TypeScript or lint errors.
