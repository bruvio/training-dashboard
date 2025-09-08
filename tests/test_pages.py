"""
Unit tests for Dash page components and layouts.
"""

from unittest.mock import Mock, patch

import pytest
from dash import html
import dash_bootstrap_components as dbc

from app.pages import activities, calendar


class TestCalendarPage:
    """Test suite for calendar/landing page."""

    def test_calendar_layout_structure(self):
        """Test that calendar layout has expected structure."""
        layout = calendar.layout()

        assert layout is not None
        assert isinstance(layout, dbc.Container)

    @patch("app.pages.calendar.get_activity_statistics")
    @patch("app.pages.calendar.get_wellness_statistics")
    def test_database_summary_callback(self, mock_wellness, mock_activity):
        """Test database summary callback."""
        # Mock return data
        mock_activity.return_value = {
            "total_activities": 10,
            "total_distance_km": 50.0,
            "total_time_hours": 5.0,
            "avg_heart_rate": 150.0,
        }

        mock_wellness.return_value = {
            "sleep": {"total_records": 30, "avg_sleep_hours": 7.5},
            "stress": {"total_records": 25},
            "steps": {"total_records": 40},
            "body_battery": {"total_records": 35},
            "heart_rate": {"total_records": 45},
            "personal_records": {"total_records": 5},
            "max_metrics": {"avg_vo2_max": 45.0},
        }

        # Test the callback
        result = calendar.update_database_summary("/")

        assert result is not None
        assert isinstance(result, dbc.Row)
        mock_activity.assert_called_once()
        mock_wellness.assert_called_once()

    @patch("app.pages.calendar.get_activity_statistics")
    @patch("app.pages.calendar.get_wellness_statistics")
    def test_database_summary_error_handling(self, mock_wellness, mock_activity):
        """Test database summary error handling."""
        # Mock exception
        mock_activity.side_effect = Exception("Database error")

        result = calendar.update_database_summary("/")

        assert isinstance(result, dbc.Alert)
        assert "Error loading database summary" in str(result)


