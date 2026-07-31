import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.report_service import build_deterministic_report
from app.services.row_validator import validate_billing_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark deterministic billing analysis for one JSON file.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--clinic-id", default=None)
    parser.add_argument("--business-date", default=None)
    args = parser.parse_args()

    started = time.perf_counter()
    records = json.loads(args.json_file.read_text(encoding="utf-8-sig"))
    load_ms = round((time.perf_counter() - started) * 1000, 2)
    clinic_id = args.clinic_id or (records[0]["clinic_id"] if records else "CLN-EMPTY")
    business_date = date.fromisoformat(args.business_date or args.json_file.stem.rsplit("_", 1)[-1])

    validate_started = time.perf_counter()
    ingestion = validate_billing_log(clinic_id=clinic_id, business_date=business_date, records=records)
    validate_ms = round((time.perf_counter() - validate_started) * 1000, 2)

    report_started = time.perf_counter()
    report = build_deterministic_report(ingestion.accepted)
    report_ms = round((time.perf_counter() - report_started) * 1000, 2)

    print(json.dumps({
        "file": args.json_file.name,
        "load_ms": load_ms,
        "validate_ms": validate_ms,
        "report_ms": report_ms,
        "received_rows": ingestion.received_rows,
        "accepted_rows": len(ingestion.accepted),
        "total_issue_count": ingestion.total_issue_count,
        "issues_truncated": ingestion.issues_truncated,
        "activity_counts": report.activity_counts.model_dump(),
        "total_billed_paise": report.reconciliation.total_billed_paise,
        "total_collected_paise": report.reconciliation.total_collected_paise,
        "total_refunds_paise": report.reconciliation.total_refunds_paise,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
