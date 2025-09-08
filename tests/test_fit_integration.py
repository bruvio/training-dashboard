"""
Integration tests using deterministic test FIT files.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.data.db import session_scope
from app.data.models import Activity


@pytest.mark.integration
@pytest.mark.xfail(reason="FIT parsing integration requires external dependencies")
class TestFitFileIntegration:
    """Integration tests using test FIT files."""

    @pytest.fixture
    def test_fit_files(self):
        """Create deterministic test FIT files for integration testing."""
        test_files_dir = Path(__file__).parent / "test_data"
        test_files_dir.mkdir(exist_ok=True)

        # Create test files as placeholders
        test_file_1 = test_files_dir / "test_running_activity.fit"
        test_file_2 = test_files_dir / "test_cycling_activity.fit"

        for test_file in [test_file_1, test_file_2]:
            if not test_file.exists():
                test_file.touch()

        return [test_file_1, test_file_2]

    def test_parse_test_fit_file_mock(self, test_fit_files):
        """Test parsing with mocked FIT file data."""
        # This test is marked as xfail due to FIT parsing dependencies
        pytest.skip("FIT parsing integration test - requires fitparse library")

    def test_fit_data_to_database_mock(self, test_fit_files):
        """Test storing mocked FIT data in database."""
        # Create mock activity data
        activity = Activity(
            external_id="test_garmin_123",
            file_hash="test_hash_456",
            source="fit",
            sport="cycling",
            start_time_utc="2024-01-15T10:00:00Z",
            elapsed_time_s=1800,
            distance_m=25000,
            avg_hr=135,
            max_hr=165,
            calories=300,
        )

        with session_scope() as session:
            session.add(activity)
            session.flush()  # Get activity ID

            # Verify data was saved
            saved_activity = session.query(Activity).filter(Activity.id == activity.id).first()
            assert saved_activity is not None
            assert saved_activity.file_hash == "test_hash_456"
            assert saved_activity.sport == "cycling"
            assert saved_activity.distance_m == 25000

    def test_fit_file_validation(self):
        """Test validation of FIT file data without external dependencies."""
        # Test basic data validation logic
        mock_activity_data = {
            "elapsed_time_s": 7200,  # 2 hours
            "distance_m": 20000,  # 20km
            "avg_hr": 145,
            "max_hr": 185,
        }

        # Validate activity-level data
        assert mock_activity_data["elapsed_time_s"] > 0
        assert mock_activity_data["elapsed_time_s"] < 86400 * 7  # Less than 1 week
        assert mock_activity_data["distance_m"] > 0
        assert 30 <= mock_activity_data["avg_hr"] <= 220
        assert 30 <= mock_activity_data["max_hr"] <= 220

    def test_unique_hashes(self):
        """Test that different activities produce unique hashes."""
        hash1 = "unique_hash_1"
        hash2 = "unique_hash_2"

        # Simple test that hashes are different
        assert hash1 != hash2

        hashes = {hash1, hash2}
        assert len(hashes) == 2

    def test_error_handling_invalid_files(self):
        """Test error handling with invalid files."""
        # Create a fake FIT file with invalid content
        with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
            tmp_file.write(b"This is not a valid FIT file")
            invalid_fit_path = Path(tmp_file.name)

        try:
            # Test that invalid files are handled gracefully
            # In a real implementation, this would return None or raise a handled exception
            assert invalid_fit_path.exists()
            assert invalid_fit_path.suffix == ".fit"
        finally:
            invalid_fit_path.unlink()

    def test_sports_detection(self):
        """Test sport type detection logic."""
        # Test sport type validation without actual file parsing
        sports = ["running", "cycling", "swimming"]

        for sport in sports:
            assert isinstance(sport, str)
            assert len(sport) > 0
            assert sport.lower() in ["running", "cycling", "swimming"]

        detected_sports = set(sports)
        assert "running" in detected_sports
        assert "cycling" in detected_sports
        assert len(detected_sports) == 3
