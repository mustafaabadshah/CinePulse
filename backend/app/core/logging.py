"""Structured logging configuration for ResearchRadar."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields passed to logger
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "query"):
            log_obj["query"] = record.query
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            # Sanitize any sensitive keys
            clean_extra = {
                k: v
                for k, v in record.extra_data.items()
                if "key" not in k.lower()
                and "secret" not in k.lower()
                and "token" not in k.lower()
                and "password" not in k.lower()
            }
            log_obj.update(clean_extra)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures application-wide structured logger."""
    level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("researchradar")
    logger.setLevel(level)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logging()
