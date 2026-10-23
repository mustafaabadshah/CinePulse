"""Meilisearch index configurations and idempotent initialization."""

from typing import Any, Dict, List

from app.core.logging import logger
from app.search.client import get_meili_client
from meilisearch import Client
from meilisearch.errors import MeilisearchApiError

INDEX_RESEARCHERS = "researchers"
INDEX_PUBLICATIONS = "publications"
INDEX_INSTITUTIONS = "institutions"

ALL_INDEXES = [INDEX_RESEARCHERS, INDEX_PUBLICATIONS, INDEX_INSTITUTIONS]

INDEX_CONFIGS: Dict[str, Dict[str, Any]] = {
    INDEX_RESEARCHERS: {
        "primary_key": "id",
        "searchable_attributes": [
            "full_name",
            "research_interests",
            "biography",
            "institution_name",
            "department",
        ],
        "filterable_attributes": [
            "country",
            "institution_name",
            "research_interests",
            "is_synthetic",
            "contact_email_verified",
        ],
        "sortable_attributes": [
            "full_name",
            "country",
        ],
        "displayed_attributes": [
            "id",
            "full_name",
            "institution_id",
            "institution_name",
            "department",
            "country",
            "research_interests",
            "biography",
            "contact_email_verified",
            "contact_email",
            "contact_source_url",
            "official_profile_url",
            "is_synthetic",
        ],
        "ranking_rules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness",
        ],
        "typo_tolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8,
            },
        },
        "pagination": {
            "maxTotalHits": 2000,
        },
    },
    INDEX_PUBLICATIONS: {
        "primary_key": "id",
        "searchable_attributes": [
            "title",
            "abstract",
            "keywords",
            "authors",
            "venue",
        ],
        "filterable_attributes": [
            "publication_year",
            "venue",
            "keywords",
            "source_provider",
            "is_synthetic",
            "primary_institution_id",
        ],
        "sortable_attributes": [
            "publication_year",
            "title",
        ],
        "displayed_attributes": [
            "id",
            "title",
            "abstract",
            "authors",
            "primary_institution_id",
            "institution_name",
            "publication_year",
            "venue",
            "doi",
            "canonical_url",
            "keywords",
            "source_provider",
            "is_synthetic",
        ],
        "ranking_rules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness",
        ],
        "typo_tolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8,
            },
        },
        "pagination": {
            "maxTotalHits": 2000,
        },
    },
    INDEX_INSTITUTIONS: {
        "primary_key": "id",
        "searchable_attributes": [
            "name",
            "city",
            "country",
        ],
        "filterable_attributes": [
            "country",
            "city",
        ],
        "sortable_attributes": [
            "name",
            "country",
        ],
        "displayed_attributes": [
            "id",
            "name",
            "country",
            "city",
            "website_url",
            "ror_id",
        ],
        "ranking_rules": [
            "words",
            "typo",
            "proximity",
            "attribute",
            "sort",
            "exactness",
        ],
        "typo_tolerance": {
            "enabled": True,
            "minWordSizeForTypos": {
                "oneTypo": 4,
                "twoTypos": 8,
            },
        },
        "pagination": {
            "maxTotalHits": 2000,
        },
    },
}


def initialize_indexes(client: Client | None = None) -> List[Dict[str, Any]]:
    """Idempotently initializes all indexes and configures settings.

    Returns a list of task tracking status objects.
    """
    if client is None:
        client = get_meili_client()

    results = []

    for index_uid, config in INDEX_CONFIGS.items():
        logger.info(f"Configuring Meilisearch index: {index_uid}")

        # 1. Ensure index exists
        try:
            client.get_index(index_uid)
            logger.info(f"Index {index_uid} already exists.")
        except MeilisearchApiError as err:
            # Check if index_not_found
            if err.status_code == 404 or "not found" in str(err).lower():
                logger.info(f"Creating index {index_uid} with primary key {config['primary_key']}")
                task = client.create_index(index_uid, {"primaryKey": config["primary_key"]})
                client.wait_for_task(task.task_uid, timeout_in_ms=10000)
            else:
                raise err

        index = client.index(index_uid)

        # 2. Update settings
        settings_payload = {
            "searchableAttributes": config["searchable_attributes"],
            "filterableAttributes": config["filterable_attributes"],
            "sortableAttributes": config["sortable_attributes"],
            "displayedAttributes": config["displayed_attributes"],
            "rankingRules": config["ranking_rules"],
            "typoTolerance": config["typo_tolerance"],
            "pagination": config["pagination"],
        }

        task = index.update_settings(settings_payload)
        logger.info(f"Submitted settings update task {task.task_uid} for index {index_uid}")

        # Wait for settings task to finish
        completed_task = client.wait_for_task(task.task_uid, timeout_in_ms=10000)
        task_status = completed_task.status
        logger.info(f"Index {index_uid} settings update status: {task_status}")

        results.append(
            {
                "index": index_uid,
                "task_uid": task.task_uid,
                "status": task_status,
            }
        )

    return results
