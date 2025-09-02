"""
Sport-specific chart generation utilities for activity visualization.

Generates a single interactive chart where users can:
- Toggle metrics dynamically
- Switch between time/distance as X-axis
- View vertical lap markers
- Filter data to a selected lap
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

from .sport_metrics import (
    SportMetricsMapper,
    calculate_running_pace,
    calculate_stride_length,
    calculate_swim_pace_per_100m,
)


class SportChartGenerator:
    """Generates interactive sport-specific charts with overlays and controls."""

    @classmethod
    def create_sport_specific_chart(
        cls,
        sport: str,
        samples_df: pd.DataFrame,
        activity_data: Dict,
        sub_sport: Optional[str] = None,
        smoothing: str = "light",
        lap_index: Optional[int] = None,
    ) -> go.Figure:
        """
        Create a single overlayed interactive chart.

        Args:
            sport: Sport type
            samples_df: Activity samples DataFrame
            activity_data: Activity metadata
            sub_sport: Optional sub-sport
            smoothing: Smoothing level
            lap_index: If provided, filter data to a specific lap
        """
        available_metrics = SportMetricsMapper.get_available_metrics(sport, samples_df, activity_data, sub_sport)
        if not available_metrics:
            return cls._create_empty_figure("No metrics available")

        # Filter by lap if requested
        if lap_index is not None and "lap_index" in samples_df.columns:
            samples_df = samples_df[samples_df["lap_index"] == lap_index]

        # Choose default x-axis (time)
        x_axis, x_title = cls._prepare_time_axis(samples_df)
        prepared_data = cls._prepare_sport_data(sport, samples_df, available_metrics, smoothing)

        return cls._create_overlay_figure(samples_df, x_axis, x_title, prepared_data, available_metrics, activity_data)

    # ---------- Data preparation ----------

    @classmethod
    def _prepare_time_axis(cls, df: pd.DataFrame) -> Tuple[pd.Series, str]:
        if "elapsed_time_s" in df.columns:
            return df["elapsed_time_s"] / 60, "Time (minutes)"
        return pd.Series(range(len(df))), "Sample Index"

    @classmethod
    def _prepare_distance_axis(cls, df: pd.DataFrame) -> Tuple[pd.Series, str]:
        if "distance_m" in df.columns:
            return df["distance_m"] / 1000, "Distance (km)"
        return pd.Series(range(len(df))), "Sample Index"

    @classmethod
    def _prepare_sport_data(
        cls, sport: str, df: pd.DataFrame, available_metrics: List[Dict], smoothing: str
    ) -> Dict[str, pd.Series]:
        prepared = {}
        for metric in available_metrics:
            data = cls._get_metric_data(metric["key"], df)
            if data is not None:
                if smoothing != "none":
                    data = cls._apply_smoothing(data, smoothing)
                prepared[metric["key"]] = data
        return prepared

    @classmethod
    def _get_metric_data(cls, key: str, df: pd.DataFrame) -> Optional[pd.Series]:
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
        if key in column_mapping and column_mapping[key] in df.columns:
            return df[column_mapping[key]]
        if key == "pace" and "speed_mps" in df.columns:
            return calculate_running_pace(df["speed_mps"])
        if key == "pace_per_100m" and "speed_mps" in df.columns:
            return calculate_swim_pace_per_100m(df["speed_mps"])
        if key == "stride_length" and "step_length_mm" in df.columns:
            return calculate_stride_length(df["step_length_mm"])
        return None

    @classmethod
    def _apply_smoothing(cls, data: pd.Series, level: str) -> pd.Series:
        if data.isna().all() or len(data) < 5:
            return data
        window_sizes = {"light": 5, "medium": 15, "heavy": 31}
        return data.rolling(window=window_sizes.get(level, 5), center=True, min_periods=1).mean()

    # ---------- Figure creation ----------

    @classmethod
    def _create_overlay_figure(
        cls,
        df: pd.DataFrame,
        x_axis: pd.Series,
        x_title: str,
        prepared_data: Dict[str, pd.Series],
        available_metrics: List[Dict],
        activity_data: Dict,
    ) -> go.Figure:
        fig = go.Figure()

        # Determine which metrics go on which axis
        primary_metrics = []
        secondary_metrics = []

        # Group similar metrics together on the same axis to avoid unit conflicts
        for i, metric in enumerate(available_metrics):
            key = metric["key"]
            # Put power, heart rate, elevation on primary axis
            if key in ["power", "heart_rate", "elevation", "temperature"]:
                primary_metrics.append((i, metric))
            # Put pace, cadence, speed on secondary axis
            else:
                secondary_metrics.append((i, metric))

        # If we don't have enough metrics for dual axis, put first half on primary, second half on secondary
        if not primary_metrics and not secondary_metrics:
            mid_point = len(available_metrics) // 2
            primary_metrics = [(i, m) for i, m in enumerate(available_metrics[:mid_point])]
            secondary_metrics = [(i, m) for i, m in enumerate(available_metrics[mid_point:])]
        elif not secondary_metrics:
            # Move half the primary metrics to secondary
            mid = len(primary_metrics) // 2
            secondary_metrics = primary_metrics[mid:]
            primary_metrics = primary_metrics[:mid]

        # Add primary axis traces
        for i, metric in primary_metrics:
            key = metric["key"]
            if key not in prepared_data:
                continue
            y_data = prepared_data[key]
            valid_mask = ~y_data.isna()
            if valid_mask.sum() == 0:
                continue

            # Create custom hover template based on metric type
            if key in ["pace", "pace_per_100m"]:
                hover_template = (
                    f"<b>{metric['name']}</b><br>" f"{x_title}: %{{x:.2f}}<br>" f"Pace: %{{customdata}}<extra></extra>"
                )
                # Convert pace from decimal minutes to mm:ss format
                pace_formatted = []
                for pace_val in y_data[valid_mask]:
                    if pd.notna(pace_val) and pace_val > 0:
                        minutes = int(pace_val)
                        seconds = int((pace_val - minutes) * 60)
                        pace_formatted.append(f"{minutes}:{seconds:02d}")
                    else:
                        pace_formatted.append("N/A")
                customdata = pace_formatted
            else:
                hover_template = (
                    f"<b>{metric['name']}</b><br>"
                    f"{x_title}: %{{x:.2f}}<br>"
                    f"Value: %{{y:.1f}} {metric['unit']}<extra></extra>"
                )
                customdata = None

            fig.add_trace(
                go.Scatter(
                    x=x_axis[valid_mask],
                    y=y_data[valid_mask],
                    mode="lines",
                    name=f"{metric['name']} ({metric['unit']})",
                    line=dict(color=metric["color"], width=2),
                    hovertemplate=hover_template,
                    customdata=customdata,
                    yaxis="y",  # Primary axis
                    visible=True,
                    legendgroup="primary",
                )
            )

        # Add secondary axis traces
        for i, metric in secondary_metrics:
            key = metric["key"]
            if key not in prepared_data:
                continue
            y_data = prepared_data[key]
            valid_mask = ~y_data.isna()
            if valid_mask.sum() == 0:
                continue

            # Create custom hover template based on metric type
            if key in ["pace", "pace_per_100m"]:
                hover_template = (
                    f"<b>{metric['name']}</b><br>" f"{x_title}: %{{x:.2f}}<br>" f"Pace: %{{customdata}}<extra></extra>"
                )
                # Convert pace from decimal minutes to mm:ss format
                pace_formatted = []
                for pace_val in y_data[valid_mask]:
                    if pd.notna(pace_val) and pace_val > 0:
                        minutes = int(pace_val)
                        seconds = int((pace_val - minutes) * 60)
                        pace_formatted.append(f"{minutes}:{seconds:02d}")
                    else:
                        pace_formatted.append("N/A")
                customdata = pace_formatted
            else:
                hover_template = (
                    f"<b>{metric['name']}</b><br>"
                    f"{x_title}: %{{x:.2f}}<br>"
                    f"Value: %{{y:.1f}} {metric['unit']}<extra></extra>"
                )
                customdata = None

            fig.add_trace(
                go.Scatter(
                    x=x_axis[valid_mask],
                    y=y_data[valid_mask],
                    mode="lines",
                    name=f"{metric['name']} ({metric['unit']})",
                    line=dict(color=metric["color"], width=2, dash="dash"),  # Dash style for secondary axis
                    hovertemplate=hover_template,
                    customdata=customdata,
                    yaxis="y2",  # Secondary axis
                    visible=True,
                    legendgroup="secondary",
                )
            )

        # Add vertical lap markers if available
        if "lap_index" in df.columns and "elapsed_time_s" in df.columns:
            lap_starts = df.groupby("lap_index")["elapsed_time_s"].min() / 60
            for lap_idx, t_start in lap_starts.items():
                fig.add_vline(
                    x=t_start,
                    line_dash="dot",
                    line_color="gray",
                    annotation_text=f"Lap {lap_idx+1}",
                    annotation_position="top left",
                )

        # Add control dropdowns
        updatemenus = []

        # X-axis selector dropdown if distance data is available
        if "distance_m" in df.columns and df["distance_m"].notna().sum() > 0:
            time_axis, time_label = cls._prepare_time_axis(df)
            distance_axis, dist_label = cls._prepare_distance_axis(df)

            # Prepare both time and distance x-axis data for each trace
            time_data = []
            distance_data = []

            for i, metric in enumerate(available_metrics):
                key = metric["key"]
                if key in prepared_data:
                    y_data = prepared_data[key]
                    valid_mask = ~y_data.isna()
                    time_data.append(time_axis[valid_mask].tolist())
                    distance_data.append(distance_axis[valid_mask].tolist())
                else:
                    time_data.append([])
                    distance_data.append([])

            updatemenus.append(
                dict(
                    buttons=[
                        dict(
                            label="Time",
                            method="update",
                            args=[{"x": time_data}, {"xaxis": {"title": time_label}}],
                        ),
                        dict(
                            label="Distance",
                            method="update",
                            args=[{"x": distance_data}, {"xaxis": {"title": dist_label}}],
                        ),
                    ],
                    direction="down",
                    showactive=True,
                    x=1.02,
                    xanchor="right",
                    y=1.15,
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(0,0,0,0.2)",
                    font=dict(size=11),
                )
            )

        # Apply updatemenus to layout if any exist
        if updatemenus:
            fig.update_layout(updatemenus=updatemenus)

        # Configure dual Y-axis layout
        yaxis_config = {}

        # Build Y-axis titles based on which metrics are on each axis
        primary_units = set()
        secondary_units = set()

        for _, metric in primary_metrics:
            primary_units.add(metric["unit"])
        for _, metric in secondary_metrics:
            secondary_units.add(metric["unit"])

        primary_title = " / ".join(sorted(primary_units)) if primary_units else "Primary Metrics"
        secondary_title = " / ".join(sorted(secondary_units)) if secondary_units else "Secondary Metrics"

        if primary_metrics:
            yaxis_config["yaxis"] = dict(
                title=primary_title,
                side="left",
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
            )

        if secondary_metrics:
            yaxis_config["yaxis2"] = dict(
                title=secondary_title,
                side="right",
                overlaying="y",
                showgrid=False,  # Only show grid on primary axis to avoid clutter
            )

        fig.update_layout(
            title=f"Interactive Activity Chart - {activity_data.get('name', 'Activity')}",
            xaxis_title=x_title,
            xaxis=dict(
                showgrid=True,
                gridcolor="rgba(128,128,128,0.2)",
            ),
            hovermode="x unified",
            height=600,
            margin=dict(t=80, r=80),  # Extra right margin for secondary axis labels
            legend=dict(
                orientation="h",
                y=-0.15,
                x=0.5,
                xanchor="center",
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="rgba(0,0,0,0.3)",
                borderwidth=1,
            ),
            **yaxis_config,
        )

        return fig

    @classmethod
    def _create_empty_figure(cls, message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="gray"))
        fig.update_layout(height=400, xaxis={"visible": False}, yaxis={"visible": False})
        return fig
