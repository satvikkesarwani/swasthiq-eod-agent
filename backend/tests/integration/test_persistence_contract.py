import os
import subprocess
import sys
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.integrations.llm_provider import DisabledNarrativeProvider
from app.main import create_app
from app.models import ClinicDay, IngestionError, LineItem, Visit
from app.repositories.clinic_day_repository import ClinicDayRepository


def client_for_database(database_url: str, *, app_env: str = "test") -> TestClient:
    app = create_app(
        settings=Settings(app_env=app_env, database_url=database_url, cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )
    return TestClient(app, raise_server_exceptions=True)


def run_alembic(tmp_path, command: str) -> str:
    db_path = tmp_path / "migration_contract.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    result = subprocess.run(
        [sys.executable, "-m", "alembic", command, "head" if command == "upgrade" else "base"],
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return env["DATABASE_URL"]


def clone_row(row: dict, *, visit_id: str, timestamp: str | None = None) -> dict:
    copied = dict(row)
    copied["visit_id"] = visit_id
    if timestamp is not None:
        copied["timestamp"] = timestamp
    copied["line_items"] = [dict(item) for item in row["line_items"]]
    return copied


def counts(client: TestClient) -> tuple[int, int, int, int]:
    with client.app.state.session_factory() as session:
        return (
            session.query(ClinicDay).count(),
            session.query(Visit).count(),
            session.query(LineItem).count(),
            session.query(IngestionError).count(),
        )


def test_migration_upgrade_downgrade_reupgrade_and_application_use(tmp_path, valid_rows):
    database_url = run_alembic(tmp_path, "upgrade")
    db_path = tmp_path / "migration_contract.db"

    app = create_app(
        settings=Settings(app_env="development", database_url=database_url, cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )
    inspector = inspect(app.state.engine)
    assert set(inspector.get_table_names()) >= {"clinic_days", "visits", "line_items", "ingestion_errors", "narratives"}
    with app.state.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1

    clinic_day_indexes = {index["name"] for index in inspector.get_indexes("clinic_days")}
    assert "ix_clinic_days_clinic_business_date" in clinic_day_indexes
    assert "ix_visits_payment_mode" in {index["name"] for index in inspector.get_indexes("visits")}
    assert "ix_ingestion_errors_clinic_day_row" in {index["name"] for index in inspector.get_indexes("ingestion_errors")}

    with TestClient(app) as client:
        response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        assert response.status_code == 200
        assert response.json()["operation"] == "created"
    app.state.engine.dispose()

    run_alembic(tmp_path, "downgrade")
    app_after_downgrade = create_app(
        settings=Settings(app_env="development", database_url=database_url, cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )
    assert inspect(app_after_downgrade.state.engine).get_table_names() == ["alembic_version"]
    app_after_downgrade.state.engine.dispose()

    run_alembic(tmp_path, "upgrade")
    app_after_reupgrade = create_app(
        settings=Settings(app_env="development", database_url=database_url, cors_origins=["http://test"]),
        narrative_provider=DisabledNarrativeProvider(),
    )
    assert "clinic_days" in inspect(app_after_reupgrade.state.engine).get_table_names()
    app_after_reupgrade.state.engine.dispose()
    assert db_path.exists()


def test_unique_constraints_and_same_visit_id_on_different_days(valid_rows):
    with client_for_database("sqlite://") as client:
        first = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": [valid_rows[0]]})
        second_row = clone_row(valid_rows[0], visit_id="V-001", timestamp="2026-07-28T09:00:00Z")
        second = client.put("/api/v1/clinic-days/CLN-001/2026-07-28", json={"records": [second_row]})
        assert first.status_code == 200
        assert second.status_code == 200

        with client.app.state.session_factory() as session:
            duplicate_day = ClinicDay(
                clinic_id="CLN-001",
                business_date=date(2026, 7, 27),
                status="completed",
                received_rows=0,
                accepted_rows=0,
                rejected_rows=0,
                source_hash="sha256:" + "a" * 64,
                report_hash="sha256:" + "b" * 64,
                report_json=first.json()["report"],
            )
            session.add(duplicate_day)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            clinic_day = session.query(ClinicDay).filter_by(clinic_id="CLN-001", business_date=date(2026, 7, 27)).one()
            duplicate_visit = Visit(
                clinic_day_id=clinic_day.id,
                visit_id="V-001",
                timestamp_utc=datetime(2026, 7, 27, 9, tzinfo=timezone.utc),
                doctor_id="DOC-X",
                payment_mode="cash",
                amount_paid_paise=0,
                discount_paise=0,
                is_refund=False,
                gross_line_total_paise=0,
                billed_paise=0,
                outstanding_paise=0,
            )
            session.add(duplicate_visit)
            with pytest.raises(IntegrityError):
                session.commit()


def test_replacement_is_atomic_and_rolls_back_on_repository_failure(monkeypatch, valid_rows):
    with client_for_database("sqlite://") as client:
        created = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        original_hash = created.json()["report_hash"]
        original_counts = counts(client)
        original_replace = ClinicDayRepository.replace

        def failing_replace(self, **kwargs):
            original_replace(self, **kwargs)
            raise RuntimeError("controlled persistence failure")

        monkeypatch.setattr(ClinicDayRepository, "replace", failing_replace)
        changed = [clone_row(valid_rows[0], visit_id="V-CHANGED")]
        changed[0]["amount_paid_paise"] = 4_500

        with pytest.raises(RuntimeError):
            client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": changed})

        monkeypatch.setattr(ClinicDayRepository, "replace", original_replace)
        assert counts(client) == original_counts
        assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27").json()["report_hash"] == original_hash


def test_repeated_replacement_has_no_duplicate_children_or_orphans(valid_rows):
    with client_for_database("sqlite://") as client:
        client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        replacement = [valid_rows[1]]
        for _ in range(3):
            response = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": replacement})
            assert response.status_code == 200

        assert counts(client) == (1, 1, 1, 0)
        with client.app.state.session_factory() as session:
            assert session.query(LineItem).outerjoin(Visit).filter(Visit.id.is_(None)).count() == 0
            assert session.query(IngestionError).outerjoin(ClinicDay).filter(ClinicDay.id.is_(None)).count() == 0

            clinic_day = session.query(ClinicDay).one()
            session.delete(clinic_day)
            session.commit()
            assert session.query(Visit).count() == 0
            assert session.query(LineItem).count() == 0
            assert session.query(IngestionError).count() == 0


def test_hash_semantics_and_narrative_invalidation(valid_rows):
    with client_for_database("sqlite://") as client:
        created = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        first = created.json()
        narrative = client.post("/api/v1/clinic-days/CLN-001/2026-07-27/narrative", json={"force_regenerate": False})
        assert narrative.json()["status"] == "fallback"

        unchanged = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": valid_rows})
        assert unchanged.json()["operation"] == "unchanged"
        assert unchanged.json()["source_hash"] == first["source_hash"]
        assert unchanged.json()["report_hash"] == first["report_hash"]
        assert unchanged.json()["narrative_status"] == "fallback"

        metadata_only = client.put(
            "/api/v1/clinic-days/CLN-001/2026-07-27",
            json={"clinic_name": "Different Name", "records": valid_rows},
        )
        assert metadata_only.json()["operation"] == "replaced"
        assert metadata_only.json()["source_hash"] != first["source_hash"]
        assert metadata_only.json()["report_hash"] == first["report_hash"]
        assert metadata_only.json()["narrative_status"] == "fallback"

        changed = [dict(valid_rows[0])]
        changed[0]["amount_paid_paise"] = 4_500
        changed_report = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": changed})
        assert changed_report.json()["report_hash"] != first["report_hash"]
        assert changed_report.json()["narrative_status"] == "not_generated"

        invalid = dict(valid_rows[0])
        invalid.pop("payment_mode")
        rejected = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": [invalid]})
        assert rejected.status_code == 422
        assert client.get("/api/v1/clinic-days/CLN-001/2026-07-27").json()["report_hash"] == changed_report.json()["report_hash"]

        empty = client.put("/api/v1/clinic-days/CLN-001/2026-07-27", json={"records": []})
        assert empty.status_code == 200
        assert empty.json()["operation"] == "replaced"
        assert empty.json()["report"]["reconciliation"]["total_billed_paise"] == 0
