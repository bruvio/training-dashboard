"""
Enhanced Garmin Data Sync Page with Calendar Widget and Smoothing Options.

This page provides a user-friendly interface for syncing Garmin Connect data
with calendar-based date selection and data aggregation options.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate

from ..services.wellness_data_service import WellnessDataService
from ..services.garmin_integration_service import GarminIntegrationService
from ..utils import get_logger

logger = get_logger(__name__)


def layout():
    """Enhanced sync page layout with calendar widgets and progress tracking."""
    return dbc.Container([
        # Header Section
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="fas fa-sync-alt me-3", style={"color": "#28a745"}),
                    "Garmin Data Sync"
                ], className="mb-4 text-center"),
                html.P(
                    "Sync your Garmin Connect health data with calendar-based date selection and smoothing options.",
                    className="text-muted text-center mb-4"
                )
            ])
        ]),
        
        # Main Sync Configuration Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-calendar-alt me-2"),
                            "Sync Configuration"
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Date Range Selection
                        dbc.Row([
                            dbc.Col([
                                html.Label("Start Date", className="form-label fw-bold"),
                                dcc.DatePickerSingle(
                                    id="sync-start-date",
                                    date=date.today() - timedelta(days=30),
                                    display_format="YYYY-MM-DD",
                                    first_day_of_week=1,  # Monday
                                    style={"width": "100%"},
                                    className="form-control"
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("End Date", className="form-label fw-bold"),
                                dcc.DatePickerSingle(
                                    id="sync-end-date", 
                                    date=date.today(),
                                    display_format="YYYY-MM-DD",
                                    first_day_of_week=1,
                                    style={"width": "100%"},
                                    className="form-control"
                                )
                            ], md=6),
                        ], className="mb-3"),
                        
                        # Date Range Summary
                        html.Div(id="sync-date-summary", className="mb-3"),
                        
                        html.Hr(),
                        
                        # Data Aggregation Options
                        dbc.Row([
                            dbc.Col([
                                html.Label("Data Aggregation", className="form-label fw-bold"),
                                dcc.Dropdown(
                                    id="sync-smoothing",
                                    options=[
                                        {"label": "📊 Raw Data (No Smoothing)", "value": "none"},
                                        {"label": "📈 Daily Average", "value": "day"},
                                        {"label": "📅 Weekly Average", "value": "week"},
                                        {"label": "📆 Monthly Average", "value": "month"},
                                        {"label": "🗓️ Yearly Average", "value": "year"}
                                    ],
                                    value="none",
                                    placeholder="Select aggregation method",
                                    className="mb-3"
                                ),
                                html.Small(
                                    "Choose how to aggregate your data. Raw data provides the most detail, "
                                    "while averaging can help identify trends over longer periods.",
                                    className="text-muted"
                                )
                            ], md=12)
                        ]),
                        
                        html.Hr(),
                        
                        # Sync Options
                        dbc.Row([
                            dbc.Col([
                                html.Label("Sync Options", className="form-label fw-bold"),
                                dbc.Checklist(
                                    id="sync-options",
                                    options=[
                                        {"label": "Include Wellness Data", "value": "wellness"},
                                        {"label": "Download FIT Files", "value": "fit_files"},
                                        {"label": "Overwrite Existing Data", "value": "overwrite"}
                                    ],
                                    value=["wellness"],  # Default to wellness data
                                    className="mb-3"
                                )
                            ], md=12)
                        ]),
                        
                        # Sync Button
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-download me-2"),
                                        "Sync Garmin Data"
                                    ],
                                    id="sync-data-btn",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                    disabled=False
                                )
                            ], md=12)
                        ])
                    ])
                ], className="mb-4")
            ], lg=8, className="mx-auto")
        ]),
        
        # Progress Section
        dbc.Row([
            dbc.Col([
                html.Div([
                    # Sync Progress Bar
                    html.Div(id="sync-progress-container", style={"display": "none"}),
                    
                    # Sync Status Messages
                    html.Div(id="sync-status-messages"),
                    
                    # Sync Results
                    html.Div(id="sync-results-container")
                ])
            ], lg=8, className="mx-auto")
        ]),
        
        # Data Summary Section
        dbc.Row([
            dbc.Col([
                html.Div(id="data-summary-container")
            ], lg=10, className="mx-auto")
        ], className="mt-4")
    ])


@callback(
    Output("sync-date-summary", "children"),
    [Input("sync-start-date", "date"), Input("sync-end-date", "date")]
)
def update_date_summary(start_date, end_date):
    """Update the date range summary display."""
    if not start_date or not end_date:
        return ""
    
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        days = (end - start).days + 1
        
        if days <= 0:
            return dbc.Alert(
                "⚠️ End date must be after start date", 
                color="warning", 
                className="mb-0"
            )
        
        return dbc.Alert([
            html.Strong(f"📅 Date Range: "),
            f"{start.strftime('%B %d, %Y')} to {end.strftime('%B %d, %Y')} ",
            html.Span(f"({days} days)", className="text-muted")
        ], color="info", className="mb-0")
        
    except Exception:
        return dbc.Alert(
            "⚠️ Invalid date format", 
            color="warning", 
            className="mb-0"
        )


@callback(
    [Output("sync-results-container", "children"),
     Output("sync-progress-container", "children"),
     Output("sync-progress-container", "style"),
     Output("sync-status-messages", "children"),
     Output("sync-data-btn", "disabled"),
     Output("sync-data-btn", "children")],
    Input("sync-data-btn", "n_clicks"),
    [State("sync-start-date", "date"),
     State("sync-end-date", "date"), 
     State("sync-smoothing", "value"),
     State("sync-options", "value")],
    prevent_initial_call=True
)
def handle_sync_data(n_clicks, start_date, end_date, smoothing, sync_options):
    """Handle data sync with progress tracking and results display."""
    if not n_clicks:
        raise PreventUpdate
    
    try:
        # Validate inputs
        if not start_date or not end_date:
            return (
                dbc.Alert("Please select both start and end dates", color="danger"),
                "", {"display": "none"}, "", False,
                [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]
            )
        
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        days = (end - start).days + 1
        
        if days <= 0:
            return (
                dbc.Alert("End date must be after start date", color="danger"),
                "", {"display": "none"}, "", False,
                [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]
            )
        
        if days > 365:
            return (
                dbc.Alert("Maximum sync period is 365 days. Please select a shorter range.", color="warning"),
                "", {"display": "none"}, "", False,
                [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]
            )
        
        # Show progress bar
        progress_bar = dbc.Progress(
            id="sync-progress-bar",
            value=10,
            striped=True,
            animated=True,
            color="primary",
            className="mb-3"
        )
        
        # Status message
        status_msg = dbc.Alert([
            html.I(className="fas fa-spinner fa-spin me-2"),
            f"Starting sync for {days} days with {smoothing} smoothing..."
        ], color="info")
        
        # Disable button and show spinner
        button_content = [
            html.I(className="fas fa-spinner fa-spin me-2"),
            "Syncing..."
        ]
        
        # Perform sync operation using Garmin Integration Service
        sync_options = sync_options or []
        wellness_enabled = "wellness" in sync_options
        fit_files_enabled = "fit_files" in sync_options
        
        try:
            # Initialize Garmin Integration Service
            garmin_service = GarminIntegrationService()
            
            # Sync wellness data using the integration service
            if wellness_enabled:
                sync_result = garmin_service.sync_wellness_data_range(
                    start_date=start,
                    end_date=end,
                    smoothing=smoothing or "none"
                )
            else:
                # If wellness is not enabled, just return a basic result
                sync_result = {
                    "success": True,
                    "message": "Sync completed (wellness data disabled)",
                    "records_synced": 0,
                    "fit_files_enabled": fit_files_enabled
                }
            
            if sync_result.get("success"):
                # Success result from Garmin Integration Service
                persistence = sync_result.get("persistence", {})
                successful_types = sum(1 for success in persistence.values() if success)
                
                result_card = dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-check-circle text-success me-2"),
                        "Sync Completed Successfully"
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H6("Days Synced", className="text-muted"),
                                html.H4(str(sync_result.get("days_synced", days)), className="text-primary")
                            ], md=3),
                            dbc.Col([
                                html.H6("Records Synced", className="text-muted"), 
                                html.H4(str(sync_result.get("records_synced", 0)), className="text-success")
                            ], md=3),
                            dbc.Col([
                                html.H6("Data Types", className="text-muted"),
                                html.H4(str(sync_result.get("data_types_persisted", f"{successful_types}/?")), 
                                        className="text-info")
                            ], md=3),
                            dbc.Col([
                                html.H6("Smoothing", className="text-muted"),
                                html.P(smoothing.title() if smoothing != "none" else "Raw Data", 
                                      className="small text-capitalize")
                            ], md=3)
                        ]),
                        html.Hr(),
                        html.P(sync_result.get("message", "Data synced successfully"), 
                              className="text-muted text-center mb-0")
                    ])
                ], color="success", outline=True)
                
                # Complete progress
                final_progress = dbc.Progress(value=100, color="success", className="mb-3")
                final_status = dbc.Alert([
                    html.I(className="fas fa-check-circle me-2"),
                    "Sync completed successfully!"
                ], color="success")
                
            else:
                # Handle sync errors from Garmin Integration Service
                error_msg = sync_result.get("error", "Unknown sync error")
                
                if "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
                    result_card = dbc.Alert([
                        html.H5("Authentication Required"),
                        html.P("Please authenticate with Garmin Connect first. Check your credentials in the Garmin login page."),
                        html.P(f"Error details: {error_msg}"),
                        dbc.Button("Go to Garmin Login", href="/garmin", color="primary", className="mt-2")
                    ], color="warning")
                else:
                    result_card = dbc.Alert([
                        html.H5("Sync Failed"),
                        html.P(f"Error: {error_msg}"),
                        html.Hr(),
                        html.Small("Try the following:"),
                        html.Ul([
                            html.Li("Check your internet connection"),
                            html.Li("Verify Garmin Connect is accessible"),
                            html.Li("Try a smaller date range"),
                            html.Li("Check the Garmin login page for authentication issues")
                        ])
                    ], color="danger")
                
                final_progress = dbc.Progress(value=0, color="danger", className="mb-3")
                final_status = dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Sync failed: {error_msg}"
                ], color="danger")
        
        except Exception as e:
            logger.error(f"Sync operation failed: {e}")
            result_card = dbc.Alert([
                html.H5("Sync Error"),
                html.P(f"An unexpected error occurred: {str(e)}")
            ], color="danger")
            
            final_progress = dbc.Progress(value=0, color="danger", className="mb-3")
            final_status = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Sync error: {str(e)}"
            ], color="danger")
        
        # Reset button
        reset_button = [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]
        
        return (
            result_card,
            final_progress,
            {"display": "block"},
            final_status,
            False,  # Re-enable button
            reset_button
        )
        
    except Exception as e:
        logger.error(f"Sync callback error: {e}")
        return (
            dbc.Alert(f"An error occurred: {str(e)}", color="danger"),
            "",
            {"display": "none"},
            "",
            False,
            [html.I(className="fas fa-download me-2"), "Sync Garmin Data"]
        )


@callback(
    Output("data-summary-container", "children"),
    Input("sync-results-container", "children"),
    prevent_initial_call=True
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
            return dbc.Alert(
                "No wellness data found. Try syncing some data first.",
                color="info"
            )
        
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
                    "stress": "fas fa-brain"
                }
                
                card = dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4([
                                html.I(className=f"{icon_map.get(data_type, 'fas fa-chart-line')} me-2"),
                                str(count)
                            ], className="text-center text-primary"),
                            html.P(data_type.replace("_", " ").title(), 
                                  className="text-center text-muted small mb-0")
                        ])
                    ], className="h-100")
                ], md=2)
                data_cards.append(card)
        
        if data_cards:
            return dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-chart-bar me-2"),
                        "Current Data Summary (Last 30 Days)"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row(data_cards),
                    html.Hr(),
                    html.P([
                        f"Total Records: {summary.get('total_records', 0)} | ",
                        f"Coverage: {summary.get('coverage_percentage', 0):.1f}%"
                    ], className="text-center text-muted mb-0")
                ])
            ])
        else:
            return ""
            
    except Exception as e:
        logger.error(f"Error updating data summary: {e}")
        return dbc.Alert(
            f"Could not load data summary: {str(e)}", 
            color="warning"
        )