"""
Enhanced unit tests for database models.
"""

from datetime import datetime, timezone

import pytest

from app.data.models import Activity, Lap, RoutePoint, Sample


class TestActivityModel:
    """Test suite for Activity model."""

    def test_activity_creation(self, db_session):
        """Test creating a new activity."""
        activity = Activity(
            external_id="test_activity_001",
            file_hash="test_hash_123",
            source="fit",
            sport="running",
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=3600,
            distance_m=10000.0,
            avg_hr=150,
            calories=500,
        )

        db_session.add(activity)
        db_session.commit()

        assert activity.id is not None
        assert activity.external_id == "test_activity_001"
        assert activity.sport == "running"
        assert activity.distance_m == 10000.0
        assert activity.elapsed_time_s == 3600

    def test_activity_relationships(self, activity_with_samples):
        """Test activity relationships with samples, laps, and route points."""
        activity_data = activity_with_samples
        activity = activity_data["activity"]

        # Test samples relationship
        assert len(activity.samples) > 0
        assert all(sample.activity_id == activity.id for sample in activity.samples)

        # Test laps relationship
        assert len(activity.laps) == 2
        assert all(lap.activity_id == activity.id for lap in activity.laps)

        # Test route points relationship
        assert len(activity.route_points) > 0
        assert all(rp.activity_id == activity.id for rp in activity.route_points)

    def test_activity_validation(self, db_session):
        """Test activity model validation."""
        # Test required fields
        with pytest.raises(Exception):  # Should fail without required fields
            activity = Activity()
            db_session.add(activity)
            db_session.commit()

    def test_activity_string_representation(self, db_session):
        """Test activity string representation."""
        activity = Activity(
            external_id="test_activity_001",
            file_hash="test_hash_123",
            source="fit",
            sport="running",
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            name="Morning Run",
        )

        db_session.add(activity)
        db_session.flush()

        assert str(activity) == f"Activity(id={activity.id}, sport=running, name=Morning Run)"


class TestSampleModel:
    """Test suite for Sample model."""

    def test_sample_creation(self, db_session, sample_activities):
        """Test creating a new sample."""
        activity = sample_activities[0]

        sample = Sample(
            activity_id=activity.id,
            timestamp=datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            elapsed_time_s=300,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=100.0,
            heart_rate=150,
            power_w=200.0,
            cadence_rpm=85,
            speed_mps=12.0,
            temperature_c=15.0,
        )

        db_session.add(sample)
        db_session.commit()

        assert sample.id is not None
        assert sample.activity_id == activity.id
        assert sample.latitude == 52.5200
        assert sample.longitude == 13.4050
        assert sample.heart_rate == 150

    def test_sample_relationships(self, activity_with_samples):
        """Test sample relationships."""
        activity_data = activity_with_samples
        samples = activity_data["samples"]
        activity = activity_data["activity"]

        for sample in samples:
            assert sample.activity == activity
            assert sample.activity_id == activity.id

    def test_sample_data_types(self, activity_with_samples):
        """Test sample data types and ranges."""
        samples = activity_with_samples["samples"]

        for sample in samples:
            # GPS coordinates should be reasonable
            if sample.latitude:
                assert -90 <= sample.latitude <= 90
            if sample.longitude:
                assert -180 <= sample.longitude <= 180

            # Heart rate should be reasonable
            if sample.heart_rate:
                assert 50 <= sample.heart_rate <= 220

            # Power should be positive
            if sample.power_w:
                assert sample.power_w >= 0

            # Speed should be positive
            if sample.speed_mps:
                assert sample.speed_mps >= 0


