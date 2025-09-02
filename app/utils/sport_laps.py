"""
Sport-specific laps/intervals table utilities.

Creates tables with appropriate metrics and units for each sport type.
"""

from typing import Dict, List, Optional
import dash_bootstrap_components as dbc
from dash import html
from app.utils.sport_metrics import SportMetricsMapper


class SportLapsTableGenerator:
    """Generates sport-specific laps/intervals tables."""

    # Define sport-specific lap metrics configuration
    SPORT_LAP_METRICS = {
        "swimming": {
            "columns": [
                {"key": "lap", "name": "Lap", "format": "int"},
                {"key": "distance", "name": "Distance", "unit": "m", "format": "distance_swim"},
                {"key": "time", "name": "Time", "format": "time"},
                {"key": "pace_100m", "name": "Pace", "unit": "min/100m", "format": "pace_swim"},
                {"key": "avg_hr", "name": "Avg HR", "unit": "bpm", "format": "int"},
                {"key": "max_hr", "name": "Max HR", "unit": "bpm", "format": "int"},
                {"key": "avg_strokes", "name": "Strokes", "unit": "spl", "format": "int"},
                {"key": "temperature", "name": "Temp", "unit": "°C", "format": "float1"},
            ]
        },
        "cycling": {
            "columns": [
                {"key": "lap", "name": "Lap", "format": "int"},
                {"key": "distance", "name": "Distance", "unit": "km", "format": "distance_cycle"},
                {"key": "time", "name": "Time", "format": "time"},
                {"key": "speed", "name": "Speed", "unit": "km/h", "format": "speed"},
                {"key": "avg_hr", "name": "Avg HR", "unit": "bpm", "format": "int"},
                {"key": "max_hr", "name": "Max HR", "unit": "bpm", "format": "int"},
                {"key": "avg_power", "name": "Avg Power", "unit": "W", "format": "int"},
                {"key": "max_power", "name": "Max Power", "unit": "W", "format": "int"},
                {"key": "avg_cadence", "name": "Cadence", "unit": "rpm", "format": "int"},
            ]
        },
        "running": {
            "columns": [
                {"key": "lap", "name": "Lap", "format": "int"},
                {"key": "distance", "name": "Distance", "unit": "km", "format": "distance_run"},
                {"key": "time", "name": "Time", "format": "time"},
                {"key": "pace", "name": "Pace", "unit": "min/km", "format": "pace_run"},
                {"key": "avg_hr", "name": "Avg HR", "unit": "bpm", "format": "int"},
                {"key": "max_hr", "name": "Max HR", "unit": "bpm", "format": "int"},
                {"key": "avg_cadence", "name": "Cadence", "unit": "spm", "format": "int"},
                {"key": "avg_power", "name": "Avg Power", "unit": "W", "format": "int"},
            ]
        },
        "generic": {
            "columns": [
                {"key": "lap", "name": "Lap", "format": "int"},
                {"key": "distance", "name": "Distance", "unit": "km", "format": "distance_run"},
                {"key": "time", "name": "Time", "format": "time"},
                {"key": "avg_hr", "name": "Avg HR", "unit": "bpm", "format": "int"},
                {"key": "max_hr", "name": "Max HR", "unit": "bpm", "format": "int"},
                {"key": "avg_cadence", "name": "Cadence", "unit": "rpm", "format": "int"},
            ]
        },
    }

    @classmethod
    def create_sport_specific_laps_table(
        cls,
        sport: str,
        sub_sport: Optional[str],
        laps_data: List[Dict],
        activity_data: Dict,
        user_settings: Optional[Dict] = None,
    ) -> html.Div:
        """
        Create sport-specific laps table.

        Args:
            sport: Sport type
            sub_sport: Sub-sport type
            laps_data: Lap data
            activity_data: Activity metadata
            user_settings: User preferences for units

        Returns:
            HTML div containing the sport-specific table
        """
        if not laps_data:
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No lap data available for this activity.",
                ],
                color="info",
            )

        # Get sport-specific column configuration
        normalized_sport = SportMetricsMapper._normalize_sport_name(sport, sub_sport)
        sport_config = cls.SPORT_LAP_METRICS.get(normalized_sport, cls.SPORT_LAP_METRICS["generic"])

        # Filter columns based on available data
        available_columns = cls._filter_available_columns(sport_config["columns"], laps_data)

        # Create table headers
        headers = cls._create_table_headers(available_columns)

        # Create table rows
        rows = cls._create_table_rows(available_columns, laps_data, normalized_sport, user_settings)

        return dbc.Table(
            headers + [html.Tbody(rows)],
            striped=True,
            hover=True,
            responsive=True,
            className="mb-0",
        )

    @classmethod
    def _filter_available_columns(cls, columns: List[Dict], laps_data: List[Dict]) -> List[Dict]:
        """Filter columns based on available data in laps."""
        available_columns = []

        for column in columns:
            key = column["key"]

            # Always include lap number, distance, and time
            if key in ["lap", "distance", "time"]:
                available_columns.append(column)
                continue

            # Check if data exists for this metric
            if cls._has_data_for_metric(key, laps_data):
                available_columns.append(column)

        return available_columns

    @classmethod
    def _has_data_for_metric(cls, metric_key: str, laps_data: List[Dict]) -> bool:
        """Check if laps data contains meaningful values for a metric."""
        mapping = {
            "avg_hr": "avg_hr",
            "max_hr": "max_hr",
            "avg_power": "avg_power_w",
            "max_power": "max_power_w",
            "avg_cadence": "avg_cadence_rpm",
            "avg_strokes": "avg_cadence_rpm",  # Reusing cadence for stroke count
            "temperature": "temperature_c",
            "pace": "avg_speed_mps",  # Pace can be calculated from speed
            "pace_100m": "avg_speed_mps",  # Swimming pace from speed
            "speed": "avg_speed_mps",  # Speed data
        }

        field_name = mapping.get(metric_key)
        if not field_name:
            return False

        # Check if any lap has meaningful data for this field
        for lap in laps_data:
            value = lap.get(field_name)
            if value is not None and value > 0:
                return True

        return False

    @classmethod
    def _create_table_headers(cls, columns: List[Dict]) -> List[html.Thead]:
        """Create table headers."""
        header_cells = []
        for column in columns:
            if "unit" in column:
                header_text = f"{column['name']} ({column['unit']})"
            else:
                header_text = column["name"]

            header_cells.append(html.Th(header_text, className="text-center"))

        return [html.Thead([html.Tr(header_cells)])]

    @classmethod
    def _create_table_rows(
        cls, columns: List[Dict], laps_data: List[Dict], sport: str, user_settings: Optional[Dict] = None
    ) -> List[html.Tr]:
        """Create table rows with sport-specific formatting."""
        rows = []

        for lap in laps_data:
            cells = []

            for column in columns:
                key = column["key"]
                format_type = column.get("format", "string")

                # Get cell value based on metric key
                cell_value = cls._get_cell_value(key, lap, sport, user_settings)

                # Format the value
                formatted_value = cls._format_cell_value(cell_value, format_type)

                cells.append(html.Td(formatted_value, className="text-center"))

            rows.append(html.Tr(cells))

        return rows

    @classmethod
    def _get_cell_value(cls, metric_key: str, lap: Dict, sport: str, user_settings: Optional[Dict] = None) -> str:
        """Get cell value for a specific metric."""

        if metric_key == "lap":
            return str(lap.get("lap_index", 0) + 1)  # 1-indexed for display

        elif metric_key == "distance":
            distance_m = lap.get("distance_m", 0)
            if sport == "swimming":
                return f"{distance_m:.0f}" if distance_m > 0 else "N/A"
            else:
                # Convert to km
                distance_km = distance_m / 1000 if distance_m else 0
                return f"{distance_km:.2f}" if distance_km > 0 else "N/A"

        elif metric_key == "time":
            elapsed_time = lap.get("elapsed_time_s", 0)
            return cls._format_duration(elapsed_time)

        elif metric_key == "pace" or metric_key == "pace_100m":
            return cls._calculate_pace(lap, sport, user_settings)

        elif metric_key == "speed":
            speed_mps = lap.get("avg_speed_mps", 0)
            if speed_mps and speed_mps > 0:
                speed_kmh = speed_mps * 3.6
                return f"{speed_kmh:.1f}"
            return "N/A"

        elif metric_key == "avg_hr":
            hr = lap.get("avg_hr", 0)
            return f"{int(hr)}" if hr and hr > 0 else "N/A"

        elif metric_key == "max_hr":
            hr = lap.get("max_hr", 0)
            return f"{int(hr)}" if hr and hr > 0 else "N/A"

        elif metric_key == "avg_power":
            power = lap.get("avg_power_w", 0)
            return f"{int(power)}" if power and power > 0 else "N/A"

        elif metric_key == "max_power":
            power = lap.get("max_power_w", 0)
            return f"{int(power)}" if power and power > 0 else "N/A"

        elif metric_key == "avg_cadence":
            cadence = lap.get("avg_cadence_rpm", 0)
            return f"{int(cadence)}" if cadence and cadence > 0 else "N/A"

        elif metric_key == "avg_strokes":
            # For swimming, interpret cadence as stroke rate
            strokes = lap.get("avg_cadence_rpm", 0)
            return f"{int(strokes)}" if strokes and strokes > 0 else "N/A"

        elif metric_key == "temperature":
            temp = lap.get("temperature_c", 0)
            return f"{temp:.1f}" if temp else "N/A"

        return "N/A"

    @classmethod
    def _calculate_pace(cls, lap: Dict, sport: str, user_settings: Optional[Dict] = None) -> str:
        """Calculate pace based on sport type and user settings."""
        speed_mps = lap.get("avg_speed_mps", 0)
        if not speed_mps or speed_mps <= 0:
            return "N/A"

        if sport == "swimming":
            # Swimming pace per 100m
            pace_sec_per_100m = 100 / speed_mps
            pace_min = int(pace_sec_per_100m // 60)
            pace_sec = int(pace_sec_per_100m % 60)
            return f"{pace_min}:{pace_sec:02d}"

        elif sport == "running":
            # Running pace per km (or mile based on settings)
            # TODO: Check user settings for km vs mile preference
            pace_sec_per_km = 1000 / speed_mps
            pace_min = int(pace_sec_per_km // 60)
            pace_sec = int(pace_sec_per_km % 60)
            return f"{pace_min}:{pace_sec:02d}"

        return "N/A"

    @classmethod
    def _format_cell_value(cls, value: str, format_type: str) -> str:
        """Apply formatting to cell value."""
        # Most formatting is already handled in _get_cell_value
        return value

    @classmethod
    def _format_duration(cls, total_seconds: int) -> str:
        """Format duration in seconds to readable string."""
        if not total_seconds:
            return "0:00"

        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
