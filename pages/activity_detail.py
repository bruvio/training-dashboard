"""
Activity detail page - Show detailed analysis and charts for a specific activity.
"""

from dash import Input, Output, State, callback, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from app.data.db import session_scope
from app.data.models import Activity, Lap, Sample

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
            # Comments section
            dbc.Row([dbc.Col([html.Div(id="activity-comments")], width=12)], className="mb-4"),
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
                                                            html.Label(
                                                                "Select Data to Display:", className="fw-bold mb-2"
                                                            ),
                                                            html.Div(id="metric-selector-container"),
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
                # Basic metrics
                "heart_rate": {"label": "Heart Rate (bpm)", "value": "heart_rate", "color": "red", "category": "basic"},
                "pace_per_km": {"label": "Pace (min/km)", "value": "pace_per_km", "color": "blue", "category": "basic"},
                "speed_mps": {"label": "Speed (m/s)", "value": "speed_mps", "color": "blue", "category": "basic"},
                "altitude_m": {"label": "Altitude (m)", "value": "altitude_m", "color": "brown", "category": "basic"},
                "cadence_rpm": {
                    "label": "Cadence (rpm)",
                    "value": "cadence_rpm",
                    "color": "purple",
                    "category": "basic",
                },
                "power_w": {"label": "Power (W)", "value": "power_w", "color": "orange", "category": "basic"},
                "temperature_c": {
                    "label": "Temperature (°C)",
                    "value": "temperature_c",
                    "color": "darkgreen",
                    "category": "basic",
                },
                # Advanced running dynamics
                "vertical_oscillation_mm": {
                    "label": "Vertical Oscillation (mm)",
                    "value": "vertical_oscillation_mm",
                    "color": "darkred",
                    "category": "running",
                },
                "vertical_ratio": {
                    "label": "Vertical Ratio (%)",
                    "value": "vertical_ratio",
                    "color": "darkblue",
                    "category": "running",
                },
                "ground_contact_time_ms": {
                    "label": "Ground Contact Time (ms)",
                    "value": "ground_contact_time_ms",
                    "color": "darkgray",
                    "category": "running",
                },
                "ground_contact_balance_pct": {
                    "label": "Ground Contact Balance (%)",
                    "value": "ground_contact_balance_pct",
                    "color": "darkmagenta",
                    "category": "running",
                },
                "step_length_mm": {
                    "label": "Step Length (mm)",
                    "value": "step_length_mm",
                    "color": "darkorange",
                    "category": "running",
                },
                # Power metrics
                "air_power_w": {
                    "label": "Air Power (W)",
                    "value": "air_power_w",
                    "color": "lightblue",
                    "category": "power",
                },
                "form_power_w": {
                    "label": "Form Power (W)",
                    "value": "form_power_w",
                    "color": "darkturquoise",
                    "category": "power",
                },
                # Biomechanics
                "leg_spring_stiffness": {
                    "label": "Leg Spring Stiffness",
                    "value": "leg_spring_stiffness",
                    "color": "maroon",
                    "category": "biomechanics",
                },
                "impact_loading_rate": {
                    "label": "Impact Loading Rate",
                    "value": "impact_loading_rate",
                    "color": "crimson",
                    "category": "biomechanics",
                },
                # Environmental (Stryd)
                "stryd_temperature_c": {
                    "label": "Stryd Temperature (°C)",
                    "value": "stryd_temperature_c",
                    "color": "forestgreen",
                    "category": "environmental",
                },
                "stryd_humidity_pct": {
                    "label": "Stryd Humidity (%)",
                    "value": "stryd_humidity_pct",
                    "color": "steelblue",
                    "category": "environmental",
                },
            }

            # Check each metric to see if it has data
            for metric_key, metric_info in metric_config.items():
                if metric_key == "pace_per_km":
                    # Special case: pace is calculated from speed
                    has_data = any(getattr(sample, "speed_mps") is not None for sample in samples)
                else:
                    has_data = any(getattr(sample, metric_key) is not None for sample in samples)

                if has_data:
                    available_metrics.append(metric_info)

            if not available_metrics:
                return dbc.Alert("No valid metrics found for this activity", color="warning")

            # Group metrics by category
            categories = {}
            for metric in available_metrics:
                category = metric["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(metric)

            # Set default values: pace and power (not form power) as requested
            default_values = []
            available_values = [m["value"] for m in available_metrics]
            if "pace_per_km" in available_values:
                default_values.append("pace_per_km")
            if "power_w" in available_values:
                default_values.append("power_w")

            # If neither pace nor power available, default to first 2 available metrics
            if not default_values:
                default_values = available_values[:2]

            # Create organized metric selector
            metric_sections = []
            category_order = ["basic", "running", "power", "biomechanics", "environmental"]
            category_labels = {
                "basic": "Basic Metrics",
                "running": "Running Dynamics",
                "power": "Power Analysis",
                "biomechanics": "Biomechanics",
                "environmental": "Environmental",
            }

            for category in category_order:
                if category in categories:
                    metric_sections.append(
                        html.Div(
                            [
                                html.H6(category_labels[category], className="text-secondary mb-2 mt-3"),
                                dbc.Checklist(
                                    options=categories[category],
                                    value=[m["value"] for m in categories[category] if m["value"] in default_values],
                                    id=f"data-overlay-selector-{category}",
                                    inline=True,
                                    className="mb-2",
                                ),
                            ]
                        )
                    )

            return html.Div(
                [
                    html.P("Select metrics to display in the chart:", className="text-muted mb-3"),
                    html.Div(metric_sections),
                    dcc.Store(id="combined-metric-selection", data=default_values),
                ]
            )

    except Exception as e:
        return dbc.Alert(f"Error loading metrics: {str(e)}", color="danger")


@callback(
    Output("combined-metric-selection", "data"),
    [
        Input("data-overlay-selector-basic", "value"),
        Input("data-overlay-selector-running", "value"),
        Input("data-overlay-selector-power", "value"),
        Input("data-overlay-selector-biomechanics", "value"),
        Input("data-overlay-selector-environmental", "value"),
    ],
    prevent_initial_call=False,
)
def combine_metric_selections(basic, running, power, biomechanics, environmental):
    """Combine metric selections from all categories."""
    combined = []
    for category_selection in [basic, running, power, biomechanics, environmental]:
        if category_selection:
            combined.extend(category_selection)
    return combined


@callback(Output("activity-comments", "children"), Input("activity-data-store", "data"))
def update_activity_comments(store_data):
    """Update activity comments section with editable text area."""
    if not store_data or "activity_id" not in store_data:
        return ""

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            activity = session.query(Activity).filter_by(id=activity_id).first()

            if not activity:
                return ""

            comments_text = activity.comments or ""

            return dbc.Card(
                [
                    dbc.CardHeader(
                        [html.H6([html.I(className="fas fa-comment-alt me-2"), "Activity Comments"], className="mb-0")]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Textarea(
                                id="activity-comments-textarea",
                                placeholder="Add your comments about this activity...",
                                value=comments_text,
                                rows=3,
                                className="mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                [html.I(className="fas fa-save me-2"), "Save Comments"],
                                                id="save-comments-btn",
                                                color="primary",
                                                size="sm",
                                            )
                                        ],
                                        width="auto",
                                    ),
                                    dbc.Col([html.Div(id="comments-save-status")], width="auto"),
                                ]
                            ),
                        ]
                    ),
                ]
            )

    except Exception as e:
        return dbc.Alert(f"Error loading comments: {str(e)}", color="danger")


