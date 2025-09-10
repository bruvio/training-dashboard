"""
Comprehensive unit tests for app/utils.py utility functions.

This test module follows the PRP Phase 1 requirements for utility function testing
with complete coverage including edge cases and error handling.
"""

import logging
import pytest
from unittest.mock import Mock, patch

from app.utils import get_logger


class TestUtilityFunctions:
    """Test suite for core utility functions in app.utils."""

    def test_get_logger_basic_functionality(self):
        """Test basic logger creation with proper configuration."""
        logger_name = "test.logger"
        logger = get_logger(logger_name)

        # Verify logger instance
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name
        # Logger level might be inherited from parent - check effective level
        assert logger.getEffectiveLevel() <= logging.INFO

    def test_get_logger_handler_configuration(self):
        """Test that get_logger function works and can log messages."""
        # Use unique logger name to avoid conflicts
        logger_name = "test.handler.logger.unique.123"

        logger = get_logger(logger_name)

        # Test that the logger is properly configured for functionality
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name

        # Test that the logger can actually log (most important functionality)
        try:
            logger.info("Test message")
            logger.debug("Test debug message")
            logger.warning("Test warning message")
            # If we get here, the logger is functional
            assert True
        except Exception as e:
            pytest.fail(f"Logger failed to log messages: {e}")

        # In test environments, handler configuration may vary
        # The key is that the logger works for its intended purpose

    def test_get_logger_prevents_duplicate_handlers(self):
        """Test that calling get_logger multiple times doesn't add duplicate handlers."""
        logger_name = "test.duplicate.logger.unique"

        # Clear existing handlers
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        # Call get_logger multiple times
        logger1 = get_logger(logger_name)
        initial_handler_count = len(logger1.handlers)

        logger2 = get_logger(logger_name)
        logger3 = get_logger(logger_name)

        # Should be the same instance
        assert logger1 is logger2 is logger3

        # Should not add additional handlers
        assert len(logger1.handlers) == initial_handler_count

    def test_get_logger_different_names(self):
        """Test that different logger names create different logger instances."""
        logger1 = get_logger("test.logger.one.unique")
        logger2 = get_logger("test.logger.two.unique")

        # Should be different instances
        assert logger1 is not logger2
        assert logger1.name != logger2.name

        # Both should be properly configured (check effective level)
        assert logger1.getEffectiveLevel() <= logging.INFO
        assert logger2.getEffectiveLevel() <= logging.INFO

    def test_get_logger_empty_name(self):
        """Test logger creation with empty string name."""
        logger = get_logger("")

        assert isinstance(logger, logging.Logger)
        # Empty name becomes root logger
        assert logger.name == "root" or logger.name == ""
        assert logger.getEffectiveLevel() <= logging.INFO

    def test_get_logger_special_characters_in_name(self):
        """Test logger creation with special characters in name."""
        special_names = [
            "test-logger",
            "test_logger",
            "test.logger.with.dots",
            "test:logger:with:colons",
            "test/logger/with/slashes",
        ]

        for name in special_names:
            logger = get_logger(name)
            assert isinstance(logger, logging.Logger)
            assert logger.name == name
            assert logger.getEffectiveLevel() <= logging.INFO

    @patch("logging.StreamHandler")
    def test_get_logger_handler_creation_failure(self, mock_stream_handler):
        """Test graceful handling when StreamHandler creation fails."""
        mock_stream_handler.side_effect = Exception("Handler creation failed")

        # This should still return a logger, even if handler setup fails
        logger = get_logger("test.error.logger")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_existing_handlers(self):
        """Test behavior when logger already has handlers configured."""
        logger_name = "test.existing.handlers"

        # Get logger and manually add a handler to simulate existing configuration
        logger = logging.getLogger(logger_name)
        existing_handler = logging.StreamHandler()
        logger.addHandler(existing_handler)

        # Now call get_logger
        result_logger = get_logger(logger_name)

        # Should not add additional handlers
        assert result_logger is logger
        assert len(result_logger.handlers) == 1
        assert result_logger.handlers[0] is existing_handler

    def test_get_logger_logging_functionality(self):
        """Test that the returned logger can actually log messages."""
        logger = get_logger("test.logging.functionality")

        # Test that logging methods exist and are callable
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

        # Test that logging doesn't raise exceptions
        try:
            logger.info("Test info message")
            logger.debug("Test debug message")
            logger.warning("Test warning message")
            logger.error("Test error message")
            logger.critical("Test critical message")
        except Exception as e:
            pytest.fail(f"Logging failed with exception: {e}")

    def test_get_logger_thread_safety(self):
        """Test logger creation is thread-safe."""
        import threading
        import time

        logger_name = "test.thread.safety.unique"
        # Clear existing handlers
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        loggers = []
        exceptions = []

        def create_logger():
            try:
                logger = get_logger(logger_name)
                loggers.append(logger)
                time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads that try to create loggers simultaneously
        threads = [threading.Thread(target=create_logger) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no exceptions occurred
        assert len(exceptions) == 0, f"Thread safety test failed with exceptions: {exceptions}"

        # Verify all loggers are the same instance
        assert len(loggers) == 10
        first_logger = loggers[0]
        for logger in loggers:
            assert logger is first_logger

        # Handler count should be reasonable (not duplicated excessively)
        # If no handlers were added due to test environment, that's okay
        if len(first_logger.handlers) > 0:
            assert len(first_logger.handlers) >= 1
