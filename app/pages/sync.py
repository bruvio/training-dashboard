"""
Enhanced Garmin Data Sync Page with Calendar Widget and Smoothing Options.

This page provides a user-friendly interface for syncing Garmin Connect data
with calendar-based date selection and data aggregation options.
"""

from datetime import date, datetime, timedelta
import threading

from dash import Input, Output, State, callback, dcc, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go

from ..services.garmin_integration_service import GarminIntegrationService
from ..services.wellness_data_service import WellnessDataService
from ..utils import get_logger

logger = get_logger(__name__)

# Global progress tracking for the sync page
_sync_progress = {"status": "idle", "message": "", "progress": 0, "details": [], "result": None}


def update_sync_progress(status: str, message: str, progress: int = 0, details: list = None):
    """Update global sync progress."""
    global _sync_progress
    _sync_progress.update(
        {
            "status": status,
            "message": message,
            "progress": progress,
            "details": details or [],
            "result": None if status in ["idle", "running"] else _sync_progress.get("result"),
        }
    )
    logger.info(f"Sync progress updated: {status} - {message} ({progress}%)")


def layout():
    """Enhanced sync page layout with calendar widgets and progress tracking."""
    return dbc.Container(
        [
            # Progress tracking components
            dcc.Interval(id="sync-progress-interval", interval=500, disabled=True),
            dcc.Store(id="sync-progress-store"),
            # Header Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                [
                                    html.I(className="fas fa-sync-alt me-3", style={"color": "#28a745"}),
                                    "Garmin Data Sync",
                                ],
                                className="mb-4 text-center",
                            ),
                            html.P(
                                "Sync your Garmin Connect health data with calendar-based date selection and smoothing options.",
                                className="text-muted text-center mb-4",
                            ),
                        ]
                    )
                ]
            ),
            # Main Sync Configuration Card
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.H5(
                                                [html.I(className="fas fa-calendar-alt me-2"), "Sync Configuration"],
                                                className="mb-0",
                                            )
                                        ]
                                    ),
                                    dbc.CardBody(
                                        [
                                            # Date Range Selection
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label("Start Date", className="form-label fw-bold"),
                                                            dcc.DatePickerSingle(
                                                                id="sync-start-date",
                                                                date=date.today() - timedelta(days=30),
                                                                display_format="YYYY-MM-DD",
                                                                first_day_of_week=1,  # Monday
                                                                style={"width": "100%"},
                                                                className="form-control",
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label("End Date", className="form-label fw-bold"),
                                                            dcc.DatePickerSingle(
                                                                id="sync-end-date",
                                                                date=date.today(),
                                                                display_format="YYYY-MM-DD",
                                                                first_day_of_week=1,
                                                                style={"width": "100%"},
                                                                className="form-control",
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Date Range Summary
                                            html.Div(id="sync-date-summary", className="mb-3"),
                                            html.Hr(),
                                            # Data Aggregation Options
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Data Aggregation", className="form-label fw-bold"
                                                            ),
                                                            dcc.Dropdown(
                                                                id="sync-smoothing",
                                                                options=[
                                                                    {
                                                                        "label": "📊 Raw Data (No Smoothing)",
                                                                        "value": "none",
                                                                    },
                                                                    {"label": "📈 Daily Average", "value": "day"},
                                                                    {"label": "📅 Weekly Average", "value": "week"},
                                                                    {"label": "📆 Monthly Average", "value": "month"},
                                                                    {"label": "🗓️ Yearly Average", "value": "year"},
                                                                ],
                                                                value="none",
                                                                placeholder="Select aggregation method",
                                                                className="mb-3",
                                                            ),
                                                            html.Small(
                                                                "Choose how to aggregate your data. Raw data provides the most detail, "
                                                                "while averaging can help identify trends over longer periods.",
                                                                className="text-muted",
                                                            ),
                                                        ],
                                                        md=12,
                                                    )
                                                ]
                                            ),
                                            html.Hr(),
                                            # Sync Button
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Button(
                                                                [
                                                                    html.I(className="fas fa-download me-2"),
                                                                    "Sync Garmin Data",
                                                                ],
                                                                id="sync-data-btn",
                                                                color="primary",
                                                                size="lg",
                                                                className="w-100",
                                                                disabled=False,
                                                            )
                                                        ],
                                                        md=12,
                                                    )
                                                ]
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            )
                        ],
                        lg=8,
                        className="mx-auto",
                    )
                ]
            ),
            # Progress Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    # Sync Progress Bar
                                    html.Div(id="wellness-sync-progress-container", style={"display": "none"}),
                                    # Sync Status Messages
                                    html.Div(id="sync-status-messages"),
                                    # Sync Results
                                    html.Div(id="sync-results-container"),
                                ]
                            )
                        ],
                        lg=8,
                        className="mx-auto",
                    )
                ]
            ),
            # Data Summary Section
            dbc.Row([dbc.Col([html.Div(id="data-summary-container")], lg=10, className="mx-auto")], className="mt-4"),
            # Wellness Data Visualization Section
            dbc.Row(
                [
                    dbc.Col(
                        [html.Div(id="wellness-charts-container", style={"display": "none"})],
                        lg=12,
                        className="mx-auto",
                    )
                ],
                className="mt-4",
            ),
        ]
    )


