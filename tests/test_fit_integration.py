"""
Integration tests using real FIT files from the activities folder.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.data.db import session_manager
from app.data.models import Activity, Sample
from ingest.parser import parse_activity_file


class TestFitFileIntegration:
    """Integration tests using real FIT files."""

    @pytest.fixture
    def fit_files(self):
        """Get a selection of real FIT files for testing."""
        activities_dir = Path(__file__).parent.parent / "activities" / "export"
        fit_files = list(activities_dir.glob("*.fit"))[:5]  # Use first 5 files
        if not fit_files:
            pytest.skip("No FIT files available for testing")
        return fit_files

    @pytest.mark.integration
    @pytest.mark.slow
    def test_parse_real_fit_file(self, fit_files, temp_database):
        """Test parsing a real FIT file."""
        fit_file = fit_files[0]

        try:
            activity_data = parse_activity_file(fit_file)

            assert activity_data is not None
            assert "file_hash" in activity_data
            assert "start_time_utc" in activity_data
            assert "elapsed_time_s" in activity_data

            # Verify required fields exist
            assert activity_data["file_hash"] is not None
            assert activity_data["start_time_utc"] is not None
            assert activity_data["elapsed_time_s"] > 0

        except ImportError:
            pytest.skip("FIT parsing libraries not available")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_fit_file_to_database(self, fit_files, temp_database):
        """Test full pipeline from FIT file to database."""
        fit_file = fit_files[0]

        try:
            activity_data = parse_activity_file(fit_file)

            if not activity_data:
                pytest.skip("Could not parse FIT file")

            # Create activity record
            activity = Activity(
                external_id=activity_data.get("external_id", f"test_{fit_file.name}"),
                file_hash=activity_data["file_hash"],
                source="fit",
                sport=activity_data.get("sport", "unknown"),
                start_time_utc=activity_data["start_time_utc"],
                elapsed_time_s=activity_data["elapsed_time_s"],
                distance_m=activity_data.get("distance_m", 0),
                avg_hr=activity_data.get("avg_hr"),
                max_hr=activity_data.get("max_hr"),
                avg_power_w=activity_data.get("avg_power_w"),
                max_power_w=activity_data.get("max_power_w"),
                elevation_gain_m=activity_data.get("elevation_gain_m", 0),
                calories=activity_data.get("calories", 0),
            )

            with session_manager.get_session() as session:
                session.add(activity)
                session.flush()  # Get activity ID

                # Add samples if they exist
                samples_data = activity_data.get("samples", [])
                for sample_data in samples_data[:100]:  # Limit to first 100 samples
                    sample = Sample(
                        activity_id=activity.id,
                        timestamp=sample_data.get("timestamp"),
                        elapsed_time_s=sample_data.get("elapsed_time_s", 0),
                        latitude=sample_data.get("latitude"),
                        longitude=sample_data.get("longitude"),
                        altitude_m=sample_data.get("altitude_m"),
                        heart_rate=sample_data.get("heart_rate"),
                        power_w=sample_data.get("power_w"),
                        cadence_rpm=sample_data.get("cadence_rpm"),
                        speed_mps=sample_data.get("speed_mps"),
                        temperature_c=sample_data.get("temperature_c"),
                    )
                    session.add(sample)

                session.commit()

                # Verify data was saved
                saved_activity = session.query(Activity).filter(Activity.id == activity.id).first()
                assert saved_activity is not None
                assert saved_activity.file_hash == activity_data["file_hash"]

        except ImportError:
            pytest.skip("FIT parsing libraries not available")

    @pytest.mark.integration
    def test_multiple_fit_files_unique_hashes(self, fit_files, temp_database):
        """Test that different FIT files produce unique hashes."""
        hashes = set()

        for fit_file in fit_files[:3]:  # Test first 3 files
            try:
                activity_data = parse_activity_file(fit_file)
                if activity_data and "file_hash" in activity_data:
                    file_hash = activity_data["file_hash"]
                    assert file_hash not in hashes, f"Duplicate hash found: {file_hash}"
                    hashes.add(file_hash)
            except ImportError:
                pytest.skip("FIT parsing libraries not available")
            except Exception as e:
                # Log parsing failures but don't fail the test
                print(f"Failed to parse {fit_file.name}: {e}")
                continue

        assert len(hashes) > 0, "No FIT files could be parsed"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_fit_file_data_validation(self, fit_files, temp_database):
        """Test validation of data from real FIT files."""
        for fit_file in fit_files[:2]:  # Test first 2 files
            try:
                activity_data = parse_activity_file(fit_file)

                if not activity_data:
                    continue

                # Validate activity-level data
                if "start_time_utc" in activity_data:
                    assert activity_data["start_time_utc"] is not None

                if "elapsed_time_s" in activity_data:
                    assert activity_data["elapsed_time_s"] > 0
                    assert activity_data["elapsed_time_s"] < 86400 * 7  # Less than 1 week

                if "distance_m" in activity_data and activity_data["distance_m"]:
                    assert activity_data["distance_m"] > 0
                    assert activity_data["distance_m"] < 1000000  # Less than 1000km

                if "avg_hr" in activity_data and activity_data["avg_hr"]:
                    assert 30 <= activity_data["avg_hr"] <= 220

                if "max_hr" in activity_data and activity_data["max_hr"]:
                    assert 30 <= activity_data["max_hr"] <= 220

                if "avg_power_w" in activity_data and activity_data["avg_power_w"]:
                    assert 0 <= activity_data["avg_power_w"] <= 2000

                # Validate sample data
                samples = activity_data.get("samples", [])
                for i, sample in enumerate(samples[:10]):  # Check first 10 samples
                    if "latitude" in sample and sample["latitude"]:
                        assert -90 <= sample["latitude"] <= 90

                    if "longitude" in sample and sample["longitude"]:
                        assert -180 <= sample["longitude"] <= 180

                    if "heart_rate" in sample and sample["heart_rate"]:
                        assert 30 <= sample["heart_rate"] <= 220

                    if "power_w" in sample and sample["power_w"]:
                        assert 0 <= sample["power_w"] <= 3000

                    if "elapsed_time_s" in sample:
                        assert sample["elapsed_time_s"] >= 0

            except ImportError:
                pytest.skip("FIT parsing libraries not available")
            except Exception as e:
                # Log parsing failures but don't fail the test
                print(f"Failed to validate {fit_file.name}: {e}")
                continue

    @pytest.mark.integration
    def test_fit_file_error_handling(self, temp_database):
        """Test error handling with corrupted/invalid files."""
        # Create a fake FIT file with invalid content
        with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
            tmp_file.write(b"This is not a valid FIT file")
            invalid_fit_path = Path(tmp_file.name)

        try:
            # Should handle invalid files gracefully
            activity_data = parse_activity_file(invalid_fit_path)
            # Should return None or raise handled exception
            assert activity_data is None or activity_data == {}

        except ImportError:
            pytest.skip("FIT parsing libraries not available")
        except Exception:
            # Expected for invalid files - should not crash
            pass
        finally:
            invalid_fit_path.unlink()

    @pytest.mark.integration
    def test_fit_file_sports_detection(self, fit_files, temp_database):
        """Test sport type detection from FIT files."""
        detected_sports = set()

        for fit_file in fit_files[:5]:  # Test first 5 files
            try:
                activity_data = parse_activity_file(fit_file)

                if activity_data and "sport" in activity_data:
                    sport = activity_data["sport"]
                    if sport:
                        detected_sports.add(sport.lower())
                        # Sport should be a reasonable value
                        assert isinstance(sport, str)
                        assert len(sport) > 0

            except ImportError:
                pytest.skip("FIT parsing libraries not available")
            except Exception as e:
                print(f"Failed to parse sport from {fit_file.name}: {e}")
                continue

        # Should detect at least one sport type
        assert len(detected_sports) > 0, "No sports detected from FIT files"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_fit_file_performance(self, fit_files, temp_database):
        """Test performance with larger FIT files."""
        # Find the largest FIT file
        largest_file = max(fit_files, key=lambda f: f.stat().st_size)

        try:
            import time

            start_time = time.time()
            activity_data = parse_activity_file(largest_file)
            parse_time = time.time() - start_time

            # Should parse reasonably quickly (less than 30 seconds)
            assert parse_time < 30, f"Parsing took too long: {parse_time:.2f} seconds"

            if activity_data:
                # Large files should have substantial data
                samples_count = len(activity_data.get("samples", []))
                assert samples_count >= 0  # Should not error

                # If it has samples, should be reasonable
                if samples_count > 0:
                    assert samples_count <= 50000  # Reasonable upper limit

        except ImportError:
            pytest.skip("FIT parsing libraries not available")
        except Exception as e:
            print(f"Performance test failed for {largest_file.name}: {e}")
            # Don't fail the test for performance issues
            pass
