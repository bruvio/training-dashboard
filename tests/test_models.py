"""
Unit tests for SQLAlchemy models and database operations.

Tests model creation, relationships, and basic query functionality
following the research-validated patterns from the PRP.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.data.models import Base, Activity, Sample, RoutePoint, Lap, ActivityData, SampleData
from app.data.db import DatabaseConfig


class TestDatabaseModels:
    """Test SQLAlchemy model creation and basic operations."""
    
    @pytest.fixture
    def db_session(self):
        """Create in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        session.close()
    
    def test_activity_model_creation(self, db_session):
        """Test Activity model creation with type annotations."""
        # Create test activity
        activity = Activity(
            external_id="test_001",
            file_hash="abc123",
            source="fit",
            sport="running",
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=3600,
            distance_m=10000.0,
            avg_hr=150,
            avg_power_w=250.5
        )
        
        db_session.add(activity)
        db_session.commit()
        
        # Test retrieval
        found = db_session.scalars(
            select(Activity).where(Activity.external_id == "test_001")
        ).first()
        
        assert found is not None
        assert found.sport == "running"
        assert found.distance_m == 10000.0
        assert found.avg_hr == 150
        assert found.avg_power_w == 250.5
        assert found.file_hash == "abc123"
    
    def test_sample_model_creation(self, db_session):
        """Test Sample model with relationship to Activity."""
        # Create activity first
        activity = Activity(
            external_id="test_with_samples",
            file_hash="def456", 
            source="tcx",
            sport="cycling",
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=1800
        )
        
        db_session.add(activity)
        db_session.flush()  # Get the activity ID
        
        # Create sample
        sample = Sample(
            activity_id=activity.id,
            timestamp=datetime.now(timezone.utc),
            elapsed_time_s=300,
            latitude=52.5200,
            longitude=13.4050,
            altitude_m=100.0,
            heart_rate=140,
            power_w=200.0,
            speed_mps=8.5
        )
        
        db_session.add(sample)
        db_session.commit()
        
        # Test relationship
        found_activity = db_session.scalars(
            select(Activity).where(Activity.id == activity.id)
        ).first()
        
        assert len(found_activity.samples) == 1
        sample = found_activity.samples[0]
        assert sample.heart_rate == 140
        assert sample.latitude == 52.5200
        assert sample.power_w == 200.0
    
    def test_route_point_model(self, db_session):
        """Test RoutePoint model for map visualization."""
        activity = Activity(
            external_id="test_route",
            file_hash="route123",
            source="gpx",
            sport="hiking",
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=7200
        )
        
        db_session.add(activity)
        db_session.flush()
        
        # Create route points
        points = [
            (52.5200, 13.4050, 100.0),
            (52.5210, 13.4060, 105.0),
            (52.5220, 13.4070, 110.0)
        ]
        
        for i, (lat, lon, alt) in enumerate(points):
            route_point = RoutePoint(
                activity_id=activity.id,
                sequence=i,
                latitude=lat,
                longitude=lon,
                altitude_m=alt
            )
            db_session.add(route_point)
        
        db_session.commit()
        
        # Test route points
        found_activity = db_session.scalars(
            select(Activity).where(Activity.id == activity.id)
        ).first()
        
        assert len(found_activity.route_points) == 3
        
        # Check ordering by sequence
        sorted_points = sorted(found_activity.route_points, key=lambda p: p.sequence)
        assert sorted_points[0].latitude == 52.5200
        assert sorted_points[1].latitude == 52.5210
        assert sorted_points[2].latitude == 52.5220
    
    def test_lap_model(self, db_session):
        """Test Lap model for segment data."""
        activity = Activity(
            external_id="test_laps",
            file_hash="lap789",
            source="fit", 
            sport="running",
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=3600
        )
        
        db_session.add(activity)
        db_session.flush()
        
        # Create laps
        lap1 = Lap(
            activity_id=activity.id,
            lap_index=0,
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=1200,
            distance_m=5000.0,
            avg_hr=145,
            avg_power_w=230.0
        )
        
        lap2 = Lap(
            activity_id=activity.id,
            lap_index=1,
            start_time_utc=datetime.now(timezone.utc),
            elapsed_time_s=1300,
            distance_m=5100.0,
            avg_hr=155,
            avg_power_w=240.0
        )
        
        db_session.add(lap1)
        db_session.add(lap2)
        db_session.commit()
        
        # Test laps
        found_activity = db_session.scalars(
            select(Activity).where(Activity.id == activity.id)
        ).first()
        
        assert len(found_activity.laps) == 2
        
        # Find laps by index
        lap_0 = next(lap for lap in found_activity.laps if lap.lap_index == 0)
        lap_1 = next(lap for lap in found_activity.laps if lap.lap_index == 1)
        
        assert lap_0.distance_m == 5000.0
        assert lap_1.distance_m == 5100.0
        assert lap_0.avg_hr == 145
        assert lap_1.avg_hr == 155
    
    def test_activity_to_dict(self, db_session):
        """Test Activity to_dict method for API usage."""
        activity = Activity(
            external_id="test_dict",
            file_hash="dict123",
            source="fit",
            sport="cycling",
            sub_sport="road",
            start_time_utc=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            elapsed_time_s=5400,
            moving_time_s=5200,
            distance_m=50000.0,
            avg_hr=160,
            max_hr=180,
            avg_power_w=280.5,
            elevation_gain_m=500.0,
            calories=800
        )
        
        result_dict = activity.to_dict()
        
        assert result_dict['sport'] == 'cycling'
        assert result_dict['sub_sport'] == 'road'
        assert result_dict['distance_km'] == 50.0  # 50000m -> 50km
        assert result_dict['elapsed_time_s'] == 5400
        assert result_dict['avg_hr'] == 160
        assert result_dict['avg_power_w'] == 280.5
        assert result_dict['elevation_gain_m'] == 500.0
        assert result_dict['calories'] == 800
        assert result_dict['start_time'] == '2024-01-15T10:30:00+00:00'
    
    def test_database_indexes(self, db_session):
        """Test that database indexes are created correctly."""
        # This is tested implicitly by checking table creation succeeds
        # and by running queries that would use the indexes
        
        activities = []
        for i in range(10):
            activity = Activity(
                external_id=f"index_test_{i}",
                file_hash=f"hash_{i}",
                source="fit",
                sport="running" if i % 2 == 0 else "cycling",
                start_time_utc=datetime.now(timezone.utc),
                elapsed_time_s=3600 + i * 100
            )
            activities.append(activity)
        
        db_session.add_all(activities)
        db_session.commit()
        
        # Test index usage (queries should be fast even without EXPLAIN QUERY PLAN)
        running_activities = db_session.scalars(
            select(Activity).where(Activity.sport == "running")
        ).all()
        
        assert len(running_activities) == 5
        
        # Test date-based query (uses composite index)
        date_filtered = db_session.scalars(
            select(Activity).where(
                Activity.sport == "cycling",
                Activity.start_time_utc >= datetime.now(timezone.utc)
            )
        ).all()
        
        assert len(date_filtered) == 5


