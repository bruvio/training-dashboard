"""
Pytest configuration and shared fixtures for Garmin Dashboard tests.

Provides common test setup, database fixtures, and test data generation
following pytest best practices and research-validated patterns.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import pytest

from app.data.db import init_database
from app.data.models import Activity, Lap, RoutePoint, Sample


@pytest.fixture(scope="session")
def temp_database():
    """Create temporary database for testing session."""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp())
    db_path = temp_dir / "test_garmin_dashboard.db"

    # Initialize database
    db_url = f"sqlite:///{db_path}"
    yield init_database(db_url)
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def db_session(temp_database):
    """Create database session for individual tests."""
    session = temp_database.get_session()

    yield session

    # Cleanup - rollback any uncommitted changes
    session.rollback()
    session.close()


@pytest.fixture
def sample_activities(db_session):
    """Create sample activities for testing."""
    activities = []
    base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Create diverse test activities
    activity_data = [
        {
            "external_id": "garmin_001",
            "sport": "running",
            "distance_m": 10000.0,
            "elapsed_time_s": 3600,
            "avg_hr": 150,
            "avg_power_w": None,
            "elevation_gain_m": 100.0,
        },
        {
            "external_id": "garmin_002",
            "sport": "cycling",
            "distance_m": 50000.0,
            "elapsed_time_s": 7200,
            "avg_hr": 140,
            "avg_power_w": 200.0,
            "elevation_gain_m": 500.0,
        },
        {
            "external_id": "garmin_003",
            "sport": "swimming",
            "distance_m": 2000.0,
            "elapsed_time_s": 2400,
            "avg_hr": 130,
            "avg_power_w": None,
            "elevation_gain_m": 0.0,
        },
        {
            "external_id": "garmin_004",
            "sport": "hiking",
            "distance_m": 15000.0,
            "elapsed_time_s": 18000,
            "avg_hr": 120,
            "avg_power_w": None,
            "elevation_gain_m": 800.0,
        },
    ]

    for i, data in enumerate(activity_data):
        activity = Activity(
            external_id=data["external_id"],
            file_hash=f"hash_{i}",
            source="fit",
            sport=data["sport"],
            start_time_utc=base_time + timedelta(days=i),
            elapsed_time_s=data["elapsed_time_s"],
            distance_m=data["distance_m"],
            avg_hr=data["avg_hr"],
            avg_power_w=data["avg_power_w"],
            elevation_gain_m=data["elevation_gain_m"],
            calories=500 + i * 100,
        )

        db_session.add(activity)
        activities.append(activity)

    db_session.commit()

    return activities


@pytest.fixture
def activity_with_samples(db_session):
    """Create activity with sample data for detailed testing."""
    # Create base activity
    activity = Activity(
        external_id="detailed_activity",
        file_hash="detailed_hash",
        source="fit",
        sport="cycling",
        start_time_utc=datetime(2024, 1, 20, 8, 0, 0, tzinfo=timezone.utc),
        elapsed_time_s=5400,  # 1.5 hours
        distance_m=45000.0,  # 45km
        avg_hr=155,
        max_hr=185,
        avg_power_w=220.0,
        max_power_w=350.0,
        elevation_gain_m=600.0,
        calories=800,
    )

    db_session.add(activity)
    db_session.flush()  # Get activity ID

    # Create samples (simulate GPS tracking every 30 seconds)
    samples = []
    route_points = []

    base_lat = 52.5200  # Berlin coordinates
    base_lon = 13.4050
    base_alt = 100.0

    for i in range(180):  # 180 samples = 90 minutes of data
        elapsed_s = i * 30

        # Simulate realistic GPS drift
        lat = base_lat + (i * 0.0001) + (0.00005 * (i % 7))  # Some variation
        lon = base_lon + (i * 0.0002) + (0.00003 * (i % 5))
        alt = base_alt + (i * 0.5) - (0.3 * (i % 11))  # Elevation changes

        # Simulate realistic sensor data
        hr = 140 + (15 * (i / 180)) + (10 * ((i % 20) / 20))  # Gradual increase with variation
        power = 200 + (50 * ((i % 30) / 30)) - (25 * ((i % 15) / 15))  # Power variation
        speed = 12.0 + (2.0 * ((i % 40) / 40)) - (1.0 * ((i % 25) / 25))  # Speed variation

        sample = Sample(
            activity_id=activity.id,
            timestamp=activity.start_time_utc + timedelta(seconds=elapsed_s),
            elapsed_time_s=elapsed_s,
            latitude=lat,
            longitude=lon,
            altitude_m=alt,
            heart_rate=int(hr),
            power_w=power,
            cadence_rpm=85 + (i % 10),
            speed_mps=speed,
            temperature_c=15.0 + (i * 0.01),  # Gradual temperature change
        )

        samples.append(sample)
        db_session.add(sample)

        # Create route points (simplified)
        if i % 5 == 0:  # Every 5th sample becomes a route point
            route_point = RoutePoint(
                activity_id=activity.id, sequence=len(route_points), latitude=lat, longitude=lon, altitude_m=alt
            )
            route_points.append(route_point)
            db_session.add(route_point)

    # Create some laps
    lap_1 = Lap(
        activity_id=activity.id,
        lap_index=0,
        start_time_utc=activity.start_time_utc,
        elapsed_time_s=2700,  # 45 minutes
        distance_m=22500.0,  # 22.5km
        avg_hr=145,
        max_hr=165,
        avg_power_w=210.0,
        max_power_w=280.0,
    )

    lap_2 = Lap(
        activity_id=activity.id,
        lap_index=1,
        start_time_utc=activity.start_time_utc + timedelta(seconds=2700),
        elapsed_time_s=2700,  # Another 45 minutes
        distance_m=22500.0,  # 22.5km
        avg_hr=165,
        max_hr=185,
        avg_power_w=230.0,
        max_power_w=350.0,
    )

    db_session.add(lap_1)
    db_session.add(lap_2)

    db_session.commit()

    return {"activity": activity, "samples": samples, "route_points": route_points, "laps": [lap_1, lap_2]}


@pytest.fixture
def mock_file_parsers():
    """Mock file parsing libraries for testing without external dependencies."""
    with patch("ingest.parser.FITPARSE_AVAILABLE", True), patch("ingest.parser.TCXPARSER_AVAILABLE", True), patch(
        "ingest.parser.GPXPY_AVAILABLE", True
    ):
        yield


@pytest.fixture
def sample_fit_file():
    """Create temporary FIT file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
        # Write some dummy binary data
        tmp_file.write(b"\x0e\x10\x43\x08\x28\x00\x00\x00.FIT")  # FIT file header
        tmp_file_path = Path(tmp_file.name)

    yield tmp_file_path

    # Cleanup
    tmp_file_path.unlink()


