"""Meilisearch indexer service for Programs and Episodes."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from meilisearch import Client
from meilisearch.errors import MeilisearchApiError
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.episode import Episode
from app.models.program import Program
from app.services.data_normalizer import normalize_thumbnail_url, split_tags
from app.search.client import get_meilisearch_client

INDEX_EPISODES = "episodes"
INDEX_PROGRAMS = "programs"

MEDIA_INDEX_CONFIGS: Dict[str, Dict[str, Any]] = {
    INDEX_EPISODES: {
        "primary_key": "id",
        "searchable_attributes": [
            "title",
            "program_name",
            "stars",
            "genre",
            "description",
            "channel_name",
            "meta_keywords",
        ],
        "filterable_attributes": [
            "is_free",
            "content_tier",
            "genre",
            "language",
            "channel_name",
            "region",
            "is_vertical",
            "program_id",
        ],
        "sortable_attributes": [
            "views",
            "duration_seconds",
            "episode_number",
            "title",
        ],
        "displayed_attributes": [
            "id",
            "program_id",
            "program_name",
            "title",
            "slug",
            "description",
            "episode_number",
            "duration",
            "duration_seconds",
            "views",
            "is_free",
            "is_enable",
            "content_tier",
            "genre",
            "genre_list",
            "region",
            "is_vertical",
            "thumbnail",
            "channel_name",
            "language",
            "stars",
            "stars_list",
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
            "maxTotalHits": 10000,
        },
    },
    INDEX_PROGRAMS: {
        "primary_key": "id",
        "searchable_attributes": [
            "name",
            "info_staring",
            "info_genre",
            "channel_name",
            "info_meta_keywords",
            "info_content_type",
        ],
        "filterable_attributes": [
            "type",
            "info_language",
            "info_genre",
            "channel_name",
            "info_content_type",
        ],
        "sortable_attributes": [
            "name",
        ],
        "displayed_attributes": [
            "id",
            "type",
            "name",
            "slug",
            "channel_name",
            "info_language",
            "info_genre",
            "genre_list",
            "info_meta_keywords",
            "info_content_type",
            "info_staring",
            "starring_list",
            "thumbnail",
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


def setup_media_indexes(client: Client) -> List[int]:
    """Ensures media indexes exist and have exact settings configured."""
    task_uids = []
    for index_uid, cfg in MEDIA_INDEX_CONFIGS.items():
        try:
            # Check if index exists or create
            client.get_index(index_uid)
        except MeilisearchApiError:
            task = client.create_index(uid=index_uid, options={"primaryKey": cfg["primary_key"]})
            task_uids.append(task.task_uid)

        idx = client.index(index_uid)
        settings_payload = {
            "searchableAttributes": cfg["searchable_attributes"],
            "filterableAttributes": cfg["filterable_attributes"],
            "sortableAttributes": cfg["sortable_attributes"],
            "displayedAttributes": cfg["displayed_attributes"],
            "rankingRules": cfg["ranking_rules"],
            "typoTolerance": cfg["typo_tolerance"],
            "pagination": cfg["pagination"],
        }
        task = idx.update_settings(settings_payload)
        task_uids.append(task.task_uid)
    return task_uids


def wait_for_meili_tasks(
    client: Client,
    task_uids: List[int],
    timeout_sec: float = 60.0,
    poll_interval: float = 0.25,
) -> Dict[str, Any]:
    """Polls Meilisearch tasks with bounded backoff until completion."""
    start_time = time.time()
    pending = set(task_uids)
    task_statuses: Dict[int, Dict[str, Any]] = {}

    while pending and (time.time() - start_time) < timeout_sec:
        for uid in list(pending):
            try:
                task = client.get_task(uid)
                status = getattr(task, "status", None) or (task.get("status") if isinstance(task, dict) else None)
                if status in ("succeeded", "failed", "canceled"):
                    pending.remove(uid)
                    task_statuses[uid] = {
                        "status": status,
                        "type": getattr(task, "type", "") if hasattr(task, "type") else task.get("type", ""),
                        "error": getattr(task, "error", None) if hasattr(task, "error") else task.get("error", None),
                    }
            except Exception as e:
                logger.warning(f"Error checking task {uid}: {e}")
        if pending:
            time.sleep(poll_interval)

    all_succeeded = all(s.get("status") == "succeeded" for s in task_statuses.values()) and not pending
    return {
        "all_succeeded": all_succeeded,
        "completed": len(task_statuses),
        "total": len(task_uids),
        "pending": list(pending),
        "task_statuses": task_statuses,
    }


def program_to_search_doc(p: Program, thumbnail: Optional[str] = None) -> Dict[str, Any]:
    """Transforms a Program ORM model into a Meilisearch document."""
    return {
        "id": p.id,
        "type": p.type,
        "name": p.name,
        "slug": p.slug,
        "channel_name": p.channel_name,
        "info_language": p.info_language,
        "info_genre": p.info_genre,
        "genre_list": split_tags(p.info_genre),
        "info_meta_keywords": p.info_meta_keywords,
        "info_content_type": p.info_content_type,
        "info_staring": p.info_staring,
        "starring_list": split_tags(p.info_staring),
        "thumbnail": thumbnail,
    }


def episode_to_search_doc(ep: Episode, program: Optional[Program] = None) -> Dict[str, Any]:
    """Transforms an Episode ORM model into an enriched Meilisearch document."""
    # Denormalize parent program fields if available
    prog_name = program.name if program else None
    chan_name = ep.channel_name or (program.channel_name if program else None)
    lang = program.info_language if program else None
    stars = program.info_staring if program else None

    return {
        "id": ep.id,
        "program_id": ep.program_id or ep.raw_program_id,
        "program_name": prog_name,
        "title": ep.title,
        "slug": ep.slug,
        "description": ep.description,
        "episode_number": ep.episode_number,
        "duration": ep.duration,
        "duration_seconds": ep.duration_seconds,
        "views": ep.views,
        "is_free": ep.is_free,
        "is_enable": ep.is_enable,
        "content_tier": ep.content_tier,
        "genre": ep.genre,
        "genre_list": split_tags(ep.genre),
        "region": ep.region,
        "is_vertical": ep.is_vertical,
        "thumbnail": normalize_thumbnail_url(ep.thumbnail),
        "channel_name": chan_name,
        "language": lang,
        "stars": stars,
        "stars_list": split_tags(stars),
    }


def sync_programs_to_index(
    client: Client,
    programs: List[Program],
    program_thumbnails: Optional[Dict[str, str]] = None,
    batch_size: int = 500,
) -> List[int]:
    """Batches and upserts Program documents into Meilisearch."""
    idx = client.index(INDEX_PROGRAMS)
    docs = [
        program_to_search_doc(p, program_thumbnails.get(p.id) if program_thumbnails else None)
        for p in programs
    ]
    task_uids = []
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        task = idx.add_documents(batch, primary_key="id")
        task_uids.append(task.task_uid)
    return task_uids


def sync_episodes_to_index(
    client: Client,
    episodes: List[Episode],
    programs_map: Dict[str, Program],
    batch_size: int = 500,
) -> List[int]:
    """Batches and upserts Episode documents into Meilisearch."""
    idx = client.index(INDEX_EPISODES)
    docs = [episode_to_search_doc(ep, programs_map.get(ep.program_id or "")) for ep in episodes]
    task_uids = []
    for i in range(0, len(docs), batch_size):
        batch = docs[i : i + batch_size]
        task = idx.add_documents(batch, primary_key="id")
        task_uids.append(task.task_uid)
    return task_uids


def rebuild_media_indexes_from_db(db: Session, client: Client) -> Dict[str, Any]:
    """Rebuilds the media indexes directly from the canonical database."""
    setup_tasks = setup_media_indexes(client)
    wait_for_meili_tasks(client, setup_tasks, timeout_sec=20.0)

    # Clean existing documents to ensure exact synchronization with the database
    clean_tasks = [
        client.index(INDEX_PROGRAMS).delete_all_documents().task_uid,
        client.index(INDEX_EPISODES).delete_all_documents().task_uid,
    ]
    wait_for_meili_tasks(client, clean_tasks, timeout_sec=20.0)

    programs = db.query(Program).all()
    programs_map = {p.id: p for p in programs}
    episodes = db.query(Episode).all()

    # Precompute program thumbnails inherited from child episodes
    program_thumbnails: Dict[str, str] = {}
    for ep in episodes:
        pid = ep.program_id or ep.raw_program_id
        if pid and pid not in program_thumbnails and ep.thumbnail:
            norm_thumb = normalize_thumbnail_url(ep.thumbnail)
            if norm_thumb:
                program_thumbnails[pid] = norm_thumb

    prog_tasks = sync_programs_to_index(client, programs, program_thumbnails)
    ep_tasks = sync_episodes_to_index(client, episodes, programs_map)

    all_tasks = prog_tasks + ep_tasks
    report = wait_for_meili_tasks(client, all_tasks, timeout_sec=60.0)

    return {
        "status": "completed" if report["all_succeeded"] else "partial",
        "programs_count": len(programs),
        "episodes_count": len(episodes),
        "tasks_total": len(all_tasks),
        "task_report": report,
    }


def get_media_index_consistency(db: Session, client: Client) -> Dict[str, Any]:
    """Compares database records and indexed document counts."""
    db_programs_count = db.query(Program).count()
    db_episodes_count = db.query(Episode).count()

    meili_programs_count = 0
    meili_episodes_count = 0
    try:
        meili_programs_count = client.index(INDEX_PROGRAMS).get_stats().number_of_documents
    except Exception:
        pass

    try:
        meili_episodes_count = client.index(INDEX_EPISODES).get_stats().number_of_documents
    except Exception:
        pass

    return {
        "programs": {
            "database_count": db_programs_count,
            "indexed_count": meili_programs_count,
            "is_consistent": db_programs_count == meili_programs_count,
        },
        "episodes": {
            "database_count": db_episodes_count,
            "indexed_count": meili_episodes_count,
            "is_consistent": db_episodes_count == meili_episodes_count,
        },
    }


class MeilisearchIndexer:
    """Service class encapsulating Meilisearch index operations for Programs and Episodes."""

    def __init__(self, db: Session, client: Optional[Client] = None):
        self.db = db
        self.client = client or get_meilisearch_client()

    def setup_indexes(self) -> Dict[str, Any]:
        task_uids = setup_media_indexes(self.client)
        report = wait_for_meili_tasks(self.client, task_uids, timeout_sec=30.0)
        return {"status": "configured", "report": report}

    def index_programs(self, batch_size: int = 500) -> Dict[str, Any]:
        programs = self.db.query(Program).all()
        task_uids = sync_programs_to_index(self.client, programs, batch_size=batch_size)
        report = wait_for_meili_tasks(self.client, task_uids, timeout_sec=60.0)
        return {"documents_indexed": len(programs), "task_report": report}

    def index_episodes(self, batch_size: int = 500) -> Dict[str, Any]:
        programs = self.db.query(Program).all()
        programs_map = {p.id: p for p in programs}
        episodes = self.db.query(Episode).all()
        task_uids = sync_episodes_to_index(self.client, episodes, programs_map, batch_size=batch_size)
        report = wait_for_meili_tasks(self.client, task_uids, timeout_sec=90.0)
        return {"documents_indexed": len(episodes), "task_report": report}

    def rebuild_all(self) -> Dict[str, Any]:
        return rebuild_media_indexes_from_db(self.db, self.client)

    def get_index_status(self) -> Dict[str, Any]:
        consistency = get_media_index_consistency(self.db, self.client)
        return {
            "healthy": True,
            "indexes": {
                INDEX_EPISODES: consistency["episodes"],
                INDEX_PROGRAMS: consistency["programs"],
            },
        }

