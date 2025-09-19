"""
Logging Configuration Module
Structured logging for the entire application
"""

import os
import sys
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any
import structlog
from pathlib import Path


class LoggingConfig:
    def __init__(self):
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
        self.LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

        # Ensure log directory exists
        Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    def setup_logging(self):
        """Setup structured logging"""

        # Configure standard logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, self.LOG_LEVEL.upper())
        )

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                self._add_service_context,
                structlog.processors.JSONRenderer() if self.LOG_FORMAT == "json"
                else structlog.dev.ConsoleRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger()

    def _add_service_context(self, logger, name, event_dict):
        """Add service context to logs"""
        event_dict["service"] = "jee-smart-ai-platform"
        event_dict["version"] = "1.0.0"
        event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
        return event_dict

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                },
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.LOG_LEVEL,
                    "formatter": "json" if self.LOG_FORMAT == "json" else "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.LOG_LEVEL,
                    "formatter": "json" if self.LOG_FORMAT == "json" else "standard",
                    "filename": self.LOG_FILE,
                    "maxBytes": 10485760,  # 10MB
                    "backupCount": 5
                }
            },
            "loggers": {
                "": {
                    "handlers": ["console", "file"],
                    "level": self.LOG_LEVEL,
                    "propagate": False
                },
                "uvicorn": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False
                },
                "sqlalchemy.engine": {
                    "handlers": ["file"],
                    "level": "WARNING",
                    "propagate": False
                }
            }
        }


# Global logging setup
logging_config = LoggingConfig()
logger = logging_config.setup_logging()

# Export configured logger
__all__ = ["logger", "logging_config"]
