"""Structured JSON Logging (Criteria 13).

Configures structlog to output machine-readable structured JSON logs with
timestamps, correlation IDs, agent identifiers, log levels, and automatic
PII redaction (Criteria 16) across all logging pipelines.
"""

import logging
import sys
from typing import Any, MutableMapping
import structlog
from app.observability.pii import redact_pii


def pii_redacting_processor(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """Processor to scrub PII from all keys and values in log event dictionaries."""
    return redact_pii(dict(event_dict))


def setup_logging(log_level: str = "INFO") -> None:
    """Configures structured JSON logging globally."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            pii_redacting_processor,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "ai_in_5_days") -> structlog.stdlib.BoundLogger:
    """Returns a bound structured JSON logger with context."""
    return structlog.get_logger(name)


# Initialize structured logging on import
setup_logging()
logger = get_logger("app.root")
