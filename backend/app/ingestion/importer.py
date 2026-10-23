"""Import engine: validates, deduplicates, stores canonical records, and indexes into Meilisearch."""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.logging import logger
from app.ingestion.normalizer import (
    compute_payload_hash,
    generate_institution_id,
    generate_publication_id,
    generate_researcher_id,
    normalize_text,
)
from app.ingestion.validator import (
    validate_institution_record,
    validate_publication_record,
    validate_researcher_record,
)
from app.models import (
    ImportJob,
    Institution,
    Publication,
    Researcher,
    SourceRecord,
)
from app.search.client import get_meili_client
from app.search.indexes import (
    INDEX_INSTITUTIONS,
    INDEX_PUBLICATIONS,
    INDEX_RESEARCHERS,
    initialize_indexes,
)
from sqlalchemy.orm import Session


class IngestionPipeline:
    def __init__(self, db: Session, client=None):
        self.db = db
        self.client = client or get_meili_client()

    def run_import(
        self, data: Dict[str, Any], source_name: str = "fixture_import", dry_run: bool = False
    ) -> ImportJob:
        """Executes full import pipeline: validation, deduplication, DB upsert, and Meilisearch indexing."""
        # 1. Create tracking job
        job = ImportJob(
            source_name=source_name,
            dry_run=dry_run,
            status="running",
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_failed=0,
            errors=[],
            meili_task_ids=[],
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        institution_docs: List[Dict[str, Any]] = []
        researcher_docs: List[Dict[str, Any]] = []
        publication_docs: List[Dict[str, Any]] = []

        try:
            # 2. Process Institutions
            raw_institutions = data.get("institutions", [])
            for raw_inst in raw_institutions:
                job.records_processed += 1
                clean, errors = validate_institution_record(raw_inst)
                if errors:
                    job.records_failed += 1
                    job.errors.append(
                        {"entity": "institution", "id": raw_inst.get("id"), "errors": errors}
                    )
                    continue

                if not clean.get("id"):
                    clean["id"] = generate_institution_id(clean["name"])

                payload_hash = compute_payload_hash(clean)

                if not dry_run:
                    existing = (
                        self.db.query(Institution).filter(Institution.id == clean["id"]).first()
                    )
                    if existing:
                        existing.name = clean["name"]
                        existing.normalized_name = normalize_text(clean["name"]).lower()
                        existing.country = clean["country"]
                        existing.city = clean["city"]
                        existing.website_url = clean["website_url"]
                        existing.ror_id = clean["ror_id"]
                        job.records_updated += 1
                    else:
                        inst_model = Institution(
                            id=clean["id"],
                            name=clean["name"],
                            normalized_name=normalize_text(clean["name"]).lower(),
                            country=clean["country"],
                            city=clean["city"],
                            website_url=clean["website_url"],
                            ror_id=clean["ror_id"],
                        )
                        self.db.add(inst_model)
                        job.records_created += 1

                    # Provenance
                    self._record_provenance(
                        entity_type="institution",
                        entity_id=clean["id"],
                        source_provider=source_name,
                        source_url=clean.get("website_url") or "local_fixture",
                        payload_hash=payload_hash,
                        is_verified=bool(clean.get("ror_id")),
                    )

                institution_docs.append(
                    {
                        "id": clean["id"],
                        "name": clean["name"],
                        "country": clean["country"],
                        "city": clean["city"],
                        "website_url": clean["website_url"],
                        "ror_id": clean["ror_id"],
                    }
                )

            if not dry_run:
                self.db.commit()

            # Cache institution names for denormalizing into researcher/publication search docs
            inst_name_map = {doc["id"]: doc["name"] for doc in institution_docs}
            if not dry_run:
                all_insts = self.db.query(Institution).all()
                for i in all_insts:
                    inst_name_map[i.id] = i.name

            # 3. Process Researchers
            raw_researchers = data.get("researchers", [])
            for raw_res in raw_researchers:
                job.records_processed += 1
                clean, errors = validate_researcher_record(raw_res)
                if errors:
                    job.records_failed += 1
                    job.errors.append(
                        {"entity": "researcher", "id": raw_res.get("id"), "errors": errors}
                    )
                    continue

                if not clean.get("id"):
                    clean["id"] = generate_researcher_id(
                        clean["full_name"], clean["institution_id"]
                    )

                payload_hash = compute_payload_hash(clean)
                inst_name = inst_name_map.get(clean["institution_id"], "Unknown Institution")

                if not dry_run:
                    existing_res = (
                        self.db.query(Researcher).filter(Researcher.id == clean["id"]).first()
                    )
                    if existing_res:
                        existing_res.full_name = clean["full_name"]
                        existing_res.official_profile_url = clean["official_profile_url"]
                        existing_res.institution_id = clean["institution_id"]
                        existing_res.department = clean["department"]
                        existing_res.country = clean["country"]
                        existing_res.research_interests = clean["research_interests"]
                        existing_res.biography = clean["biography"]
                        existing_res.contact_email_verified = clean["contact_email_verified"]
                        existing_res.contact_email = clean["contact_email"]
                        existing_res.contact_source_url = clean["contact_source_url"]
                        existing_res.last_verified_at = clean.get("last_verified_at")
                        existing_res.is_synthetic = clean["is_synthetic"]
                        job.records_updated += 1
                    else:
                        res_model = Researcher(
                            id=clean["id"],
                            full_name=clean["full_name"],
                            official_profile_url=clean["official_profile_url"],
                            institution_id=clean["institution_id"],
                            department=clean["department"],
                            country=clean["country"],
                            research_interests=clean["research_interests"],
                            biography=clean["biography"],
                            contact_email_verified=clean["contact_email_verified"],
                            contact_email=clean["contact_email"],
                            contact_source_url=clean["contact_source_url"],
                            last_verified_at=clean.get("last_verified_at"),
                            is_synthetic=clean["is_synthetic"],
                        )
                        self.db.add(res_model)
                        job.records_created += 1

                    self._record_provenance(
                        entity_type="researcher",
                        entity_id=clean["id"],
                        source_provider=source_name,
                        source_url=clean.get("contact_source_url")
                        or clean.get("official_profile_url")
                        or "local_fixture",
                        payload_hash=payload_hash,
                        is_verified=not clean["is_synthetic"] and clean["contact_email_verified"],
                    )

                researcher_docs.append(
                    {
                        "id": clean["id"],
                        "full_name": clean["full_name"],
                        "institution_id": clean["institution_id"],
                        "institution_name": inst_name,
                        "department": clean["department"],
                        "country": clean["country"],
                        "research_interests": clean["research_interests"],
                        "biography": clean["biography"],
                        "contact_email_verified": clean["contact_email_verified"],
                        "contact_email": clean["contact_email"],
                        "contact_source_url": clean["contact_source_url"],
                        "official_profile_url": clean["official_profile_url"],
                        "is_synthetic": clean["is_synthetic"],
                    }
                )

            if not dry_run:
                self.db.commit()

            # 4. Process Publications
            raw_publications = data.get("publications", [])
            for raw_pub in raw_publications:
                job.records_processed += 1
                clean, errors = validate_publication_record(raw_pub)
                if errors:
                    job.records_failed += 1
                    job.errors.append(
                        {"entity": "publication", "id": raw_pub.get("id"), "errors": errors}
                    )
                    continue

                if not clean.get("id"):
                    clean["id"] = generate_publication_id(
                        clean["title"], clean["publication_year"], clean.get("doi")
                    )

                payload_hash = compute_payload_hash(clean)
                inst_id = clean.get("primary_institution_id")
                inst_name = inst_name_map.get(inst_id, "") if inst_id else None

                if not dry_run:
                    existing_pub = (
                        self.db.query(Publication).filter(Publication.id == clean["id"]).first()
                    )
                    if existing_pub:
                        existing_pub.title = clean["title"]
                        existing_pub.abstract = clean["abstract"]
                        existing_pub.authors = clean["authors"]
                        existing_pub.primary_institution_id = clean["primary_institution_id"]
                        existing_pub.publication_year = clean["publication_year"]
                        existing_pub.venue = clean["venue"]
                        existing_pub.doi = clean["doi"]
                        existing_pub.canonical_url = clean["canonical_url"]
                        existing_pub.keywords = clean["keywords"]
                        existing_pub.source_provider = clean["source_provider"]
                        existing_pub.is_synthetic = clean["is_synthetic"]
                        job.records_updated += 1
                    else:
                        pub_model = Publication(
                            id=clean["id"],
                            title=clean["title"],
                            abstract=clean["abstract"],
                            authors=clean["authors"],
                            primary_institution_id=clean["primary_institution_id"],
                            publication_year=clean["publication_year"],
                            venue=clean["venue"],
                            doi=clean["doi"],
                            canonical_url=clean["canonical_url"],
                            keywords=clean["keywords"],
                            source_provider=clean["source_provider"],
                            is_synthetic=clean["is_synthetic"],
                        )
                        self.db.add(pub_model)
                        job.records_created += 1

                    self._record_provenance(
                        entity_type="publication",
                        entity_id=clean["id"],
                        source_provider=clean["source_provider"],
                        source_url=clean.get("canonical_url")
                        or clean.get("doi")
                        or "local_fixture",
                        payload_hash=payload_hash,
                        is_verified=not clean["is_synthetic"],
                    )

                publication_docs.append(
                    {
                        "id": clean["id"],
                        "title": clean["title"],
                        "abstract": clean["abstract"],
                        "authors": clean["authors"],
                        "primary_institution_id": clean["primary_institution_id"],
                        "institution_name": inst_name,
                        "publication_year": clean["publication_year"],
                        "venue": clean["venue"],
                        "doi": clean["doi"],
                        "canonical_url": clean["canonical_url"],
                        "keywords": clean["keywords"],
                        "source_provider": clean["source_provider"],
                        "is_synthetic": clean["is_synthetic"],
                    }
                )

            if not dry_run:
                self.db.commit()

            # 5. Submit documents to Meilisearch if not dry run
            if not dry_run:
                # Ensure indexes exist
                initialize_indexes(self.client)

                task_ids = []
                if institution_docs:
                    t_inst = self.client.index(INDEX_INSTITUTIONS).add_documents(
                        institution_docs, primary_key="id"
                    )
                    task_ids.append(t_inst.task_uid)

                if researcher_docs:
                    t_res = self.client.index(INDEX_RESEARCHERS).add_documents(
                        researcher_docs, primary_key="id"
                    )
                    task_ids.append(t_res.task_uid)

                if publication_docs:
                    t_pub = self.client.index(INDEX_PUBLICATIONS).add_documents(
                        publication_docs, primary_key="id"
                    )
                    task_ids.append(t_pub.task_uid)

                job.meili_task_ids = task_ids

                # Wait for Meilisearch indexing tasks to finish and verify their outcomes
                for tid in task_ids:
                    task = self.client.wait_for_task(tid, timeout_in_ms=10000)
                    if task.status != "succeeded":
                        err_msg = f"Meilisearch indexing task {tid} failed with status: {task.status}. Error: {getattr(task, 'error', None)}"
                        logger.error(err_msg)
                        job.errors.append({"task_uid": tid, "error": err_msg})
                        job.status = "failed"

            if job.status != "failed":
                job.status = "completed"

        except Exception as e:
            logger.exception(f"Unhandled error during ingestion: {e}")
            job.status = "failed"
            job.errors.append({"fatal_error": str(e)})

        finally:
            job.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)

        return job

    def _record_provenance(
        self,
        entity_type: str,
        entity_id: str,
        source_provider: str,
        source_url: str,
        payload_hash: str,
        is_verified: bool,
    ) -> None:
        """Records or updates data provenance."""
        existing = (
            self.db.query(SourceRecord)
            .filter(
                SourceRecord.entity_type == entity_type,
                SourceRecord.entity_id == entity_id,
            )
            .first()
        )
        if existing:
            existing.raw_payload_hash = payload_hash
            existing.source_url = source_url
            existing.is_verified = is_verified
            existing.source_provider = source_provider
        else:
            rec = SourceRecord(
                entity_type=entity_type,
                entity_id=entity_id,
                source_provider=source_provider,
                source_url=source_url,
                raw_payload_hash=payload_hash,
                is_verified=is_verified,
            )
            self.db.add(rec)
