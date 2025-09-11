"""
Activities page - Dedicated page for browsing and filtering all activities.
"""

from datetime import datetime, timedelta

from dash import Input, Output, callback, dcc, html
import dash_bootstrap_components as dbc

from app.data.web_queries import get_activities_for_date_range, get_filter_options
from app.utils import filter_activities_by_distance, parse_duration_to_seconds, sort_activities


def layout():
    """
    Dedicated activities page layout with filters and activity list.
    """
    return dbc.Container(
        [
            # Header
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1([html.I(className="fas fa-running me-3"), "Activities"], className="mb-3"),
                            html.P(
                                "Browse, filter, and analyze all activities in your database.",
                                className="text-muted mb-4 fs-5",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Filters section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H6("Filters", className="mb-3"),
                                            dbc.Row(
                                                [
                                                    # Date range filter
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Date Range:", size="sm"),
                                                            dcc.DatePickerRange(
                                                                id="activities-date-range-picker",
                                                                start_date=datetime.now() - timedelta(days=90),
                                                                end_date=datetime.now() + timedelta(days=7),
                                                                display_format="YYYY-MM-DD",
                                                                style={"width": "100%"},
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    # Sport filter
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Sport:", size="sm"),
                                                            dcc.Dropdown(
                                                                id="activities-sport-filter",
                                                                placeholder="All Sports",
                                                                value="all",
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        md=2,
                                                    ),
                                                    # Duration filter
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Duration (min):", size="sm"),
                                                            dcc.RangeSlider(
                                                                id="activities-duration-filter",
                                                                step=5,
                                                                marks=None,
                                                                tooltip={
                                                                    "placement": "bottom",
                                                                    "always_visible": False,
                                                                },
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    # Distance filter
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Distance (km):", size="sm"),
                                                            dcc.RangeSlider(
                                                                id="activities-distance-filter",
                                                                step=0.5,
                                                                marks=None,
                                                                tooltip={
                                                                    "placement": "bottom",
                                                                    "always_visible": False,
                                                                },
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                ]
                                            ),
                                            html.Hr(className="my-3"),
                                            dbc.Row(
                                                [
                                                    # Sort dropdown
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Sort by:", size="sm"),
                                                            dcc.Dropdown(
                                                                id="activities-sort-dropdown",
                                                                options=[
                                                                    {"label": "Date (Newest)", "value": "date_desc"},
                                                                    {"label": "Date (Oldest)", "value": "date_asc"},
                                                                    {
                                                                        "label": "Distance (High-Low)",
                                                                        "value": "distance_desc",
                                                                    },
                                                                    {
                                                                        "label": "Distance (Low-High)",
                                                                        "value": "distance_asc",
                                                                    },
                                                                    {
                                                                        "label": "Duration (Long-Short)",
                                                                        "value": "duration_desc",
                                                                    },
                                                                    {
                                                                        "label": "Duration (Short-Long)",
                                                                        "value": "duration_asc",
                                                                    },
                                                                ],
                                                                value="date_desc",
                                                                clearable=False,
                                                                style={"fontSize": "14px"},
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    # Search box
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Search:", size="sm"),
                                                            dbc.Input(
                                                                id="activities-search-input",
                                                                placeholder="Search activities...",
                                                                size="sm",
                                                                debounce=True,
                                                            ),
                                                        ],
                                                        md=3,
                                                    ),
                                                    # Refresh button
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Actions:", size="sm"),
                                                            html.Br(),
                                                            dbc.Button(
                                                                [
                                                                    html.I(className="fas fa-sync me-2"),
                                                                    "Refresh",
                                                                ],
                                                                id="activities-refresh-button",
                                                                color="primary",
                                                                size="sm",
                                                            ),
                                                        ],
                                                        md=2,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                className="mb-3",
                            )
                        ],
                        width=12,
                    )
                ]
            ),
            # Activity summary stats
            dbc.Row([dbc.Col([html.Div(id="activities-summary-cards")], width=12)], className="mb-4"),
            # Activity table
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col([html.H5("Your Activities", className="mb-0")], width=8),
                                                    dbc.Col(
                                                        [html.Div(id="activities-count-badge", className="float-end")],
                                                        width=4,
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardBody([html.Div(id="activities-table-container")]),
                                ]
                            )
                        ],
                        width=12,
                    )
                ]
            ),
        ],
        fluid=True,
    )


