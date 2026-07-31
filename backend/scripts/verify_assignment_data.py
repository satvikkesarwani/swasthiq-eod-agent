"""Run locally against the confidential assignment files without committing them.

Usage:
  python scripts/verify_assignment_data.py /path/to/billing_log_2026-07-27.json
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.report_service import build_deterministic_report
from app.services.row_validator import validate_billing_log


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_assignment_data.py <billing-log.json>")
        return 2
    path = Path(sys.argv[1])
    records = json.loads(path.read_text(encoding="utf-8"))
    business_date = date.fromisoformat(path.stem.removeprefix("billing_log_"))
    clinic_id = records[0]["clinic_id"] if records else "CLN-KNP-014"
    ingestion = validate_billing_log(clinic_id=clinic_id, business_date=business_date, records=records)
    report = build_deterministic_report(ingestion.accepted)
    print(json.dumps({
        "received_rows": ingestion.received_rows,
        "accepted_rows": len(ingestion.accepted),
        "rejected_rows": len(ingestion.rejected),
        "errors": [error.model_dump(exclude={"raw_row"}) for error in ingestion.rejected],
        "report": report.model_dump(mode="json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
