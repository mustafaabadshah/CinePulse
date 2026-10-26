"""Meilisearch index configurations and idempotent initialization for Tamasha media catalog."""

from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.search.client import get_meili_client
from meilisearch import Client
from meilisearch.errors import MeilisearchApiError

from app.services.meilisearch_indexer import (
    INDEX_EPISODES,
    INDEX_PROGRAMS,
    MEDIA_INDEX_CONFIGS,
)

ALL_INDEXES = [
    INDEX_EPISODES,
    INDEX_PROGRAMS,
]

INDEX_CONFIGS: Dict[str, Dict[str, Any]] = MEDIA_INDEX_CONFIGS


def initialize_indexes(client: Optional[Client] = None) -> List[Dict[str, Any]]:
    """Idempotently initializes all media indexes and configures settings."""
    if client is None:
        client = get_meili_client()

    results = []

    for index_uid, config in INDEX_CONFIGS.items():
        logger.info(f"Configuring Meilisearch media index: {index_uid}")

        # 1. Ensure index exists
        try:
            client.get_index(index_uid)
            logger.info(f"Index {index_uid} already exists.")
        except MeilisearchApiError as err:
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
