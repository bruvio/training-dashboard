"""
Activity Calendar Page for Garmin Dashboard.

Research-validated implementation using dash.register_page() with
DatePickerRange, sport filters, and DataTable following PRP specifications.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

from app.data.web_queries import get_activities_for_date_range, get_activity_summary_stats, check_database_connection

# Register this page (Dash 2.17+ pattern)
dash.register_page(
    __name__,
    path="/",
    title="Activity Calendar - Garmin Dashboard",
    name="Activity Calendar",
    description="View and filter your Garmin activities by date and sport type",
)


def layout():
    """
    Layout for the activity calendar page.

    Research-validated implementation with responsive Bootstrap grid,
    date picker range, sport filters, and interactive DataTable.
    """
    return dbc.Container(
        [
            # Page header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                [html.I(className="fas fa-calendar-alt me-2 text-primary"), "Activity Calendar"],
                                className="mb-1",
                            ),
                            html.P(
                                "View and filter your fitness activities by date range and sport type",
                                className="text-muted mb-4",
                            ),
                        ]
                    )
                ]
            ),
            # Filters section
            dbc.Card(
                [
                    dbc.CardHeader([html.H5([html.I(className="fas fa-filter me-2"), "Filters"], className="mb-0")]),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    # Date range picker
                                    dbc.Col(
                                        [
                                            html.Label("Date Range:", className="form-label fw-bold"),
                                            dcc.DatePickerRange(
                                                id="date-picker-range",
                                                display_format="YYYY-MM-DD",
                                                start_date_placeholder_text="Start Date",
                                                end_date_placeholder_text="End Date",
                                                start_date=date.today() - timedelta(days=30),  # Last 30 days
                                                end_date=date.today(),
                                                className="form-control-sm",
                                            ),
                                        ],
                                        lg=4,
                                        md=6,
                                        sm=12,
                                    ),
                                    # Sport filter
                                    dbc.Col(
                                        [
                                            html.Label("Sport Type:", className="form-label fw-bold"),
                                            dcc.Dropdown(
                                                id="sport-filter",
                                                options=[
                                                    {"label": "All Sports", "value": "all"},
                                                    {"label": "🏃 Running", "value": "running"},
                                                    {"label": "🚴 Cycling", "value": "cycling"},
                                                    {"label": "🏊 Swimming", "value": "swimming"},
                                                    {"label": "🥾 Hiking", "value": "hiking"},
                                                    {"label": "💪 Strength", "value": "strength"},
                                                    {"label": "🏋️ Gym", "value": "cardio"},
                                                    {"label": "🎿 Winter Sports", "value": "skiing"},
                                                    {"label": "⚽ Other Sports", "value": "other"},
                                                ],
                                                value="all",
                                                clearable=False,
                                                className="form-control-sm",
                                            ),
                                        ],
                                        lg=3,
                                        md=6,
                                        sm=12,
                                    ),
                                    # Search box
                                    dbc.Col(
                                        [
                                            html.Label("Search:", className="form-label fw-bold"),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="search-input",
                                                        type="text",
                                                        placeholder="Search activities...",
                                                        className="form-control-sm",
                                                    ),
                                                    dbc.Button(
                                                        [html.I(className="fas fa-search")],
                                                        id="search-button",
                                                        outline=True,
                                                        color="secondary",
                                                        size="sm",
                                                    ),
                                                ]
                                            ),
                                        ],
                                        lg=3,
                                        md=6,
                                        sm=12,
                                    ),
                                    # Quick date buttons
                                    dbc.Col(
                                        [
                                            html.Label("Quick Select:", className="form-label fw-bold"),
                                            dbc.ButtonGroup(
                                                [
                                                    dbc.Button(
                                                        "This Week",
                                                        id="btn-week",
                                                        size="sm",
                                                        outline=True,
                                                        color="primary",
                                                    ),
                                                    dbc.Button(
                                                        "This Month",
                                                        id="btn-month",
                                                        size="sm",
                                                        outline=True,
                                                        color="primary",
                                                    ),
                                                    dbc.Button(
                                                        "Last 30 Days",
                                                        id="btn-30days",
                                                        size="sm",
                                                        outline=True,
                                                        color="primary",
                                                    ),
                                                    dbc.Button(
                                                        "This Year",
                                                        id="btn-year",
                                                        size="sm",
                                                        outline=True,
                                                        color="primary",
                                                    ),
                                                ],
                                                size="sm",
                                            ),
                                        ],
                                        lg=2,
                                        md=6,
                                        sm=12,
                                    ),
                                ],
                                className="g-3",
                            )
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Summary stats cards
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(id="total-activities", children="0", className="text-primary mb-1"),
                                            html.P("Total Activities", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                id="total-distance", children="0 km", className="text-success mb-1"
                                            ),
                                            html.P("Total Distance", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(id="total-time", children="0h", className="text-info mb-1"),
                                            html.P("Total Time", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(id="avg-hr", children="0 bpm", className="text-danger mb-1"),
                                            html.P("Avg Heart Rate", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(id="avg-power", children="0 W", className="text-warning mb-1"),
                                            html.P("Avg Power", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4(
                                                id="elevation-gain", children="0 m", className="text-secondary mb-1"
                                            ),
                                            html.P("Elevation Gain", className="text-muted mb-0 small"),
                                        ]
                                    )
                                ],
                                className="text-center h-100",
                            )
                        ],
                        lg=2,
                        md=4,
                        sm=6,
                    ),
                ],
                className="mb-4",
            ),
            # Loading indicator
            dcc.Loading(
                id="loading-activities",
                type="default",
                children=[
                    # Activity table
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                [html.H5([html.I(className="fas fa-table me-2"), "Activities"], className="mb-0")]
                            ),
                            dbc.CardBody(
                                [
                                    dash_table.DataTable(
                                        id="activity-table",
                                        columns=[
                                            {
                                                "name": "📅 Date",
                                                "id": "start_time",
                                                "type": "datetime",
                                                "presentation": "markdown",
                                            },
                                            {"name": "🏃 Sport", "id": "sport", "presentation": "markdown"},
                                            {
                                                "name": "📏 Distance",
                                                "id": "distance_km",
                                                "type": "numeric",
                                                "format": dash_table.Format(
                                                    precision=2, scheme=dash_table.Scheme.fixed
                                                ),
                                            },
                                            {"name": "⏱️ Duration", "id": "duration_str"},
                                            {"name": "❤️ Avg HR", "id": "avg_hr", "type": "numeric"},
                                            {"name": "⚡ Avg Power", "id": "avg_power_w", "type": "numeric"},
                                            {"name": "📈 Elevation", "id": "elevation_gain_m", "type": "numeric"},
                                        ],
                                        data=[],  # Will be populated by callback
                                        # Research-validated DataTable configuration
                                        sort_action="native",
                                        filter_action="native",
                                        page_action="native",
                                        page_size=20,
                                        # Styling
                                        style_table={"overflowX": "auto"},
                                        style_cell={
                                            "textAlign": "left",
                                            "padding": "10px",
                                            "fontFamily": "Arial, sans-serif",
                                            "fontSize": "14px",
                                        },
                                        style_header={
                                            "backgroundColor": "rgb(248, 249, 250)",
                                            "fontWeight": "bold",
                                            "border": "1px solid #dee2e6",
                                        },
                                        style_data={
                                            "border": "1px solid #dee2e6",
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                        },
                                        style_data_conditional=[
                                            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248, 248, 248)"},
                                            {
                                                "if": {"state": "active"},
                                                "backgroundColor": "rgba(0, 123, 255, 0.1)",
                                                "border": "1px solid rgb(0, 123, 255)",
                                            },
                                        ],
                                        # Row selection for navigation
                                        row_selectable="single",
                                        selected_rows=[],
                                        # Tooltip data
                                        tooltip_data=[],
                                        tooltip_duration=None,
                                    )
                                ],
                                className="p-0",
                            ),
                        ]
                    )
                ],
            ),
            # Empty state message
            html.Div(
                id="empty-state",
                children=[
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            html.I(className="fas fa-inbox fa-3x text-muted mb-3"),
                                            html.H4("No Activities Found", className="text-muted"),
                                            html.P(
                                                [
                                                    "Try adjusting your filters or ",
                                                    html.A(
                                                        "import some activities", href="#", className="text-primary"
                                                    ),
                                                    " to get started.",
                                                ],
                                                className="text-muted",
                                            ),
                                        ],
                                        className="text-center py-5",
                                    )
                                ]
                            )
                        ]
                    )
                ],
                style={"display": "none"},  # Hidden by default
            ),
        ],
        fluid=True,
    )


# Callback for quick date selection buttons
@callback(
    [Output("date-picker-range", "start_date"), Output("date-picker-range", "end_date")],
    [
        Input("btn-week", "n_clicks"),
        Input("btn-month", "n_clicks"),
        Input("btn-30days", "n_clicks"),
        Input("btn-year", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def update_date_range(btn_week, btn_month, btn_30days, btn_year):
    """
    Update date range based on quick select buttons.

    Research-validated callback pattern with prevent_initial_call
    and proper button identification.
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    today = date.today()

    if button_id == "btn-week":
        # This week (Monday to Sunday)
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return monday, today
    elif button_id == "btn-month":
        # This month (1st to today)
        first_of_month = date(today.year, today.month, 1)
        return first_of_month, today
    elif button_id == "btn-30days":
        return today - timedelta(days=30), today
    elif button_id == "btn-year":
        return date(today.year, 1, 1), today

    return dash.no_update, dash.no_update


