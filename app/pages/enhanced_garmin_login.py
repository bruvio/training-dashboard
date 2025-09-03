"""
Enhanced Garmin Connect login with proper session persistence and wellness data sync.
"""

import base64
import logging
import pickle

from dash import Input, Output, State, ctx, dcc, html
import dash_bootstrap_components as dbc

# Import the garth sync functionality
from garmin_client.garth_sync import sync_garmin_wellness_data

logger = logging.getLogger(__name__)


def layout():
    return dbc.Container(
        [
            # Page load detection component
            dcc.Location(id="garmin-page-location", refresh=False),
            dbc.Row(
                dbc.Col(
                    [
                        html.H1(
                            [html.I(className="fas fa-user-lock me-3"), "Garmin Connect Integration"], className="mb-4"
                        ),
                        html.P(
                            "Connect to your Garmin Connect account to download and synchronize your activity and wellness data automatically.",
                            className="text-muted mb-4",
                        ),
                    ],
                    width=12,
                )
            ),
            # Authentication status display
            html.Div(id="auth-status-display"),
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Garmin Connect Authentication", className="mb-0")),
                                dbc.CardBody(
                                    [
                                        dcc.Store(id="login-status-store", data={}),
                                        # Login form - shown when not authenticated
                                        html.Div(
                                            id="login-form",
                                            children=[
                                                dbc.Form(
                                                    [
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label(
                                                                        "Email/Username", html_for="garmin-email"
                                                                    ),
                                                                    dbc.Input(
                                                                        type="email",
                                                                        id="garmin-email",
                                                                        placeholder="your.email@example.com",
                                                                        required=True,
                                                                    ),
                                                                ],
                                                                width=12,
                                                                className="mb-3",
                                                            )
                                                        ),
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Label("Password", html_for="garmin-password"),
                                                                    dbc.Input(
                                                                        type="password",
                                                                        id="garmin-password",
                                                                        placeholder="Enter your password",
                                                                        required=True,
                                                                    ),
                                                                ],
                                                                width=12,
                                                                className="mb-3",
                                                            )
                                                        ),
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Checkbox(
                                                                        id="remember-me-checkbox",
                                                                        label="Remember my credentials",
                                                                        value=False,
                                                                        className="mb-3",
                                                                    ),
                                                                ],
                                                                width=12,
                                                            )
                                                        ),
                                                        dbc.Row(
                                                            dbc.Col(
                                                                [
                                                                    dbc.Button(
                                                                        [
                                                                            html.I(className="fas fa-sign-in-alt me-2"),
                                                                            "Login",
                                                                        ],
                                                                        id="login-button",
                                                                        color="primary",
                                                                        size="lg",
                                                                        className="w-100",
                                                                    ),
                                                                ],
                                                                width=12,
                                                            )
                                                        ),
                                                    ]
                                                )
                                            ],
                                        ),
                                        # MFA section
                                        html.Div(id="mfa-section", children=[], style={"display": "none"}),
                                        # Status messages
                                        html.Div(id="login-status", className="mt-3"),
                                        # Success section - shown when authenticated
                                        html.Div(id="success-section", children=[], style={"display": "none"}),
                                    ]
                                ),
                            ]
                        )
                    ],
                    width=8,
                ),
                justify="center",
                className="mb-4",
            ),
            # Data synchronization section
            dbc.Row(
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Wellness Data Synchronization", className="mb-0")),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="sync-controls",
                                            children=[
                                                dbc.Alert(
                                                    "Please authenticate first to enable wellness data synchronization.",
                                                    color="info",
                                                    className="mb-3",
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                dbc.Label("Data Types to Sync"),
                                                                dbc.Checklist(
                                                                    id="sync-data-types",
                                                                    options=[
                                                                        {"label": "Sleep Data", "value": "sleep"},
                                                                        {"label": "Stress Data", "value": "stress"},
                                                                        {"label": "Steps & Activity", "value": "steps"},
                                                                        {
                                                                            "label": "Intensity Minutes",
                                                                            "value": "intensity",
                                                                        },
                                                                    ],
                                                                    value=["sleep", "stress", "steps", "intensity"],
                                                                    className="mb-3",
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                dbc.Label("Sync Period"),
                                                                dbc.Select(
                                                                    id="sync-period",
                                                                    options=[
                                                                        {"label": "Last 7 days", "value": "7"},
                                                                        {"label": "Last 30 days", "value": "30"},
                                                                        {"label": "Last 90 days", "value": "90"},
                                                                    ],
                                                                    value="30",
                                                                    className="mb-3",
                                                                ),
                                                                dbc.Button(
                                                                    [
                                                                        html.I(className="fas fa-download me-2"),
                                                                        "Sync Wellness Data",
                                                                    ],
                                                                    id="sync-wellness-button",
                                                                    color="success",
                                                                    size="lg",
                                                                    disabled=True,
                                                                ),
                                                            ],
                                                            width=6,
                                                        ),
                                                    ]
                                                ),
                                            ],
                                        ),
                                        html.Div(id="sync-status", className="mt-3"),
                                        html.Div(
                                            id="sync-progress",
                                            className="mt-3",
                                            style={"display": "none"},
                                            children=[
                                                dbc.Progress(id="sync-progress-bar", value=0, className="mb-2"),
                                                html.P(id="sync-progress-text", className="text-muted small"),
                                            ],
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ],
                    width=8,
                ),
                justify="center",
            ),
        ],
        fluid=True,
    )


