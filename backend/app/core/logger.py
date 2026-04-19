"""Structured logging with correlation IDs."""

import json
import sys
from typing import Dict, Any, Optional
from contextvars import ContextVar
from datetime import datetime

# Context variable for correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class StructuredLogger:
    """Structured JSON logger with correlation ID support."""

    def __init__(self, name: str):
        self.name = name

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None
    ):
        """Emit structured log entry."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
            "correlation_id": correlation_id.get(""),
        }

        if extra:
            entry["extra"] = extra

        if error:
            entry["error"] = {
                "type": type(error).__name__,
                "message": str(error),
            }

        # Output to stderr for production (stdout is for app output)
        print(json.dumps(entry), file=sys.stderr)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self._log("DEBUG", message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self._log("INFO", message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        self._log("WARNING", message, extra)

    def error(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        self._log("ERROR", message, extra, error)

    def critical(self, message: str, error: Optional[Exception] = None, extra: Optional[Dict[str, Any]] = None):
        self._log("CRITICAL", message, extra, error)


def set_correlation_id(cid: str):
    """Set correlation ID for current context."""
    correlation_id.set(cid)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return correlation_id.get("")


def clear_correlation_id():
    """Clear correlation ID from context."""
    correlation_id.set("")


# Default logger instance
logger = StructuredLogger("wine_verify")
