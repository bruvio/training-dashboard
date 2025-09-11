"""
Comprehensive tests for app.utils.save_activity_page module.

Tests the save_rendered_page function and command-line interface
with various scenarios including error handling.
"""

import argparse
import pytest
from unittest.mock import Mock, patch, mock_open

from app.utils.save_activity_page import save_rendered_page, main


class TestSaveRenderedPage:
    """Test cases for the save_rendered_page function."""

    @patch("app.utils.save_activity_page.sync_playwright")
    def test_save_rendered_page_success(self, mock_sync_playwright):
        """Test successful page rendering and saving."""
        # Setup mocks
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = "<html><body>Test content</body></html>"

        # Mock file writing
        with patch("builtins.open", mock_open()) as mock_file:
            save_rendered_page("http://test.com", "output.html")

            # Verify browser interactions
            mock_playwright.chromium.launch.assert_called_once_with(headless=True)
            mock_browser.new_page.assert_called_once()
            mock_page.goto.assert_called_once_with("http://test.com")
            mock_page.wait_for_load_state.assert_called_once_with("networkidle")
            mock_page.content.assert_called_once()
            mock_browser.close.assert_called_once()

            # Verify file writing
            mock_file.assert_called_once_with("output.html", "w", encoding="utf-8")
            mock_file().write.assert_called_once_with("<html><body>Test content</body></html>")

    @patch("app.utils.save_activity_page.sync_playwright")
    @patch("builtins.print")
    def test_save_rendered_page_page_load_failure(self, mock_print, mock_sync_playwright):
        """Test handling of page load failure."""
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Simulate page.goto failure
        mock_page.goto.side_effect = Exception("Network error")

        save_rendered_page("http://invalid-url.com", "output.html")

        # Verify error handling
        mock_browser.close.assert_called_once()
        mock_print.assert_called()

        # Check error message was printed
        error_calls = [call for call in mock_print.call_args_list if "ERROR" in str(call)]
        assert len(error_calls) > 0
        assert "Network error" in str(error_calls[0])

    @patch("app.utils.save_activity_page.sync_playwright")
    def test_save_rendered_page_browser_launch_failure(self, mock_sync_playwright):
        """Test handling of browser launch failure."""
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        # Simulate browser launch failure
        mock_playwright.chromium.launch.side_effect = Exception("Browser launch failed")

        with pytest.raises(RuntimeError) as exc_info:
            save_rendered_page("http://test.com", "output.html")

        assert "Failed to launch Playwright browser" in str(exc_info.value)
        assert "Browser launch failed" in str(exc_info.value)
        assert "playwright install" in str(exc_info.value)

    @patch("app.utils.save_activity_page.sync_playwright", side_effect=ImportError("No module named 'playwright'"))
    def test_save_rendered_page_import_error(self, mock_sync_playwright):
        """Test handling of playwright import error."""
        with pytest.raises(ImportError) as exc_info:
            save_rendered_page("http://test.com", "output.html")

        assert "Playwright is not installed" in str(exc_info.value)
        assert "pip install playwright" in str(exc_info.value)

    @patch("app.utils.save_activity_page.sync_playwright")
    @patch("builtins.open", side_effect=IOError("Permission denied"))
    @patch("builtins.print")
    def test_save_rendered_page_file_write_failure(self, mock_print, mock_open, mock_sync_playwright):
        """Test handling of file write failure."""
        # Setup successful playwright mocks
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = "<html>content</html>"

        # File write failure is caught and handled gracefully by the function
        save_rendered_page("http://test.com", "output.html")

        # Browser should still be closed properly
        mock_browser.close.assert_called_once()

        # Error should be logged/printed
        error_calls = [call for call in mock_print.call_args_list if "ERROR" in str(call)]
        assert len(error_calls) > 0

    @patch("app.utils.save_activity_page.sync_playwright")
    @patch("builtins.print")
    def test_save_rendered_page_success_messages(self, mock_print, mock_sync_playwright):
        """Test that success messages are printed."""
        # Setup successful mocks
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = "<html>test</html>"

        with patch("builtins.open", mock_open()):
            save_rendered_page("http://example.com", "test_output.html")

        # Check info messages were printed
        print_calls = [str(call) for call in mock_print.call_args_list]
        loading_message = any("Loading: http://example.com" in call for call in print_calls)
        saved_message = any("Saved rendered page to: test_output.html" in call for call in print_calls)

        assert loading_message, "Loading message not found in print calls"
        assert saved_message, "Saved message not found in print calls"

    @patch("app.utils.save_activity_page.sync_playwright")
    def test_save_rendered_page_with_special_characters(self, mock_sync_playwright):
        """Test saving page content with special characters."""
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Content with special characters
        special_content = "<html><body>Test with émojis 🚀 and ñoñó</body></html>"
        mock_page.content.return_value = special_content

        with patch("builtins.open", mock_open()) as mock_file:
            save_rendered_page("http://test.com", "output.html")

            # Verify UTF-8 encoding was used
            mock_file.assert_called_once_with("output.html", "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(special_content)

    @patch("app.utils.save_activity_page.sync_playwright")
    def test_save_rendered_page_wait_for_network_idle(self, mock_sync_playwright):
        """Test that the function waits for network idle state."""
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        mock_page.content.return_value = "<html>content</html>"

        with patch("builtins.open", mock_open()):
            save_rendered_page("http://test.com", "output.html")

        # Verify wait_for_load_state was called with networkidle
        mock_page.wait_for_load_state.assert_called_once_with("networkidle")


class TestMainFunction:
    """Test cases for the main function and CLI interface."""

    @patch("app.utils.save_activity_page.save_rendered_page")
    @patch("sys.argv", ["script_name", "--url", "http://test.com", "--output", "test.html"])
    def test_main_with_all_arguments(self, mock_save_rendered_page):
        """Test main function with all command line arguments."""
        main()

        mock_save_rendered_page.assert_called_once_with("http://test.com", "test.html")

    @patch("app.utils.save_activity_page.save_rendered_page")
    @patch("sys.argv", ["script_name", "--url", "http://example.com"])
    def test_main_with_default_output(self, mock_save_rendered_page):
        """Test main function with default output filename."""
        main()

        mock_save_rendered_page.assert_called_once_with("http://example.com", "rendered_page.html")

    @patch("sys.argv", ["script_name"])
    @patch("sys.stderr")
    def test_main_missing_required_url(self, mock_stderr):
        """Test main function with missing required URL argument."""
        with pytest.raises(SystemExit):
            main()

    @patch("app.utils.save_activity_page.save_rendered_page")
    @patch("sys.argv", ["script_name", "--url", "https://localhost:8050/activity/123", "--output", "activity_123.html"])
    def test_main_with_activity_url(self, mock_save_rendered_page):
        """Test main function with realistic activity URL."""
        main()

        mock_save_rendered_page.assert_called_once_with("https://localhost:8050/activity/123", "activity_123.html")

    @patch("app.utils.save_activity_page.save_rendered_page", side_effect=RuntimeError("Test error"))
    @patch("sys.argv", ["script_name", "--url", "http://test.com"])
    def test_main_handles_save_error(self, mock_save_rendered_page):
        """Test that main function propagates save_rendered_page errors."""
        with pytest.raises(RuntimeError):
            main()


class TestArgumentParser:
    """Test cases for argument parsing functionality."""

    def test_argument_parser_creation(self):
        """Test that argument parser is created correctly."""
        parser = argparse.ArgumentParser(description="Save a fully rendered webpage as HTML.")
        parser.add_argument("--url", required=True, help="URL of the page to capture.")
        parser.add_argument(
            "--output", default="rendered_page.html", help="Output HTML file (default: rendered_page.html)"
        )

        # Test parsing with all arguments
        args = parser.parse_args(["--url", "http://test.com", "--output", "custom.html"])
        assert args.url == "http://test.com"
        assert args.output == "custom.html"

        # Test parsing with only required argument
        args = parser.parse_args(["--url", "http://example.com"])
        assert args.url == "http://example.com"
        assert args.output == "rendered_page.html"

    def test_argument_parser_missing_url(self):
        """Test that parser fails when URL is missing."""
        parser = argparse.ArgumentParser(description="Save a fully rendered webpage as HTML.")
        parser.add_argument("--url", required=True, help="URL of the page to capture.")
        parser.add_argument(
            "--output", default="rendered_page.html", help="Output HTML file (default: rendered_page.html)"
        )

        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestIntegrationScenarios:
    """Integration test scenarios for the module."""

    @patch("app.utils.save_activity_page.sync_playwright")
    @patch("builtins.print")
    def test_full_workflow_success(self, mock_print, mock_sync_playwright):
        """Test the complete workflow from URL to saved file."""
        # Setup complete mock chain
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        test_html = "<html><head><title>Test</title></head><body><h1>Test Page</h1></body></html>"
        mock_page.content.return_value = test_html

        with patch("builtins.open", mock_open()) as mock_file:
            save_rendered_page("http://localhost:8050/activity/42", "activity_42_rendered.html")

            # Verify complete workflow
            mock_playwright.chromium.launch.assert_called_once_with(headless=True)
            mock_browser.new_page.assert_called_once()
            mock_page.goto.assert_called_once_with("http://localhost:8050/activity/42")
            mock_page.wait_for_load_state.assert_called_once_with("networkidle")
            mock_page.content.assert_called_once()
            mock_browser.close.assert_called_once()

            mock_file.assert_called_once_with("activity_42_rendered.html", "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(test_html)

            # Check success messages
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Loading: http://localhost:8050/activity/42" in call for call in print_calls)
            assert any("Saved rendered page to: activity_42_rendered.html" in call for call in print_calls)

    @patch("app.utils.save_activity_page.sync_playwright")
    @patch("builtins.print")
    def test_error_recovery_workflow(self, mock_print, mock_sync_playwright):
        """Test error handling and cleanup in failure scenarios."""
        mock_playwright = Mock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright

        mock_browser = Mock()
        mock_page = Mock()
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page

        # Simulate timeout on page load
        mock_page.wait_for_load_state.side_effect = Exception("Timeout waiting for networkidle")

        save_rendered_page("http://slow-site.com", "output.html")

        # Browser should still be closed despite error
        mock_browser.close.assert_called_once()

        # Error should be printed
        error_calls = [call for call in mock_print.call_args_list if "ERROR" in str(call)]
        assert len(error_calls) > 0
        assert "Timeout waiting for networkidle" in str(error_calls[0])