@pytest.fixture
def sample_tcx_file():
    """Create temporary TCX file for testing."""
    tcx_content = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
    <Activities>
        <Activity Sport="Running">
            <Id>2024-01-15T10:00:00Z</Id>
            <TotalTimeSeconds>3600</TotalTimeSeconds>
            <DistanceMeters>10000</DistanceMeters>
            <Calories>500</Calories>
        </Activity>
    </Activities>
</TrainingCenterDatabase>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".tcx", delete=False, encoding="utf-8") as tmp_file:
        tmp_file.write(tcx_content)
        tmp_file_path = Path(tmp_file.name)

    yield tmp_file_path

    # Cleanup
    tmp_file_path.unlink()


@pytest.fixture
def sample_gpx_file():
    """Create temporary GPX file for testing."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
    <trk>
        <name>Test Track</name>
        <trkseg>
            <trkpt lat="52.5200" lon="13.4050">
                <ele>100</ele>
                <time>2024-01-15T10:00:00Z</time>
            </trkpt>
            <trkpt lat="52.5210" lon="13.4060">
                <ele>105</ele>
                <time>2024-01-15T10:01:00Z</time>
            </trkpt>
        </trkseg>
    </trk>
</gpx>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False, encoding="utf-8") as tmp_file:
        tmp_file.write(gpx_content)
        tmp_file_path = Path(tmp_file.name)

    yield tmp_file_path

    # Cleanup
    tmp_file_path.unlink()


@pytest.fixture(autouse=True)
def reset_global_database():
    """Reset global database state between tests."""
    # Import here to avoid circular imports

    # Reset global database config to avoid test interference
    import app.data.db

    original_config = app.data.db._db_config

    yield

    # Restore original config
    app.data.db._db_config = original_config


# Custom pytest markers for test categorization
pytest_markers = [
    "unit: marks tests as unit tests (deselect with '-m \"not unit\"')",
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "parser: marks tests related to file parsing",
    "database: marks tests related to database operations",
    "web: marks tests related to web query functions",
    "models: marks tests related to SQLAlchemy models",
    "pages: marks tests related to Dash page components",
    "fit: marks tests related to FIT file processing",
]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location."""
    for item in items:
        # Mark based on test file names
        if "test_parser" in item.nodeid:
            item.add_marker(pytest.mark.parser)
            item.add_marker(pytest.mark.unit)
        elif "test_models" in item.nodeid:
            item.add_marker(pytest.mark.models)
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.unit)
        elif "test_web_queries" in item.nodeid:
            item.add_marker(pytest.mark.web)
            item.add_marker(pytest.mark.database)
            item.add_marker(pytest.mark.integration)
        elif "test_pages" in item.nodeid:
            item.add_marker(pytest.mark.pages)
            item.add_marker(pytest.mark.unit)
        elif "test_fit_integration" in item.nodeid:
            item.add_marker(pytest.mark.fit)
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "test_utils" in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Mark tests with fixtures as potentially slow
        if hasattr(item, "fixturenames") and "activity_with_samples" in item.fixturenames:
            item.add_marker(pytest.mark.slow)
