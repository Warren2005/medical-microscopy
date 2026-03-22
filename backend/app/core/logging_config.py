"""
Structured logging configuration using JSON format.

Benefits:
- Machine-parseable logs (easy to grep, search, analyze)
- Consistent format across all log messages
- Includes context: timestamp, level, module, function
- Pretty-printed in development, compact in production
"""

import logging
import sys

from app.core.config import settings


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(settings.log_level)
    logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    logger.addHandler(console_handler)
    return logger


# Create logger instance
# Import this in other modules: from app.core.logging_config import logger
logger = setup_logging()