# Initialize filter options for activities page
@callback(
    [
        Output("activities-sport-filter", "options"),
        Output("activities-duration-filter", "min"),
        Output("activities-duration-filter", "max"),
        Output("activities-duration-filter", "value"),
        Output("activities-distance-filter", "min"),
        Output("activities-distance-filter", "max"),
        Output("activities-distance-filter", "value"),
    ],
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def initialize_activities_filters(pathname):
    """Initialize filter components with data from database."""
    if pathname != "/activities":
        return [], 0, 180, [0, 180], 0, 50, [0, 50]

    try:
        filter_options = get_filter_options()

        # Sport options
        sport_options = [{"label": "All Sports", "value": "all"}]
        for sport in filter_options["sports"]:
            sport_options.append({"label": sport.replace("_", " ").title(), "value": sport})

        # Duration in minutes - set reasonable defaults that don't filter out activities
        duration_max_mins = int((filter_options["duration_range"]["max"] or 3600) / 60)
        duration_value = [0, max(duration_max_mins, 300)]

        # Distance in km - set reasonable defaults that don't filter out activities
        distance_max_km = int(filter_options["distance_range"]["max"] or 100)
        distance_value = [0, max(distance_max_km, 200)]

        return (
            sport_options,
            0,
            max(duration_max_mins, 300),
            duration_value,
            0,
            max(distance_max_km, 200),
            distance_value,
        )
    except Exception as e:
        # Fallback values if there's an error
        return (
            [{"label": "All Sports", "value": "all"}],
            0,
            300,
            [0, 300],
            0,
            200,
            [0, 200],
        )


@callback(
    Output("activities-summary-cards", "children"),
    [
        Input("activities-date-range-picker", "start_date"),
        Input("activities-date-range-picker", "end_date"),
        Input("activities-sport-filter", "value"),
        Input("activities-search-input", "value"),
    ],
)
def update_activities_summary(start_date, end_date, sport, search_term):
    """Load and display activity summary statistics with filters."""
    try:
        from app.data.web_queries import get_activity_summary_stats

        # Convert date strings to date objects
        start_date_obj = None
        end_date_obj = None
        if start_date:
            start_date_obj = datetime.fromisoformat(start_date).date()
        if end_date:
            end_date_obj = datetime.fromisoformat(end_date).date()

        # Get filtered summary stats
        stats = get_activity_summary_stats(
            start_date=start_date_obj,
            end_date=end_date_obj,
            sport=sport,
            search_term=search_term,
        )

        if int(stats["total_activities"]) == 0:
            return dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "No activities found with the current filters. Try adjusting your search criteria.",
                ],
                color="info",
                className="text-center",
            )

        return dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3(stats["total_activities"], className="text-primary mb-1"),
                                        html.P("Total Activities", className="mb-0 text-muted"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3(stats["total_distance"], className="text-success mb-1"),
                                        html.P("Total Distance", className="mb-0 text-muted"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3(stats["total_time"], className="text-info mb-1"),
                                        html.P("Total Time", className="mb-0 text-muted"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardBody(
                                    [
                                        html.H3(stats["avg_hr"], className="text-danger mb-1"),
                                        html.P("Avg Heart Rate", className="mb-0 text-muted"),
                                    ],
                                    className="text-center",
                                )
                            ]
                        )
                    ],
                    width=3,
                ),
            ]
        )

    except Exception as e:
        return dbc.Alert(f"Error loading summary: {str(e)}", color="warning")