def register_callbacks(app):
    from garmin_client.client import GarminConnectClient

    # Check authentication status on page load
    @app.callback(
        [
            Output("auth-status-display", "children"),
            Output("login-form", "style"),
            Output("success-section", "children"),
            Output("success-section", "style"),
            Output("sync-wellness-button", "disabled"),
            Output("session-store", "data", allow_duplicate=True),  # Update global session
        ],
        [Input("garmin-page-location", "pathname")],
        [State("session-store", "data")],
        prevent_initial_call=False,
    )
    def check_auth_on_load(pathname, session_data):
        """Check authentication status when page loads."""
        if pathname != "/garmin":
            # Not on garmin page, no update needed
            return "", {}, [], {"display": "none"}, True, session_data or {}

        # Check if we have existing session data indicating authentication
        session_data = session_data or {}

        if session_data.get("garmin_authenticated"):
            # Already authenticated, show success state
            success_content = [
                dbc.Alert(
                    [
                        html.H4("✅ Already Connected!", className="mb-2"),
                        html.P(f"Authenticated as: {session_data.get('garmin_email', 'Unknown')}", className="mb-2"),
                        html.P(
                            "You can now sync your wellness data or navigate to the Stats page to view your data.",
                            className="mb-0",
                        ),
                    ],
                    color="success",
                )
            ]

            return (
                "",  # auth-status-display
                {"display": "none"},  # login-form hidden
                success_content,  # success-section content
                {"display": "block"},  # success-section visible
                False,  # sync button enabled
                session_data,  # session data unchanged
            )

        else:
            # Not authenticated, show login form
            return (
                "",  # auth-status-display
                {"display": "block"},  # login-form visible
                [],  # success-section empty
                {"display": "none"},  # success-section hidden
                True,  # sync button disabled
                session_data,  # session data unchanged
            )

    # Handle Garmin login (existing callback enhanced)
    @app.callback(
        [
            Output("login-status", "children"),
            Output("mfa-section", "children"),
            Output("mfa-section", "style"),
            Output("success-section", "children", allow_duplicate=True),
            Output("success-section", "style", allow_duplicate=True),
            Output("login-form", "style", allow_duplicate=True),
            Output("login-status-store", "data"),
            Output("sync-wellness-button", "disabled", allow_duplicate=True),
            Output("session-store", "data", allow_duplicate=True),  # Update global session
        ],
        [Input("login-button", "n_clicks")],
        [
            State("garmin-email", "value"),
            State("garmin-password", "value"),
            State("remember-me-checkbox", "value"),
            State("login-status-store", "data"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_garmin_login(n_clicks, email, password, remember_me, store_data, session_data):
        if not ctx.triggered or not n_clicks:
            return "", [], {"display": "none"}, [], {"display": "none"}, {}, {}, True, session_data or {}

        if not email or not password:
            return (
                dbc.Alert("Please enter both email and password.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
                True,
                session_data or {},
            )

        client = GarminConnectClient()
        result = client.authenticate(email, password, remember_me=remember_me)

        # Debug logging to track what's happening
        logger.info(f"Authentication result: {result}")
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")

        if result["status"] == "MFA_REQUIRED":
            logger.info("🔐 MFA_REQUIRED status detected, creating MFA dialog")
            mfa_content = [
                dbc.Alert(
                    "Multi-Factor Authentication required. Please enter your MFA code.", color="info", className="mb-3"
                ),
                dbc.Form(
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Label("MFA Code", html_for="mfa-code"),
                                dbc.Input(
                                    type="text",
                                    id="mfa-code",
                                    placeholder="Enter 6-digit MFA code",
                                    maxLength=6,
                                    pattern="[0-9]{6}",
                                    required=True,
                                    className="mb-3",
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-key me-2"), "Verify MFA"],
                                    id="mfa-verify-button",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                ),
                            ],
                            width=12,
                        )
                    )
                ),
            ]
            return (
                "",
                mfa_content,
                {"display": "block"},
                [],
                {"display": "none"},
                {"display": "none"},
                {
                    "mfa_required": True,
                    "email": email,
                    "password": password,
                    "remember_me": remember_me,
                    "mfa_context": result.get("mfa_context"),
                    "mfa_content": mfa_content,
                },
                True,  # Keep sync button disabled during MFA
                session_data or {},  # Don't update session yet
            )

        elif result["status"] == "SUCCESS":
            success_content = [
                dbc.Alert(
                    [
                        html.H4("Login Successful!"),
                        html.P(f"Connected to Garmin account: {email}"),
                        html.Hr(),
                        html.P("You can now sync your wellness data or visit the Stats page to view your data."),
                        html.A("📊 View Stats Dashboard", href="/stats", className="btn btn-outline-primary"),
                    ],
                    color="success",
                )
            ]

            # Update global session with authentication status
            updated_session = session_data or {}
            updated_session.update(
                {
                    "garmin_authenticated": True,
                    "garmin_email": email,
                    "garmin_auth_time": str(ctx.triggered[0]["timestamp"]) if ctx.triggered else None,
                }
            )

            return (
                "",
                [],
                {"display": "none"},
                success_content,
                {"display": "block"},
                {"display": "none"},
                {"logged_in": True, "email": email},
                False,  # Enable sync button
                updated_session,  # Update global session
            )

        else:
            return (
                dbc.Alert("Authentication failed. Check credentials.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                {},
                True,
                session_data or {},
            )

    # Handle MFA verification (existing callback)
    @app.callback(
        [
            Output("login-status", "children", allow_duplicate=True),
            Output("mfa-section", "children", allow_duplicate=True),
            Output("mfa-section", "style", allow_duplicate=True),
            Output("success-section", "children", allow_duplicate=True),
            Output("success-section", "style", allow_duplicate=True),
            Output("login-form", "style", allow_duplicate=True),
            Output("login-status-store", "data", allow_duplicate=True),
            Output("sync-wellness-button", "disabled", allow_duplicate=True),
            Output("session-store", "data", allow_duplicate=True),
        ],
        [Input("mfa-verify-button", "n_clicks")],
        [State("mfa-code", "value"), State("login-status-store", "data"), State("session-store", "data")],
        prevent_initial_call=True,
    )
    def handle_mfa_verification(n_clicks, mfa_code, store_data, session_data):
        from dash import no_update

        if not ctx.triggered or not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        if not store_data.get("mfa_required"):
            return (
                dbc.Alert("Invalid MFA state.", color="danger"),
                [],
                {"display": "none"},
                [],
                {"display": "none"},
                {},
                store_data,
                True,
                session_data or {},
            )

        if not mfa_code or len(mfa_code) != 6:
            return (
                dbc.Alert("Enter a valid 6-digit MFA code.", color="danger"),
                store_data.get("mfa_content", []),
                {"display": "block"},
                [],
                {"display": "none"},
                {"display": "none"},
                store_data,
                True,
                session_data or {},
            )

        client = GarminConnectClient()
        email, password = store_data["email"], store_data["password"]

        mfa_context = None
        if store_data.get("mfa_context"):
            try:
                mfa_context = pickle.loads(base64.b64decode(store_data["mfa_context"]))
            except Exception as e:
                logger.error(f"Failed to deserialize MFA context: {e}")

        def web_mfa_callback():
            return mfa_code

        result = client.authenticate(
            email,
            password,
            mfa_callback=web_mfa_callback,
            remember_me=store_data.get("remember_me", False),
            mfa_context=mfa_context,
        )

        if result["status"] == "SUCCESS":
            success_content = [
                dbc.Alert(
                    [
                        html.H4("Login Successful!"),
                        html.P(f"Connected to Garmin account: {email}"),
                        html.Hr(),
                        html.P("You can now sync your wellness data or visit the Stats page to view your data."),
                        html.A("📊 View Stats Dashboard", href="/stats", className="btn btn-outline-primary"),
                    ],
                    color="success",
                )
            ]

            # Update global session with authentication status
            updated_session = session_data or {}
            updated_session.update(
                {
                    "garmin_authenticated": True,
                    "garmin_email": email,
                    "garmin_auth_time": str(ctx.triggered[0]["timestamp"]) if ctx.triggered else None,
                }
            )

            return (
                "",
                [],
                {"display": "none"},
                success_content,
                {"display": "block"},
                {"display": "none"},
                {"logged_in": True, "email": email},
                False,  # Enable sync button
                updated_session,
            )

        return (
            dbc.Alert("MFA verification failed.", color="danger"),
            store_data.get("mfa_content", []),
            {"display": "block"},
            [],
            {"display": "none"},
            {"display": "none"},
            store_data,
            True,
            session_data or {},
        )

    # Handle wellness data sync
    @app.callback(
        [
            Output("sync-status", "children"),
            Output("sync-progress", "style"),
            Output("sync-progress-bar", "value"),
            Output("sync-progress-text", "children"),
        ],
        [Input("sync-wellness-button", "n_clicks")],
        [
            State("sync-period", "value"),
            State("sync-data-types", "value"),
            State("session-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_wellness_sync(n_clicks, sync_period, data_types, session_data):
        if not n_clicks or not session_data.get("garmin_authenticated"):
            return "", {"display": "none"}, 0, ""

        try:
            days = int(sync_period or 30)

            # Show progress
            sync_status = dbc.Alert(
                [
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    "Synchronizing wellness data...",
                ],
                color="info",
            )

            # Perform sync
            results = sync_garmin_wellness_data(days)

            # Create results summary
            total_inserted = sum(r[0] for r in results.values())
            total_updated = sum(r[1] for r in results.values())

            if total_inserted + total_updated > 0:
                result_items = []
                for data_type, (inserted, updated) in results.items():
                    if inserted + updated > 0:
                        result_items.append(html.Li(f"{data_type.title()}: {inserted} new, {updated} updated"))

                success_status = dbc.Alert(
                    [
                        html.H5("✅ Sync Complete!", className="mb-2"),
                        html.P(
                            f"Successfully synchronized {total_inserted + total_updated} records:", className="mb-2"
                        ),
                        html.Ul(result_items, className="mb-2"),
                        html.P("Data is now available in the Stats dashboard.", className="mb-0"),
                        html.A("📊 View Your Stats", href="/stats", className="btn btn-outline-success mt-2"),
                    ],
                    color="success",
                )
            else:
                success_status = dbc.Alert(
                    [
                        html.H5("ℹ️ Sync Complete", className="mb-2"),
                        html.P("No new data found to sync. Your data is already up to date.", className="mb-0"),
                    ],
                    color="info",
                )

            return success_status, {"display": "none"}, 100, "Complete"

        except Exception as e:
            logger.error(f"Wellness sync failed: {e}")
            error_status = dbc.Alert(
                [
                    html.H5("❌ Sync Failed", className="mb-2"),
                    html.P(f"Error: {str(e)}", className="mb-0"),
                ],
                color="danger",
            )
            return error_status, {"display": "none"}, 0, "Failed"
