"""
app/pages/garmin_login.py

Garmin Connect login & sync page (Dash).
Uses `python-garminconnect` via the local package `garmin_client`.
Plots activity metrics after sync.
"""

from __future__ import annotations

import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, State, dcc, html, no_update, dash_table
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

# Import from your local package
from garmin_client.client import GarminConnectClient, GarminAuthError
from garmin_client.sync import sync_range
from garmin_client.activity_import import ActivityImportService

logger = logging.getLogger(__name__)

# Global client manager for maintaining MFA state across callbacks
_client_instance = None


def get_client():
    """Get or create global client instance to maintain MFA state."""
    global _client_instance
    if _client_instance is None:
        _client_instance = GarminConnectClient()
    return _client_instance


def reset_client():
    """Reset the global client instance."""
    global _client_instance
    _client_instance = None


def layout():
    return dbc.Container(
        [
            dcc.Store(id="garmin-auth-store"),
            dcc.Store(id="garmin-activities-store"),
            dcc.Store(id="garmin-client-state"),  # Store for maintaining client state
            dbc.Row(
                dbc.Col(
                    [
                        html.H2("Garmin Connect Integration"),
                        html.P("Sign in to Garmin Connect, sync recent activities, and view charts below."),
                        html.Div(id="garmin-status-alert"),
                    ],
                    width=12,
                )
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Login"),
                                dbc.CardBody(
                                    [
                                        dbc.Form(
                                            id="garmin-login-form",
                                            children=[
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            dbc.Input(
                                                                id="garmin-email",
                                                                type="email",
                                                                placeholder="Email",
                                                                autoComplete="username",
                                                            ),
                                                            md=5,
                                                        ),
                                                        dbc.Col(
                                                            dbc.Input(
                                                                id="garmin-password",
                                                                type="password",
                                                                placeholder="Password",
                                                                autoComplete="current-password",
                                                            ),
                                                            md=5,
                                                        ),
                                                        dbc.Col(
                                                            dbc.Button(
                                                                "Login",
                                                                id="garmin-login-btn",
                                                                color="primary",
                                                                className="w-100",
                                                            ),
                                                            md=2,
                                                        ),
                                                    ],
                                                    className="g-2",
                                                ),
                                                dbc.Checkbox(
                                                    id="garmin-remember-me",
                                                    label="Remember me (save tokens)",
                                                    value=True,
                                                    className="mt-2",
                                                ),
                                            ],
                                        )
                                    ]
                                ),
                            ]
                        ),
                        width=12,
                        lg=8,
                    ),
                ],
                className="mt-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Two‑Factor Authentication"),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="garmin-mfa-form",
                                            hidden=True,
                                            children=[
                                                dbc.Input(id="garmin-mfa-code", placeholder="Enter 6‑digit code"),
                                                dbc.Button(
                                                    "Verify", id="garmin-mfa-verify-btn", color="info", className="mt-2"
                                                ),
                                                html.Small("Check your email/SMS for the Garmin verification code."),
                                            ],
                                        )
                                    ]
                                ),
                            ]
                        ),
                        width=12,
                        lg=8,
                    ),
                ],
                className="mt-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Sync & Preview"),
                                dbc.CardBody(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Select(
                                                        id="garmin-days-dropdown",
                                                        options=[
                                                            {"label": "1 day", "value": 1},
                                                            {"label": "7 days", "value": 7},
                                                            {"label": "14 days", "value": 14},
                                                            {"label": "30 days", "value": 30},
                                                            {"label": "90 days", "value": 90},
                                                        ],
                                                        value=30,
                                                    ),
                                                    md=3,
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Sync now",
                                                        id="garmin-sync-btn",
                                                        color="success",
                                                        className="w-100",
                                                    ),
                                                    md=3,
                                                ),
                                                dbc.Col(
                                                    dbc.Select(
                                                        id="garmin-metric-select",
                                                        options=[
                                                            {"label": "Distance (km)", "value": "distance_km"},
                                                            {"label": "Duration (min)", "value": "duration_min"},
                                                            {"label": "Avg HR (bpm)", "value": "avg_hr"},
                                                            {"label": "Speed (km/h)", "value": "speed_kmh"},
                                                            {"label": "Pace (min/km)", "value": "pace_min_per_km"},
                                                            {"label": "Calories", "value": "calories"},
                                                            {"label": "Elev Gain (m)", "value": "elev_gain_m"},
                                                        ],
                                                        value="distance_km",
                                                    ),
                                                    md=3,
                                                ),
                                                dbc.Col(
                                                    dbc.Select(
                                                        id="garmin-type-filter",
                                                        options=[
                                                            {"label": "All types", "value": ""},
                                                            {"label": "Running", "value": "running"},
                                                            {"label": "Cycling", "value": "cycling"},
                                                            {"label": "Swimming", "value": "swimming"},
                                                            {"label": "Strength", "value": "strength_training"},
                                                            {"label": "Other", "value": "other"},
                                                        ],
                                                        value="",
                                                    ),
                                                    md=3,
                                                ),
                                            ],
                                            className="g-2",
                                        ),
                                        html.Div(id="garmin-sync-result", className="mt-3"),
                                    ]
                                ),
                            ]
                        ),
                        width=12,
                        lg=10,
                    ),
                ],
                className="mt-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Activity Chart"),
                                dbc.CardBody([html.Div(id="garmin-activity-chart")]),
                            ]
                        ),
                        width=12,
                        lg=10,
                    )
                ],
                className="mt-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader("Recent Activities"),
                                dbc.CardBody(
                                    [
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        dbc.ButtonGroup(
                                                            [
                                                                dbc.Button(
                                                                    "Import Selected Activities",
                                                                    id="import-selected-btn",
                                                                    color="success",
                                                                    disabled=True,
                                                                ),
                                                                dbc.Button(
                                                                    "Import All Activities",
                                                                    id="import-all-btn",
                                                                    color="info",
                                                                    disabled=True,
                                                                ),
                                                            ]
                                                        ),
                                                    ],
                                                    width=6,
                                                ),
                                                dbc.Col([html.Div(id="import-status", className="text-end")], width=6),
                                            ],
                                            className="mb-3",
                                        ),
                                        dash_table.DataTable(
                                            id="garmin-activity-table",
                                            columns=[
                                                {"name": "Date/Time", "id": "start"},
                                                {"name": "Type", "id": "type"},
                                                {"name": "Title", "id": "name"},
                                                {"name": "Distance (km)", "id": "distance_km"},
                                                {"name": "Duration (min)", "id": "duration_min"},
                                                {"name": "Avg HR", "id": "avg_hr"},
                                                {"name": "Speed (km/h)", "id": "speed_kmh"},
                                                {"name": "Pace (min/km)", "id": "pace_min_per_km"},
                                                {"name": "Calories", "id": "calories"},
                                            ],
                                            data=[],
                                            page_size=10,
                                            row_selectable="multi",
                                            selected_rows=[],
                                            sort_action="native",
                                            filter_action="native",
                                            style_table={"overflowX": "auto"},
                                            style_cell={"padding": "6px", "fontSize": "0.9rem"},
                                        ),
                                    ]
                                ),
                            ]
                        ),
                        width=12,
                        lg=10,
                    )
                ],
                className="mt-3 mb-5",
            ),
        ],
        fluid=True,
        className="py-3",
    )


