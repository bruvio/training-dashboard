"""
Sport-specific chart generation utilities for activity visualization.

Creates charts optimized for each sport type with relevant metrics.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .sport_metrics import (
    SportMetricsMapper,
    calculate_swim_pace_per_100m,
    calculate_running_pace,
    calculate_stride_length,
)


class SportChartGenerator:
    """Generates sport-specific charts based on available data."""

    @classmethod
    def create_sport_specific_charts(
        cls,
        sport: str,
        samples_df: pd.DataFrame,
        activity_data: Dict,
        sub_sport: Optional[str] = None,
        smoothing: str = "light",
    ) -> go.Figure:
        """
        Create charts optimized for the specific sport.

        Args:
            sport: Sport type
            samples_df: Activity samples DataFrame
            activity_data: Activity metadata
            sub_sport: Sub-sport type
            smoothing: Smoothing level

        Returns:
            Plotly figure with sport-specific charts
        """
        # Get available metrics for this sport
        available_metrics = SportMetricsMapper.get_available_metrics(sport, samples_df, activity_data, sub_sport)

        if not available_metrics:
            return cls._create_empty_figure("No metrics available for this activity")

        # Prepare time axis
        x_axis, x_title = cls._prepare_time_axis(samples_df)

        # Prepare metric data with sport-specific calculations
        prepared_data = cls._prepare_sport_data(sport, samples_df, available_metrics, smoothing)

        # Create sport-specific chart layout
        return cls._create_sport_chart_layout(sport, x_axis, x_title, prepared_data, available_metrics, activity_data)

    @classmethod
    def _prepare_time_axis(cls, samples_df: pd.DataFrame) -> Tuple[pd.Series, str]:
        """Prepare time axis for charts."""
        if "elapsed_time_s" in samples_df.columns:
            x_axis = samples_df["elapsed_time_s"] / 60  # Convert to minutes
            x_title = "Time (minutes)"
        else:
            x_axis = pd.Series(range(len(samples_df)))
            x_title = "Sample Index"
        return x_axis, x_title

    @classmethod
    def _prepare_sport_data(
        cls, sport: str, samples_df: pd.DataFrame, available_metrics: List[Dict], smoothing: str = "light"
    ) -> Dict[str, pd.Series]:
        """Prepare metric data with sport-specific calculations."""
        prepared_data = {}

        for metric in available_metrics:
            key = metric["key"]
            data = cls._get_metric_data(key, samples_df)

            if data is not None:
                # Apply smoothing if requested
                if smoothing != "none":
                    data = cls._apply_smoothing(data, smoothing)
                prepared_data[key] = data

        return prepared_data

    @classmethod
    def _get_metric_data(cls, metric_key: str, samples_df: pd.DataFrame) -> Optional[pd.Series]:
        """Extract metric data from samples DataFrame."""

        # Direct column mappings
        column_mapping = {
            "heart_rate": "heart_rate_bpm",
            "power": "power_w",
            "cadence": "cadence_rpm",
            "speed": "speed_mps",
            "elevation": "altitude_m",
            "temperature": "temperature_c",
            "vertical_oscillation": "vertical_oscillation_mm",
            "ground_contact_time": "ground_contact_time_ms",
        }

        # Check direct mappings first
        if metric_key in column_mapping:
            col_name = column_mapping[metric_key]
            if col_name in samples_df.columns:
                return samples_df[col_name]

        # Calculated metrics
        if metric_key == "pace" and "speed_mps" in samples_df.columns:
            return calculate_running_pace(samples_df["speed_mps"])

        if metric_key == "pace_per_100m" and "speed_mps" in samples_df.columns:
            return calculate_swim_pace_per_100m(samples_df["speed_mps"])

        if metric_key == "stride_length" and "step_length_mm" in samples_df.columns:
            return calculate_stride_length(samples_df["step_length_mm"])

        return None

    @classmethod
    def _apply_smoothing(cls, data: pd.Series, smoothing: str) -> pd.Series:
        """Apply smoothing to data series."""
        if data.isna().all() or len(data) < 5:
            return data

        window_sizes = {"light": 5, "medium": 15, "heavy": 31}
        window = window_sizes.get(smoothing, 5)

        try:
            # Use rolling mean for smoothing
            smoothed = data.rolling(window=window, center=True, min_periods=1).mean()
            return smoothed
        except Exception:
            return data  # Return original if smoothing fails

    @classmethod
    def _create_sport_chart_layout(
        cls,
        sport: str,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        """Create sport-specific chart layout."""

        sport_normalized = SportMetricsMapper._normalize_sport_name(sport)

        if sport_normalized == "swimming":
            return cls._create_swimming_charts(x_axis, x_title, prepared_data, available_metrics, activity_data)
        elif sport_normalized == "cycling":
            return cls._create_cycling_charts(x_axis, x_title, prepared_data, available_metrics, activity_data)
        elif sport_normalized == "running":
            return cls._create_running_charts(x_axis, x_title, prepared_data, available_metrics, activity_data)
        else:
            return cls._create_generic_charts(x_axis, x_title, prepared_data, available_metrics, activity_data)

    @classmethod
    def _create_swimming_charts(
        cls,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        """Create swimming-specific chart layout."""

        # Priority order for swimming charts
        swim_priority = ["pace_per_100m", "heart_rate", "stroke_rate", "temperature", "swolf"]

        # Filter and order available metrics by swimming priority
        ordered_metrics = []
        for priority_key in swim_priority:
            for metric in available_metrics:
                if metric["key"] == priority_key and priority_key in prepared_data:
                    ordered_metrics.append(metric)
                    break

        # Add any remaining metrics
        for metric in available_metrics:
            if metric not in ordered_metrics and metric["key"] in prepared_data:
                ordered_metrics.append(metric)

        return cls._create_subplot_figure(
            x_axis, x_title, prepared_data, ordered_metrics, activity_data, title_prefix="🏊 Swimming"
        )

    @classmethod
    def _create_cycling_charts(
        cls,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        """Create cycling-specific chart layout."""

        # Priority order for cycling charts
        cycling_priority = ["power", "heart_rate", "speed", "cadence", "elevation"]

        # Filter and order available metrics by cycling priority
        ordered_metrics = []
        for priority_key in cycling_priority:
            for metric in available_metrics:
                if metric["key"] == priority_key and priority_key in prepared_data:
                    ordered_metrics.append(metric)
                    break

        # Add any remaining metrics
        for metric in available_metrics:
            if metric not in ordered_metrics and metric["key"] in prepared_data:
                ordered_metrics.append(metric)

        return cls._create_subplot_figure(
            x_axis, x_title, prepared_data, ordered_metrics, activity_data, title_prefix="🚴 Cycling"
        )

    @classmethod
    def _create_running_charts(
        cls,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        """Create running-specific chart layout."""

        # Priority order for running charts
        running_priority = ["pace", "heart_rate", "cadence", "stride_length", "elevation", "power"]

        # Filter and order available metrics by running priority
        ordered_metrics = []
        for priority_key in running_priority:
            for metric in available_metrics:
                if metric["key"] == priority_key and priority_key in prepared_data:
                    ordered_metrics.append(metric)
                    break

        # Add any remaining metrics
        for metric in available_metrics:
            if metric not in ordered_metrics and metric["key"] in prepared_data:
                ordered_metrics.append(metric)

        return cls._create_subplot_figure(
            x_axis, x_title, prepared_data, ordered_metrics, activity_data, title_prefix="🏃 Running"
        )

    @classmethod
    def _create_generic_charts(
        cls,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        """Create generic chart layout for unknown sports."""

        return cls._create_subplot_figure(
            x_axis, x_title, prepared_data, available_metrics, activity_data, title_prefix="⚽ Activity"
        )

    @classmethod
    def _create_subplot_figure(
        cls,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        ordered_metrics: List[Dict],
        activity_data: Dict,
        title_prefix: str = "Activity",
    ) -> go.Figure:
        """Create subplot figure with ordered metrics."""

        n_charts = len(ordered_metrics)
        if n_charts == 0:
            return cls._create_empty_figure("No data available")

        # Calculate vertical spacing
        if n_charts <= 1:
            vertical_spacing = 0.3
        elif n_charts <= 5:
            vertical_spacing = 0.08
        else:
            vertical_spacing = max(0.05, 0.8 / (n_charts - 1))

        # Create subplot titles
        subplot_titles = [f"{metric['name']} ({metric['unit']})" for metric in ordered_metrics]

        fig = make_subplots(
            rows=n_charts, cols=1, shared_xaxes=True, vertical_spacing=vertical_spacing, subplot_titles=subplot_titles
        )

        # Add traces for each metric
        for i, metric in enumerate(ordered_metrics, 1):
            key = metric["key"]
            if key in prepared_data:
                y_data = prepared_data[key]
                valid_mask = ~y_data.isna()

                if valid_mask.sum() > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=x_axis[valid_mask],
                            y=y_data[valid_mask],
                            mode="lines",
                            name=metric["name"],
                            line=dict(color=metric["color"], width=2),
                            hovertemplate=(
                                f"<b>{metric['name']}</b><br>"
                                f"Time: %{{x:.1f}} min<br>"
                                f"{metric['name']}: %{{y:.1f}} {metric['unit']}"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                        ),
                        row=i,
                        col=1,
                    )

                    # Update y-axis for this subplot
                    fig.update_yaxes(title_text=metric["unit"], row=i, col=1)

        # Update layout
        fig.update_xaxes(title_text=x_title, row=n_charts, col=1)
        fig.update_layout(
            height=150 * n_charts + 100,
            title_text=f"{title_prefix} - {activity_data.get('name', 'Activity Charts')}",
            showlegend=False,
            hovermode="x unified",
        )

        return fig

    @classmethod
    def _create_empty_figure(cls, message: str = "No data available") -> go.Figure:
        """Create empty figure with message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message, xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray")
        )
        fig.update_layout(height=400, showlegend=False, xaxis={"visible": False}, yaxis={"visible": False})
        return fig