@callback(
    [
        Output("activities-table-container", "children"),
        Output("activities-count-badge", "children"),
    ],
    [
        Input("activities-date-range-picker", "start_date"),
        Input("activities-date-range-picker", "end_date"),
        Input("activities-sport-filter", "value"),
        Input("activities-duration-filter", "value"),
        Input("activities-distance-filter", "value"),
        Input("activities-search-input", "value"),
        Input("activities-sort-dropdown", "value"),
        Input("activities-refresh-button", "n_clicks"),
    ],
    prevent_initial_call=False,
)
def update_activities_table(
    start_date, end_date, sport, duration_range, distance_range, search_term, sort_by, n_clicks
):
    """Load and display activities in a filtered table format."""
    try:
        # Provide defaults if values are None
        if start_date is None:
            start_date_obj = None
        else:
            start_date_obj = datetime.fromisoformat(start_date).date()

        if end_date is None:
            end_date_obj = None
        else:
            end_date_obj = datetime.fromisoformat(end_date).date()

        if sport is None:
            sport = "all"

        if search_term is None:
            search_term = ""

        if sort_by is None:
            sort_by = "date_desc"

        # Get filtered activities
        activities_data = get_activities_for_date_range(
            start_date=start_date_obj,
            end_date=end_date_obj,
            sport=sport,
            search_term=search_term,
        )

        # Apply duration and distance filters if specified
        if duration_range and len(duration_range) == 2 and (duration_range[0] != 0 or duration_range[1] < 180):
            min_duration_s = duration_range[0] * 60
            max_duration_s = duration_range[1] * 60
            filtered_activities = []
            for activity in activities_data:
                duration_str = activity.get("duration_str", "")
                duration_s = parse_duration_to_seconds(duration_str)

                if duration_s > 0 and min_duration_s <= duration_s <= max_duration_s:
                    filtered_activities.append(activity)
            activities_data = filtered_activities

        if distance_range and len(distance_range) == 2 and (distance_range[0] != 0 or distance_range[1] < 100):
            min_distance = distance_range[0]
            max_distance = distance_range[1]
            activities_data = filter_activities_by_distance(activities_data, min_distance, max_distance)

        # Create count badge
        count_badge = dbc.Badge(f"{len(activities_data)} activities", color="primary", className="fs-6")

        if not activities_data:
            return (
                dbc.Alert(
                    [
                        html.H4("No Activities Found", className="alert-heading"),
                        html.P("No activities match your current filter criteria."),
                        html.Hr(),
                        html.P("Try adjusting the filters to see more activities."),
                    ],
                    color="info",
                ),
                count_badge,
            )

        # Apply sorting using shared helper
        activities_data = sort_activities(activities_data, sort_by)

        # Create activity cards
        activity_cards = []
        for activity in activities_data:
            activity_name = activity.get("name", f"Activity {activity['id']}")

            card = dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H5(activity_name, className="card-title"),
                            html.P(
                                [
                                    html.Strong("Sport: "),
                                    activity.get("sport", "Unknown"),
                                    html.Br(),
                                    html.Strong("Duration: "),
                                    activity.get("duration_str", "N/A"),
                                    html.Br(),
                                    html.Strong("Distance: "),
                                    f"{activity.get('distance_km', 0):.2f} km",
                                    html.Br(),
                                    html.Strong("Date: "),
                                    activity.get("start_time", "Unknown"),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Button(
                                                "View Details",
                                                href=f"/activity/{activity['id']}",
                                                color="primary",
                                                size="sm",
                                            ),
                                        ],
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                f"HR: {activity.get('avg_hr', 'N/A')} | Power: {activity.get('avg_power_w', 'N/A')}W | Elevation: {activity.get('elevation_gain_m', 0)}m",
                                                className="text-muted",
                                            )
                                        ]
                                    ),
                                ]
                            ),
                        ]
                    )
                ],
                className="mb-3",
            )
            activity_cards.append(card)

        return html.Div(activity_cards), count_badge

    except Exception as e:
        return dbc.Alert(f"Error loading activities: {str(e)}", color="danger"), dbc.Badge(
            "0 activities", color="danger"
        )
