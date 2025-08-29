"""
Unit tests for activity file parsers.

Tests FIT, TCX, and GPX parsing with error handling and data validation
following the research-validated patterns from the enhanced PRP.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import hashlib

from ingest.parser import (
    ActivityParser, ParserError, FileNotSupportedError, 
    CorruptFileError, calculate_file_hash
)
from app.data.models import ActivityData, SampleData


class TestActivityParser:
    """Test the unified ActivityParser class."""
    
    def test_calculate_file_hash(self):
        """Test file hash calculation for deduplication."""
        # Create a temporary file with known content
        test_content = b"test file content"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = Path(tmp_file.name)
        
        try:
            calculated_hash = ActivityParser.calculate_file_hash(tmp_file_path)
            assert calculated_hash == expected_hash
        finally:
            tmp_file_path.unlink()  # Clean up
    
    def test_calculate_file_hash_nonexistent_file(self):
        """Test file hash calculation with non-existent file."""
        nonexistent_path = Path("/nonexistent/file.fit")
        
        with pytest.raises(CorruptFileError, match="Cannot read file"):
            ActivityParser.calculate_file_hash(nonexistent_path)
    
    def test_parse_activity_file_unsupported_format(self):
        """Test parsing with unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(FileNotSupportedError, match="Unsupported file format"):
                ActivityParser.parse_activity_file(tmp_file_path)
        finally:
            tmp_file_path.unlink()
    
    def test_parse_activity_file_nonexistent(self):
        """Test parsing non-existent file."""
        nonexistent_path = Path("/nonexistent/activity.fit")
        
        with pytest.raises(CorruptFileError, match="File does not exist"):
            ActivityParser.parse_activity_file(nonexistent_path)
    
    @patch('ingest.parser.FITPARSE_AVAILABLE', False)
    def test_parse_fit_file_library_unavailable(self):
        """Test FIT parsing when fitparse library is unavailable."""
        with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(FileNotSupportedError, match="fitparse library not available"):
                ActivityParser.parse_fit_file(tmp_file_path)
        finally:
            tmp_file_path.unlink()
    
    @patch('ingest.parser.TCXPARSER_AVAILABLE', False)
    def test_parse_tcx_file_library_unavailable(self):
        """Test TCX parsing when tcxparser library is unavailable."""
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(FileNotSupportedError, match="tcxparser library not available"):
                ActivityParser.parse_tcx_file(tmp_file_path)
        finally:
            tmp_file_path.unlink()
    
    @patch('ingest.parser.GPXPY_AVAILABLE', False)
    def test_parse_gpx_file_library_unavailable(self):
        """Test GPX parsing when gpxpy library is unavailable."""
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(FileNotSupportedError, match="gpxpy library not available"):
                ActivityParser.parse_gpx_file(tmp_file_path)
        finally:
            tmp_file_path.unlink()
    
    @patch('ingest.parser.fitparse')
    @patch('ingest.parser.FITPARSE_AVAILABLE', True)
    def test_parse_fit_file_success(self, mock_fitparse):
        """Test successful FIT file parsing."""
        # Mock FIT file and messages
        mock_fitfile = MagicMock()
        mock_fitparse.FitFile.return_value = mock_fitfile
        
        # Mock session message
        mock_session = MagicMock()
        mock_session.get_value.side_effect = lambda key: {
            'sport': 'running',
            'start_time': datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            'total_elapsed_time': 3600,
            'total_distance': 10000.0,
            'avg_heart_rate': 150,
            'max_heart_rate': 180,
            'avg_power': 250.0,
            'max_power': 300.0,
            'total_ascent': 100.0,
            'total_descent': 80.0,
            'total_calories': 500
        }.get(key)
        
        # Mock file_id message
        mock_file_id = MagicMock()
        mock_file_id.get_value.return_value = 12345
        
        # Mock record messages (samples)
        mock_record = MagicMock()
        mock_record.get_value.side_effect = lambda key: {
            'timestamp': datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc),
            'position_lat': int(52.5200 * (2**31) / 180),  # Semicircles
            'position_long': int(13.4050 * (2**31) / 180),  # Semicircles
            'altitude': 100.0,
            'heart_rate': 145,
            'power': 240.0,
            'cadence': 90,
            'speed': 4.5,
            'temperature': 15.0
        }.get(key)
        
        # Configure mock to return messages
        mock_fitfile.get_messages.side_effect = lambda msg_type: {
            'session': [mock_session],
            'file_id': [mock_file_id],
            'record': [mock_record] * 5,  # 5 sample records
            'lap': []
        }.get(msg_type, [])
        
        # Create temporary FIT file
        with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            result = ActivityParser.parse_fit_file(tmp_file_path)
            
            assert result is not None
            assert isinstance(result, ActivityData)
            assert result.sport == 'running'
            assert result.distance_m == 10000.0
            assert result.avg_hr == 150
            assert result.max_hr == 180
            assert result.avg_power_w == 250.0
            assert result.elevation_gain_m == 100.0
            assert result.calories == 500
            assert len(result.samples) == 5
            assert len(result.route_points) == 5  # All samples have GPS
            
            # Check sample data
            sample = result.samples[0]
            assert isinstance(sample, SampleData)
            assert sample.heart_rate == 145
            assert sample.power_w == 240.0
            assert abs(sample.latitude - 52.5200) < 0.001  # Converted from semicircles
            assert abs(sample.longitude - 13.4050) < 0.001
            
        finally:
            tmp_file_path.unlink()
    
    @patch('ingest.parser.tcxparser')
    @patch('ingest.parser.TCXPARSER_AVAILABLE', True)
    def test_parse_tcx_file_success(self, mock_tcxparser):
        """Test successful TCX file parsing."""
        # Mock TCX parser
        mock_tcx = MagicMock()
        mock_tcx.activity_type = 'cycling'
        mock_tcx.started_at = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        mock_tcx.duration = 3600.0
        mock_tcx.distance = 50000.0
        mock_tcx.hr_avg = 155.0
        mock_tcx.hr_max = 185.0
        mock_tcx.calories = 600.0
        
        # Mock trackpoints
        mock_trackpoint = MagicMock()
        mock_trackpoint.time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        mock_trackpoint.latitude = 52.5200
        mock_trackpoint.longitude = 13.4050
        mock_trackpoint.elevation = 105.0
        mock_trackpoint.hr_value = 150.0
        mock_trackpoint.speed = 12.5
        
        mock_tcx.trackpoints = [mock_trackpoint] * 3
        mock_tcxparser.TCXParser.return_value = mock_tcx
        
        # Create temporary TCX file
        with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            result = ActivityParser.parse_tcx_file(tmp_file_path)
            
            assert result is not None
            assert result.sport == 'cycling'
            assert result.elapsed_time_s == 3600
            assert result.distance_m == 50000.0
            assert result.avg_hr == 155
            assert result.calories == 600
            assert len(result.samples) == 3
            assert len(result.route_points) == 3
            
            # Check sample data
            sample = result.samples[0]
            assert sample.latitude == 52.5200
            assert sample.longitude == 13.4050
            assert sample.altitude_m == 105.0
            assert sample.heart_rate == 150.0
            assert sample.speed_mps == 12.5
            
        finally:
            tmp_file_path.unlink()
    
    @patch('ingest.parser.gpxpy')
    @patch('ingest.parser.GPXPY_AVAILABLE', True)
    def test_parse_gpx_file_success(self, mock_gpxpy):
        """Test successful GPX file parsing."""
        # Mock GPX structure
        mock_point = MagicMock()
        mock_point.latitude = 52.5200
        mock_point.longitude = 13.4050
        mock_point.elevation = 110.0
        mock_point.time = datetime(2024, 1, 15, 10, 5, 0, tzinfo=timezone.utc)
        
        mock_segment = MagicMock()
        mock_segment.points = [mock_point] * 4
        
        mock_track = MagicMock()
        mock_track.segments = [mock_segment]
        mock_track.length_2d.return_value = 8000.0  # 8km distance
        
        mock_gpx = MagicMock()
        mock_gpx.tracks = [mock_track]
        
        mock_gpxpy.parse.return_value = mock_gpx
        
        # Mock file open
        mock_file_content = "<gpx>mock content</gpx>"
        
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with patch('builtins.open', mock_open(read_data=mock_file_content)):
                result = ActivityParser.parse_gpx_file(tmp_file_path)
            
            assert result is not None
            assert result.distance_m == 8000.0
            assert len(result.samples) == 4
            assert len(result.route_points) == 4
            
            # Check GPS coordinates
            sample = result.samples[0]
            assert sample.latitude == 52.5200
            assert sample.longitude == 13.4050
            assert sample.altitude_m == 110.0
            
            # Check route points
            route_point = result.route_points[0]
            assert route_point == (52.5200, 13.4050, 110.0)
            
        finally:
            tmp_file_path.unlink()
    
    def test_derive_metrics_speed_calculation(self):
        """Test metric derivation calculations."""
        activity_data = ActivityData(
            distance_m=10000.0,
            elapsed_time_s=3600,  # 1 hour
            avg_speed_mps=None,
            avg_pace_s_per_km=None
        )
        
        ActivityParser._derive_metrics(activity_data)
        
        # Should calculate speed: 10000m / 3600s = 2.78 m/s
        assert abs(activity_data.avg_speed_mps - (10000.0 / 3600.0)) < 0.01
        
        # Should calculate pace: 1000 / speed = 1000 / 2.78 = ~360 seconds per km
        expected_pace = 1000.0 / activity_data.avg_speed_mps
        assert abs(activity_data.avg_pace_s_per_km - expected_pace) < 1.0
    
    def test_derive_metrics_with_existing_values(self):
        """Test that existing values are not overwritten."""
        activity_data = ActivityData(
            distance_m=10000.0,
            elapsed_time_s=3600,
            avg_speed_mps=5.0,  # Already set
            avg_pace_s_per_km=200.0,  # Already set
            moving_time_s=3500  # Already set
        )
        
        ActivityParser._derive_metrics(activity_data)
        
        # Should not overwrite existing values
        assert activity_data.avg_speed_mps == 5.0
        assert activity_data.avg_pace_s_per_km == 200.0
        assert activity_data.moving_time_s == 3500
    
    def test_derive_metrics_edge_cases(self):
        """Test metric derivation with edge cases."""
        # Test with zero elapsed time
        activity_data = ActivityData(
            distance_m=10000.0,
            elapsed_time_s=0
        )
        
        ActivityParser._derive_metrics(activity_data)
        
        # Should not crash or set invalid values
        assert activity_data.avg_speed_mps is None
        assert activity_data.avg_pace_s_per_km is None
        
        # Test with zero speed
        activity_data2 = ActivityData(avg_speed_mps=0.0)
        ActivityParser._derive_metrics(activity_data2)
        
        # Should not calculate pace from zero speed
        assert activity_data2.avg_pace_s_per_km is None
    
    @patch('ingest.parser.fitparse')
    @patch('ingest.parser.FITPARSE_AVAILABLE', True)
    def test_parse_fit_file_with_corrupted_data(self, mock_fitparse):
        """Test FIT file parsing with corrupted/invalid data."""
        # Mock FIT file that raises an exception
        mock_fitparse.FitFile.side_effect = Exception("Corrupted FIT file")
        
        with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
            tmp_file_path = Path(tmp_file.name)
        
        try:
            with pytest.raises(CorruptFileError, match="FIT parse error"):
                ActivityParser.parse_fit_file(tmp_file_path)
        finally:
            tmp_file_path.unlink()
    
    def test_convenience_function(self):
        """Test the convenience calculate_file_hash function."""
        test_content = b"convenience test"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_content)
            tmp_file_path = Path(tmp_file.name)
        
        try:
            from ingest.parser import calculate_file_hash
            result = calculate_file_hash(tmp_file_path)
            expected = hashlib.sha256(test_content).hexdigest()
            assert result == expected
        finally:
            tmp_file_path.unlink()