@callback(Output("sync-date-summary", "children"), [Input("sync-start-date", "date"), Input("sync-end-date", "date")])
def update_date_summary(start_date, end_date):
    """Update the date range summary display."""
    if not start_date or not end_date:
        return ""

    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        days = (end - start).days + 1

        if days <= 0:
            return dbc.Alert("⚠️ End date must be after start date", color="warning", className="mb-0")

        return dbc.Alert(
            [
                html.Strong(f"📅 Date Range: "),
                f"{start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')} ",
                html.Span(f"({days} days)", className="text-muted"),
            ],
            color="info",
            className="mb-0",
        )

    except Exception:
        return dbc.Alert("⚠️ Invalid date format", color="warning", className="mb-0")


@callback(
    [
        Output("sync-progress-interval", "disabled"),
        Output("sync-data-btn", "disabled"),
        Output("sync-data-btn", "children"),
    ],
    Input("sync-data-btn", "n_clicks"),
    [
        State("sync-start-date", "date"),
        State("sync-end-date", "date"),
        State("sync-smoothing", "value"),
    ],
    prevent_initial_call=True,
)
def start_sync_data(n_clicks, start_date, end_date, smoothing):
    """Start sync in background thread and enable progress tracking."""
    if not n_clicks:
        raise PreventUpdate

    # Validate inputs
    if not start_date or not end_date:
        return True, False, [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]

    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()
    days = (end - start).days + 1

    if days <= 0 or days > 365:
        return True, False, [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]

    # Reset progress and start background sync
    update_sync_progress("running", "Starting sync...", 5)

    def run_sync():
        """Background sync function with progress updates."""
        try:
            update_sync_progress("running", "Initializing Garmin connection...", 10)

            # Initialize GarminIntegrationService for database persistence
            garmin_service = GarminIntegrationService()

            update_sync_progress("running", f"Fetching and persisting {days} days of wellness data...", 30)

            # Use GarminIntegrationService to sync and persist data
            sync_result = garmin_service.sync_wellness_data_range(
                start_date=start, end_date=end, smoothing=smoothing or "none"
            )

            # Data is already persisted - charts will use database queries
            if sync_result.get("success"):
                update_sync_progress("running", "Data successfully persisted to database...", 70)

            # Store result in global progress
            global _sync_progress
            _sync_progress["result"] = sync_result

            if sync_result.get("success"):
                details = [
                    f"Days synced: {sync_result.get('days_synced', days)}",
                    f"Records: {sync_result.get('records_synced', 0)}",
                    f"Data types: {sync_result.get('data_types_synced', 0)}",
                ]
                update_sync_progress("completed", "Sync completed successfully!", 100, details)
            else:
                update_sync_progress("error", f"Sync failed: {sync_result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Background sync error: {e}")
            update_sync_progress("error", f"Sync error: {str(e)}")

    # Start background sync
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()

    return (
        False,  # Enable progress interval
        True,  # Disable sync button
        [html.I(className="fas fa-spinner fa-spin me-2"), "Syncing..."],
    )


