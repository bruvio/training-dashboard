import dash
from dash import html
import dash_bootstrap_components as dbc
dash.register_page(__name__, path="/", name="Home")
layout = dbc.Container([html.H2("Home"), html.P("If you can see this, pages are rendering.")], fluid=True)
