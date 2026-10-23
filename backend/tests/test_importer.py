"""Tests for ingestion pipeline, dry-run mode, and duplicate handling."""

from app.ingestion.importer import IngestionPipeline
from app.models import Institution, SourceRecord


def test_dry_run_does_not_persist(db_session):
    pipeline = IngestionPipeline(db_session)
    data = {
        "institutions": [
            {
                "id": "inst_dry_test",
                "name": "Dry Run Institute",
                "country": "Germany",
                "city": "Berlin",
            }
        ],
        "researchers": [],
        "publications": [],
    }

    job = pipeline.run_import(data, source_name="dry_test", dry_run=True)
    assert job.status == "completed"
    assert job.records_processed == 1

    # Ensure institution was NOT saved to DB
    found = db_session.query(Institution).filter(Institution.id == "inst_dry_test").first()
    assert found is None


def test_real_import_persists_and_records_provenance(db_session):
    pipeline = IngestionPipeline(db_session)
    data = {
        "institutions": [
            {
                "id": "inst_real_test",
                "name": "Real Test Institute",
                "country": "Canada",
                "city": "Montreal",
                "website_url": "https://www.realtest.ca",
            }
        ],
        "researchers": [],
        "publications": [],
    }

    job = pipeline.run_import(data, source_name="unit_test", dry_run=False)
    assert job.status == "completed"
    assert job.records_created >= 1

    inst = db_session.query(Institution).filter(Institution.id == "inst_real_test").first()
    assert inst is not None
    assert inst.name == "Real Test Institute"

    # Check provenance
    prov = db_session.query(SourceRecord).filter(SourceRecord.entity_id == "inst_real_test").first()
    assert prov is not None
    assert prov.source_provider == "unit_test"
