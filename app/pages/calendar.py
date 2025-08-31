"""
Calendar page - Main activity list and calendar view.
"""

from datetime import datetime, timedelta

from dash import dcc, html
import dash_bootstrap_components as dbc

# Manual routing - no dash.register_page()


def layout():
    """
    Main layout for the calendar/activity list page.
    """
    return dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(
                                [
                                    html.I(
                                        className="bi bi-calendar-event",
                                        style={"marginRight": "10px"},
                                    ),
                                    "Activity Calendar",
                                ]
                            ),
                            html.Hr(),
                            dcc.DatePickerRange(
                                id="calendar-date-picker",
                                start_date=datetime.now() - timedelta(days=30),
                                end_date=datetime.now(),
                                display_format="YYYY-MM-DD",
                            ),
                            html.Div(id="calendar-content"),
                        ]
                    )
                ]
            )
        ],
        fluid=True,
    )