class TestParserIntegration:
    """Integration tests for parser with different file types."""
    
    def test_parse_activity_file_routing(self):
        """Test that parse_activity_file routes to correct parser."""
        with patch.object(ActivityParser, 'parse_fit_file') as mock_fit, \
             patch.object(ActivityParser, 'parse_tcx_file') as mock_tcx, \
             patch.object(ActivityParser, 'parse_gpx_file') as mock_gpx:
            
            mock_fit.return_value = ActivityData()
            mock_tcx.return_value = ActivityData()
            mock_gpx.return_value = ActivityData()
            
            # Test FIT file routing
            with tempfile.NamedTemporaryFile(suffix=".fit", delete=False) as tmp_file:
                tmp_file_path = Path(tmp_file.name)
            
            try:
                ActivityParser.parse_activity_file(tmp_file_path)
                mock_fit.assert_called_once_with(tmp_file_path)
                mock_tcx.assert_not_called()
                mock_gpx.assert_not_called()
            finally:
                tmp_file_path.unlink()
            
            # Reset mocks
            mock_fit.reset_mock()
            mock_tcx.reset_mock()
            mock_gpx.reset_mock()
            
            # Test TCX file routing
            with tempfile.NamedTemporaryFile(suffix=".tcx", delete=False) as tmp_file:
                tmp_file_path = Path(tmp_file.name)
            
            try:
                ActivityParser.parse_activity_file(tmp_file_path)
                mock_tcx.assert_called_once_with(tmp_file_path)
                mock_fit.assert_not_called()
                mock_gpx.assert_not_called()
            finally:
                tmp_file_path.unlink()


# Validation Gate: Run this test with `pytest tests/test_parser.py -v`
if __name__ == "__main__":
    pytest.main([__file__, "-v"])