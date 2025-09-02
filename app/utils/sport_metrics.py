"""
Sport-specific metrics configuration for activity visualization.

Maps activities to their relevant metrics and chart types based on available data.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class SportMetricsMapper:
    """Maps sport types to their relevant metrics and visualization preferences."""

    # Define sport-specific metric priorities and chart configurations
    SPORT_METRICS = {
        "swimming": {
            "primary_metrics": [
                {
                    "key": "pace_per_100m",
                    "name": "Pace per 100m",
                    "unit": "min/100m",
                    "color": "blue",
                    "chart_type": "line",
                    "description": "Swimming pace - spotting pacing fade",
                },
                {
                    "key": "heart_rate",
                    "name": "Heart Rate",
                    "unit": "bpm",
                    "color": "red",
                    "chart_type": "line",
                    "description": "Heart rate over time (if HR strap used)",
                },
                {
                    "key": "stroke_rate",
                    "name": "Stroke Rate",
                    "unit": "strokes/min",
                    "color": "orange",
                    "chart_type": "line",
                    "description": "Stroke rate for efficiency analysis",
                },
                {
                    "key": "swolf",
                    "name": "SWOLF Score",
                    "unit": "score",
                    "color": "purple",
                    "chart_type": "line",
                    "description": "Stroke efficiency metric",
                },
                {
                    "key": "temperature",
                    "name": "Water Temperature",
                    "unit": "°C",
                    "color": "cyan",
                    "chart_type": "line",
                    "description": "Water temperature during swim",
                },
            ],
            "secondary_metrics": [
                {
                    "key": "stroke_type_breakdown",
                    "name": "Stroke Breakdown",
                    "chart_type": "stacked_bar",
                    "description": "Drill breakdown - freestyle, backstroke, drills, kicks",
                },
                {
                    "key": "rest_intervals",
                    "name": "Rest Intervals",
                    "chart_type": "timeline",
                    "description": "Rest intervals - are you sticking to set rest?",
                },
                {
                    "key": "distance_per_set",
                    "name": "Distance per Set",
                    "chart_type": "bar",
                    "description": "Distance per set - main set vs warm-up/cool-down",
                },
            ],
        },
        "cycling": {
            "primary_metrics": [
                {
                    "key": "power",
                    "name": "Power",
                    "unit": "W",
                    "color": "green",
                    "chart_type": "line",
                    "description": "Power over time - line chart",
                },
                {
                    "key": "heart_rate",
                    "name": "Heart Rate",
                    "unit": "bpm",
                    "color": "red",
                    "chart_type": "line",
                    "description": "Heart rate vs. power - to spot decoupling",
                },
                {
                    "key": "cadence",
                    "name": "Cadence",
                    "unit": "rpm",
                    "color": "orange",
                    "chart_type": "line",
                    "description": "Cadence over time - gear choice/efficiency",
                },
                {
                    "key": "speed",
                    "name": "Speed",
                    "unit": "km/h",
                    "color": "blue",
                    "chart_type": "line",
                    "description": "Speed vs elevation - climbs/descents effect",
                },
                {
                    "key": "elevation",
                    "name": "Elevation",
                    "unit": "m",
                    "color": "brown",
                    "chart_type": "area",
                    "description": "Elevation profile with speed overlay",
                },
            ],
            "secondary_metrics": [
                {
                    "key": "normalized_power",
                    "name": "Normalized Power",
                    "unit": "W",
                    "description": "NP, IF, TSS - summary metrics",
                },
                {
                    "key": "power_distribution",
                    "name": "Power Distribution",
                    "chart_type": "histogram",
                    "description": "Power distribution histogram",
                },
                {
                    "key": "hr_power_decoupling",
                    "name": "HR-Power Decoupling",
                    "chart_type": "dual_axis",
                    "description": "Aerobic efficiency analysis",
                },
            ],
        },
        "running": {
            "primary_metrics": [
                {
                    "key": "pace",
                    "name": "Pace",
                    "unit": "min/km",
                    "color": "blue",
                    "chart_type": "line",
                    "description": "Pace over time - line chart",
                },
                {
                    "key": "heart_rate",
                    "name": "Heart Rate",
                    "unit": "bpm",
                    "color": "red",
                    "chart_type": "line",
                    "description": "Heart rate vs pace - HR drift detection",
                },
                {
                    "key": "cadence",
                    "name": "Cadence",
                    "unit": "spm",
                    "color": "orange",
                    "chart_type": "line",
                    "description": "Cadence trends - form issues/fatigue",
                },
                {
                    "key": "stride_length",
                    "name": "Stride Length",
                    "unit": "m",
                    "color": "purple",
                    "chart_type": "line",
                    "description": "Stride length trends",
                },
                {
                    "key": "elevation",
                    "name": "Elevation",
                    "unit": "m",
                    "color": "brown",
                    "chart_type": "area",
                    "description": "Elevation profile with pace overlay",
                },
            ],
            "secondary_metrics": [
                {
                    "key": "power",
                    "name": "Running Power",
                    "unit": "W",
                    "color": "green",
                    "chart_type": "line",
                    "description": "Power vs pace, power distribution",
                },
                {
                    "key": "vertical_oscillation",
                    "name": "Vertical Oscillation",
                    "unit": "mm",
                    "color": "pink",
                    "chart_type": "line",
                    "description": "Running form metrics",
                },
                {
                    "key": "ground_contact_time",
                    "name": "Ground Contact Time",
                    "unit": "ms",
                    "color": "darkred",
                    "chart_type": "line",
                    "description": "Ground contact efficiency",
                },
            ],
        },
    }

    @classmethod
    def get_sport_metrics(cls, sport: str, sub_sport: Optional[str] = None) -> Dict:
        """Get metrics configuration for a sport."""
        # Normalize sport name
        sport_key = cls._normalize_sport_name(sport, sub_sport)
        return cls.SPORT_METRICS.get(sport_key, cls._get_default_metrics())

    @classmethod
    def _normalize_sport_name(cls, sport: str, sub_sport: Optional[str] = None) -> str:
        """Normalize sport names to match our mapping keys."""
        sport_lower = sport.lower() if sport else ""
        sub_sport_lower = sub_sport.lower() if sub_sport else ""

        # Swimming variants
        if "swim" in sport_lower or "swim" in sub_sport_lower:
            return "swimming"

        # Cycling variants
        if any(term in sport_lower for term in ["cycl", "bik"]) or any(
            term in sub_sport_lower for term in ["cycl", "bik"]
        ):
            return "cycling"

        # Running variants
        if any(term in sport_lower for term in ["run", "jog"]) or any(
            term in sub_sport_lower for term in ["run", "jog", "tread"]
        ):
            return "running"

        return "generic"

    @classmethod
    def _get_default_metrics(cls) -> Dict:
        """Default metrics for unknown sports."""
        return {
            "primary_metrics": [
                {
                    "key": "heart_rate",
                    "name": "Heart Rate",
                    "unit": "bpm",
                    "color": "red",
                    "chart_type": "line",
                    "description": "Heart rate over time",
                },
                {
                    "key": "speed",
                    "name": "Speed",
                    "unit": "km/h",
                    "color": "blue",
                    "chart_type": "line",
                    "description": "Speed over time",
                },
            ],
            "secondary_metrics": [],
        }

    @classmethod
    def get_available_metrics(
        cls, sport: str, samples_df: pd.DataFrame, activity_data: Dict, sub_sport: Optional[str] = None
    ) -> List[Dict]:
        """
        Get available metrics for a sport based on actual data availability.

        Args:
            sport: Sport type
            samples_df: Activity samples DataFrame
            activity_data: Activity metadata
            sub_sport: Sub-sport type

        Returns:
            List of available metric configurations
        """
        sport_config = cls.get_sport_metrics(sport, sub_sport)
        available_metrics = []

        # Check primary metrics
        for metric in sport_config["primary_metrics"]:
            if cls._is_metric_available(metric, samples_df, activity_data):
                available_metrics.append(metric)

        # Check secondary metrics
        for metric in sport_config.get("secondary_metrics", []):
            if cls._is_metric_available(metric, samples_df, activity_data):
                available_metrics.append(metric)

        return available_metrics

    @classmethod
    def _is_metric_available(cls, metric: Dict, samples_df: pd.DataFrame, activity_data: Dict) -> bool:
        """Check if a metric is available in the data."""
        key = metric["key"]

        # Map metric keys to actual data columns
        column_mapping = {
            "heart_rate": "heart_rate_bpm",
            "power": "power_w",
            "cadence": "cadence_rpm",
            "speed": "speed_mps",
            "elevation": "altitude_m",
            "temperature": "temperature_c",
            "pace": "speed_mps",  # Can calculate pace from speed
            "pace_per_100m": "speed_mps",  # Can calculate from speed
            "stride_length": "step_length_mm",
            "vertical_oscillation": "vertical_oscillation_mm",
            "ground_contact_time": "ground_contact_time_ms",
        }

        # Check if required column exists and has data
        required_col = column_mapping.get(key)
        if required_col and required_col in samples_df.columns:
            return samples_df[required_col].notna().sum() > 0

        # Special cases for calculated metrics
        if key in ["stroke_rate", "swolf", "normalized_power"]:
            # These would need to be calculated from other metrics
            return False  # Not implemented yet

        if key in ["stroke_type_breakdown", "rest_intervals", "distance_per_set"]:
            # These require lap/interval data analysis
            return False  # Not implemented yet

        return False


def calculate_swim_pace_per_100m(speed_mps: pd.Series) -> pd.Series:
    """Calculate swimming pace per 100m from speed."""
    # Convert m/s to min/100m, handling zero speeds
    speed_valid = speed_mps > 0.01  # Avoid division by very small numbers
    pace_per_100m = np.where(speed_valid, (100 / speed_mps) / 60, np.nan)
    return pd.Series(pace_per_100m, index=speed_mps.index)


def calculate_running_pace(speed_mps: pd.Series) -> pd.Series:
    """Calculate running pace (min/km) from speed."""
    speed_kmh = speed_mps * 3.6
    speed_valid = speed_kmh > 0.1
    pace_min_per_km = np.where(speed_valid, 60 / speed_kmh, np.nan)
    # Cap at reasonable max pace (15 min/km)
    pace_min_per_km = np.where(pace_min_per_km > 15, 15, pace_min_per_km)
    return pd.Series(pace_min_per_km, index=speed_mps.index)


def calculate_stride_length(step_length_mm: pd.Series) -> pd.Series:
    """Convert step length to stride length (2 steps = 1 stride)."""
    return step_length_mm * 2 / 1000  # Convert to meters
