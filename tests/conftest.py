"""
Minimal pytest configuration for basic unit tests.
"""

import pytest


@pytest.fixture
def mock_session():
    """Mock database session for testing."""
    from unittest.mock import Mock

    return Mock()


# Custom pytest markers for test categorization
pytest_markers = [
    "unit: marks tests as unit tests (deselect with '-m \"not unit\"')",
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "parser: marks tests related to file parsing",
    "database: marks tests related to database operations",
    "web: marks tests related to web query functions",
    "models: marks tests related to SQLAlchemy models",
    "pages: marks tests related to Dash page components",
    "fit: marks tests related to FIT file processing",
]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark based on test file names
        if "test_parser" in item.nodeid:
            item.add_marker(pytest.mark.parser)
            item.add_marker(pytest.mark.unit)
        elif "test_models" in item.nodeid:
            item.add_marker(pytest.mark.models)
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.unit)
        elif "test_web_queries" in item.nodeid:
            item.add_marker(pytest.mark.web)
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.integration)
        elif "test_pages" in item.nodeid:
            item.add_marker(pytest.mark.pages)
            item.add_marker(pytest.mark.unit)
        elif "test_fit_integration" in item.nodeid:
            item.add_marker(pytest.mark.fit)
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "test_utils" in item.nodeid:
            item.add_marker(pytest.mark.unit)
