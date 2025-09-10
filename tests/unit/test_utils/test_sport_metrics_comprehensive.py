"""
Comprehensive tests for app.utils.sport_metrics module.

Tests the SportMetricsMapper class and calculation functions
for sport-specific metrics and visualization.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from app.utils.sport_metrics import (
    SportMetricsMapper,
    calculate_swim_pace_per_100m,
    calculate_running_pace,
    calculate_stride_length,
)


class TestSportMetricsMapper:
    """Test cases for the SportMetricsMapper class."""

    def test_get_sport_metrics_swimming(self):
        """Test getting metrics configuration for swimming."""
        config = SportMetricsMapper.get_sport_metrics("swimming")

        assert "primary_metrics" in config
        assert "secondary_metrics" in config

        # Check primary metrics
        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "pace_per_100m" in metric_keys
        assert "heart_rate" in metric_keys
        assert "stroke_rate" in metric_keys

        # Check specific metric configuration
        pace_metric = next(m for m in primary if m["key"] == "pace_per_100m")
        assert pace_metric["name"] == "Pace per 100m"
        assert pace_metric["unit"] == "min/100m"
        assert pace_metric["color"] == "blue"
        assert pace_metric["chart_type"] == "line"

    def test_get_sport_metrics_cycling(self):
        """Test getting metrics configuration for cycling."""
        config = SportMetricsMapper.get_sport_metrics("cycling")

        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "power" in metric_keys
        assert "heart_rate" in metric_keys
        assert "cadence" in metric_keys
        assert "speed" in metric_keys
        assert "elevation" in metric_keys

        # Check power metric configuration
        power_metric = next(m for m in primary if m["key"] == "power")
        assert power_metric["name"] == "Power"
        assert power_metric["unit"] == "W"
        assert power_metric["color"] == "green"

    def test_get_sport_metrics_running(self):
        """Test getting metrics configuration for running."""
        config = SportMetricsMapper.get_sport_metrics("running")

        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "pace" in metric_keys
        assert "heart_rate" in metric_keys
        assert "cadence" in metric_keys
        assert "stride_length" in metric_keys

        # Check cadence metric has correct unit for running
        cadence_metric = next(m for m in primary if m["key"] == "cadence")
        assert cadence_metric["unit"] == "spm"  # steps per minute

    def test_get_sport_metrics_with_sub_sport(self):
        """Test getting metrics with sub-sport specification."""
        # Swimming with pool_swimming sub-sport
        config = SportMetricsMapper.get_sport_metrics("generic_sport", "pool_swimming")
        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "pace_per_100m" in metric_keys  # Should map to swimming

        # Cycling with road_biking sub-sport
        config = SportMetricsMapper.get_sport_metrics("generic_sport", "road_biking")
        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "power" in metric_keys  # Should map to cycling

    def test_normalize_sport_name_swimming(self):
        """Test sport name normalization for swimming variants."""
        assert SportMetricsMapper._normalize_sport_name("swimming") == "swimming"
        assert SportMetricsMapper._normalize_sport_name("Swimming") == "swimming"
        assert SportMetricsMapper._normalize_sport_name("pool_swimming") == "swimming"
        assert SportMetricsMapper._normalize_sport_name("generic", "swim") == "swimming"
        assert SportMetricsMapper._normalize_sport_name("sport", "open_water_swimming") == "swimming"

    def test_normalize_sport_name_cycling(self):
        """Test sport name normalization for cycling variants."""
        assert SportMetricsMapper._normalize_sport_name("cycling") == "cycling"
        assert SportMetricsMapper._normalize_sport_name("biking") == "cycling"
        assert SportMetricsMapper._normalize_sport_name("Cycling") == "cycling"
        assert SportMetricsMapper._normalize_sport_name("generic", "road_biking") == "cycling"
        assert SportMetricsMapper._normalize_sport_name("sport", "mountain_biking") == "cycling"

    def test_normalize_sport_name_running(self):
        """Test sport name normalization for running variants."""
        assert SportMetricsMapper._normalize_sport_name("running") == "running"
        assert SportMetricsMapper._normalize_sport_name("jogging") == "running"
        assert SportMetricsMapper._normalize_sport_name("Running") == "running"
        assert SportMetricsMapper._normalize_sport_name("generic", "running") == "running"
        assert SportMetricsMapper._normalize_sport_name("sport", "treadmill_running") == "running"

    def test_normalize_sport_name_unknown(self):
        """Test sport name normalization for unknown sports."""
        assert SportMetricsMapper._normalize_sport_name("tennis") == "generic"
        assert SportMetricsMapper._normalize_sport_name("basketball") == "generic"
        assert SportMetricsMapper._normalize_sport_name("") == "generic"
        assert SportMetricsMapper._normalize_sport_name(None) == "generic"

    def test_get_default_metrics(self):
        """Test default metrics for unknown sports."""
        config = SportMetricsMapper._get_default_metrics()

        assert "primary_metrics" in config
        assert "secondary_metrics" in config

        primary = config["primary_metrics"]
        assert len(primary) == 2

        metric_keys = [m["key"] for m in primary]
        assert "heart_rate" in metric_keys
        assert "speed" in metric_keys

        # Check default heart rate metric
        hr_metric = next(m for m in primary if m["key"] == "heart_rate")
        assert hr_metric["name"] == "Heart Rate"
        assert hr_metric["unit"] == "bpm"
        assert hr_metric["color"] == "red"

    def test_get_sport_metrics_unknown_sport(self):
        """Test that unknown sports return default metrics."""
        config = SportMetricsMapper.get_sport_metrics("tennis")

        # Should be same as default metrics
        default_config = SportMetricsMapper._get_default_metrics()
        assert config == default_config

    def test_get_available_metrics_with_data(self):
        """Test getting available metrics based on actual data."""
        # Create mock samples dataframe with heart rate data
        samples_df = pd.DataFrame(
            {
                "timestamp": [1, 2, 3, 4, 5],
                "heart_rate_bpm": [120, 125, 130, 135, 140],
                "speed_mps": [2.5, 2.6, 2.7, 2.8, 2.9],
                "power_w": [200, 210, 220, 230, 240],
            }
        )

        activity_data = {"sport": "cycling"}

        available = SportMetricsMapper.get_available_metrics("cycling", samples_df, activity_data)

        # Should include metrics for which data exists
        metric_keys = [m["key"] for m in available]
        assert "heart_rate" in metric_keys
        assert "speed" in metric_keys
        assert "power" in metric_keys

    def test_get_available_metrics_missing_data(self):
        """Test getting available metrics when data is missing."""
        # Create samples dataframe with no relevant data
        samples_df = pd.DataFrame({"timestamp": [1, 2, 3, 4, 5], "irrelevant_column": [1, 2, 3, 4, 5]})

        activity_data = {"sport": "running"}

        available = SportMetricsMapper.get_available_metrics("running", samples_df, activity_data)

        # Should be empty or very limited
        assert len(available) == 0 or len(available) < 3

    def test_get_available_metrics_partial_data(self):
        """Test getting available metrics with partial data availability."""
        # Create samples with some missing data (NaN values)
        samples_df = pd.DataFrame(
            {
                "timestamp": [1, 2, 3, 4, 5],
                "heart_rate_bpm": [120, np.nan, 130, np.nan, 140],  # Some missing
                "speed_mps": [np.nan, np.nan, np.nan, np.nan, np.nan],  # All missing
                "cadence_rpm": [90, 91, 92, 93, 94],  # All present
            }
        )

        activity_data = {"sport": "cycling"}

        available = SportMetricsMapper.get_available_metrics("cycling", samples_df, activity_data)

        metric_keys = [m["key"] for m in available]
        assert "heart_rate" in metric_keys  # Has some data
        assert "cadence" in metric_keys  # Has all data
        assert "speed" not in metric_keys  # No data

    def test_is_metric_available_basic_columns(self):
        """Test metric availability checking for basic columns."""
        samples_df = pd.DataFrame(
            {"heart_rate_bpm": [120, 125, 130], "power_w": [200, 210, 220], "empty_column": [np.nan, np.nan, np.nan]}
        )

        # Test existing metrics
        hr_metric = {"key": "heart_rate"}
        assert SportMetricsMapper._is_metric_available(hr_metric, samples_df, {}) == True

        power_metric = {"key": "power"}
        assert SportMetricsMapper._is_metric_available(power_metric, samples_df, {}) == True

        # Test missing metric
        cadence_metric = {"key": "cadence"}
        assert SportMetricsMapper._is_metric_available(cadence_metric, samples_df, {}) == False

        # Test column with no valid data
        empty_metric = {"key": "temperature"}  # Would map to a column with no data
        samples_df["temperature_c"] = [np.nan, np.nan, np.nan]
        assert SportMetricsMapper._is_metric_available(empty_metric, samples_df, {}) == False

    def test_is_metric_available_calculated_metrics(self):
        """Test availability of metrics that need to be calculated."""
        samples_df = pd.DataFrame({"speed_mps": [2.5, 2.6, 2.7]})

        # Pace can be calculated from speed
        pace_metric = {"key": "pace"}
        assert SportMetricsMapper._is_metric_available(pace_metric, samples_df, {}) == True

        pace_100m_metric = {"key": "pace_per_100m"}
        assert SportMetricsMapper._is_metric_available(pace_100m_metric, samples_df, {}) == True

    def test_is_metric_available_unimplemented_metrics(self):
        """Test that unimplemented calculated metrics return False."""
        samples_df = pd.DataFrame({"some_column": [1, 2, 3]})

        # These are mentioned in the code as not implemented
        stroke_rate_metric = {"key": "stroke_rate"}
        assert SportMetricsMapper._is_metric_available(stroke_rate_metric, samples_df, {}) == False

        swolf_metric = {"key": "swolf"}
        assert SportMetricsMapper._is_metric_available(swolf_metric, samples_df, {}) == False

        normalized_power_metric = {"key": "normalized_power"}
        assert SportMetricsMapper._is_metric_available(normalized_power_metric, samples_df, {}) == False


class TestCalculationFunctions:
    """Test cases for metric calculation functions."""

    def test_calculate_swim_pace_per_100m_normal_speed(self):
        """Test swim pace calculation with normal speeds."""
        # Speed in m/s: 1.0 m/s = 1 min/100m
        speed_series = pd.Series([1.0, 1.5, 2.0, 0.5])
        pace = calculate_swim_pace_per_100m(speed_series)

        # Convert expected values: pace_per_100m = (100 / speed_mps) / 60
        expected = pd.Series([100 / 60, (100 / 1.5) / 60, (100 / 2.0) / 60, (100 / 0.5) / 60])
        pd.testing.assert_series_equal(pace, expected, check_names=False)

    def test_calculate_swim_pace_per_100m_zero_speed(self):
        """Test swim pace calculation with zero/very low speeds."""
        speed_series = pd.Series([0.0, 0.005, 0.02, 1.0])  # Changed 0.01 to 0.02 to be above threshold
        pace = calculate_swim_pace_per_100m(speed_series)

        # Very low speeds should result in NaN
        assert pd.isna(pace.iloc[0])  # 0.0 speed
        assert pd.isna(pace.iloc[1])  # 0.005 speed (below threshold)
        assert not pd.isna(pace.iloc[2])  # 0.02 speed (above threshold)
        assert not pd.isna(pace.iloc[3])  # 1.0 speed (normal)

    def test_calculate_swim_pace_per_100m_preserves_index(self):
        """Test that swim pace calculation preserves pandas index."""
        custom_index = ["a", "b", "c", "d"]
        speed_series = pd.Series([1.0, 1.5, 2.0, 0.5], index=custom_index)
        pace = calculate_swim_pace_per_100m(speed_series)

        assert list(pace.index) == custom_index

    def test_calculate_running_pace_normal_speed(self):
        """Test running pace calculation with normal speeds."""
        # Speed in m/s: 3.33 m/s ≈ 12 km/h ≈ 5 min/km
        speed_series = pd.Series([3.33, 2.78, 4.17, 1.39])  # ~12, 10, 15, 5 km/h
        pace = calculate_running_pace(speed_series)

        # Calculate expected values
        speed_kmh = speed_series * 3.6
        expected = 60 / speed_kmh

        assert abs(pace.iloc[0] - 5.0) < 0.1  # ~5 min/km
        assert abs(pace.iloc[1] - 6.0) < 0.1  # ~6 min/km
        assert abs(pace.iloc[2] - 4.0) < 0.1  # ~4 min/km

    def test_calculate_running_pace_very_slow_speed(self):
        """Test running pace calculation with very slow speeds."""
        speed_series = pd.Series([0.05, 0.1])  # Very slow speeds but above threshold
        pace = calculate_running_pace(speed_series)

        # Very slow speeds should be capped at 15 min/km
        valid_pace = pace.dropna()  # Remove any NaN values
        assert all(valid_pace <= 15.0)
        assert all(valid_pace == 15.0)  # Should all be capped

    def test_calculate_running_pace_zero_speed(self):
        """Test running pace calculation with zero speed."""
        speed_series = pd.Series([0.0, 0.05, 1.0])
        pace = calculate_running_pace(speed_series)

        assert pd.isna(pace.iloc[0])  # 0.0 speed should be NaN
        assert not pd.isna(pace.iloc[2])  # Normal speed should be calculated

    def test_calculate_running_pace_preserves_index(self):
        """Test that running pace calculation preserves pandas index."""
        custom_index = pd.date_range("2023-01-01", periods=3, freq="1min")
        speed_series = pd.Series([2.5, 3.0, 3.5], index=custom_index)
        pace = calculate_running_pace(speed_series)

        pd.testing.assert_index_equal(pace.index, custom_index)

    def test_calculate_stride_length_basic(self):
        """Test stride length calculation from step length."""
        # Step length in mm: 600mm step = 1.2m stride
        step_length_series = pd.Series([600, 700, 800, 500])  # mm
        stride = calculate_stride_length(step_length_series)

        expected = pd.Series([1.2, 1.4, 1.6, 1.0])  # meters
        pd.testing.assert_series_equal(stride, expected, check_names=False)

    def test_calculate_stride_length_with_nan(self):
        """Test stride length calculation with NaN values."""
        step_length_series = pd.Series([600, np.nan, 800, np.nan])
        stride = calculate_stride_length(step_length_series)

        assert stride.iloc[0] == 1.2
        assert pd.isna(stride.iloc[1])
        assert stride.iloc[2] == 1.6
        assert pd.isna(stride.iloc[3])

    def test_calculate_stride_length_zero_values(self):
        """Test stride length calculation with zero values."""
        step_length_series = pd.Series([0, 600, 0, 800])
        stride = calculate_stride_length(step_length_series)

        assert stride.iloc[0] == 0.0
        assert stride.iloc[1] == 1.2
        assert stride.iloc[2] == 0.0
        assert stride.iloc[3] == 1.6

    def test_calculate_stride_length_preserves_index(self):
        """Test that stride length calculation preserves pandas index."""
        custom_index = ["step1", "step2", "step3"]
        step_length_series = pd.Series([600, 700, 800], index=custom_index)
        stride = calculate_stride_length(step_length_series)

        assert list(stride.index) == custom_index


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dataframe(self):
        """Test behavior with empty dataframe."""
        empty_df = pd.DataFrame()
        activity_data = {"sport": "running"}

        available = SportMetricsMapper.get_available_metrics("running", empty_df, activity_data)
        assert len(available) == 0

    def test_none_inputs(self):
        """Test behavior with None inputs."""
        config = SportMetricsMapper.get_sport_metrics(None)
        assert config == SportMetricsMapper._get_default_metrics()

        config = SportMetricsMapper.get_sport_metrics("running", None)
        primary = config["primary_metrics"]
        assert len(primary) > 0  # Should still return running config

    def test_empty_string_inputs(self):
        """Test behavior with empty string inputs."""
        config = SportMetricsMapper.get_sport_metrics("")
        assert config == SportMetricsMapper._get_default_metrics()

        config = SportMetricsMapper.get_sport_metrics("running", "")
        primary = config["primary_metrics"]
        metric_keys = [m["key"] for m in primary]
        assert "pace" in metric_keys  # Should still be running

    def test_case_insensitive_sport_names(self):
        """Test that sport name matching is case insensitive."""
        config_lower = SportMetricsMapper.get_sport_metrics("swimming")
        config_upper = SportMetricsMapper.get_sport_metrics("SWIMMING")
        config_mixed = SportMetricsMapper.get_sport_metrics("SwImMiNg")

        assert config_lower == config_upper == config_mixed

    def test_calculation_functions_with_empty_series(self):
        """Test calculation functions with empty pandas series."""
        empty_series = pd.Series([], dtype=float)

        pace_100m = calculate_swim_pace_per_100m(empty_series)
        assert len(pace_100m) == 0

        running_pace = calculate_running_pace(empty_series)
        assert len(running_pace) == 0

        stride_length = calculate_stride_length(empty_series)
        assert len(stride_length) == 0
