"""
Comprehensive tests for app.utils.logging_config module.

Tests the DashboardLogger class and related logging utility functions
with various configurations and edge cases.
"""

import logging
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call
import sys

from app.utils.logging_config import DashboardLogger, get_logger, log_function_call, log_error


class TestDashboardLogger:
    """Test cases for the DashboardLogger class."""

    def setup_method(self):
        """Reset logger configuration before each test."""
        DashboardLogger._configured = False
        DashboardLogger._logger = None
        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_get_logger_default_name(self):
        """Test getting logger with default name."""
        logger = DashboardLogger.get_logger()

        assert isinstance(logger, logging.Logger)
        assert logger.name == "garmin_dashboard"
        assert DashboardLogger._configured is True

    def test_get_logger_custom_name(self):
        """Test getting logger with custom name."""
        custom_name = "test_logger"
        logger = DashboardLogger.get_logger(custom_name)

        assert isinstance(logger, logging.Logger)
        assert logger.name == custom_name
        assert DashboardLogger._configured is True

    def test_configure_logging_default_settings(self):
        """Test configure_logging with default settings."""
        DashboardLogger.configure_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) == 1  # Console handler only
        assert DashboardLogger._configured is True

    def test_configure_logging_custom_level(self):
        """Test configure_logging with custom level."""
        DashboardLogger.configure_logging(level="DEBUG")

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_no_console(self):
        """Test configure_logging without console output."""
        DashboardLogger.configure_logging(console_output=False)

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 0  # No handlers

    def test_configure_logging_with_file(self):
        """Test configure_logging with file handler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"

            DashboardLogger.configure_logging(log_file=log_file)

            root_logger = logging.getLogger()
            assert len(root_logger.handlers) == 2  # Console + file handlers

            # Test file handler exists
            file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1
            assert log_file.exists()

    def test_configure_logging_creates_log_directory(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "subdir" / "test.log"

            DashboardLogger.configure_logging(log_file=log_file)

            assert log_file.parent.exists()
            assert log_file.exists()

    def test_configure_logging_only_once(self):
        """Test that configure_logging only runs once."""
        # First call
        DashboardLogger.configure_logging(level="DEBUG")
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)

        # Second call should not add more handlers
        DashboardLogger.configure_logging(level="ERROR")
        assert len(root_logger.handlers) == initial_handler_count
        # Level should still be DEBUG from first call
        assert root_logger.level == logging.DEBUG

    def test_configure_logging_clears_existing_handlers(self):
        """Test that existing handlers are cleared."""
        # Add a handler first
        root_logger = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root_logger.addHandler(dummy_handler)
        initial_count = len(root_logger.handlers)

        DashboardLogger.configure_logging()

        # Should have only the new console handler
        assert len(root_logger.handlers) == 1

    def test_configure_logging_sets_third_party_levels(self):
        """Test that third-party logger levels are configured."""
        DashboardLogger.configure_logging()

        assert logging.getLogger("werkzeug").level == logging.WARNING
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("requests").level == logging.WARNING

    def test_configure_logging_invalid_level(self):
        """Test configure_logging with invalid level."""
        with pytest.raises(AttributeError):
            DashboardLogger.configure_logging(level="INVALID")

    def test_formatter_configuration(self):
        """Test that formatter is properly configured."""
        DashboardLogger.configure_logging()

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]
        formatter = handler.formatter

        assert isinstance(formatter, logging.Formatter)
        assert "%(asctime)s" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(levelname)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def setup_method(self):
        """Reset logger configuration before each test."""
        DashboardLogger._configured = False
        DashboardLogger._logger = None
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_get_logger_convenience_function(self):
        """Test the get_logger convenience function."""
        logger = get_logger()

        assert isinstance(logger, logging.Logger)
        assert logger.name == "garmin_dashboard"

    def test_get_logger_convenience_custom_name(self):
        """Test get_logger convenience function with custom name."""
        custom_name = "test_convenience"
        logger = get_logger(custom_name)

        assert isinstance(logger, logging.Logger)
        assert logger.name == custom_name

    @patch("app.utils.logging_config.get_logger")
    def test_log_function_call_basic(self, mock_get_logger):
        """Test log_function_call with basic parameters."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_function_call("test_function", param1="value1", param2="value2")

        mock_get_logger.assert_called_once()
        mock_logger.debug.assert_called_once()

        # Check the debug message format
        debug_call = mock_logger.debug.call_args[0][0]
        assert "test_function" in debug_call
        assert "param1=value1" in debug_call
        assert "param2=value2" in debug_call

    @patch("app.utils.logging_config.get_logger")
    def test_log_function_call_no_params(self, mock_get_logger):
        """Test log_function_call with no parameters."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_function_call("simple_function")

        mock_logger.debug.assert_called_once()
        debug_call = mock_logger.debug.call_args[0][0]
        assert "simple_function()" in debug_call

    @patch("app.utils.logging_config.get_logger")
    def test_log_function_call_special_values(self, mock_get_logger):
        """Test log_function_call with special parameter values."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        log_function_call("test_function", none_param=None, bool_param=True, int_param=42)

        debug_call = mock_logger.debug.call_args[0][0]
        assert "none_param=None" in debug_call
        assert "bool_param=True" in debug_call
        assert "int_param=42" in debug_call

    @patch("app.utils.logging_config.get_logger")
    def test_log_error_with_context(self, mock_get_logger):
        """Test log_error with context."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        test_error = ValueError("Test error message")
        context = "Test context"

        log_error(test_error, context)

        mock_get_logger.assert_called_once()
        mock_logger.error.assert_called_once()

        error_call = mock_logger.error.call_args
        assert "Test context" in error_call[0][0]
        assert "Test error message" in error_call[0][0]
        assert error_call[1]["exc_info"] is True

    @patch("app.utils.logging_config.get_logger")
    def test_log_error_without_context(self, mock_get_logger):
        """Test log_error without context."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        test_error = RuntimeError("Runtime error")

        log_error(test_error)

        error_call = mock_logger.error.call_args
        assert "Error: Runtime error" in error_call[0][0]
        assert error_call[1]["exc_info"] is True

    @patch("app.utils.logging_config.get_logger")
    def test_log_error_empty_context(self, mock_get_logger):
        """Test log_error with empty context."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        test_error = Exception("Generic error")

        log_error(test_error, "")

        error_call = mock_logger.error.call_args
        assert "Error: Generic error" in error_call[0][0]
        assert error_call[1]["exc_info"] is True


class TestLoggerIntegration:
    """Integration tests for logger functionality."""

    def setup_method(self):
        """Reset logger configuration before each test."""
        DashboardLogger._configured = False
        DashboardLogger._logger = None
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)

    def test_logger_output_integration(self):
        """Test that logger actually outputs messages."""
        with patch("sys.stdout") as mock_stdout:
            DashboardLogger.configure_logging(level="DEBUG")
            logger = get_logger("test_integration")

            logger.info("Test integration message")

            # Should have written to stdout
            mock_stdout.write.assert_called()

    def test_file_logging_integration(self):
        """Test that file logging works end-to-end."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "integration_test.log"

            DashboardLogger.configure_logging(level="INFO", log_file=log_file)
            logger = get_logger("file_test")

            test_message = "Integration test file message"
            logger.info(test_message)

            # Force flush handlers
            for handler in logging.getLogger().handlers:
                handler.flush()

            # Check file content
            assert log_file.exists()
            log_content = log_file.read_text()
            assert test_message in log_content
            assert "file_test" in log_content

    def test_multiple_loggers_same_config(self):
        """Test that multiple loggers share the same configuration."""
        DashboardLogger.configure_logging(level="WARNING")

        logger1 = get_logger("logger1")
        logger2 = get_logger("logger2")

        # Both should use the same root configuration
        assert logger1.getEffectiveLevel() == logging.WARNING
        assert logger2.getEffectiveLevel() == logging.WARNING

    def test_logger_hierarchy(self):
        """Test logger hierarchy works correctly."""
        DashboardLogger.configure_logging(level="INFO")

        parent_logger = get_logger("parent")
        child_logger = get_logger("parent.child")

        assert child_logger.parent == parent_logger
        assert child_logger.getEffectiveLevel() == logging.INFO