# Progress monitoring callback
@callback(
    [
        Output("sync-results-container", "children"),
        Output("wellness-sync-progress-container", "children"),
        Output("wellness-sync-progress-container", "style"),
        Output("sync-status-messages", "children"),
        Output("sync-data-btn", "disabled", allow_duplicate=True),
        Output("sync-data-btn", "children", allow_duplicate=True),
        Output("sync-progress-interval", "disabled", allow_duplicate=True),
    ],
    Input("sync-progress-interval", "n_intervals"),
    prevent_initial_call=True,
)
def update_sync_progress_display(n_intervals):
    """Update the sync progress display in real-time."""
    if _sync_progress["status"] == "idle":
        return (
            "",
            "",
            {"display": "none"},
            "",
            False,
            [html.I(className="fas fa-download me-2"), "Sync Garmin Data"],
            True,
        )

    # Progress bar
    progress_bar = dbc.Progress(
        value=_sync_progress["progress"],
        striped=True,
        animated=_sync_progress["status"] == "running",
        color=(
            "success"
            if _sync_progress["status"] == "completed"
            else ("danger" if _sync_progress["status"] == "error" else "info")
        ),
        className="mb-2",
    )

    # Progress details
    details_list = []
    if _sync_progress.get("details"):
        for detail in _sync_progress["details"]:
            details_list.append(html.Li(detail))

    progress_content = [
        html.H6(f"{_sync_progress['message']} ({_sync_progress['progress']}%)", className="mb-2"),
        progress_bar,
    ]

    if details_list:
        progress_content.append(html.Ul(details_list, className="small"))

    # Handle completion
    if _sync_progress["status"] == "completed":
        sync_result = _sync_progress.get("result", {})

        # Success result card
        if sync_result and sync_result.get("success"):
            persistence = sync_result.get("persistence", {})
            successful_types = sum(1 for success in persistence.values() if success)

            result_card = dbc.Card(
                [
                    dbc.CardHeader(
                        [html.I(className="fas fa-check-circle text-success me-2"), "Sync Completed Successfully"]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H6("Days Synced", className="text-muted"),
                                            html.H4(str(sync_result.get("days_synced", 0)), className="text-primary"),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H6("Records Synced", className="text-muted"),
                                            html.H4(
                                                str(sync_result.get("records_synced", 0)), className="text-success"
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H6("Data Types", className="text-muted"),
                                            html.H4(
                                                str(sync_result.get("data_types_synced", successful_types)),
                                                className="text-info",
                                            ),
                                        ],
                                        md=3,
                                    ),
                                    dbc.Col(
                                        [
                                            html.H6("Status", className="text-muted"),
                                            html.P("✅ Complete", className="text-success small"),
                                        ],
                                        md=3,
                                    ),
                                ]
                            ),
                            html.Hr(),
                            html.P(
                                sync_result.get("message", "Data synced successfully"),
                                className="text-muted text-center mb-0",
                            ),
                        ]
                    ),
                ],
                color="success",
                outline=True,
            )
        else:
            result_card = dbc.Alert("Sync completed with unknown result", color="info")

        return (
            result_card,
            progress_content,
            {"display": "block"},
            dbc.Alert([html.I(className="fas fa-check-circle me-2"), "Sync completed successfully!"], color="success"),
            False,  # Re-enable button
            [html.I(className="fas fa-download me-2"), "Sync Garmin Data"],
            True,  # Disable progress interval
        )

    elif _sync_progress["status"] == "error":
        error_msg = _sync_progress.get("message", "Unknown error")

        if "authentication" in error_msg.lower() or "not authenticated" in error_msg.lower():
            result_card = dbc.Alert(
                [
                    html.H5([html.I(className="fas fa-key me-2"), "Authentication Required"]),
                    html.P("You need to authenticate with Garmin Connect first."),
                    html.P(f"Error: {error_msg}", className="text-muted small"),
                    html.Hr(),
                    dbc.Button(
                        [html.I(className="fas fa-sign-in-alt me-2"), "Go to Garmin Login"],
                        href="/garmin",
                        color="primary",
                    ),
                ],
                color="warning",
            )
        else:
            result_card = dbc.Alert(
                [
                    html.H5("Sync Failed"),
                    html.P(f"Error: {error_msg}"),
                    html.Hr(),
                    html.Small("Try refreshing the page and attempting the sync again."),
                ],
                color="danger",
            )

        return (
            result_card,
            progress_content,
            {"display": "block"},
            dbc.Alert(
                [html.I(className="fas fa-exclamation-triangle me-2"), f"Sync failed: {error_msg}"], color="danger"
            ),
            False,  # Re-enable button
            [html.I(className="fas fa-download me-2"), "Sync Garmin Data"],
            True,  # Disable progress interval
        )

    # Still running
    return (
        "",
        progress_content,
        {"display": "block"},
        dbc.Alert([html.I(className="fas fa-spinner fa-spin me-2"), _sync_progress["message"]], color="info"),
        True,  # Keep button disabled
        [html.I(className="fas fa-spinner fa-spin me-2"), "Syncing..."],
        False,  # Keep progress interval enabled
    )


