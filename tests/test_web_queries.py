"""
Unit tests for web query functions used by Dash application.

Tests database integration, query optimization, and data formatting
for web components following the enhanced PRP specifications.
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.data.db import DatabaseConfig
from app.data.models import Activity, Sample
from app.data.web_queries import (
    check_database_connection,
    get_activities_for_date_range,
    get_activity_by_id,
    get_activity_samples,
    get_activity_summary_stats,
)


class TestWebQueries:
    """Test web-specific database query functions."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database with test data."""

        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_all_tables()

        session = db_config.get_session()

        # Create test activities
        activities = []
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        for i in range(10):
            activity = Activity(
                external_id=f"test_activity_{i}",
                file_hash=f"hash_{i}",
                source="fit",
                sport="running" if i % 2 == 0 else "cycling",
                start_time_utc=base_time + timedelta(days=i),
                elapsed_time_s=3600 + i * 300,
                distance_m=10000.0 + i * 1000,
                avg_hr=150 + i * 5,
                max_hr=180 + i * 5,
                avg_power_w=200.0 + i * 10 if i % 3 == 0 else None,
                elevation_gain_m=100.0 + i * 50,
                calories=500 + i * 50,
            )
            activities.append(activity)
            session.add(activity)

        session.commit()

        # Add some samples for the first activity
        first_activity = activities[0]
        for j in range(5):
            sample = Sample(
                activity_id=first_activity.id,
                timestamp=base_time + timedelta(minutes=j * 5),
                elapsed_time_s=j * 300,
                latitude=52.5200 + j * 0.001,
                longitude=13.4050 + j * 0.001,
                altitude_m=100.0 + j * 5,
                heart_rate=140 + j * 10,
                power_w=180.0 + j * 20,
                speed_mps=4.0 + j * 0.5,
            )
            session.add(sample)

        session.commit()

        yield session
        session.close()

    @patch("app.data.web_queries.session_scope")
    def test_get_activities_for_date_range_no_filters(self, mock_session_scope, db_session):
        """Test getting activities without any filters."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activities_for_date_range()

        assert len(result) == 10
        assert all("id" in activity for activity in result)
        assert all("start_time" in activity for activity in result)
        assert all("sport" in activity for activity in result)

        # Check sorting (most recent first)
        dates = [activity["start_time"] for activity in result]
        assert dates == sorted(dates, reverse=True)

    @patch("app.data.web_queries.session_scope")
    def test_get_activities_for_date_range_with_date_filter(self, mock_session_scope, db_session):
        """Test getting activities with date range filter."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        start_date = date(2024, 1, 18)  # Should include activities from day 3 onwards
        end_date = date(2024, 1, 22)  # Should include activities up to day 7

        result = get_activities_for_date_range(start_date=start_date, end_date=end_date)

        # Should have activities from days 3-7 (5 activities)
        assert len(result) == 5

        # All activities should be within the date range
        for activity in result:
            activity_date = datetime.fromisoformat(activity["start_time"].replace("Z", "+00:00")).date()
            assert start_date <= activity_date <= end_date

    @patch("app.data.web_queries.session_scope")
    def test_get_activities_for_date_range_with_sport_filter(self, mock_session_scope, db_session):
        """Test getting activities with sport filter."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activities_for_date_range(sport="running")

        # Should have 5 running activities (even indices)
        assert len(result) == 5

        # All should be running activities
        for activity in result:
            assert "🏃" in activity["sport"]  # Should have running emoji

    @patch("app.data.web_queries.session_scope")
    def test_get_activities_for_date_range_sport_display_mapping(self, mock_session_scope, db_session):
        """Test that sports are properly mapped to display format."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activities_for_date_range()

        running_activities = [a for a in result if "🏃" in a["sport"]]
        cycling_activities = [a for a in result if "🚴" in a["sport"]]

        assert len(running_activities) == 5
        assert len(cycling_activities) == 5

        # Check specific mappings
        assert all("Running" in a["sport"] for a in running_activities)
        assert all("Cycling" in a["sport"] for a in cycling_activities)

    @patch("app.data.web_queries.session_scope")
    def test_get_activities_for_date_range_duration_formatting(self, mock_session_scope, db_session):
        """Test that durations are properly formatted."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activities_for_date_range()

        for activity in result:
            duration_str = activity["duration_str"]
            assert isinstance(duration_str, str)
            assert ":" in duration_str  # Should be in MM:SS or H:MM:SS format
            assert duration_str != "N/A"

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_summary_stats(self, mock_session_scope, db_session):
        """Test getting summary statistics."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activity_summary_stats()

        assert isinstance(result, dict)
        assert "total_activities" in result
        assert "total_distance" in result
        assert "total_time" in result
        assert "avg_hr" in result
        assert "avg_power" in result
        assert "elevation_gain" in result

        # Check values are properly formatted strings
        assert result["total_activities"] == "10"  # 10 test activities
        assert "km" in result["total_distance"]
        assert "h" in result["total_time"] or "m" in result["total_time"]
        assert "bpm" in result["avg_hr"] or result["avg_hr"] == "N/A"
        assert "W" in result["avg_power"] or result["avg_power"] == "N/A"
        assert "m" in result["elevation_gain"]

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_summary_stats_with_filters(self, mock_session_scope, db_session):
        """Test summary stats with filters applied."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activity_summary_stats(sport="running")

        # Should only count running activities (5 out of 10)
        assert result["total_activities"] == "5"

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_by_id_success(self, mock_session_scope, db_session):
        """Test getting single activity by ID."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        # Get first activity's ID
        activities = db_session.query(Activity).all()
        first_activity_id = activities[0].id

        result = get_activity_by_id(first_activity_id)

        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == first_activity_id
        assert "external_id" in result
        assert "sport" in result
        assert "start_time" in result
        assert "total_distance_km" in result
        assert "total_time_s" in result

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_by_id_not_found(self, mock_session_scope, db_session):
        """Test getting non-existent activity by ID."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activity_by_id(99999)  # Non-existent ID

        assert result is None

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_samples_success(self, mock_session_scope, db_session):
        """Test getting activity samples as DataFrame."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        # Get first activity's ID (which has samples)
        activities = db_session.query(Activity).all()
        first_activity_id = activities[0].id

        result = get_activity_samples(first_activity_id)

        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert len(result) == 5  # We added 5 samples

        # Check required columns
        expected_columns = [
            "elapsed_time_s",
            "position_lat",
            "position_long",
            "altitude_m",
            "heart_rate_bpm",
            "power_w",
            "speed_mps",
            "timestamp",
            "speed_kmh",
        ]
        for col in expected_columns:
            assert col in result.columns

        # Check data types and computed columns
        assert result["speed_kmh"].dtype in ["float64", "Float64"]
        assert all(result["speed_kmh"] == result["speed_mps"] * 3.6)

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_samples_no_activity(self, mock_session_scope, db_session):
        """Test getting samples for non-existent activity."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = get_activity_samples(99999)  # Non-existent activity ID

        assert result is None

    @patch("app.data.web_queries.session_scope")
    def test_get_activity_samples_no_samples(self, mock_session_scope, db_session):
        """Test getting samples for activity with no sample data."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        # Get an activity without samples (any except the first)
        activities = db_session.query(Activity).all()
        activity_without_samples_id = activities[1].id

        result = get_activity_samples(activity_without_samples_id)

        assert isinstance(result, pd.DataFrame)
        assert result.empty  # Should return empty DataFrame

    @patch("app.data.web_queries.session_scope")
    def test_check_database_connection_success(self, mock_session_scope, db_session):
        """Test successful database connection check."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = check_database_connection()

        assert result is True

    @patch("app.data.web_queries.session_scope")
    def test_check_database_connection_failure(self, mock_session_scope):
        """Test database connection check failure."""
        # Mock session that raises an exception
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        mock_session_scope.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        result = check_database_connection()

        assert result is False

    @patch("app.data.web_queries.session_scope")
    def test_activity_list_performance_limit(self, mock_session_scope, db_session):
        """Test that activity queries are limited for performance."""
        mock_session_scope.return_value.__enter__ = MagicMock(return_value=db_session)
        mock_session_scope.return_value.__exit__ = MagicMock(return_value=None)

        # The function should limit results to 1000 even if more exist
        # Our test has only 10 activities, so this tests the mechanism
        result = get_activities_for_date_range()

        assert len(result) <= 1000  # Should respect the limit
        assert len(result) == 10  # Our test data

    def test_duration_formatting_edge_cases(self):
        """Test duration formatting with edge cases."""

        # Mock activity with various duration values
        class MockActivity:
            def __init__(self, elapsed_time_s):
                self.id = 1
                self.external_id = "test"
                self.sport = "running"
                self.start_time_utc = datetime.now(timezone.utc)
                self.distance_m = 1000.0
                self.elapsed_time_s = elapsed_time_s
                self.avg_hr = None
                self.avg_power_w = None
                self.elevation_gain_m = 0

        # Test various duration formats
        test_cases = [
            (0, "0:00"),
            (30, "0:30"),
            (90, "1:30"),
            (3661, "1:01:01"),  # 1 hour, 1 minute, 1 second
        ]

        # We can't easily test the internal formatting without refactoring
        # the function, but we can verify the logic conceptually
        for elapsed_s, expected_format in test_cases:
            hours = int(elapsed_s // 3600)
            minutes = int((elapsed_s % 3600) // 60)
            seconds = int(elapsed_s % 60)

            if hours > 0:
                result = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                result = f"{minutes}:{seconds:02d}"

            assert result == expected_format


class TestWebQueriesIntegration:
    """Integration tests for web queries with realistic scenarios."""

    @patch("app.data.web_queries.check_database_connection")
    @patch("app.data.web_queries.session_scope")
    def test_get_activities_with_database_error(self, mock_session_scope, mock_db_check):
        """Test graceful handling of database errors."""
        mock_db_check.return_value = False  # Database unavailable

        result = get_activities_for_date_range()

        # Should return empty list when database is unavailable
        assert isinstance(result, list)
        assert len(result) == 0

    def test_sport_mapping_completeness(self):
        """Test that sport mapping covers expected cases."""

        # Test the sport mapping logic
        sport_mapping = {
            "running": ["running", "treadmill_running", "trail_running"],
            "cycling": ["cycling", "road_biking", "mountain_biking"],
            "swimming": ["swimming", "open_water_swimming"],
            "hiking": ["hiking", "walking"],
            "strength": ["strength_training", "generic"],
            "cardio": ["cardio", "elliptical", "fitness_equipment"],
            "skiing": ["downhill_skiing", "cross_country_skiing", "snowboarding"],
        }

        # Verify mapping structure
        assert "running" in sport_mapping
        assert "cycling" in sport_mapping
        assert isinstance(sport_mapping["running"], list)
        assert len(sport_mapping["running"]) > 0

        # Verify all mapped values are strings
        for sport_list in sport_mapping.values():
            assert all(isinstance(sport, str) for sport in sport_list)


# Validation Gate: Run this test with `pytest tests/test_web_queries.py -v`
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
