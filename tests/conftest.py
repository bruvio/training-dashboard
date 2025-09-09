"""
Pytest configuration and fixtures for the Garmin Dashboard test suite.
"""

import os
import tempfile
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.data.db import DatabaseConfig
from app.data.models import Base, Activity, Sample, Lap, RoutePoint


def is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv('IS_CI') == 'true' or os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.fixture(scope="function")
def test_database():
    """Create a test database with minimal data for CI/local testing."""
    # Use in-memory database to avoid file conflicts
    database_url = "sqlite:///:memory:"
    
    # Create engine and tables
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Add minimal test data
    try:
        # Create test activities
        activity1 = Activity(
            id=1,
            external_id="test_001",
            file_hash="hash_001",
            source="test",
            sport="running",
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=3600,
            distance_m=10000.0,
            avg_hr=150,
            max_hr=180,
            elevation_gain_m=100.0,
            calories=500,
        )
        
        activity2 = Activity(
            id=2,
            external_id="test_002", 
            file_hash="hash_002",
            source="test",
            sport="cycling",
            start_time_utc=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=7200,
            distance_m=50000.0,
            avg_hr=140,
            max_hr=170,
            avg_power_w=200.0,
            elevation_gain_m=500.0,
            calories=800,
        )
        
        session.add(activity1)
        session.add(activity2)
        session.flush()  # Get IDs
        
        # Add test samples
        sample1 = Sample(
            activity_id=activity1.id,
            timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=0,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50,
            heart_rate=140,
            speed_mps=3.0,
        )
        
        sample2 = Sample(
            activity_id=activity1.id,
            timestamp=datetime(2024, 1, 15, 10, 0, 30, tzinfo=timezone.utc),
            elapsed_time_s=30,
            latitude=52.5210,
            longitude=13.4060,
            altitude_m=52,
            heart_rate=145,
            speed_mps=3.2,
        )
        
        session.add(sample1)
        session.add(sample2)
        
        # Add test lap
        lap1 = Lap(
            activity_id=activity1.id,
            lap_index=1,
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=1800,
            distance_m=5000.0,
            avg_speed_mps=2.78,
            avg_hr=148,
            max_hr=160,
        )
        
        session.add(lap1)
        
        # Add test route points
        route_point1 = RoutePoint(
            activity_id=activity1.id,
            sequence=1,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50.0,
        )
        
        session.add(route_point1)
        
        session.commit()
        
        yield {
            'database_url': database_url,
            'engine': engine,
            'session': session,
        }
        
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def db_session(test_database):
    """Provide a database session for tests."""
    return test_database['session']


@pytest.fixture 
def temp_database_config(test_database):
    """Provide a DatabaseConfig instance using the test database."""
    config = DatabaseConfig(database_url=test_database['database_url'])
    return config


# Sample data fixtures
@pytest.fixture
def sample_activities():
    """Provide sample activity data for testing."""
    return [
        {
            "id": 1,
            "external_id": "test_001",
            "sport": "running",
            "start_time": "2024-01-15T10:00:00",
            "elapsed_time_s": 3600,
            "distance_km": 10.0,
            "distance_m": 10000,
            "avg_hr": 150,
            "duration_str": "1:00:00",
        },
        {
            "id": 2,
            "external_id": "test_002", 
            "sport": "cycling",
            "start_time": "2024-01-16T10:00:00",
            "elapsed_time_s": 7200,
            "distance_km": 50.0,
            "distance_m": 50000,
            "avg_hr": 140,
            "duration_str": "2:00:00",
        }
    ]


@pytest.fixture
def activity_with_samples():
    """Provide activity data with GPS samples."""
    return {
        "id": 1,
        "external_id": "test_with_samples",
        "sport": "running",
        "start_time": "2024-01-15T10:00:00",
        "samples": [
            {
                "latitude": 52.5200,
                "longitude": 13.4050,
                "altitude_m": 50,
                "heart_rate": 140,
                "elapsed_time_s": 0,
            },
            {
                "latitude": 52.5210,
                "longitude": 13.4060, 
                "altitude_m": 52,
                "heart_rate": 145,
                "elapsed_time_s": 30,
            }
        ]
    }


@pytest.fixture
def mock_session():
    """Mock database session for testing."""
    from unittest.mock import Mock
    return Mock()


# Pytest markers
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
    "auth: marks tests requiring authentication",
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
        elif any(auth_test in item.nodeid for auth_test in ['test_wellness_sync', 'test_real_api', 'test_real_mfa', 'test_complete_sync', 'test_corrected_sync', 'test_transformation_fix']):
            item.add_marker(pytest.mark.auth)