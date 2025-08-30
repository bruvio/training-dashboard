"""
Activity detail page - Show detailed analysis and charts for a specific activity.
"""

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from app.data.db import session_scope
from app.data.models import Activity, Sample

# This page uses manual routing - no registration needed


def layout(activity_id=None):
    """
    Layout for activity detail page.

    Args:
        activity_id: Activity ID from URL path
    """
    if not activity_id:
        return dbc.Alert("Invalid activity ID", color="danger")

    try:
        activity_id = int(activity_id)
    except ValueError:
        return dbc.Alert("Invalid activity ID format", color="danger")

    return dbc.Container(
        [
            dcc.Store(id="activity-data-store", data={"activity_id": activity_id}),
            # Header section
            dbc.Row([dbc.Col([html.Div(id="activity-header"), html.Hr()], width=12)]),
            # Summary section
            dbc.Row([dbc.Col([html.Div(id="activity-summary")], width=12)], className="mb-4"),
            # Charts and data section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Activity Charts", className="mb-0")]),
                                    dbc.CardBody(
                                        [
                                            # Data type selector
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label("Select Data to Display:", className="fw-bold mb-2"),
                                                            html.Div(id="metric-selector-container")
                                                        ]
                                                    )
                                                ]
                                            ),
                                            html.Div(id="activity-charts"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mb-4",
            ),
            # Route map section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Route Map", className="mb-0")]),
                                    dbc.CardBody([html.Div(id="activity-map")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ]
            ),
            # Lap splits section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader([html.H5("Lap Splits", className="mb-0")]),
                                    dbc.CardBody([html.Div(id="activity-laps")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ],
                className="mt-4",
            ),
        ],
        fluid=True,
    )


@callback(Output("metric-selector-container", "children"), Input("activity-data-store", "data"))
def update_metric_selector(store_data):
    """Update metric selector with only available data."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            # Get samples to check which metrics have data
            samples = session.query(Sample).filter_by(activity_id=activity_id).limit(100).all()
            
            if not samples:
                return dbc.Alert("No sample data found", color="info")

            # Check which metrics have non-null values
            available_metrics = []
            metric_config = {
                "heart_rate": {"label": "Heart Rate", "value": "heart_rate"},
                "speed_mps": {"label": "Speed", "value": "speed_mps"},
                "altitude_m": {"label": "Altitude", "value": "altitude_m"},
                "cadence_rpm": {"label": "Cadence", "value": "cadence_rpm"},
                "power_w": {"label": "Power", "value": "power_w"},
                "temperature_c": {"label": "Temperature", "value": "temperature_c"},
            }

            # Check each metric to see if it has data
            for metric_key, metric_info in metric_config.items():
                has_data = any(getattr(sample, metric_key) is not None for sample in samples)
                if has_data:
                    available_metrics.append(metric_info)

            if not available_metrics:
                return dbc.Alert("No valid metrics found for this activity", color="warning")

            # Default to first available metric
            default_value = [available_metrics[0]["value"]] if available_metrics else []

            return dbc.Checklist(
                options=available_metrics,
                value=default_value,
                id="data-overlay-selector",
                inline=True,
                className="mb-3",
            )

    except Exception as e:
        return dbc.Alert(f"Error loading metrics: {str(e)}", color="danger")


@callback(Output("activity-header", "children"), Input("activity-data-store", "data"))
def update_activity_header(store_data):
    """Update activity header with basic info."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            activity = session.query(Activity).filter_by(id=activity_id).first()

            if not activity:
                return dbc.Alert(f"Activity {activity_id} not found", color="danger")

            # Format activity details
            duration_str = f"{activity.elapsed_time_s // 60:.0f} min" if activity.elapsed_time_s else "N/A"
            distance_str = f"{activity.distance_m/1000:.2f} km" if activity.distance_m else "N/A"
            speed_str = f"{activity.avg_speed_mps * 3.6:.1f} km/h" if activity.avg_speed_mps else "N/A"

            return html.Div(
                [
                    html.H1([html.I(className="fas fa-chart-line me-3"), f"Activity {activity_id}"]),
                    dbc.Row(
                        [
                            dbc.Col([html.Strong("Sport: "), activity.sport or "Unknown"], width=3),
                            dbc.Col([html.Strong("Duration: "), duration_str], width=3),
                            dbc.Col([html.Strong("Distance: "), distance_str], width=3),
                            dbc.Col([html.Strong("Avg Speed: "), speed_str], width=3),
                        ],
                        className="mb-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Strong("Date: "),
                                    (
                                        activity.start_time_utc.strftime("%Y-%m-%d %H:%M:%S")
                                        if activity.start_time_utc
                                        else "Unknown"
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [html.Strong("Source: "), activity.source.upper() if activity.source else "Unknown"],
                                width=6,
                            ),
                        ]
                    ),
                ]
            )

    except Exception as e:
        return dbc.Alert(f"Error loading activity: {str(e)}", color="danger")


