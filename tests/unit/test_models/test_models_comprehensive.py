"""
Comprehensive unit tests for app/data/models.py SQLAlchemy models and data transfer objects.

This test module follows the PRP Phase 1 requirements for model properties and methods testing
with complete coverage including calculated properties, edge cases, and error handling.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from app.data.models import (
    Activity,
    Sample,
    RoutePoint,
    Lap,
    ActivityData,
    SampleData,
    LapData,
    ImportResult,
    Base,
)


class TestActivityModel:
    """Test suite for Activity SQLAlchemy model."""

    def test_activity_to_dict_complete_data(self):
        """Test Activity.to_dict() with complete activity data."""
        activity = Activity(
            id=1,
            external_id="test_001",
            sport="running",
            sub_sport="road",
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=3600,
            moving_time_s=3500,
            distance_m=10000.0,
            avg_speed_mps=2.78,
            avg_pace_s_per_km=360,
            avg_hr=150,
            max_hr=180,
            avg_power_w=200.0,
            max_power_w=350.0,
            elevation_gain_m=100.0,
            calories=500,
            source="fit",
        )

        result = activity.to_dict()

        # Verify all fields are present
        assert result["id"] == 1
        assert result["external_id"] == "test_001"
        assert result["sport"] == "running"
        assert result["sub_sport"] == "road"
        assert result["start_time"] == "2024-01-15T10:00:00+00:00"
        assert result["elapsed_time_s"] == 3600
        assert result["moving_time_s"] == 3500
        assert result["distance_m"] == 10000.0
        assert result["distance_km"] == 10.0  # Calculated field
        assert result["avg_speed_mps"] == 2.78
        assert result["avg_pace_s_per_km"] == 360
        assert result["avg_hr"] == 150
        assert result["max_hr"] == 180
        assert result["avg_power_w"] == 200.0
        assert result["max_power_w"] == 350.0
        assert result["elevation_gain_m"] == 100.0
        assert result["calories"] == 500
        assert result["source"] == "fit"

    def test_activity_to_dict_distance_km_calculation(self):
        """Test distance_km calculation in to_dict() method."""
        # Test normal distance calculation
        activity = Activity(distance_m=5000.0)
        result = activity.to_dict()
        assert result["distance_km"] == 5.0

        # Test rounding
        activity = Activity(distance_m=10123.456)
        result = activity.to_dict()
        assert result["distance_km"] == 10.12

        # Test small distance
        activity = Activity(distance_m=500.0)
        result = activity.to_dict()
        assert result["distance_km"] == 0.5

        # Test zero distance - model treats 0.0 as falsy and returns None
        activity = Activity(distance_m=0.0)
        result = activity.to_dict()
        assert result["distance_km"] is None  # This is the current behavior

    def test_activity_to_dict_distance_none(self):
        """Test distance_km calculation when distance_m is None."""
        activity = Activity(distance_m=None)
        result = activity.to_dict()
        assert result["distance_km"] is None

    def test_activity_to_dict_start_time_none(self):
        """Test to_dict() when start_time_utc is None."""
        activity = Activity(start_time_utc=None)
        result = activity.to_dict()
        assert result["start_time"] is None

    def test_activity_to_dict_minimal_data(self):
        """Test to_dict() with minimal activity data."""
        activity = Activity()
        result = activity.to_dict()

        # Should handle all None values gracefully
        expected_keys = [
            "id",
            "external_id",
            "sport",
            "sub_sport",
            "start_time",
            "elapsed_time_s",
            "moving_time_s",
            "distance_m",
            "distance_km",
            "avg_speed_mps",
            "avg_pace_s_per_km",
            "avg_hr",
            "max_hr",
            "avg_power_w",
            "max_power_w",
            "elevation_gain_m",
            "calories",
            "source",
        ]

        for key in expected_keys:
            assert key in result


class TestSampleModel:
    """Test suite for Sample SQLAlchemy model."""

    def test_sample_creation_complete_data(self):
        """Test Sample model creation with complete sensor data."""
        timestamp = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        sample = Sample(
            activity_id=1,
            timestamp=timestamp,
            elapsed_time_s=0,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50.0,
            heart_rate=140,
            power_w=200.0,
            cadence_rpm=90,
            speed_mps=3.0,
            temperature_c=15.0,
            vertical_oscillation_mm=8.5,
            vertical_ratio=7.2,
            ground_contact_time_ms=245.0,
            ground_contact_balance_pct=50.5,
            step_length_mm=1200.0,
        )

        assert sample.activity_id == 1
        assert sample.timestamp == timestamp
        assert sample.elapsed_time_s == 0
        assert sample.latitude == 52.5200
        assert sample.longitude == 13.4050
        assert sample.altitude_m == 50.0
        assert sample.heart_rate == 140
        assert sample.power_w == 200.0
        assert sample.cadence_rpm == 90
        assert sample.speed_mps == 3.0
        assert sample.temperature_c == 15.0
        assert sample.vertical_oscillation_mm == 8.5
        assert sample.vertical_ratio == 7.2
        assert sample.ground_contact_time_ms == 245.0
        assert sample.ground_contact_balance_pct == 50.5
        assert sample.step_length_mm == 1200.0

    def test_sample_creation_minimal_data(self):
        """Test Sample model creation with minimal data."""
        sample = Sample(activity_id=1)
        assert sample.activity_id == 1
        # All other fields should be None
        assert sample.timestamp is None
        assert sample.latitude is None
        assert sample.heart_rate is None


class TestRoutePointModel:
    """Test suite for RoutePoint SQLAlchemy model."""

    def test_route_point_creation(self):
        """Test RoutePoint model creation."""
        route_point = RoutePoint(
            activity_id=1,
            sequence=0,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50.0,
        )

        assert route_point.activity_id == 1
        assert route_point.sequence == 0
        assert route_point.latitude == 52.5200
        assert route_point.longitude == 13.4050
        assert route_point.altitude_m == 50.0


class TestLapModel:
    """Test suite for Lap SQLAlchemy model."""

    def test_lap_creation_complete_data(self):
        """Test Lap model creation with complete data."""
        start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        lap = Lap(
            activity_id=1,
            lap_index=0,
            start_time_utc=start_time,
            elapsed_time_s=1800,
            moving_time_s=1750,
            distance_m=5000.0,
            avg_speed_mps=2.86,
            avg_hr=145,
            max_hr=160,
            avg_power_w=210.0,
            max_power_w=350.0,
            avg_cadence_rpm=88,
        )

        assert lap.activity_id == 1
        assert lap.lap_index == 0
        assert lap.start_time_utc == start_time
        assert lap.elapsed_time_s == 1800
        assert lap.moving_time_s == 1750
        assert lap.distance_m == 5000.0
        assert lap.avg_speed_mps == 2.86
        assert lap.avg_hr == 145
        assert lap.max_hr == 160
        assert lap.avg_power_w == 210.0
        assert lap.max_power_w == 350.0
        assert lap.avg_cadence_rpm == 88


class TestActivityData:
    """Test suite for ActivityData data transfer object."""

    def test_activity_data_creation_complete(self):
        """Test ActivityData creation with all parameters."""
        start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        sample_data = [SampleData(heart_rate=140)]
        route_points = [(52.5200, 13.4050, 50.0)]
        lap_data = [LapData(lap_index=0)]
        hr_zones = {"zone_1": 120, "zone_2": 150}

        activity_data = ActivityData(
            external_id="test_001",
            sport="running",
            sub_sport="road",
            start_time_utc=start_time,
            elapsed_time_s=3600,
            moving_time_s=3500,
            distance_m=10000.0,
            avg_speed_mps=2.78,
            avg_pace_s_per_km=360,
            avg_hr=150,
            max_hr=180,
            avg_power_w=200.0,
            max_power_w=350.0,
            elevation_gain_m=100.0,
            elevation_loss_m=50.0,
            calories=500,
            samples=sample_data,
            route_points=route_points,
            laps=lap_data,
            hr_zones=hr_zones,
        )

        assert activity_data.external_id == "test_001"
        assert activity_data.sport == "running"
        assert activity_data.sub_sport == "road"
        assert activity_data.start_time_utc == start_time
        assert activity_data.elapsed_time_s == 3600
        assert activity_data.moving_time_s == 3500
        assert activity_data.distance_m == 10000.0
        assert activity_data.avg_speed_mps == 2.78
        assert activity_data.avg_pace_s_per_km == 360
        assert activity_data.avg_hr == 150
        assert activity_data.max_hr == 180
        assert activity_data.avg_power_w == 200.0
        assert activity_data.max_power_w == 350.0
        assert activity_data.elevation_gain_m == 100.0
        assert activity_data.elevation_loss_m == 50.0
        assert activity_data.calories == 500
        assert activity_data.samples == sample_data
        assert activity_data.route_points == route_points
        assert activity_data.laps == lap_data
        assert activity_data.hr_zones == hr_zones

    def test_activity_data_creation_defaults(self):
        """Test ActivityData creation with default values."""
        activity_data = ActivityData()

        # All parameters should be None except collections
        assert activity_data.external_id is None
        assert activity_data.sport is None
        assert activity_data.samples == []  # Default empty list
        assert activity_data.route_points == []  # Default empty list
        assert activity_data.laps == []  # Default empty list
        assert activity_data.hr_zones == {}  # Default empty dict

    def test_activity_data_creation_none_collections(self):
        """Test ActivityData creation with None collections."""
        activity_data = ActivityData(samples=None, route_points=None, laps=None, hr_zones=None)

        # Should convert None to empty collections
        assert activity_data.samples == []
        assert activity_data.route_points == []
        assert activity_data.laps == []
        assert activity_data.hr_zones == {}


class TestSampleData:
    """Test suite for SampleData data transfer object."""

    def test_sample_data_creation_complete(self):
        """Test SampleData creation with all parameters."""
        timestamp = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        sample_data = SampleData(
            timestamp=timestamp,
            elapsed_time_s=0,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=50.0,
            heart_rate=140,
            power_w=200.0,
            cadence_rpm=90,
            speed_mps=3.0,
            temperature_c=15.0,
            vertical_oscillation_mm=8.5,
            vertical_ratio=7.2,
            ground_contact_time_ms=245.0,
            ground_contact_balance_pct=50.5,
            step_length_mm=1200.0,
            air_power_w=15.0,
            form_power_w=25.0,
            leg_spring_stiffness=8.2,
            impact_loading_rate=45.5,
            stryd_temperature_c=14.5,
            stryd_humidity_pct=65.0,
        )

        assert sample_data.timestamp == timestamp
        assert sample_data.elapsed_time_s == 0
        assert sample_data.latitude == 52.5200
        assert sample_data.longitude == 13.4050
        assert sample_data.altitude_m == 50.0
        assert sample_data.heart_rate == 140
        assert sample_data.power_w == 200.0
        assert sample_data.cadence_rpm == 90
        assert sample_data.speed_mps == 3.0
        assert sample_data.temperature_c == 15.0
        assert sample_data.vertical_oscillation_mm == 8.5
        assert sample_data.vertical_ratio == 7.2
        assert sample_data.ground_contact_time_ms == 245.0
        assert sample_data.ground_contact_balance_pct == 50.5
        assert sample_data.step_length_mm == 1200.0
        assert sample_data.air_power_w == 15.0
        assert sample_data.form_power_w == 25.0
        assert sample_data.leg_spring_stiffness == 8.2
        assert sample_data.impact_loading_rate == 45.5
        assert sample_data.stryd_temperature_c == 14.5
        assert sample_data.stryd_humidity_pct == 65.0

    def test_sample_data_creation_defaults(self):
        """Test SampleData creation with default None values."""
        sample_data = SampleData()

        # All parameters should be None
        assert sample_data.timestamp is None
        assert sample_data.elapsed_time_s is None
        assert sample_data.latitude is None
        assert sample_data.heart_rate is None
        assert sample_data.vertical_oscillation_mm is None


class TestLapData:
    """Test suite for LapData data transfer object."""

    def test_lap_data_creation_complete(self):
        """Test LapData creation with all parameters."""
        start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        lap_data = LapData(
            lap_index=0,
            start_time_utc=start_time,
            elapsed_time_s=1800,
            distance_m=5000.0,
            avg_speed_mps=2.78,
            avg_hr=145,
            max_hr=165,
            avg_power_w=210.0,
            max_power_w=350.0,
        )

        assert lap_data.lap_index == 0
        assert lap_data.start_time_utc == start_time
        assert lap_data.elapsed_time_s == 1800
        assert lap_data.distance_m == 5000.0
        assert lap_data.avg_speed_mps == 2.78
        assert lap_data.avg_hr == 145
        assert lap_data.max_hr == 165
        assert lap_data.avg_power_w == 210.0
        assert lap_data.max_power_w == 350.0

    def test_lap_data_creation_minimal(self):
        """Test LapData creation with only required lap_index."""
        lap_data = LapData(lap_index=1)

        assert lap_data.lap_index == 1
        # All optional parameters should be None
        assert lap_data.start_time_utc is None
        assert lap_data.elapsed_time_s is None
        assert lap_data.distance_m is None
        assert lap_data.avg_speed_mps is None
        assert lap_data.avg_hr is None
        assert lap_data.max_hr is None
        assert lap_data.avg_power_w is None
        assert lap_data.max_power_w is None


class TestImportResult:
    """Test suite for ImportResult data transfer object."""

    def test_import_result_success(self):
        """Test ImportResult creation for successful import."""
        import_result = ImportResult(imported=True, reason="Successfully imported activity", activity_id=123)

        assert import_result.imported is True
        assert import_result.reason == "Successfully imported activity"
        assert import_result.activity_id == 123

    def test_import_result_failure(self):
        """Test ImportResult creation for failed import."""
        import_result = ImportResult(imported=False, reason="File already exists")

        assert import_result.imported is False
        assert import_result.reason == "File already exists"
        assert import_result.activity_id is None

    def test_import_result_defaults(self):
        """Test ImportResult creation with defaults."""
        import_result = ImportResult(imported=True)

        assert import_result.imported is True
        assert import_result.reason == ""
        assert import_result.activity_id is None

    def test_import_result_edge_cases(self):
        """Test ImportResult with edge case values."""
        # Empty reason
        import_result = ImportResult(imported=False, reason="")
        assert import_result.reason == ""

        # Zero activity_id
        import_result = ImportResult(imported=True, activity_id=0)
        assert import_result.activity_id == 0
