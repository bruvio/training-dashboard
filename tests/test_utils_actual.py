"""
Unit tests for actual app utility functions.
"""

from app.utils import (
    filter_activities_by_distance,
    parse_duration_to_seconds,
    sort_activities,
    has_valid_distance,
    is_valid_gps_coordinate,
    extract_valid_route_positions,
)


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_parse_duration_to_seconds_simple(self):
        """Test parsing simple duration strings."""
        assert parse_duration_to_seconds("0:00:30") == 30
        assert parse_duration_to_seconds("0:02:30") == 150  # 2:30 minutes
        assert parse_duration_to_seconds("1:30:45") == 5445  # 1 hour 30 min 45 sec

    def test_parse_duration_to_seconds_invalid(self):
        """Test parsing invalid duration strings."""
        assert parse_duration_to_seconds("invalid") == 0
        assert parse_duration_to_seconds("") == 0
        assert parse_duration_to_seconds(None) == 0

    def test_parse_duration_to_seconds_edge_cases(self):
        """Test parsing edge cases."""
        assert parse_duration_to_seconds("0:00:00") == 0
        assert parse_duration_to_seconds("24:00:00") == 86400  # 24 hours

    def test_sort_activities_date_desc(self):
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

    def test_sort_activities_date_asc(self):
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

    def test_sort_activities_distance_desc(self):
        """Test sorting activities by distance descending."""
        activities = [
            {"distance_km": 5.0, "start_time": "2024-01-01T10:00:00"},
            {"distance_km": 15.0, "start_time": "2024-01-02T10:00:00"},
            {"distance_km": 10.0, "start_time": "2024-01-03T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "distance_desc")

        assert sorted_activities[0]["distance_km"] == 15.0
        assert sorted_activities[1]["distance_km"] == 10.0
        assert sorted_activities[2]["distance_km"] == 5.0

    def test_sort_activities_distance_asc(self):
        """Test sorting activities by distance ascending."""
        activities = [
            {"distance_km": 15.0, "start_time": "2024-01-01T10:00:00"},
            {"distance_km": 5.0, "start_time": "2024-01-02T10:00:00"},
            {"distance_km": 10.0, "start_time": "2024-01-03T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "distance_asc")

        assert sorted_activities[0]["distance_km"] == 5.0
        assert sorted_activities[1]["distance_km"] == 10.0
        assert sorted_activities[2]["distance_km"] == 15.0

    def test_sort_activities_duration_desc(self):
        """Test sorting activities by duration descending."""
        activities = [
            {"duration_str": "1:00:00", "start_time": "2024-01-01T10:00:00"},
            {"duration_str": "2:30:00", "start_time": "2024-01-02T10:00:00"},
            {"duration_str": "0:45:00", "start_time": "2024-01-03T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "duration_desc")

        assert sorted_activities[0]["duration_str"] == "2:30:00"
        assert sorted_activities[1]["duration_str"] == "1:00:00"
        assert sorted_activities[2]["duration_str"] == "0:45:00"

    def test_filter_activities_by_distance_within_range(self):
        """Test filtering activities by distance within range."""
        activities = [
            {"distance_km": 5.0, "id": 1},
            {"distance_km": 15.0, "id": 2},
            {"distance_km": 25.0, "id": 3},
        ]

        filtered = filter_activities_by_distance(activities, 10.0, 20.0)

        assert len(filtered) == 1
        assert filtered[0]["id"] == 2

    def test_filter_activities_by_distance_edge_cases(self):
        """Test filtering activities by distance edge cases."""
        activities = [
            {"distance_km": 10.0, "id": 1},
            {"distance_km": 20.0, "id": 2},
            {"distance_km": 30.0, "id": 3},
        ]

        # Test exact boundaries
        filtered = filter_activities_by_distance(activities, 10.0, 20.0)
        assert len(filtered) == 2
        assert {act["id"] for act in filtered} == {1, 2}

    def test_has_valid_distance_valid(self):
        """Test has_valid_distance with valid data."""
        activity_valid = {"distance_km": 10.5}
        assert has_valid_distance(activity_valid) == True

        activity_zero = {"distance_km": 0.0}
        assert has_valid_distance(activity_zero) == True  # 0.0 is valid distance

    def test_has_valid_distance_invalid(self):
        """Test has_valid_distance with invalid data."""
        activity_none = {"distance_km": None}
        assert has_valid_distance(activity_none) == False

        activity_missing = {}
        assert has_valid_distance(activity_missing) == False

    def test_is_valid_gps_coordinate_valid(self):
        """Test is_valid_gps_coordinate with valid coordinates."""
        assert is_valid_gps_coordinate(52.5200, 13.4050) == True  # Berlin
        assert is_valid_gps_coordinate(0.0, 0.0) == True  # Null Island
        assert is_valid_gps_coordinate(-90.0, -180.0) == True  # Valid boundaries
        assert is_valid_gps_coordinate(90.0, 180.0) == True  # Valid boundaries

    def test_is_valid_gps_coordinate_invalid(self):
        """Test is_valid_gps_coordinate with invalid coordinates."""
        assert is_valid_gps_coordinate(91.0, 0.0) == False  # Lat too high
        assert is_valid_gps_coordinate(-91.0, 0.0) == False  # Lat too low
        assert is_valid_gps_coordinate(0.0, 181.0) == False  # Lon too high
        assert is_valid_gps_coordinate(0.0, -181.0) == False  # Lon too low
        assert is_valid_gps_coordinate(None, 0.0) == False  # None latitude
        assert is_valid_gps_coordinate(0.0, None) == False  # None longitude

    def test_extract_valid_route_positions(self):
        """Test extracting valid GPS positions from route data."""
        route_points = [
            {"position_lat": 52.5200, "position_long": 13.4050},  # Valid Berlin
            {"position_lat": None, "position_long": 13.4050},  # Invalid - None lat
            {"position_lat": 52.5210, "position_long": None},  # Invalid - None lon
            {"position_lat": 95.0, "position_long": 13.4050},  # Invalid - lat too high
            {"position_lat": 52.5220, "position_long": 13.4060},  # Valid Berlin
        ]

        valid_positions = extract_valid_route_positions(route_points)

        assert len(valid_positions) == 2
        assert valid_positions[0] == [52.5200, 13.4050]
        assert valid_positions[1] == [52.5220, 13.4060]

    def test_extract_valid_route_positions_empty(self):
        """Test extracting valid positions from empty or all-invalid data."""
        # Empty list
        assert extract_valid_route_positions([]) == []

        # All invalid
        invalid_route = [
            {"position_lat": None, "position_long": None},
            {"position_lat": 95.0, "position_long": 200.0},
        ]
        assert extract_valid_route_positions(invalid_route) == []