# Main callback for updating activity data (placeholder)
@callback(
    [
        Output("activity-table", "data"),
        Output("activity-table", "tooltip_data"),
        Output("total-activities", "children"),
        Output("total-distance", "children"),
        Output("total-time", "children"),
        Output("avg-hr", "children"),
        Output("avg-power", "children"),
        Output("elevation-gain", "children"),
        Output("empty-state", "style"),
    ],
    [
        Input("date-picker-range", "start_date"),
        Input("date-picker-range", "end_date"),
        Input("sport-filter", "value"),
        Input("search-input", "value"),
        Input("search-button", "n_clicks"),
    ],
)
def update_activity_data(start_date, end_date, sport, search_term, search_clicks):
    """
    Update activity table and summary statistics based on filters.

    Research-validated database integration with proper error handling
    and graceful degradation for web applications.
    """
    try:
        # Check database connection first
        if not check_database_connection():
            # Return empty state with error message
            return ([], [], "DB Error", "N/A", "N/A", "N/A", "N/A", "N/A", {"display": "block"})

        # Convert date strings to date objects if needed
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()

        # Get activities from database
        activities = get_activities_for_date_range(
            start_date=start_date, end_date=end_date, sport=sport, search_term=search_term
        )

        # Get summary statistics
        stats = get_activity_summary_stats(
            start_date=start_date, end_date=end_date, sport=sport, search_term=search_term
        )

        # Create tooltips for activity rows
        tooltips = []
        for i, activity in enumerate(activities):
            tooltip_row = {}
            for col in ["start_time", "sport", "distance_km", "duration_str"]:
                if col in activity:
                    tooltip_row[col] = {
                        "value": f"Click to view details for this {activity.get('sport', 'activity')}",
                        "type": "text",
                    }
            tooltips.append(tooltip_row)

        # Show/hide empty state
        empty_style = {"display": "none"} if activities else {"display": "block"}

        return (
            activities,
            tooltips,
            stats["total_activities"],
            stats["total_distance"],
            stats["total_time"],
            stats["avg_hr"],
            stats["avg_power"],
            stats["elevation_gain"],
            empty_style,
        )

    except Exception as e:
        # Log error and return safe fallback
        import logging

        logging.error(f"Error updating activity data: {e}")

        return ([], [], "Error", "N/A", "N/A", "N/A", "N/A", "N/A", {"display": "block"})


# Callback for row selection and navigation (placeholder)
@callback(
    Output("url", "pathname", allow_duplicate=True),
    [Input("activity-table", "selected_rows")],
    [State("activity-table", "data")],
    prevent_initial_call=True,
)
def navigate_to_activity_detail(selected_rows, table_data):
    """
    Navigate to activity detail page when row is selected.

    Research-validated navigation pattern for multi-page Dash apps
    with proper activity ID extraction from table data.
    """
    if selected_rows and table_data:
        try:
            # Get the selected row index
            row_index = selected_rows[0]

            # Get the activity data from that row
            if row_index < len(table_data):
                activity = table_data[row_index]
                activity_id = activity.get("id")

                if activity_id:
                    return f"/activity/{activity_id}"
        except (IndexError, KeyError, TypeError):
            # Handle any errors gracefully
            pass

    return dash.no_update
