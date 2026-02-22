"""Structured logging configuration with request ID correlation."""

from __future__ import annotations

import logging
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

# Context variable to store the request ID across async boundaries
request_id_var: ContextVar[str] = ContextVar("request_id", default="unknown")


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request_id to log records from context variable."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to the log record.

        Args:
            record: The log record being processed.

        Returns:
            True to include the record in the log output.
        """
        record.request_id = request_id_var.get()
        return True


def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure structured JSON logging with request ID correlation.

    This sets up the root logger to output JSON-formatted logs with
    timestamp, log level, request ID, logger name, and message.

    Args:
        log_level: The logging level (default: INFO).
    """
    log_format = "%(asctime)s %(levelname)s %(request_id)s %(name)s %(message)s"
    formatter = jsonlogger.JsonFormatter(
        log_format,
        rename_fields={"levelname": "level", "asctime": "timestamp"},
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
