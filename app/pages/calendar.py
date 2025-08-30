"""
Calendar page - Main activity list and calendar view.
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from app.data.db import session_scope
from app.data.models import Activity

# Manual routing - no dash.register_page()

def layout():
    """
    Main layout for the calendar/activity list page.
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1([
                    html.I(className="bi bi-calendar-event", style={"marginRight": "10px"}),
                    "Activity Calendar",
                ]),
                html.Hr(),
                dcc.DatePickerRange(
                    id="calendar-date-picker",
                    start_date=datetime.today() - timedelta(days=30),
                    end_date=datetime.today(),
                    display_format="YYYY-MM-DD",
                ),
                html.Div(id="calendar-content"),
            ])
        ])
    ], fluid=True)