@callback(
    Output("comments-save-status", "children"),
    Input("save-comments-btn", "n_clicks"),
    [State("activity-comments-textarea", "value"), State("activity-data-store", "data")],
    prevent_initial_call=True,
)
def save_activity_comments(n_clicks, comments_text, store_data):
    """Save activity comments to database."""
    if not n_clicks or not store_data or "activity_id" not in store_data:
        return ""

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            activity = session.query(Activity).filter_by(id=activity_id).first()

            if not activity:
                return dbc.Alert("Activity not found", color="danger")

            activity.comments = comments_text
            session.commit()

            return dbc.Alert(
                [html.I(className="fas fa-check me-2"), "Comments saved successfully!"],
                color="success",
                dismissable=True,
                duration=3000,
            )

    except Exception as e:
        return dbc.Alert(
            [html.I(className="fas fa-exclamation-triangle me-2"), f"Error saving comments: {str(e)}"],
            color="danger",
            dismissable=True,
        )


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


@callback(Output("activity-summary", "children"), Input("activity-data-store", "data"))
def update_activity_summary(store_data):
    """Update activity summary with key metrics and available data types."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            activity = session.query(Activity).filter_by(id=activity_id).first()

            if not activity:
                return dbc.Alert(f"Activity {activity_id} not found", color="danger")

            # Get sample data to check what metrics are available
            samples = session.query(Sample).filter_by(activity_id=activity_id).limit(10).all()

            # Determine available metrics
            available_metrics = set()
            if samples:
                for sample in samples[:5]:  # Check first 5 samples
                    for attr in ["heart_rate", "speed_mps", "altitude_m", "power_w", "cadence_rpm", "temperature_c"]:
                        if getattr(sample, attr) is not None:
                            available_metrics.add(attr)

            # Check for GPS data
            has_gps = any(sample.latitude and sample.longitude for sample in samples[:5]) if samples else False

            # Create summary cards
            summary_cards = []

            # Distance card
            if activity.distance_m and activity.distance_m > 0:
                distance_km = activity.distance_m / 1000
                summary_cards.append(
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(f"{distance_km:.2f} km", className="text-primary mb-0"),
                                            html.P("Distance", className="text-muted mb-0"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=2,
                    )
                )

            # Duration card
            if activity.elapsed_time_s:
                hours = int(activity.elapsed_time_s // 3600)
                minutes = int((activity.elapsed_time_s % 3600) // 60)
                seconds = int(activity.elapsed_time_s % 60)
                duration_str = (
                    f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
                )
                summary_cards.append(
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(duration_str, className="text-success mb-0"),
                                            html.P("Duration", className="text-muted mb-0"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=2,
                    )
                )

            # Pace card (for running activities)
            if activity.avg_pace_s_per_km and activity.sport == "running":
                pace_min = int(activity.avg_pace_s_per_km // 60)
                pace_sec = int(activity.avg_pace_s_per_km % 60)
                pace_str = f"{pace_min}:{pace_sec:02d}"
                summary_cards.append(
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(f"{pace_str}/km", className="text-info mb-0"),
                                            html.P("Avg Pace", className="text-muted mb-0"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=2,
                    )
                )

            # Speed/Pace card
            if activity.avg_speed_mps:
                if activity.sport == "running":
                    # Show pace for running activities
                    pace_s_per_km = 1000 / activity.avg_speed_mps
                    pace_min = int(pace_s_per_km // 60)
                    pace_sec = int(pace_s_per_km % 60)
                    summary_cards.append(
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4(f"{pace_min}:{pace_sec:02d} /km", className="text-info mb-0"),
                                                html.P("Avg Pace", className="text-muted mb-0"),
                                            ],
                                            className="text-center",
                                        )
                                    ]
                                )
                            ],
                            width=2,
                        )
                    )
                else:
                    # Show speed for other activities
                    speed_kmh = activity.avg_speed_mps * 3.6
                    summary_cards.append(
                        dbc.Col(
                            [
                                dbc.Card(
                                    [
                                        dbc.CardBody(
                                            [
                                                html.H4(f"{speed_kmh:.1f} km/h", className="text-info mb-0"),
                                                html.P("Avg Speed", className="text-muted mb-0"),
                                            ],
                                            className="text-center",
                                        )
                                    ]
                                )
                            ],
                            width=2,
                        )
                    )

            # Heart Rate card
            if activity.avg_hr:
                summary_cards.append(
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(f"{activity.avg_hr} bpm", className="text-danger mb-0"),
                                            html.P("Avg Heart Rate", className="text-muted mb-0"),
                                        ],
                                        className="text-center",
                                    )
                                ]
                            )
                        ],
                        width=2,
                    )
                )

            # Available data types card
            metric_labels = {
                "heart_rate": "HR",
                "speed_mps": "Speed",
                "altitude_m": "Elevation",
                "power_w": "Power",
                "cadence_rpm": "Cadence",
                "temperature_c": "Temperature",
            }
            available_labels = [metric_labels.get(metric, metric) for metric in available_metrics]
            if has_gps:
                available_labels.append("GPS")

            data_types_str = ", ".join(available_labels) if available_labels else "Heart Rate only"
            summary_cards.append(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H6("Available Data", className="text-muted mb-1"),
                                        html.P(data_types_str, className="mb-0 small"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=4,
                )
            )

            return dbc.Row(summary_cards)

    except Exception as e:
        return dbc.Alert(f"Error loading summary: {str(e)}", color="danger")


@callback(
    Output("activity-charts", "children"),
    [Input("activity-data-store", "data"), Input("combined-metric-selection", "data")],
    prevent_initial_call=False,
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

            # Convert to DataFrame with all metrics and pace calculation
            sample_data = []
            for sample in samples:
                # Calculate pace from speed (min/km)
                pace_per_km = None
                if sample.speed_mps and sample.speed_mps > 0:
                    pace_per_km = (1000 / sample.speed_mps) / 60  # Convert to minutes per km

                sample_data.append(
                    {
                        "time": sample.elapsed_time_s / 60,  # Convert to minutes
                        # Basic metrics
                        "heart_rate": sample.heart_rate,
                        "pace_per_km": pace_per_km,
                        "speed_mps": sample.speed_mps,
                        "altitude_m": sample.altitude_m,
                        "cadence_rpm": sample.cadence_rpm,
                        "power_w": sample.power_w,
                        "temperature_c": sample.temperature_c,
                        # Advanced running dynamics
                        "vertical_oscillation_mm": sample.vertical_oscillation_mm,
                        "vertical_ratio": sample.vertical_ratio,
                        "ground_contact_time_ms": sample.ground_contact_time_ms,
                        "ground_contact_balance_pct": sample.ground_contact_balance_pct,
                        "step_length_mm": sample.step_length_mm,
                        # Power metrics
                        "air_power_w": sample.air_power_w,
                        "form_power_w": sample.form_power_w,
                        # Biomechanics
                        "leg_spring_stiffness": sample.leg_spring_stiffness,
                        "impact_loading_rate": sample.impact_loading_rate,
                        # Environmental
                        "stryd_temperature_c": sample.stryd_temperature_c,
                        "stryd_humidity_pct": sample.stryd_humidity_pct,
                    }
                )

            df = pd.DataFrame(sample_data)

            # Create multi-axis plot
            fig = go.Figure()

            # Define colors and labels for each metric (matching the selector)
            metric_config = {
                # Basic metrics
                "heart_rate": {"color": "red", "name": "Heart Rate", "unit": "bpm"},
                "pace_per_km": {"color": "blue", "name": "Pace", "unit": "min/km"},
                "speed_mps": {"color": "blue", "name": "Speed", "unit": "m/s"},
                "altitude_m": {"color": "brown", "name": "Altitude", "unit": "m"},
                "cadence_rpm": {"color": "purple", "name": "Cadence", "unit": "rpm"},
                "power_w": {"color": "orange", "name": "Power", "unit": "W"},
                "temperature_c": {"color": "darkgreen", "name": "Temperature", "unit": "°C"},
                # Advanced running dynamics
                "vertical_oscillation_mm": {"color": "darkred", "name": "Vertical Oscillation", "unit": "mm"},
                "vertical_ratio": {"color": "darkblue", "name": "Vertical Ratio", "unit": "%"},
                "ground_contact_time_ms": {"color": "darkgray", "name": "Ground Contact Time", "unit": "ms"},
                "ground_contact_balance_pct": {"color": "darkmagenta", "name": "Ground Contact Balance", "unit": "%"},
                "step_length_mm": {"color": "darkorange", "name": "Step Length", "unit": "mm"},
                # Power metrics
                "air_power_w": {"color": "lightblue", "name": "Air Power", "unit": "W"},
                "form_power_w": {"color": "darkturquoise", "name": "Form Power", "unit": "W"},
                # Biomechanics
                "leg_spring_stiffness": {"color": "maroon", "name": "Leg Spring Stiffness", "unit": ""},
                "impact_loading_rate": {"color": "crimson", "name": "Impact Loading Rate", "unit": ""},
                # Environmental
                "stryd_temperature_c": {"color": "forestgreen", "name": "Stryd Temperature", "unit": "°C"},
                "stryd_humidity_pct": {"color": "steelblue", "name": "Stryd Humidity", "unit": "%"},
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

                        valid_traces.append({"metric": metric, "yaxis": yaxis_ref, "config": metric_config[metric]})
                        axes_used.append(yaxis_ref)

            if not valid_traces:
                return dbc.Alert(
                    "No data available for the selected metrics. Please select different metrics from the available options.",
                    color="warning",
                )

            # Configure layout with proper multi-axis formatting
            layout_config = {
                "title": {"text": "Activity Data Over Time", "x": 0.5, "font": {"size": 16}},
                "xaxis": {
                    "title": "Time (minutes)",
                    "showgrid": True,
                    "gridcolor": "rgba(128,128,128,0.2)",
                },
                "height": 600,
                "hovermode": "x unified",
                "legend": {"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "center", "x": 0.5},
                "margin": {"l": 60, "r": 60, "t": 80, "b": 60},
            }

            # Configure multiple y-axes
            for i, trace in enumerate(valid_traces):
                yaxis_key = "yaxis" if i == 0 else f"yaxis{i+1}"

                axis_config = {
                    "title": {
                        "text": f"{trace['config']['name']} ({trace['config']['unit']})",
                        "font": {"color": trace["config"]["color"]},
                    },
                    "tickfont": {"color": trace["config"]["color"]},
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
                        axis_config["position"] = 1.0 - (i - 1) * 0.08

                layout_config[yaxis_key] = axis_config

            fig.update_layout(**layout_config)

            if not selected_metrics or all(metric not in df.columns for metric in selected_metrics):
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


@callback(Output("activity-laps", "children"), Input("activity-data-store", "data"))
def update_activity_laps(store_data):
    """Update activity lap splits table."""
    if not store_data or "activity_id" not in store_data:
        return dbc.Alert("No activity data", color="warning")

    activity_id = store_data["activity_id"]

    try:
        with session_scope() as session:
            # Get lap data
            laps = session.query(Lap).filter_by(activity_id=activity_id).order_by(Lap.lap_index).all()

            if not laps:
                return dbc.Alert("No lap data available for this activity", color="info")

            # Create lap splits table
            table_header = [
                html.Thead(
                    [
                        html.Tr(
                            [
                                html.Th("Lap", style={"width": "10%"}),
                                html.Th("Distance", style={"width": "15%"}),
                                html.Th("Time", style={"width": "15%"}),
                                html.Th("Avg HR", style={"width": "15%"}),
                                html.Th("Max HR", style={"width": "15%"}),
                                html.Th("Avg Power", style={"width": "15%"}),
                                html.Th("Avg Speed", style={"width": "15%"}),
                            ]
                        )
                    ]
                )
            ]

            table_rows = []
            for lap in laps:
                # Format lap time
                if lap.elapsed_time_s:
                    minutes = int(lap.elapsed_time_s // 60)
                    seconds = int(lap.elapsed_time_s % 60)
                    time_str = f"{minutes}:{seconds:02d}"
                else:
                    time_str = "N/A"

                # Format distance
                distance_str = f"{lap.distance_m/1000:.2f} km" if lap.distance_m else "N/A"

                # Format speed/pace
                speed_mps = lap.avg_speed_mps
                # Calculate speed if not stored but distance and time available
                if not speed_mps and lap.distance_m and lap.elapsed_time_s and lap.elapsed_time_s > 0:
                    speed_mps = lap.distance_m / lap.elapsed_time_s

                if speed_mps:
                    # Get activity to check sport type
                    activity = session.query(Activity).filter_by(id=activity_id).first()
                    if activity and activity.sport == "running":
                        # Show pace for running
                        pace_s_per_km = 1000 / speed_mps
                        pace_min = int(pace_s_per_km // 60)
                        pace_sec = int(pace_s_per_km % 60)
                        speed_str = f"{pace_min}:{pace_sec:02d}/km"
                    else:
                        # Show speed for other activities
                        speed_kmh = speed_mps * 3.6
                        speed_str = f"{speed_kmh:.1f} km/h"
                else:
                    speed_str = "N/A"

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(f"{lap.lap_index + 1}"),
                            html.Td(distance_str),
                            html.Td(time_str),
                            html.Td(f"{lap.avg_hr}" if lap.avg_hr else "N/A"),
                            html.Td(f"{lap.max_hr}" if lap.max_hr else "N/A"),
                            html.Td(f"{lap.avg_power_w:.0f}W" if lap.avg_power_w else "N/A"),
                            html.Td(speed_str),
                        ]
                    )
                )

            table_body = [html.Tbody(table_rows)]

            return dbc.Table(
                table_header + table_body, bordered=True, hover=True, responsive=True, striped=True, className="mb-0"
            )

    except Exception as e:
        return dbc.Alert(f"Error loading lap splits: {str(e)}", color="danger")
