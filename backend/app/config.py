"""Application Configuration module for ResearchRadar."""

import os
from typing import List, Set

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "researchradar.db").replace("\\", "/")
DEFAULT_DATA_DIR = os.path.join(PROJECT_ROOT, "data")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core Application
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    port: int = Field(default=8000, alias="PORT")
    host: str = Field(default="127.0.0.1", alias="HOST")

    # Security
    admin_api_key: str = Field(default="rr_admin_secret_dev_key_change_me", alias="ADMIN_API_KEY")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
    )

    # Database
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH}", alias="DATABASE_URL")

    # Meilisearch
    meili_http_addr: str = Field(default="http://127.0.0.1:7700", alias="MEILI_HTTP_ADDR")
    meili_master_key: str = Field(
        default="masterKey_ResearchRadar_Dev_2026_Secure", alias="MEILI_MASTER_KEY"
    )
    meili_timeout_ms: int = Field(default=5000, alias="MEILI_TIMEOUT_MS")

    # Search Limits
    default_search_limit: int = Field(default=20, alias="DEFAULT_SEARCH_LIMIT")
    max_search_limit: int = Field(default=100, alias="MAX_SEARCH_LIMIT")
    max_page_size: int = Field(default=50, alias="MAX_PAGE_SIZE")
    ingestion_batch_size: int = Field(default=100, alias="INGESTION_BATCH_SIZE")

    # CSV Data Ingestion Settings
    csv_data_dir: str = Field(default=DEFAULT_DATA_DIR, alias="CSV_DATA_DIR")
    csv_enrichment_file: str = Field(default="prod_enrichment.csv", alias="CSV_ENRICHMENT_FILE")
    csv_episodes_file: str = Field(default="episodes_prod.csv", alias="CSV_EPISODES_FILE")

    # Allowlisted Search Filters (Security hardening against arbitrary expressions)
    allowed_researcher_filters: Set[str] = {
        "country",
        "institution_name",
        "research_interests",
        "is_synthetic",
        "contact_email_verified",
    }

    allowed_publication_filters: Set[str] = {
        "publication_year",
        "venue",
        "keywords",
        "source_provider",
        "is_synthetic",
    }

    allowed_institution_filters: Set[str] = {"country", "city"}

    allowed_program_filters: Set[str] = {
        "type",
        "info_language",
        "channel_name",
        "info_content_type",
    }

    allowed_episode_filters: Set[str] = {
        "is_free",
        "content_tier",
        "genre",
        "language",
        "channel_name",
        "region",
        "is_vertical",
        "program_id",
    }

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