@callback(
    Output("data-summary-container", "children"), Input("sync-results-container", "children"), prevent_initial_call=True
)
def update_data_summary(sync_results):
    """Update data summary after sync completion."""
    if not sync_results:
        raise PreventUpdate

    try:
        # Get current data summary from WellnessDataService
        wellness_service = WellnessDataService()
        summary = wellness_service.get_wellness_summary(days=30)

        if not summary or summary.get("total_records", 0) == 0:
            return dbc.Alert("No wellness data found. Try syncing some data first.", color="info")

        # Create summary cards
        data_cards = []
        data_availability = summary.get("data_availability", {})

        for data_type, count in data_availability.items():
            if count > 0:
                icon_map = {
                    "sleep": "fas fa-moon",
                    "steps": "fas fa-walking",
                    "heart_rate": "fas fa-heartbeat",
                    "body_battery": "fas fa-battery-three-quarters",
                    "stress": "fas fa-brain",
                }

                card = dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H4(
                                            [
                                                html.I(
                                                    className=f"{icon_map.get(data_type, 'fas fa-chart-line')} me-2"
                                                ),
                                                str(count),
                                            ],
                                            className="text-center text-primary",
                                        ),
                                        html.P(
                                            data_type.replace("_", " ").title(),
                                            className="text-center text-muted small mb-0",
                                        ),
                                    ]
                                )
                            ],
                            className="h-100",
                        )
                    ],
                    md=2,
                )
                data_cards.append(card)

        if data_cards:
            return dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.H5(
                                [html.I(className="fas fa-chart-bar me-2"), "Current Data Summary (Last 30 Days)"],
                                className="mb-0",
                            )
                        ]
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(data_cards),
                            html.Hr(),
                            html.P(
                                [
                                    f"Total Records: {summary.get('total_records', 0)} | ",
                                    f"Coverage: {summary.get('coverage_percentage', 0):.1f}%",
                                ],
                                className="text-center text-muted mb-0",
                            ),
                        ]
                    ),
                ]
            )
        else:
            return ""

    except Exception as e:
        logger.error(f"Error updating data summary: {e}")
        return dbc.Alert(f"Could not load data summary: {str(e)}", color="warning")


