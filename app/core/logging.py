"""
Structured logging configuration for the application.
"""

import json
import logging
import os
from datetime import datetime
from logging.config import dictConfig
from typing import Any

from fastapi import Request
from loguru import logger


class StructuredFormatter:
    """Custom formatter for structured JSON logging."""

    def format(self, record: dict[str, Any]) -> str:
        """Format log record as structured JSON."""
        # Extract Loguru record fields
        timestamp = record["time"].isoformat()
        level = record["level"].name
        message = record["message"]
        module = record["name"]
        function = record["function"]
        line = record["line"]

        # Build structured log entry
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "module": module,
            "function": function,
            "line": line,
            "process_id": os.getpid(),
        }

        # Add extra fields if present
        if record.get("extra"):
            log_entry.update(record["extra"])

        # Add exception info if present
        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }

        return json.dumps(log_entry, ensure_ascii=False)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "app.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 10,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console", "file"], "level": "INFO"},
        "fastapi": {"handlers": ["console", "file"], "level": "INFO"},
        "app": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

def setup_logging():
    """Applies the logging configuration."""
    dictConfig(LOGGING_CONFIG)

def get_logger(name: str) -> logging.Logger:
    """Retrieves a logger instance."""
    return logging.getLogger(name)


# Middleware for request logging
class LoggingMiddleware:
    """Middleware to log HTTP requests and responses."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info
        request_start = datetime.now()
        request = Request(scope, receive)

        # Prepare request log data
        request_data = {
            "log_type": "access",
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request.headers.get("x-request-id", "unknown"),
        }

        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            **request_data
        )

        # Process response
        response_body = b""
        status_code = 500

        async def send_wrapper(message):
            nonlocal response_body, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exception=e,
                **request_data
            )
            raise
        finally:
            # Calculate duration
            request_duration = (datetime.now() - request_start).total_seconds()

            # Log response
            response_data = {
                **request_data,
                "status_code": status_code,
                "response_size": len(response_body),
                "duration_seconds": request_duration,
            }

            # Log level based on status code
            if status_code >= 500:
                log_level = "error"
            elif status_code >= 400:
                log_level = "warning"
            else:
                log_level = "info"

            getattr(logger, log_level)(
                f"Response: {status_code} {request.method} {request.url.path} ({request_duration:.3f}s)",
                **response_data
            )


# Security audit logging
def log_security_event(
    event_type: str,
    details: dict[str, Any],
    request: Request | None = None,
    severity: str = "info"
) -> None:
    """Log security-related events."""

    audit_data = {
        "log_type": "audit",
        "event_type": event_type,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        **details
    }

    if request:
        audit_data.update({
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "request_id": request.headers.get("x-request-id"),
            "url": str(request.url),
            "method": request.method,
        })

    getattr(logger, severity)(
        f"Security event: {event_type}",
        **audit_data
    )


# Performance monitoring
def log_performance_metric(
    metric_name: str,
    value: float,
    unit: str = "seconds",
    tags: dict[str, str] | None = None
) -> None:
    """Log performance metrics."""

    metric_data = {
        "log_type": "metrics",
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.now().isoformat(),
    }

    if tags:
        metric_data["tags"] = tags

    logger.info(
        f"Metric: {metric_name}={value}{unit}",
        **metric_data
    )


# Database operation logging
def log_database_operation(
    operation: str,
    table: str,
    duration: float,
    records_affected: int | None = None,
    error: str | None = None
) -> None:
    """Log database operations for monitoring."""

    db_data = {
        "log_type": "database",
        "operation": operation,
        "table": table,
        "duration_ms": duration * 1000,
        "timestamp": datetime.now().isoformat(),
    }

    if records_affected is not None:
        db_data["records_affected"] = records_affected

    if error:
        db_data["error"] = error
        logger.error(f"Database error: {operation} on {table}", **db_data)
    else:
        logger.info(f"Database: {operation} on {table} ({duration:.3f}s)", **db_data)


# Business logic logging
def log_business_event(
    event_name: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
    user_id: str | None = None
) -> None:
    """Log business logic events."""

    business_data = {
        "log_type": "business",
        "event_name": event_name,
        "entity_type": entity_type,
        "timestamp": datetime.now().isoformat(),
    }

    if entity_id:
        business_data["entity_id"] = entity_id

    if user_id:
        business_data["user_id"] = user_id

    if details:
        business_data.update(details)

    logger.info(
        f"Business event: {event_name} on {entity_type}",
        **business_data
    )


# Error context manager
class ErrorContext:
    """Context manager for error logging with additional context."""

    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        logger.info(f"Starting: {self.operation}", **self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()

        if exc_type:
            logger.error(
                f"Failed: {self.operation} ({duration:.3f}s)",
                exception=exc_val,
                **self.context
            )
        else:
            logger.info(
                f"Completed: {self.operation} ({duration:.3f}s)",
                **self.context
            )

        return False  # Don't suppress exceptions


# Health check logging
def log_health_check(component: str, status: str, details: dict[str, Any] | None = None) -> None:
    """Log health check results."""

    health_data = {
        "log_type": "health",
        "component": component,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }

    if details:
        health_data.update(details)

    log_level = "info" if status == "healthy" else "error"
    getattr(logger, log_level)(
        f"Health check: {component} is {status}",
        **health_data
    )