# --------- Callbacks


def register_callbacks(app):
    # On page load — try restoring tokens
    @app.callback(
        Output("garmin-auth-store", "data"),
        Output("garmin-status-alert", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def _bootstrap_auth(_):
        try:
            cli = get_client()
            state = cli.load_session()
            if state.get("is_authenticated"):
                return state, dbc.Alert(f"Signed in as {state.get('username')}.", color="success", dismissable=True)
            return state, no_update
        except Exception as e:
            return {"is_authenticated": False, "username": None, "mfa_required": False}, dbc.Alert(
                str(e), color="danger"
            )

    # Login
    @app.callback(
        Output("garmin-auth-store", "data", allow_duplicate=True),
        Output("garmin-status-alert", "children", allow_duplicate=True),
        Output("garmin-mfa-form", "hidden"),
        Input("garmin-login-btn", "n_clicks"),
        State("garmin-email", "value"),
        State("garmin-password", "value"),
        State("garmin-remember-me", "value"),
        prevent_initial_call=True,
    )
    def _login(n_clicks, email, password, remember):
        if not n_clicks:
            raise PreventUpdate
        if not email or not password:
            return no_update, dbc.Alert("Please enter both email and password.", color="warning"), True
        try:
            reset_client()  # Reset any previous state
            cli = get_client()  # Get shared client instance
            result = cli.login(str(email).strip(), str(password), remember=bool(remember))
            if result.get("mfa_required"):
                return (
                    {"is_authenticated": False, "username": None, "mfa_required": True},
                    dbc.Alert("Two‑factor authentication required. Enter the code to continue.", color="info"),
                    False,
                )
            return (
                {"is_authenticated": True, "username": result.get("username"), "mfa_required": False},
                dbc.Alert(f"Logged in as {result.get('username')}.", color="success", dismissable=True),
                True,
            )
        except GarminAuthError as e:
            return (
                {"is_authenticated": False, "username": None, "mfa_required": False},
                dbc.Alert(f"Login failed: {e}", color="danger", dismissable=True),
                True,
            )
        except Exception as e:
            return (
                {"is_authenticated": False, "username": None, "mfa_required": False},
                dbc.Alert(f"Login error: {e}", color="danger", dismissable=True),
                True,
            )

    # Complete MFA
    @app.callback(
        Output("garmin-auth-store", "data", allow_duplicate=True),
        Output("garmin-status-alert", "children", allow_duplicate=True),
        Output("garmin-mfa-form", "hidden", allow_duplicate=True),
        Input("garmin-mfa-verify-btn", "n_clicks"),
        State("garmin-mfa-code", "value"),
        State("garmin-remember-me", "value"),
        prevent_initial_call=True,
    )
    def _verify_mfa(n_clicks, code, remember):
        if not n_clicks:
            raise PreventUpdate
        if not code:
            return no_update, dbc.Alert("Please enter the MFA code.", color="warning"), False
        try:
            cli = get_client()  # Use shared client instance with MFA context
            result = cli.submit_mfa(str(code).strip(), remember=bool(remember))
            return (
                {"is_authenticated": True, "username": result.get("username"), "mfa_required": False},
                dbc.Alert(f"MFA successful. Logged in as {result.get('username')}.", color="success", dismissable=True),
                True,
            )
        except GarminAuthError as e:
            return no_update, dbc.Alert(f"MFA failed: {e}", color="danger"), False
        except Exception as e:
            return no_update, dbc.Alert(f"MFA error: {e}", color="danger"), False

    # Sync button -> message + store data
    @app.callback(
        Output("garmin-sync-result", "children"),
        Output("garmin-activities-store", "data"),
        Input("garmin-sync-btn", "n_clicks"),
        State("garmin-auth-store", "data"),
        State("garmin-days-dropdown", "value"),
        State("garmin-email", "value"),
        State("garmin-password", "value"),
        State("garmin-type-filter", "value"),
        prevent_initial_call=True,
    )
    def _sync(n_clicks, auth, days, email, password, type_filter):
        if not n_clicks:
            raise PreventUpdate
        is_authed = bool(auth and auth.get("is_authenticated"))
        try:
            if is_authed:
                summary = sync_range(days=int(days or 30), fetch_wellness=True)
            else:
                if not email or not password:
                    return dbc.Alert("Please login first or provide credentials.", color="warning"), no_update
                summary = sync_range(
                    email=str(email).strip(), password=str(password), days=int(days or 30), fetch_wellness=True
                )
            if not summary.get("ok"):
                if summary.get("mfa_required"):
                    return dbc.Alert("MFA is required. Complete login first.", color="info"), no_update
                return dbc.Alert(f"Sync failed: {summary.get('error')}", color="danger"), no_update

            activities = summary.get("activities_norm", [])
            # Apply type filter if any
            if type_filter:
                activities = [a for a in activities if (a.get("type") or "").lower() == str(type_filter).lower()]

            msg = (
                f"✅ Synced {summary['activities_count']} activities "
                f"from {summary['start_date']} to {summary['end_date']}."
            )
            if summary.get("wellness_records"):
                msg += f" Added {summary['wellness_records']} wellness records."
            if summary.get("fit_downloaded"):
                msg += f" Downloaded {summary['fit_downloaded']} FIT files."
            return dbc.Alert(msg, color="success", dismissable=True), activities
        except Exception as e:
            return dbc.Alert(f"Sync error: {e}", color="danger"), no_update

    # Activities table renderer
    @app.callback(
        Output("garmin-activity-table", "data"),
        Input("garmin-activities-store", "data"),
        prevent_initial_call=True,
    )
    def _render_table(activities):
        if not activities:
            raise PreventUpdate
        # Sort by start descending if available
        try:
            return sorted(activities, key=lambda a: a.get("start") or "", reverse=True)
        except Exception:
            return activities

    # Activity chart renderer
    @app.callback(
        Output("garmin-activity-chart", "children"),
        Input("garmin-activities-store", "data"),
        Input("garmin-metric-select", "value"),
        prevent_initial_call=True,
    )
    def _render_chart(activities, metric):
        if not activities:
            return dbc.Alert("No activities to chart yet. Click Sync.", color="secondary")
        metric = metric or "distance_km"
        # Build a time-series scatter/line chart
        x = [a.get("start") for a in activities]
        y = [a.get(metric) for a in activities]
        names = [a.get("name") or "" for a in activities]

        # Fallback: filter out None values to avoid gaps
        points = [(xi, yi, ni) for xi, yi, ni in zip(x, y, names) if yi is not None and xi is not None]
        if not points:
            return dbc.Alert("Selected metric has no data for this window.", color="warning")

        x, y, names = zip(*points)

        title_map = {
            "distance_km": "Distance (km)",
            "duration_min": "Duration (min)",
            "avg_hr": "Avg HR (bpm)",
            "speed_kmh": "Speed (km/h)",
            "pace_min_per_km": "Pace (min/km)",
            "calories": "Calories",
            "elev_gain_m": "Elevation Gain (m)",
        }
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=list(x),
                y=list(y),
                mode="lines+markers",
                text=list(names),
                hovertemplate="<b>%{text}</b><br>%{x}<br>%{y}<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Activities — {title_map.get(metric, metric)}",
            xaxis_title="Date/Time",
            yaxis_title=title_map.get(metric, metric),
            height=420,
            hovermode="x unified",
            margin=dict(l=40, r=20, t=60, b=40),
        )
        return dcc.Graph(figure=fig)

    # Enable/disable import buttons based on table data and selection
    @app.callback(
        Output("import-selected-btn", "disabled"),
        Output("import-all-btn", "disabled"),
        Input("garmin-activity-table", "selected_rows"),
        Input("garmin-activities-store", "data"),
        Input("garmin-auth-store", "data"),
        prevent_initial_call=False,
    )
    def _update_import_buttons(selected_rows, activities, auth_data):
        is_authenticated = bool(auth_data and auth_data.get("is_authenticated"))
        has_activities = bool(activities and len(activities) > 0)
        has_selection = bool(selected_rows and len(selected_rows) > 0)

        return (
            not (is_authenticated and has_activities and has_selection),  # Import Selected disabled
            not (is_authenticated and has_activities),  # Import All disabled
        )

    # Import selected activities
    @app.callback(
        Output("import-status", "children"),
        Input("import-selected-btn", "n_clicks"),
        Input("import-all-btn", "n_clicks"),
        State("garmin-activity-table", "selected_rows"),
        State("garmin-activity-table", "data"),
        State("garmin-auth-store", "data"),
        prevent_initial_call=True,
    )
    def _import_activities(import_selected_clicks, import_all_clicks, selected_rows, table_data, auth_data):
        if not any([import_selected_clicks, import_all_clicks]):
            raise PreventUpdate

        if not (auth_data and auth_data.get("is_authenticated")):
            return dbc.Alert("Please login first.", color="warning")

        if not table_data:
            return dbc.Alert("No activities available to import.", color="warning")

        try:
            client = get_client()
            import_service = ActivityImportService(client)

            # Determine which activities to import
            if import_selected_clicks and selected_rows:
                # Import selected activities
                activities_to_import = [table_data[i] for i in selected_rows if i < len(table_data)]
                action = "selected"
            else:
                # Import all activities
                activities_to_import = table_data
                action = "all"

            if not activities_to_import:
                return dbc.Alert("No activities to import.", color="warning")

            # Import each activity
            imported_count = 0
            skipped_count = 0
            failed_count = 0

            for activity in activities_to_import:
                activity_id = activity.get("activity_id")
                if not activity_id:
                    failed_count += 1
                    continue

                result = import_service.import_activity_by_id(str(activity_id), download_fit=True)

                if result.get("success"):
                    if result.get("status") == "imported":
                        imported_count += 1
                    else:
                        skipped_count += 1
                else:
                    failed_count += 1

            # Generate result message
            total = len(activities_to_import)
            if imported_count > 0:
                color = "success"
                message = f"✅ Import completed: {imported_count} imported"
                if skipped_count > 0:
                    message += f", {skipped_count} already existed"
                if failed_count > 0:
                    message += f", {failed_count} failed"
                message += f" (out of {total} {action} activities)"
            elif skipped_count > 0:
                color = "info"
                message = f"ℹ️ All {skipped_count} {action} activities already existed in database"
            else:
                color = "danger"
                message = f"❌ Failed to import {failed_count} {action} activities"

            return dbc.Alert(message, color=color, dismissable=True)

        except Exception as e:
            logger.error(f"Activity import error: {e}")
            return dbc.Alert(f"Import error: {e}", color="danger", dismissable=True)
