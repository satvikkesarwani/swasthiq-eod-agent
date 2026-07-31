from datetime import date


def row_for_day(base_row: dict, *, visit_id: str, day: int, clinic_id: str = "CLN-001") -> dict:
    copied = dict(base_row)
    copied["clinic_id"] = clinic_id
    copied["visit_id"] = visit_id
    copied["timestamp"] = f"2026-07-{day:02d}T09:00:00Z"
    copied["line_items"] = [dict(item) for item in base_row["line_items"]]
    return copied


def create_day(client, clinic_id: str, day: int, rows: list[dict]):
    return client.put(f"/api/v1/clinic-days/{clinic_id}/2026-07-{day:02d}", json={"records": rows})


def test_list_zero_multiple_filters_pagination_and_ordering(client, valid_rows):
    empty = client.get("/api/v1/clinic-days")
    assert empty.status_code == 200
    assert empty.json() == {"items": [], "limit": 20, "offset": 0, "count": 0}

    create_day(client, "CLN-001", 25, [row_for_day(valid_rows[0], visit_id="A", day=25)])
    create_day(client, "CLN-002", 27, [row_for_day(valid_rows[0], visit_id="B", day=27, clinic_id="CLN-002")])
    create_day(client, "CLN-001", 26, [row_for_day(valid_rows[1], visit_id="C", day=26)])

    all_days = client.get("/api/v1/clinic-days").json()
    assert [item["business_date"] for item in all_days["items"]] == ["2026-07-27", "2026-07-26", "2026-07-25"]
    assert all_days["items"][0]["total_billed_paise"] == 4_500
    assert all_days["items"][0]["report_hash"].startswith("sha256:")

    filtered_clinic = client.get("/api/v1/clinic-days", params={"clinic_id": "CLN-001"}).json()
    assert [item["clinic_id"] for item in filtered_clinic["items"]] == ["CLN-001", "CLN-001"]

    filtered_dates = client.get(
        "/api/v1/clinic-days",
        params={"date_from": "2026-07-26", "date_to": "2026-07-27"},
    ).json()
    assert [item["business_date"] for item in filtered_dates["items"]] == ["2026-07-27", "2026-07-26"]

    paged = client.get("/api/v1/clinic-days", params={"limit": 1, "offset": 1}).json()
    assert paged["limit"] == 1
    assert paged["offset"] == 1
    assert paged["count"] == 1
    assert paged["items"][0]["business_date"] == "2026-07-26"

    too_large = client.get("/api/v1/clinic-days", params={"limit": 101})
    assert too_large.status_code == 422
    assert too_large.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_detail_errors_missing_and_no_raw_rows(client, valid_rows):
    malformed = dict(valid_rows[0])
    malformed.pop("payment_mode")
    response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": [valid_rows[1], malformed]})
    assert response.status_code == 200

    detail = client.get("/api/v1/clinic-days/CLN-001/2026-07-27")
    assert detail.status_code == 200
    assert detail.json()["business_date"] == "2026-07-27"
    assert "raw_row_json" not in detail.text

    errors = client.get("/api/v1/clinic-days/CLN-001/2026-07-27/errors", params={"limit": 1, "offset": 0})
    assert errors.status_code == 200
    body = errors.json()
    assert body["count"] == 1
    assert body["errors"][0]["field_path"] == "payment_mode"
    assert body["errors"][0]["error_code"] == "FIELD_REQUIRED"
    assert "raw_row_json" not in errors.text

    missing = client.get("/api/v1/clinic-days/CLN-404/2026-07-27")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "CLINIC_DAY_NOT_FOUND"


def test_no_stale_narrative_returned_after_report_change(client, valid_rows):
    client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
    generated = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
    assert generated.status_code == 200

    changed = [dict(valid_rows[0])]
    changed[0]["amount_paid_paise"] = 4_500
    client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": changed})

    stale = client.get("/api/v1/clinic-days/CLN-001/2026-07-27/narrative")
    assert stale.status_code == 404
    assert stale.json()["error"]["code"] == "NARRATIVE_NOT_GENERATED"


def test_openapi_contract_contains_required_public_schema():
    from app.main import create_app

    schema = create_app().openapi()
    paths = schema["paths"]
    required = {
        "/api/v1/health": {"get"},
        "/api/v1/clinic-days": {"get"},
        "/api/v1/clinic-days/{clinic_id}/{business_date}": {"put", "get"},
        "/api/v1/clinic-days/{clinic_id}/{business_date}/errors": {"get"},
        "/api/v1/clinic-days/{clinic_id}/{business_date}/narrative": {"get", "post"},
    }
    for path, methods in required.items():
        assert path in paths
        assert methods.issubset(paths[path])

    put_operation = paths["/api/v1/clinic-days/{clinic_id}/{business_date}"]["put"]
    assert put_operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("BillingLogRequest")
    assert "ClinicDayResponse" in schema["components"]["schemas"]
    assert "ErrorResponse" in schema["components"]["schemas"]
    assert "/api/v1" in "\n".join(paths)
    serialized = str(schema)
    assert "raw_row_json" not in serialized

    reconciliation = schema["components"]["schemas"]["ReconciliationReport"]["properties"]
    assert reconciliation["total_billed_paise"]["type"] == "integer"
    assert reconciliation["total_collected_paise"]["type"] == "integer"
    assert schema["components"]["schemas"]["ClinicDayResponse"]["properties"]["operation"]["anyOf"][0]["type"] == "string"