def create_wellness_chart(df, title, y_columns):
    """Create a simple wellness data chart using plotly."""
    if df.empty:
        return dbc.Alert(f"No data available for {title}", color="info", className="text-center")

    # Prepare data
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Create simple chart
    fig = go.Figure()

    # Add a trace for each metric that has data
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8"]

    for i, col in enumerate(y_columns):
        if col not in df.columns:
            continue

        # Get data that's not null
        data = df[df[col].notna()]
        if data.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data[col],
                mode="lines+markers",
                name=col.replace("_", " ").title(),
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
            )
        )

    fig.update_layout(title=title, xaxis_title="Date", yaxis_title="Value", height=400, showlegend=True)

    return dcc.Graph(figure=fig)


@callback(
    Output("wellness-charts-container", "children"),
    Output("wellness-charts-container", "style"),
    Input("sync-results-container", "children"),
    prevent_initial_call=True,
)
def update_wellness_charts(sync_results):
    """Display wellness data charts after successful sync using same queries as stats page."""
    if not sync_results:
        raise PreventUpdate

    sync_result = _sync_progress.get("result", {})

    logger.info(f"Chart callback triggered. Sync result keys: {list(sync_result.keys()) if sync_result else 'None'}")

    if not sync_result or not sync_result.get("success", False):
        logger.warning("Sync not successful, not showing charts")
        return "", {"display": "none"}

    # Use the same database queries that the stats page uses
    try:
        from ..data.web_queries import get_body_battery_data, get_heart_rate_data, get_sleep_data

        charts = []

        # Sleep data chart (same as stats page)
        sleep_df = get_sleep_data(days=7)
        if not sleep_df.empty:
            sleep_fig = go.Figure()

            has_sleep_data = False

            # Sleep score (if available)
            if "sleep_score" in sleep_df.columns and sleep_df["sleep_score"].notna().any():
                sleep_fig.add_trace(
                    go.Scatter(
                        x=sleep_df.index,
                        y=sleep_df["sleep_score"],
                        mode="lines+markers",
                        name="Sleep Score",
                        line=dict(color="blue", width=2),
                        hovertemplate="<b>%{x}</b><br>Sleep Score: %{y}<extra></extra>",
                    )
                )
                has_sleep_data = True

            # Sleep efficiency (calculated from sleep stages)
            if "efficiency_percentage" in sleep_df.columns and sleep_df["efficiency_percentage"].notna().any():
                sleep_fig.add_trace(
                    go.Scatter(
                        x=sleep_df.index,
                        y=sleep_df["efficiency_percentage"],
                        mode="lines+markers",
                        name="Sleep Efficiency (%)",
                        line=dict(color="green", width=2),
                        hovertemplate="<b>%{x}</b><br>Efficiency: %{y}%<extra></extra>",
                    )
                )
                has_sleep_data = True

            if has_sleep_data:
                sleep_fig.update_layout(
                    title="Sleep Quality & Efficiency",
                    xaxis_title="Date",
                    yaxis_title="Score/Percentage",
                    height=400,
                    hovermode="x unified",
                )

                charts.append(dbc.Card([dbc.CardBody([dcc.Graph(figure=sleep_fig)])], className="mb-4"))
                logger.info("Created sleep chart from database data")

        # Heart Rate data chart (same as stats page) - use 30 days to capture more VO2 Max data
        hr_df = get_heart_rate_data(days=30)
        if not hr_df.empty:
            hr_fig = go.Figure()

            # Resting HR
            if "resting_hr" in hr_df.columns and hr_df["resting_hr"].notna().any():
                hr_fig.add_trace(
                    go.Scatter(
                        x=hr_df.index,
                        y=hr_df["resting_hr"],
                        mode="lines+markers",
                        name="Resting HR",
                        line=dict(color="red", width=2),
                        hovertemplate="<b>%{x}</b><br>Resting HR: %{y} bpm<extra></extra>",
                    )
                )

            # VO2 Max
            if "vo2max" in hr_df.columns and hr_df["vo2max"].notna().any():
                vo2_data = hr_df["vo2max"].dropna()
                hr_fig.add_trace(
                    go.Scatter(
                        x=vo2_data.index,
                        y=vo2_data.values,
                        mode="lines+markers",
                        name="VO2 Max",
                        line=dict(color="green", width=2),
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>VO2 Max: %{y} ml/kg/min<extra></extra>",
                    )
                )

            # HRV - create separate chart for better scaling
            hrv_chart_created = False
            if "hrv_score" in hr_df.columns and hr_df["hrv_score"].notna().any():
                hrv_data = hr_df["hrv_score"].dropna()
                hr_fig.add_trace(
                    go.Scatter(
                        x=hrv_data.index,
                        y=hrv_data.values,
                        mode="lines+markers",
                        name="HRV Score",
                        line=dict(color="purple", width=2),
                        marker=dict(size=8),
                        hovertemplate="<b>%{x}</b><br>HRV Score: %{y}<extra></extra>",
                        yaxis="y2",
                    )
                )
                hrv_chart_created = True

            # Update layout with dual y-axes if HRV data exists
            if hrv_chart_created:
                hr_fig.update_layout(
                    title="Heart Rate, VO2 Max & HRV",
                    xaxis_title="Date",
                    yaxis=dict(title="HR (bpm) / VO2 Max (ml/kg/min)", side="left"),
                    yaxis2=dict(title="HRV Score", side="right", overlaying="y"),
                    height=400,
                    hovermode="x unified",
                )
            else:
                hr_fig.update_layout(
                    title="Heart Rate & VO2 Max",
                    xaxis_title="Date",
                    yaxis_title="HR (bpm) / VO2 Max (ml/kg/min)",
                    height=400,
                    hovermode="x unified",
                )

            charts.append(dbc.Card([dbc.CardBody([dcc.Graph(figure=hr_fig)])], className="mb-4"))
            logger.info("Created heart rate chart from database data")

        # Body Battery chart (same as stats page)
        bb_df = get_body_battery_data(days=7)
        if not bb_df.empty:
            bb_fig = go.Figure()

            bb_fig.add_trace(
                go.Scatter(
                    x=bb_df.index,
                    y=bb_df["body_battery_score"],
                    mode="markers",
                    name="Daily Score",
                    marker=dict(color="lightgreen", size=6),
                    hovertemplate="<b>%{x}</b><br>Body Battery: %{y}<extra></extra>",
                )
            )

            if "bb_7d_avg" in bb_df.columns:
                bb_fig.add_trace(
                    go.Scatter(
                        x=bb_df.index,
                        y=bb_df["bb_7d_avg"],
                        mode="lines",
                        name="7-day Average",
                        line=dict(color="green", width=2),
                        hovertemplate="<b>%{x}</b><br>7-day Average: %{y:.1f}<extra></extra>",
                    )
                )

            bb_fig.update_layout(
                title="Body Battery Energy Levels",
                xaxis_title="Date",
                yaxis_title="Body Battery Score (0-100)",
                height=400,
                hovermode="x unified",
            )

            charts.append(dbc.Card([dbc.CardBody([dcc.Graph(figure=bb_fig)])], className="mb-4"))
            logger.info("Created body battery chart from database data")

        if not charts:
            logger.warning("No charts created from database data")
            return dbc.Alert("No wellness data available in database", color="info"), {"display": "block"}

        logger.info(f"Returning {len(charts)} charts from database data")
        return charts, {"display": "block"}

    except Exception as e:
        logger.error(f"Error creating charts from database data: {e}")
        return dbc.Alert(f"Error loading charts: {str(e)}", color="danger"), {"display": "block"}
