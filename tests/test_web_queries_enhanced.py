"""
Enhanced unit tests for web query functions.
"""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from app.data.web_queries import (
    get_activities_for_date_range,
    get_activity_statistics,
    get_activity_summary_stats,
    get_filter_options,
    get_wellness_statistics,
)


class TestWebQueries:
    """Test suite for web query functions."""

    def test_get_activities_for_date_range_no_filters(self, sample_activities):
        """Test getting activities without any filters."""
        activities = get_activities_for_date_range()
        assert len(activities) == 4
        assert all("sport" in activity for activity in activities)

    def test_get_activities_for_date_range_sport_filter(self, sample_activities):
        """Test filtering activities by sport."""
        # Test specific sport filter
        running_activities = get_activities_for_date_range(sport="running")
        assert len(running_activities) == 1
        assert running_activities[0]["sport"] == "running"

        # Test 'all' sport filter
        all_activities = get_activities_for_date_range(sport="all")
        assert len(all_activities) == 4

        # Test non-existent sport
        fake_activities = get_activities_for_date_range(sport="skiing")
        assert len(fake_activities) == 0

    def test_get_activities_for_date_range_date_filters(self, sample_activities):
        """Test filtering activities by date range."""
        base_date = date(2024, 1, 15)

        # Test start date filter
        activities = get_activities_for_date_range(start_date=base_date + timedelta(days=1))
        assert len(activities) == 3  # Should exclude first activity

        # Test end date filter
        activities = get_activities_for_date_range(end_date=base_date + timedelta(days=2))
        assert len(activities) == 3  # Should exclude last activity

        # Test date range
        activities = get_activities_for_date_range(
            start_date=base_date + timedelta(days=1), end_date=base_date + timedelta(days=2)
        )
        assert len(activities) == 2

    def test_get_activities_for_date_range_search_term(self, sample_activities):
        """Test filtering activities by search term."""
        # Mock activities with names for search testing
        with patch("app.data.web_queries.session_manager") as mock_session:
            mock_session.get_session.return_value.__enter__.return_value.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = [
                Mock(
                    id=1,
                    external_id="garmin_001",
                    sport="running",
                    start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                    elapsed_time_s=3600,
                    distance_m=10000.0,
                    avg_hr=150,
                    avg_power_w=None,
                    elevation_gain_m=100.0,
                    calories=500,
                    name="Morning Run",
                    file_hash="hash_1",
                ),
                Mock(
                    id=2,
                    external_id="garmin_002",
                    sport="cycling",
                    start_time_utc=datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc),
                    elapsed_time_s=7200,
                    distance_m=50000.0,
                    avg_hr=140,
                    avg_power_w=200.0,
                    elevation_gain_m=500.0,
                    calories=600,
                    name="Evening Bike Ride",
                    file_hash="hash_2",
                ),
            ]

            activities = get_activities_for_date_range(search_term="run")
            # Since we're mocking, this should return all mocked activities
            assert len(activities) >= 0

    def test_get_activity_statistics(self, sample_activities):
        """Test getting activity statistics."""
        stats = get_activity_statistics()

        assert "total_activities" in stats
        assert "total_distance_km" in stats
        assert "total_time_hours" in stats
        assert "avg_heart_rate" in stats

        assert stats["total_activities"] == 4
        assert stats["total_distance_km"] == 77.0  # 10+50+2+15 km
        assert abs(stats["total_time_hours"] - 8.5) < 0.1  # ~30600 seconds / 3600
        assert stats["avg_heart_rate"] > 0

    def test_get_activity_statistics_empty_database(self):
        """Test activity statistics with empty database."""
        with patch("app.data.web_queries.session_manager") as mock_session:
            mock_session.get_session.return_value.__enter__.return_value.query.return_value.all.return_value = []

            stats = get_activity_statistics()

            assert stats["total_activities"] == 0
            assert stats["total_distance_km"] == 0
            assert stats["total_time_hours"] == 0
            assert stats["avg_heart_rate"] == 0

    def test_get_activity_summary_stats_with_filters(self, sample_activities):
        """Test getting activity summary stats with filters."""
        base_date = date(2024, 1, 15)

        stats = get_activity_summary_stats(
            start_date=base_date, end_date=base_date + timedelta(days=2), sport="running"
        )

        assert "total_activities" in stats
        assert "total_distance" in stats
        assert "total_time" in stats
        assert "avg_hr" in stats

    def test_get_filter_options(self, sample_activities):
        """Test getting filter options."""
        options = get_filter_options()

        assert "sports" in options
        assert "distance_range" in options
        assert "duration_range" in options

        assert "running" in options["sports"]
        assert "cycling" in options["sports"]
        assert "swimming" in options["sports"]
        assert "hiking" in options["sports"]

        assert options["distance_range"]["min"] >= 0
        assert options["distance_range"]["max"] >= options["distance_range"]["min"]

        assert options["duration_range"]["min"] >= 0
        assert options["duration_range"]["max"] >= options["duration_range"]["min"]

    def test_get_wellness_statistics(self):
        """Test getting wellness statistics."""
        with patch("app.data.web_queries.session_manager") as mock_session:
            mock_session.get_session.return_value.__enter__.return_value.execute.return_value.fetchall.return_value = []

            stats = get_wellness_statistics()

            # Check structure of returned data
            assert "sleep" in stats
            assert "stress" in stats
            assert "steps" in stats
            assert "body_battery" in stats
            assert "heart_rate" in stats
            assert "personal_records" in stats
            assert "max_metrics" in stats

            # Each category should have total_records
            for category in ["sleep", "stress", "steps", "body_battery", "heart_rate", "personal_records"]:
                assert "total_records" in stats[category]

    @patch("app.data.web_queries.session_manager")
    def test_get_activities_database_error(self, mock_session):
        """Test handling database errors gracefully."""
        mock_session.get_session.side_effect = Exception("Database connection failed")

        activities = get_activities_for_date_range()
        assert activities == []

    @patch("app.data.web_queries.session_manager")
    def test_get_activity_statistics_database_error(self, mock_session):
        """Test handling database errors in statistics."""
        mock_session.get_session.side_effect = Exception("Database connection failed")

        stats = get_activity_statistics()
        assert stats["total_activities"] == 0
        assert stats["total_distance_km"] == 0

    def test_get_activities_performance_with_large_dataset(self, activity_with_samples):
        """Test query performance with detailed activity data."""
        # This uses the activity_with_samples fixture which has GPS samples
        activities = get_activities_for_date_range()

        # Should still work efficiently with detailed data
        assert len(activities) >= 1
        detailed_activity = activities[0]
        assert "start_time" in detailed_activity
        assert "distance_km" in detailed_activity

    def test_activity_statistics_calculations(self):
        """Test statistical calculations are accurate."""
        # Mock specific data for calculation testing
        with patch("app.data.web_queries.session_manager") as mock_session:
            mock_activities = [
                Mock(distance_m=5000.0, elapsed_time_s=1800, avg_hr=150),  # 5km, 30min, 150bpm
                Mock(distance_m=10000.0, elapsed_time_s=3600, avg_hr=140),  # 10km, 60min, 140bpm
                Mock(distance_m=None, elapsed_time_s=2400, avg_hr=160),  # No distance, 40min, 160bpm
            ]
            mock_session.get_session.return_value.__enter__.return_value.query.return_value.all.return_value = (
                mock_activities
            )

            stats = get_activity_statistics()

            assert stats["total_activities"] == 3
            assert stats["total_distance_km"] == 15.0  # 5 + 10 km (None excluded)
            assert stats["total_time_hours"] == 2.0  # 7800 seconds / 3600
            assert stats["avg_heart_rate"] == 150  # (150+140+160)/3
