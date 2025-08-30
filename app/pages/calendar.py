"""
Calendar page - Main activity list and calendar view.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta


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
                                    html.I(className="bi bi-calendar-event", style={"marginRight": "10px"}),
                                    "Activity Calendar",
                                ]
                            ),
                            html.Hr(),
                            dcc.DatePickerRange(
                                id="calendar-date-picker",
                                start_date=datetime.today() - timedelta(days=30),
                                end_date=datetime.today(),
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