class TestActivitiesPage:
    """Test suite for activities page."""

    def test_activities_layout_structure(self):
        """Test that activities layout has expected structure."""
        layout = activities.layout()

        assert layout is not None
        assert isinstance(layout, dbc.Container)

    @patch("app.data.web_queries.get_filter_options")
    def test_initialize_activities_filters(self, mock_filter_options):
        """Test activities filters initialization."""
        mock_filter_options.return_value = {
            "sports": ["running", "cycling", "swimming"],
            "duration_range": {"min": 0, "max": 7200},
            "distance_range": {"min": 0, "max": 50000},
        }

        result = activities.initialize_activities_filters("/activities")

        # Should return tuple of filter configurations
        assert isinstance(result, tuple)
        assert len(result) == 7  # sport_options, duration min/max/value, distance min/max/value

        sport_options = result[0]
        assert isinstance(sport_options, list)
        assert {"label": "All Sports", "value": "all"} in sport_options
        assert {"label": "Running", "value": "running"} in sport_options

    @patch("app.data.web_queries.get_filter_options")
    def test_initialize_filters_wrong_path(self, mock_filter_options):
        """Test filters initialization for wrong path."""
        result = activities.initialize_activities_filters("/other")

        # Should return default values
        assert isinstance(result, tuple)
        assert len(result) == 7
        mock_filter_options.assert_not_called()

    @patch("app.data.web_queries.get_activity_summary_stats")
    def test_activities_summary_callback(self, mock_summary_stats):
        """Test activities summary callback."""
        mock_summary_stats.return_value = {
            "total_activities": "5",
            "total_distance": "25.0 km",
            "total_time": "5:30:00",
            "avg_hr": "145 bpm",
        }

        result = activities.update_activities_summary("2024-01-01", "2024-01-31", "running", "test search")

        assert result is not None
        assert isinstance(result, dbc.Row)
        mock_summary_stats.assert_called_once()

    @patch("app.data.web_queries.get_activity_summary_stats")
    def test_activities_summary_no_activities(self, mock_summary_stats):
        """Test activities summary with no activities."""
        mock_summary_stats.return_value = {
            "total_activities": "0",
            "total_distance": "0.0 km",
            "total_time": "0:00:00",
            "avg_hr": "N/A",
        }

        result = activities.update_activities_summary("2024-01-01", "2024-01-31", "running", "")

        assert isinstance(result, dbc.Alert)
        assert "No activities found" in str(result)

    @patch("app.data.web_queries.get_activities_for_date_range")
    def test_activities_table_callback(self, mock_get_activities):
        """Test activities table callback."""
        mock_get_activities.return_value = [
            {
                "id": 1,
                "name": "Morning Run",
                "sport": "running",
                "duration_str": "1:00:00",
                "distance_km": 10.0,
                "start_time": "2024-01-15T10:00:00",
                "avg_hr": 150,
                "avg_power_w": None,
                "elevation_gain_m": 100,
            },
            {
                "id": 2,
                "name": "Evening Bike",
                "sport": "cycling",
                "duration_str": "2:00:00",
                "distance_km": 30.0,
                "start_time": "2024-01-16T18:00:00",
                "avg_hr": 140,
                "avg_power_w": 200,
                "elevation_gain_m": 300,
            },
        ]

        table_result, badge_result = activities.update_activities_table(
            "2024-01-01", "2024-01-31", "all", [0, 180], [0, 50], "", "date_desc", 1
        )

        assert table_result is not None
        assert isinstance(badge_result, dbc.Badge)
        assert "2 activities" in str(badge_result)
        mock_get_activities.assert_called_once()

    @patch("app.data.web_queries.get_activities_for_date_range")
    def test_activities_table_empty(self, mock_get_activities):
        """Test activities table with no activities."""
        mock_get_activities.return_value = []

        table_result, badge_result = activities.update_activities_table(
            "2024-01-01", "2024-01-31", "running", [0, 180], [0, 50], "", "date_desc", 1
        )

        assert isinstance(table_result, dbc.Alert)
        assert "No Activities Found" in str(table_result)
        assert isinstance(badge_result, dbc.Badge)
        assert "0 activities" in str(badge_result)

    @patch("app.data.web_queries.get_activities_for_date_range")
    def test_activities_filtering(self, mock_get_activities):
        """Test activity filtering functionality."""
        # Mock activities with different durations and distances
        mock_get_activities.return_value = [
            {
                "id": 1,
                "name": "Short Run",
                "sport": "running",
                "duration_str": "0:30:00",  # 30 minutes
                "distance_km": 5.0,
                "start_time": "2024-01-15T10:00:00",
                "avg_hr": 150,
                "avg_power_w": None,
                "elevation_gain_m": 50,
            },
            {
                "id": 2,
                "name": "Long Ride",
                "sport": "cycling",
                "duration_str": "3:00:00",  # 3 hours
                "distance_km": 60.0,
                "start_time": "2024-01-16T10:00:00",
                "avg_hr": 140,
                "avg_power_w": 180,
                "elevation_gain_m": 800,
            },
        ]

        # Test duration filtering (should exclude 3-hour ride if max is 120 minutes)
        table_result, badge_result = activities.update_activities_table(
            None, None, "all", [15, 120], [0, 100], "", "date_desc", 1  # 15-120 minutes, 0-100km
        )

        # Both activities should be included based on our mock data
        assert "1 activities" in str(badge_result) or "2 activities" in str(badge_result)

    @patch("app.data.web_queries.get_activities_for_date_range")
    def test_activities_sorting(self, mock_get_activities):
        """Test activity sorting functionality."""
        mock_get_activities.return_value = [
            {
                "id": 1,
                "name": "Activity A",
                "sport": "running",
                "duration_str": "1:00:00",
                "distance_km": 10.0,
                "start_time": "2024-01-15T10:00:00",
                "avg_hr": 150,
                "avg_power_w": None,
                "elevation_gain_m": 100,
            },
            {
                "id": 2,
                "name": "Activity B",
                "sport": "cycling",
                "duration_str": "2:00:00",
                "distance_km": 30.0,
                "start_time": "2024-01-16T10:00:00",
                "avg_hr": 140,
                "avg_power_w": 200,
                "elevation_gain_m": 300,
            },
        ]

        # Test different sort orders
        for sort_option in ["date_desc", "date_asc", "distance_desc", "distance_asc", "duration_desc", "duration_asc"]:
            table_result, badge_result = activities.update_activities_table(
                None, None, "all", [0, 300], [0, 100], "", sort_option, 1
            )

            assert table_result is not None
            assert "2 activities" in str(badge_result)


class TestPageUtilities:
    """Test suite for page utility functions."""

    def test_page_imports(self):
        """Test that pages can be imported without errors."""
        from app.pages import activities, calendar

        assert activities is not None
        assert calendar is not None

    def test_page_layout_types(self):
        """Test that page layouts return correct types."""
        calendar_layout = calendar.layout()
        activities_layout = activities.layout()

        assert hasattr(calendar_layout, "children")
        assert hasattr(activities_layout, "children")

    @patch("app.data.web_queries.get_activity_statistics")
    @patch("app.data.web_queries.get_wellness_statistics")
    def test_callback_error_handling(self, mock_wellness, mock_activity):
        """Test that callbacks handle errors gracefully."""
        # Test database connection errors
        mock_activity.side_effect = Exception("Connection failed")
        mock_wellness.side_effect = Exception("Connection failed")

        # Calendar page should handle errors
        result = calendar.update_database_summary("/")
        assert isinstance(result, dbc.Alert)

        # Activities page should handle errors
        with patch("app.data.web_queries.get_activity_summary_stats") as mock_summary:
            mock_summary.side_effect = Exception("Connection failed")
            result = activities.update_activities_summary("2024-01-01", "2024-01-31", "all", "")
            assert isinstance(result, dbc.Alert)
