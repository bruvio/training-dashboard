"""
Unit tests for app utility functions.
"""


from app.utils import (
    filter_activities_by_distance,
    parse_duration_to_seconds,
    sort_activities,
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

    def test_sort_activities_default(self):
        """Test default sorting behavior."""
        activities = [
            {"start_time": "2024-01-01T10:00:00"},
            {"start_time": "2024-01-02T10:00:00"},
        ]

        sorted_activities = sort_activities(activities, "invalid_sort")

        # With invalid sort, should preserve original order (returns "" as sort key)
        assert sorted_activities[0]["start_time"] == "2024-01-01T10:00:00"
        assert sorted_activities[1]["start_time"] == "2024-01-02T10:00:00"

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

    def test_filter_activities_by_distance_empty_result(self):
        """Test filtering activities with no results."""
        activities = [
            {"distance_km": 5.0, "id": 1},
            {"distance_km": 35.0, "id": 2},
        ]

        filtered = filter_activities_by_distance(activities, 10.0, 20.0)
        assert len(filtered) == 0

    def test_filter_activities_by_distance_missing_distance(self):
        """Test filtering activities with missing distance data."""
        activities = [
            {"distance_km": None, "id": 1},
            {"distance_km": 15.0, "id": 2},
            {"id": 3},  # Missing distance_km entirely
        ]

        filtered = filter_activities_by_distance(activities, 10.0, 20.0)
        assert len(filtered) == 1
        assert filtered[0]["id"] == 2
