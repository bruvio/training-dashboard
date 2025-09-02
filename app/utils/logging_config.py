"""
Central logging configuration for the Garmin Dashboard application.

Provides consistent logging across all modules with proper formatting
and level management.
"""

import logging
from pathlib import Path
import sys
from typing import Optional


class DashboardLogger:
    """Centralized logger configuration for the Garmin Dashboard."""

    _configured = False
    _logger = None

    @classmethod
    def get_logger(cls, name: str = "garmin_dashboard") -> logging.Logger:
        """
        Get a configured logger instance.

        Args:
            name: Logger name, defaults to 'garmin_dashboard'

        Returns:
            Configured logger instance
        """
        if not cls._configured:
            cls.configure_logging()

        return logging.getLogger(name)

    @classmethod
    def configure_logging(
        cls, level: str = "INFO", log_file: Optional[Path] = None, console_output: bool = True
    ) -> None:
        """
        Configure application-wide logging.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            console_output: Whether to output to console
        """
        if cls._configured:
            return

        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Configure specific loggers to reduce noise
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

        cls._configured = True


def get_logger(name: str = "garmin_dashboard") -> logging.Logger:
    """
    Convenience function to get a configured logger.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return DashboardLogger.get_logger(name)


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log a function call with parameters.

    Args:
        func_name: Function name
        **kwargs: Function parameters to log
    """
    logger = get_logger()
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.debug(f"Calling {func_name}({params})")


def log_error(error: Exception, context: str = "") -> None:
    """
    Log an error with context.

    Args:
        error: Exception that occurred
        context: Additional context about where the error occurred
    """
    logger = get_logger()
    if context:
        logger.error(f"{context}: {error}", exc_info=True)
    else:
        logger.error(f"Error: {error}", exc_info=True)