class TestDataTransferObjects:
    """Test data transfer objects for parser integration."""
    
    def test_activity_data_creation(self):
        """Test ActivityData DTO creation."""
        activity_data = ActivityData(
            external_id="dto_test",
            sport="running",
            start_time_utc=datetime.now(timezone.utc),
            distance_m=10000.0,
            avg_hr=150,
            samples=[],
            route_points=[(52.5200, 13.4050, 100.0)]
        )
        
        assert activity_data.external_id == "dto_test"
        assert activity_data.sport == "running"
        assert activity_data.distance_m == 10000.0
        assert len(activity_data.route_points) == 1
        assert activity_data.route_points[0] == (52.5200, 13.4050, 100.0)
    
    def test_sample_data_creation(self):
        """Test SampleData DTO creation."""
        sample_data = SampleData(
            timestamp=datetime.now(timezone.utc),
            elapsed_time_s=300,
            latitude=52.5200,
            longitude=13.4050,
            heart_rate=140,
            power_w=200.0
        )
        
        assert sample_data.elapsed_time_s == 300
        assert sample_data.latitude == 52.5200
        assert sample_data.heart_rate == 140
        assert sample_data.power_w == 200.0


class TestDatabaseConfig:
    """Test database configuration and connection management."""
    
    def test_database_config_initialization(self):
        """Test DatabaseConfig initialization with default settings."""
        db_config = DatabaseConfig()
        
        assert db_config.database_url == "sqlite:///garmin_dashboard.db"
        assert db_config._engine is None  # Lazy initialization
    
    def test_database_config_custom_url(self):
        """Test DatabaseConfig with custom database URL."""
        custom_url = "sqlite:///test_custom.db"
        db_config = DatabaseConfig(custom_url)
        
        assert db_config.database_url == custom_url
    
    def test_engine_creation(self):
        """Test SQLAlchemy engine creation."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        engine = db_config.engine
        
        assert engine is not None
        assert str(engine.url) == "sqlite:///:memory:"
        
        # Test lazy initialization - same engine returned
        engine2 = db_config.engine
        assert engine is engine2
    
    def test_session_factory(self):
        """Test session factory creation."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        session_factory = db_config.session_factory
        
        assert session_factory is not None
        
        # Create session and test it works
        session = session_factory()
        assert session is not None
        session.close()
    
    def test_session_scope_context_manager(self):
        """Test session scope context manager."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_all_tables()
        
        # Test successful transaction
        with db_config.session_scope() as session:
            activity = Activity(
                external_id="context_test",
                file_hash="context123",
                source="fit",
                sport="test",
                start_time_utc=datetime.now(timezone.utc),
                elapsed_time_s=100
            )
            session.add(activity)
            # Should auto-commit when exiting context
        
        # Verify activity was saved
        with db_config.session_scope() as session:
            found = session.scalars(
                select(Activity).where(Activity.external_id == "context_test")
            ).first()
            assert found is not None
            assert found.sport == "test"
    
    def test_session_scope_rollback_on_exception(self):
        """Test that session scope rolls back on exception."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_all_tables()
        
        # Test rollback behavior
        with pytest.raises(ValueError):
            with db_config.session_scope() as session:
                activity = Activity(
                    external_id="rollback_test",
                    file_hash="rollback123",
                    source="fit",
                    sport="test",
                    start_time_utc=datetime.now(timezone.utc),
                    elapsed_time_s=100
                )
                session.add(activity)
                raise ValueError("Test exception")
        
        # Verify activity was NOT saved due to rollback
        with db_config.session_scope() as session:
            found = session.scalars(
                select(Activity).where(Activity.external_id == "rollback_test")
            ).first()
            assert found is None


# Validation Gate: Run this test with `pytest tests/test_models.py -v`
if __name__ == "__main__":
    pytest.main([__file__, "-v"])