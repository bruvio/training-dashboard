"""
Comprehensive unit tests for app/utils/activity_helpers.py functions.

This test module follows the PRP Phase 1 requirements for comprehensive utility
function testing including all edge cases, error handling, and complete coverage.
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.utils.activity_helpers import (
    parse_duration_to_seconds,
    get_activity_sort_key,
    sort_activities,
    get_neutral_map_defaults,
    get_map_center_from_route,
    has_valid_distance,
    filter_activities_by_distance,
    is_valid_gps_coordinate,
    extract_valid_route_positions,
)


class TestParseDurationToSeconds:
    """Test suite for parse_duration_to_seconds function."""

    def test_parse_duration_mm_ss_format(self):
        """Test parsing MM:SS format durations."""
        assert parse_duration_to_seconds("00:30") == 30
        assert parse_duration_to_seconds("02:30") == 150  # 2:30 minutes
        assert parse_duration_to_seconds("59:59") == 3599  # 59:59
        assert parse_duration_to_seconds("00:00") == 0

    def test_parse_duration_h_mm_ss_format(self):
        """Test parsing H:MM:SS format durations."""
        assert parse_duration_to_seconds("1:30:45") == 5445  # 1 hour 30 min 45 sec
        assert parse_duration_to_seconds("0:02:30") == 150  # 0 hours 2 min 30 sec
        assert parse_duration_to_seconds("24:00:00") == 86400  # 24 hours
        assert parse_duration_to_seconds("0:00:00") == 0

    def test_parse_duration_invalid_formats(self):
        """Test parsing invalid duration formats."""
        assert parse_duration_to_seconds("invalid") == 0
        assert parse_duration_to_seconds("") == 0
        assert parse_duration_to_seconds(None) == 0
        assert parse_duration_to_seconds("60") == 0  # No colon
        assert parse_duration_to_seconds("1:2:3:4") == 0  # Too many parts

    def test_parse_duration_invalid_values(self):
        """Test parsing durations with invalid numeric values."""
        assert parse_duration_to_seconds("1:abc") == 0
        assert parse_duration_to_seconds("abc:30") == 0
        assert parse_duration_to_seconds("1:2:abc") == 0
        assert parse_duration_to_seconds("1.5:30") == 0  # Float values

    def test_parse_duration_edge_cases(self):
        """Test edge cases for duration parsing."""
        assert parse_duration_to_seconds(":") == 0  # Just colon
        assert parse_duration_to_seconds("::") == 0  # Double colon
        assert parse_duration_to_seconds("1:") == 0  # Missing seconds
        assert parse_duration_to_seconds(":30") == 0  # Missing minutes


class TestGetActivitySortKey:
    """Test suite for get_activity_sort_key function."""

    def test_sort_key_date_formats(self):
        """Test date sort key with various datetime formats."""
        # Test ISO format with timezone
        activity1 = {"start_time": "2024-01-15T10:00:00+00:00"}
        result1 = get_activity_sort_key(activity1, "date_desc")
        assert isinstance(result1, datetime)

        # Test ISO format without timezone
        activity2 = {"start_time": "2024-01-15T10:00:00"}
        result2 = get_activity_sort_key(activity2, "date_asc")
        assert isinstance(result2, datetime)

    def test_sort_key_date_with_microseconds(self):
        """Test date sort key with microseconds."""
        activity = {"start_time": "2024-01-15T10:00:00.123456"}
        result = get_activity_sort_key(activity, "date_desc")
        assert isinstance(result, datetime)

    def test_sort_key_date_invalid_format(self):
        """Test date sort key with invalid date formats."""
        activity = {"start_time": "invalid-date"}
        result = get_activity_sort_key(activity, "date_desc")
        assert result == datetime.min

    def test_sort_key_date_missing_start_time(self):
        """Test date sort key when start_time is missing."""
        activity = {}
        result = get_activity_sort_key(activity, "date_desc")
        assert result == datetime.min

    def test_sort_key_distance(self):
        """Test distance sort key."""
        activity = {"distance_km": 10.5}
        result = get_activity_sort_key(activity, "distance_desc")
        assert result == 10.5

        result = get_activity_sort_key(activity, "distance_asc")
        assert result == 10.5

    def test_sort_key_distance_missing(self):
        """Test distance sort key when distance is missing."""
        activity = {}
        result = get_activity_sort_key(activity, "distance_desc")
        assert result == 0

    def test_sort_key_duration(self):
        """Test duration sort key."""
        activity = {"duration_str": "1:30:45"}
        result = get_activity_sort_key(activity, "duration_desc")
        assert result == 5445  # 1 hour 30 min 45 sec

    def test_sort_key_duration_missing(self):
        """Test duration sort key when duration is missing."""
        activity = {}
        result = get_activity_sort_key(activity, "duration_desc")
        assert result == 0

    def test_sort_key_unknown_criteria(self):
        """Test sort key with unknown sort criteria."""
        activity = {"start_time": "2024-01-15T10:00:00"}
        result = get_activity_sort_key(activity, "unknown")
        assert result == ""


class TestSortActivities:
    """Test suite for sort_activities function."""

    def test_sort_activities_empty_list(self):
        """Test sorting empty activity list."""
        result = sort_activities([], "date_desc")
        assert result == []

    def test_sort_activities_date_descending(self):
        """Test sorting activities by date descending (newest first)."""
        activities = [
            {"start_time": "2024-01-01T10:00:00"},
            {"start_time": "2024-01-03T10:00:00"},
            {"start_time": "2024-01-02T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "date_desc")

        assert sorted_activities[0]["start_time"] == "2024-01-03T10:00:00"
        assert sorted_activities[1]["start_time"] == "2024-01-02T10:00:00"
        assert sorted_activities[2]["start_time"] == "2024-01-01T10:00:00"

    def test_sort_activities_date_ascending(self):
        """Test sorting activities by date ascending (oldest first)."""
        activities = [
            {"start_time": "2024-01-03T10:00:00"},
            {"start_time": "2024-01-01T10:00:00"},
            {"start_time": "2024-01-02T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "date_asc")

        assert sorted_activities[0]["start_time"] == "2024-01-01T10:00:00"
        assert sorted_activities[1]["start_time"] == "2024-01-02T10:00:00"
        assert sorted_activities[2]["start_time"] == "2024-01-03T10:00:00"

    def test_sort_activities_distance(self):
        """Test sorting activities by distance."""
        activities = [
            {"distance_km": 5.0},
            {"distance_km": 10.0},
            {"distance_km": 2.5},
        ]

        # Test descending
        sorted_desc = sort_activities(activities, "distance_desc")
        assert sorted_desc[0]["distance_km"] == 10.0
        assert sorted_desc[1]["distance_km"] == 5.0
        assert sorted_desc[2]["distance_km"] == 2.5

        # Test ascending
        sorted_asc = sort_activities(activities, "distance_asc")
        assert sorted_asc[0]["distance_km"] == 2.5
        assert sorted_asc[1]["distance_km"] == 5.0
        assert sorted_asc[2]["distance_km"] == 10.0

    def test_sort_activities_duration(self):
        """Test sorting activities by duration."""
        activities = [
            {"duration_str": "1:00:00"},  # 3600 seconds
            {"duration_str": "2:00:00"},  # 7200 seconds
            {"duration_str": "0:30:00"},  # 1800 seconds
        ]

        # Test descending
        sorted_desc = sort_activities(activities, "duration_desc")
        assert sorted_desc[0]["duration_str"] == "2:00:00"
        assert sorted_desc[1]["duration_str"] == "1:00:00"
        assert sorted_desc[2]["duration_str"] == "0:30:00"


class TestMapHelpers:
    """Test suite for map helper functions."""

    def test_get_neutral_map_defaults(self):
        """Test neutral map defaults for activities without GPS."""
        center, zoom, message = get_neutral_map_defaults()

        assert center == [0, 0]
        assert zoom == 2
        assert message == "No GPS data available for this activity"

    def test_get_map_center_empty_route(self):
        """Test map center calculation with empty route."""
        center, zoom = get_map_center_from_route([])

        assert center == [0, 0]
        assert zoom == 2

    def test_get_map_center_with_route(self):
        """Test map center calculation with route positions."""
        route_positions = [[52.5200, 13.4050], [52.5210, 13.4060], [52.5220, 13.4070]]  # Berlin

        center, zoom = get_map_center_from_route(route_positions)

        assert center == [52.5200, 13.4050]  # First position
        assert zoom == 13


class TestDistanceValidation:
    """Test suite for distance validation functions."""

    def test_has_valid_distance_valid_cases(self):
        """Test has_valid_distance with valid distance values."""
        assert has_valid_distance({"distance_km": 10.0}) == True
        assert has_valid_distance({"distance_km": 0}) == True
        assert has_valid_distance({"distance_km": 0.0}) == True
        assert has_valid_distance({"distance_km": 42.195}) == True

    def test_has_valid_distance_invalid_cases(self):
        """Test has_valid_distance with invalid distance values."""
        assert has_valid_distance({"distance_km": None}) == False
        assert has_valid_distance({}) == False
        assert has_valid_distance({"distance_km": "10.0"}) == False
        assert has_valid_distance({"distance_km": -1}) == False

    def test_filter_activities_by_distance_valid_range(self):
        """Test filtering activities by distance within valid range."""
        activities = [
            {"distance_km": 5.0},
            {"distance_km": 10.0},
            {"distance_km": 15.0},
            {"distance_km": 20.0},
        ]

        filtered = filter_activities_by_distance(activities, 8.0, 18.0)

        assert len(filtered) == 2
        assert filtered[0]["distance_km"] == 10.0
        assert filtered[1]["distance_km"] == 15.0

    def test_filter_activities_by_distance_excludes_invalid(self):
        """Test that filtering excludes activities with invalid distance."""
        activities = [
            {"distance_km": 5.0},
            {"distance_km": None},
            {},
            {"distance_km": "invalid"},
            {"distance_km": -1},
            {"distance_km": 10.0},
        ]

        filtered = filter_activities_by_distance(activities, 0, 20)

        assert len(filtered) == 2
        assert filtered[0]["distance_km"] == 5.0
        assert filtered[1]["distance_km"] == 10.0

    def test_filter_activities_by_distance_empty_list(self):
        """Test filtering empty activity list."""
        result = filter_activities_by_distance([], 0, 100)
        assert result == []


class TestGPSValidation:
    """Test suite for GPS coordinate validation functions."""

    def test_is_valid_gps_coordinate_valid_cases(self):
        """Test GPS coordinate validation with valid coordinates."""
        assert is_valid_gps_coordinate(52.5200, 13.4050) == True  # Berlin
        assert is_valid_gps_coordinate(0, 0) == True  # Origin
        assert is_valid_gps_coordinate(-90, -180) == True  # Min values
        assert is_valid_gps_coordinate(90, 180) == True  # Max values
        assert is_valid_gps_coordinate(0.0, 0.0) == True  # Float zeros

    def test_is_valid_gps_coordinate_invalid_cases(self):
        """Test GPS coordinate validation with invalid coordinates."""
        assert is_valid_gps_coordinate(None, 13.4050) == False
        assert is_valid_gps_coordinate(52.5200, None) == False
        assert is_valid_gps_coordinate(None, None) == False
        assert is_valid_gps_coordinate("52.5200", 13.4050) == False
        assert is_valid_gps_coordinate(52.5200, "13.4050") == False
        assert is_valid_gps_coordinate(91, 0) == False  # Lat out of range
        assert is_valid_gps_coordinate(-91, 0) == False  # Lat out of range
        assert is_valid_gps_coordinate(0, 181) == False  # Lng out of range
        assert is_valid_gps_coordinate(0, -181) == False  # Lng out of range

    def test_extract_valid_route_positions_valid_data(self):
        """Test extracting valid route positions from sample data."""
        samples_data = [
            {"position_lat": 52.5200, "position_long": 13.4050},
            {"position_lat": 52.5210, "position_long": 13.4060},
            {"position_lat": 52.5220, "position_long": 13.4070},
        ]

        route_positions = extract_valid_route_positions(samples_data)

        assert len(route_positions) == 3
        assert route_positions[0] == [52.5200, 13.4050]
        assert route_positions[1] == [52.5210, 13.4060]
        assert route_positions[2] == [52.5220, 13.4070]

    def test_extract_valid_route_positions_mixed_data(self):
        """Test extracting route positions with mix of valid and invalid data."""
        samples_data = [
            {"position_lat": 52.5200, "position_long": 13.4050},  # Valid
            {"position_lat": None, "position_long": 13.4060},  # Invalid lat
            {"position_lat": 52.5220, "position_long": None},  # Invalid lng
            {"position_lat": "invalid", "position_long": 13.4070},  # Invalid types
            {"position_lat": 52.5240, "position_long": 13.4080},  # Valid
        ]

        route_positions = extract_valid_route_positions(samples_data)

        assert len(route_positions) == 2
        assert route_positions[0] == [52.5200, 13.4050]
        assert route_positions[1] == [52.5240, 13.4080]

    def test_extract_valid_route_positions_empty_data(self):
        """Test extracting route positions from empty or invalid data."""
        assert extract_valid_route_positions([]) == []
        assert extract_valid_route_positions(None) == []
        assert extract_valid_route_positions("invalid") == []

    def test_extract_valid_route_positions_no_gps_data(self):
        """Test extracting route positions when samples have no GPS data."""
        samples_data = [
            {"heart_rate": 150, "elapsed_time_s": 0},
            {"heart_rate": 155, "elapsed_time_s": 30},
        ]

        route_positions = extract_valid_route_positions(samples_data)

        assert len(route_positions) == 0