class TestLapModel:
    """Test suite for Lap model."""

    def test_lap_creation(self, db_session, sample_activities):
        """Test creating a new lap."""
        activity = sample_activities[0]

        lap = Lap(
            activity_id=activity.id,
            lap_index=0,
            start_time_utc=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            elapsed_time_s=1800,  # 30 minutes
            distance_m=5000.0,  # 5km
            avg_hr=145,
            max_hr=165,
            avg_power_w=210.0,
            max_power_w=280.0,
        )

        db_session.add(lap)
        db_session.commit()

        assert lap.id is not None
        assert lap.activity_id == activity.id
        assert lap.lap_index == 0
        assert lap.elapsed_time_s == 1800
        assert lap.distance_m == 5000.0

    def test_lap_relationships(self, activity_with_samples):
        """Test lap relationships."""
        activity_data = activity_with_samples
        laps = activity_data["laps"]
        activity = activity_data["activity"]

        for lap in laps:
            assert lap.activity == activity
            assert lap.activity_id == activity.id

    def test_lap_ordering(self, activity_with_samples):
        """Test lap ordering by lap_index."""
        laps = activity_with_samples["laps"]

        # Laps should be ordered by lap_index
        lap_indices = [lap.lap_index for lap in laps]
        assert lap_indices == sorted(lap_indices)

    def test_lap_data_consistency(self, activity_with_samples):
        """Test lap data consistency."""
        laps = activity_with_samples["laps"]

        for lap in laps:
            # Max values should be >= avg values
            if lap.max_hr and lap.avg_hr:
                assert lap.max_hr >= lap.avg_hr
            if lap.max_power_w and lap.avg_power_w:
                assert lap.max_power_w >= lap.avg_power_w

            # Time and distance should be positive
            assert lap.elapsed_time_s > 0
            assert lap.distance_m > 0


class TestRoutePointModel:
    """Test suite for RoutePoint model."""

    def test_route_point_creation(self, db_session, sample_activities):
        """Test creating a new route point."""
        activity = sample_activities[0]

        route_point = RoutePoint(
            activity_id=activity.id,
            sequence=0,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=100.0,
        )

        db_session.add(route_point)
        db_session.commit()

        assert route_point.id is not None
        assert route_point.activity_id == activity.id
        assert route_point.sequence == 0
        assert route_point.latitude == 52.5200
        assert route_point.longitude == 13.4050

    def test_route_point_relationships(self, activity_with_samples):
        """Test route point relationships."""
        activity_data = activity_with_samples
        route_points = activity_data["route_points"]
        activity = activity_data["activity"]

        for route_point in route_points:
            assert route_point.activity == activity
            assert route_point.activity_id == activity.id

    def test_route_point_ordering(self, activity_with_samples):
        """Test route point ordering by sequence."""
        route_points = activity_with_samples["route_points"]

        # Route points should be ordered by sequence
        sequences = [rp.sequence for rp in route_points]
        assert sequences == sorted(sequences)

    def test_route_point_coordinates(self, activity_with_samples):
        """Test route point coordinate validation."""
        route_points = activity_with_samples["route_points"]

        for rp in route_points:
            # GPS coordinates should be in valid ranges
            assert -90 <= rp.latitude <= 90
            assert -180 <= rp.longitude <= 180
            # Altitude can be negative (below sea level) but should be reasonable
            assert -1000 <= rp.altitude_m <= 10000


class TestModelInteractions:
    """Test suite for model interactions and complex queries."""

    def test_activity_sample_count(self, activity_with_samples):
        """Test counting samples for an activity."""
        activity = activity_with_samples["activity"]

        sample_count = len(activity.samples)
        assert sample_count == 180  # Should match fixture data

    def test_activity_duration_calculation(self, activity_with_samples):
        """Test activity duration calculations."""
        activity = activity_with_samples["activity"]
        samples = activity.samples

        if samples:
            # Last sample elapsed time should be close to activity duration
            last_sample = max(samples, key=lambda s: s.elapsed_time_s)
            assert abs(last_sample.elapsed_time_s - activity.elapsed_time_s) <= 60  # Within 1 minute

    def test_lap_time_consistency(self, activity_with_samples):
        """Test lap timing consistency."""
        activity = activity_with_samples["activity"]
        laps = activity.laps

        total_lap_time = sum(lap.elapsed_time_s for lap in laps)
        assert abs(total_lap_time - activity.elapsed_time_s) <= 60  # Within 1 minute

    def test_cascade_delete(self, db_session, activity_with_samples):
        """Test cascade delete behavior."""
        activity = activity_with_samples["activity"]
        activity_id = activity.id

        # Count related objects before delete
        sample_count = len(activity.samples)
        lap_count = len(activity.laps)
        route_count = len(activity.route_points)

        assert sample_count > 0
        assert lap_count > 0
        assert route_count > 0

        # Delete activity
        db_session.delete(activity)
        db_session.commit()

        # Verify related objects are also deleted
        remaining_samples = db_session.query(Sample).filter(Sample.activity_id == activity_id).count()
        remaining_laps = db_session.query(Lap).filter(Lap.activity_id == activity_id).count()
        remaining_routes = db_session.query(RoutePoint).filter(RoutePoint.activity_id == activity_id).count()

        assert remaining_samples == 0
        assert remaining_laps == 0
        assert remaining_routes == 0
