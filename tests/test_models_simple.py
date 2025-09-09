"""
Simple unit tests for database models without schema conflicts.
"""

from datetime import datetime, timezone

import pytest

from app.data.db import DatabaseConfig
from app.data.models import ActivityData, SampleData


class TestDataTransferObjects:
    """Test data transfer objects without database dependencies."""

    def test_activity_data_creation(self):
        """Test ActivityData creation with type annotations."""
        activity_data = ActivityData(
            external_id="test_001",
            sport="running",
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=3600,
            distance_m=10000.0,
            avg_hr=150,
        )

        # Verify attributes
        assert activity_data.external_id == "test_001"
        assert activity_data.sport == "running"
        assert activity_data.elapsed_time_s == 3600
        assert activity_data.distance_m == 10000.0
        assert activity_data.avg_hr == 150

    def test_sample_data_creation(self):
        """Test SampleData creation with coordinates."""
        sample_data = SampleData(
            timestamp=datetime.now(timezone.utc),
            elapsed_time_s=300,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50.0,
            heart_rate=145,
            power_w=200.0,
            speed_mps=4.2,
        )

        # Verify attributes
        assert sample_data.elapsed_time_s == 300
        assert sample_data.latitude == 52.5200
        assert sample_data.longitude == 13.4050
        assert sample_data.altitude_m == 50.0
        assert sample_data.heart_rate == 145
        assert sample_data.power_w == 200.0
        assert sample_data.speed_mps == 4.2


class TestDatabaseConfig:
    """Test database configuration without schema creation."""

    def test_database_config_initialization(self):
        """Test DatabaseConfig initialization."""
        config = DatabaseConfig(database_url="sqlite:///test.db")
        assert config.database_url == "sqlite:///test.db"

    def test_database_config_custom_url(self):
        """Test DatabaseConfig with custom URL."""
        custom_url = "sqlite:///custom_test.db"
        config = DatabaseConfig(database_url=custom_url)
        assert config.database_url == custom_url

    def test_engine_creation(self):
        """Test SQLAlchemy engine creation."""
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        engine = config.engine
        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"

    def test_session_factory(self):
        """Test session factory creation."""
        config = DatabaseConfig(database_url="sqlite:///:memory:")
        session_factory = config.session_factory
        assert session_factory is not None
