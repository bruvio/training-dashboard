"""
Utility functions for the Garmin Dashboard application.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with consistent formatting.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if no handlers exist (prevent duplicate configuration)
    if not logger.handlers:
        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Create console handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