@callback(
    Output("activity-charts", "children"), 
    [Input("activity-data-store", "data"), Input("data-overlay-selector", "value")],
    prevent_initial_call=True
)
def update_activity_charts(store_data, selected_metrics):
    """Update activity charts with sample data."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        if not selected_metrics:
            selected_metrics = ["heart_rate"]  # Default

        with session_scope() as session:
            # Get activity samples
            samples = session.query(Sample).filter_by(activity_id=activity_id).order_by(Sample.elapsed_time_s).all()

            if not samples:
                return dbc.Alert("No sample data found for this activity", color="info")

            # Convert to DataFrame
            sample_data = []
            for sample in samples:
                sample_data.append(
                    {
                        "time": sample.elapsed_time_s / 60,  # Convert to minutes
                        "heart_rate": sample.heart_rate,
                        "speed_mps": sample.speed_mps * 3.6 if sample.speed_mps else None,  # Convert to km/h
                        "altitude_m": sample.altitude_m,
                        "power_w": sample.power_w,
                        "cadence_rpm": sample.cadence_rpm,
                        "temperature_c": sample.temperature_c,
                    }
                )

            df = pd.DataFrame(sample_data)

            # Create multi-axis plot
            fig = go.Figure()

            # Define colors and labels for each metric
            metric_config = {
                "heart_rate": {"color": "#FF6B6B", "name": "Heart Rate", "unit": "bpm", "side": "left"},
                "speed_mps": {"color": "#4ECDC4", "name": "Speed", "unit": "km/h", "side": "right"},
                "altitude_m": {"color": "#45B7D1", "name": "Altitude", "unit": "m", "side": "right"},
                "power_w": {"color": "#FFA07A", "name": "Power", "unit": "W", "side": "right"},
                "cadence_rpm": {"color": "#98D8C8", "name": "Cadence", "unit": "rpm", "side": "right"},
                "temperature_c": {"color": "#F7DC6F", "name": "Temperature", "unit": "°C", "side": "right"},
            }

            # Filter out metrics with no data and build traces
            valid_traces = []
            axes_used = []
            
            for i, metric in enumerate(selected_metrics):
                if metric in metric_config and metric in df.columns:
                    # Check if data exists and has non-null values
                    data_series = df[metric].dropna()
                    if len(data_series) > 0:
                        # Assign y-axis (y, y2, y3, etc.)
                        yaxis_ref = "y" if i == 0 else f"y{i+1}"
                        
                        fig.add_trace(
                            go.Scatter(
                                x=df["time"],
                                y=df[metric],
                                mode="lines",
                                name=f"{metric_config[metric]['name']} ({metric_config[metric]['unit']})",
                                line=dict(color=metric_config[metric]["color"], width=2),
                                yaxis=yaxis_ref,
                                hovertemplate=(
                                    f"<b>{metric_config[metric]['name']}</b><br>"
                                    + "Time: %{x:.1f} min<br>"
                                    + f"Value: %{{y}} {metric_config[metric]['unit']}<br>"
                                    + "<extra></extra>"
                                ),
                            )
                        )
                        
                        valid_traces.append({
                            "metric": metric,
                            "yaxis": yaxis_ref,
                            "config": metric_config[metric]
                        })
                        axes_used.append(yaxis_ref)

            if not valid_traces:
                return dbc.Alert("No data available for the selected metrics. Please select different metrics from the available options.", color="warning")

            # Configure layout with proper multi-axis formatting
            layout_config = {
                "title": {
                    "text": "Activity Data Over Time",
                    "x": 0.5,
                    "font": {"size": 16}
                },
                "xaxis": {
                    "title": "Time (minutes)",
                    "showgrid": True,
                    "gridcolor": "rgba(128,128,128,0.2)",
                },
                "height": 600,
                "hovermode": "x unified",
                "legend": {
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "center",
                    "x": 0.5
                },
                "margin": {"l": 60, "r": 60, "t": 80, "b": 60},
            }

            # Configure multiple y-axes
            for i, trace in enumerate(valid_traces):
                yaxis_key = "yaxis" if i == 0 else f"yaxis{i+1}"
                
                axis_config = {
                    "title": {
                        "text": f"{trace['config']['name']} ({trace['config']['unit']})",
                        "font": {"color": trace['config']['color']}
                    },
                    "tickfont": {"color": trace['config']['color']},
                    "showgrid": i == 0,  # Only show grid for primary axis
                }
                
                if i == 0:
                    # Primary axis (left side)
                    axis_config["side"] = "left"
                else:
                    # Secondary axes (right side)
                    axis_config["overlaying"] = "y"
                    axis_config["side"] = "right"
                    if i > 1:
                        # Offset additional axes
                        axis_config["position"] = 1.0 - (i-1) * 0.08
                
                layout_config[yaxis_key] = axis_config

            fig.update_layout(**layout_config)

            if not selected_metrics or not any(metric in df.columns for metric in selected_metrics):
                return dbc.Alert("No data available for selected metrics", color="info")

            return dcc.Graph(figure=fig, style={"height": "500px"})

    except Exception as e:
        return dbc.Alert(f"Error loading charts: {str(e)}", color="danger")


@callback(Output("activity-map", "children"), Input("activity-data-store", "data"))
def update_activity_map(store_data):
    """Update activity route map."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            # Get GPS coordinates from samples
            samples = (
                session.query(Sample)
                .filter_by(activity_id=activity_id)
                .filter(Sample.latitude.isnot(None), Sample.longitude.isnot(None))
                .order_by(Sample.elapsed_time_s)
                .all()
            )

            if not samples:
                return dbc.Alert("No GPS data found for this activity", color="info")

            # Create route data
            lats = [sample.latitude for sample in samples]
            lons = [sample.longitude for sample in samples]

            if not lats or not lons:
                return dbc.Alert("No valid GPS coordinates found", color="info")

            # Create map
            fig = go.Figure()

            # Add route line
            fig.add_trace(
                go.Scattermapbox(
                    mode="lines+markers",
                    lon=lons,
                    lat=lats,
                    marker={"size": 4, "color": "red"},
                    line={"width": 3, "color": "red"},
                    name="Route",
                    hovertemplate="<b>Lat:</b> %{lat}<br><b>Lon:</b> %{lon}<extra></extra>",
                )
            )

            # Add start marker
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[0]],
                    lat=[lats[0]],
                    marker={"size": 12, "color": "green"},
                    name="Start",
                    hovertemplate="<b>Start</b><extra></extra>",
                )
            )

            # Add end marker
            fig.add_trace(
                go.Scattermapbox(
                    mode="markers",
                    lon=[lons[-1]],
                    lat=[lats[-1]],
                    marker={"size": 12, "color": "red"},
                    name="End",
                    hovertemplate="<b>End</b><extra></extra>",
                )
            )

            # Calculate center and zoom
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)

            fig.update_layout(
                mapbox_style="open-street-map",
                mapbox=dict(center=dict(lat=center_lat, lon=center_lon), zoom=12),
                showlegend=True,
                height=400,
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
            )

            return dcc.Graph(figure=fig)

    except Exception as e:
        return dbc.Alert(f"Error loading map: {str(e)}", color="danger")
