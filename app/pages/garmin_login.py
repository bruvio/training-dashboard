"""
Garmin Connect login and data synchronization page.
(Updated v7: adopts tokens from temporary client to garth.client and avoids profile calls during MFA.)
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

from dash import Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

logger = logging.getLogger(__name__)

# Attempt project imports; otherwise use built-ins below.
get_client = None
GarminAuthError = None
sync_recent = None

try:
    from garmin_client.client import get_client as _gc, GarminAuthError as _gae  # type: ignore

    get_client, GarminAuthError = _gc, _gae
except Exception:
    try:
        from client import get_client as _gc2, GarminAuthError as _gae2  # type: ignore

        get_client, GarminAuthError = _gc2, _gae2
    except Exception:
        pass

try:
    from garmin_client.garth_sync import sync_recent as _sr, sync_health_data as _shd, sync_comprehensive as _sc  # type: ignore

    sync_recent = _sr
    sync_health_data = _shd
    sync_comprehensive = _sc
except Exception:
    try:
        from garth_sync import sync_recent as _sr2, sync_health_data as _shd2, sync_comprehensive as _sc2  # type: ignore

        sync_recent = _sr2
        sync_health_data = _shd2
        sync_comprehensive = _sc2
    except Exception:
        pass

# Built-in fallbacks when project imports are unavailable
if get_client is None or GarminAuthError is None:

    class GarminAuthError(Exception):
        pass

    try:
        import json
        import garth  # type: ignore
    except Exception:
        garth = None

    DEFAULT_TOKEN_PATH = Path.home() / ".garmin" / "tokens.json"

    class _MFAKick(Exception):
        pass

    def _adopt_tokens(src):
        try:
            garth.client.oauth1_token = getattr(src, "oauth1_token", None)
            garth.client.oauth2_token = getattr(src, "oauth2_token", None)
            if hasattr(src, "session"):
                garth.client.session = src.session
        except Exception as e:
            logger.debug("Token adoption warning: %s", e)

    class _FallbackGarminClient:
        def __init__(self, token_file: Path = DEFAULT_TOKEN_PATH):
            self.token_file = token_file
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            self._authenticated = False
            self._pending_mfa = False
            self._username: Optional[str] = None

            self._mfa_ctx: Optional[Any] = None  # for newer garth
            self._pending_creds: Optional[tuple[str, str]] = None  # for older garth
            self._remember_after_mfa: bool = False

            self.load_session()

        @property
        def is_authenticated(self) -> bool:
            return self._authenticated

        @property
        def username(self) -> Optional[str]:
            return self._username

        def _save_tokens(self):
            if garth is None:
                return
            try:
                data = garth.client.dump_tokens()
                self.token_file.write_text(json.dumps(data))
            except Exception as e:
                logger.exception("Failed to save tokens: %s", e)

        def _load_tokens(self) -> bool:
            if garth is None or not self.token_file.exists():
                return False
            try:
                data = json.loads(self.token_file.read_text())
                garth.client.load_tokens(data)
                garth.client.refresh_oauth_token()
                return True
            except Exception as e:
                logger.warning("Existing tokens invalid or expired: %s", e)
                return False

        def load_session(self) -> bool:
            if garth is None:
                self._authenticated = False
                self._username = None
                self._pending_mfa = False
                self._mfa_ctx = None
                self._pending_creds = None
                self._remember_after_mfa = False
                return False
            ok = self._load_tokens()
            self._authenticated = bool(ok)
            if self._authenticated:
                self._username = "Garmin User"
            return self._authenticated

        def login(self, email: str, password: str, remember: bool = False) -> Dict:
            if garth is None:
                self._authenticated = True
                self._username = email.split("@")[0] if "@" in email else email
                self._pending_mfa = False
                return {"authenticated": True, "username": self._username, "dev_mode": True}
            if hasattr(garth, "resume_login"):
                try:
                    result1, ctx = garth.login(email, password, return_on_mfa=True)
                    if result1 == "needs_mfa":
                        self._pending_mfa = True
                        self._mfa_ctx = ctx
                        self._remember_after_mfa = bool(remember)
                        return {"mfa_required": True}
                    self._pending_mfa = False
                    self._authenticated = True
                    self._mfa_ctx = None
                    self._username = email
                    if remember:
                        self._save_tokens()
                    return {"authenticated": True, "username": self._username}
                except Exception as e:
                    logger.exception("Login failed: %s", e)
                    raise GarminAuthError(str(e)) from e
            # older garth
            try:
                c = garth.Client()

                def _kick():
                    raise _MFAKick()

                c.login(email, password, prompt_mfa=_kick)
                _adopt_tokens(c)
                self._pending_mfa = False
                self._authenticated = True
                self._pending_creds = None
                self._username = email
                if remember:
                    self._save_tokens()
                return {"authenticated": True, "username": self._username}
            except _MFAKick:
                self._pending_mfa = True
                self._pending_creds = (email, password)
                self._remember_after_mfa = bool(remember)
                return {"mfa_required": True}
            except Exception as e:
                logger.exception("Login failed: %s", e)
                raise GarminAuthError(str(e)) from e

        def submit_mfa(self, code: str, remember: bool = False) -> Dict:
            if garth is None:
                self._pending_mfa = False
                self._authenticated = True
                return {"authenticated": True, "username": self._username or "Garmin User", "dev_mode": True}
            if hasattr(garth, "resume_login"):
                if not self._mfa_ctx:
                    raise GarminAuthError("No MFA context. Start login first.")
                try:
                    _oauth1, _oauth2 = garth.resume_login(self._mfa_ctx, code)
                    self._pending_mfa = False
                    self._authenticated = True
                    self._mfa_ctx = None
                    self._username = "Garmin User"
                    if self._remember_after_mfa or remember:
                        self._save_tokens()
                    return {"authenticated": True, "username": self._username}
                except Exception as e:
                    logger.exception("MFA verification failed: %s", e)
                    raise GarminAuthError(str(e)) from e
            if not self._pending_creds:
                raise GarminAuthError("No pending credentials for MFA. Please login again.")
            email, password = self._pending_creds
            try:
                c = garth.Client()
                c.login(email, password, prompt_mfa=lambda: code)
                _adopt_tokens(c)
                self._pending_mfa = False
                self._authenticated = True
                self._pending_creds = None
                self._username = email
                if self._remember_after_mfa or remember:
                    self._save_tokens()
                return {"authenticated": True, "username": self._username}
            except Exception as e:
                logger.exception("MFA verification failed: %s", e)
                raise GarminAuthError(str(e)) from e

    _singleton = None

    def get_client():
        global _singleton
        if _singleton is None:
            _singleton = _FallbackGarminClient()
        return _singleton


if sync_recent is None or sync_health_data is None or sync_comprehensive is None:
    try:
        from datetime import datetime, timedelta, timezone
        import garth  # type: ignore
    except Exception:
        garth = None

    def sync_recent(days: int):
        if garth is None:
            return {
                "ok": True,
                "activities_fetched": 0,
                "wellness_synced": False,
                "dev_mode": True,
                "msg": f"(dev) Would sync last {days} days of activities.",
            }
        try:
            c = garth.client
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days)
            activities = c.activities(start=start.date(), limit=500)
            count = 0
            for _ in activities:
                count += 1
            return {
                "ok": True,
                "activities_fetched": count,
                "wellness_synced": False,
                "msg": f"Synced {count} activities from the last {days} days.",
            }
        except Exception as e:
            logger.exception("Sync failed: %s", e)
            return {"ok": False, "error": str(e)}

    def sync_health_data(days: int, data_types: list = None):
        """Fallback health data sync function."""
        if garth is None:
            return {
                "ok": True,
                "wellness_synced": False,
                "dev_mode": True,
                "msg": f"(dev) Would sync {days} days of health data.",
                "data": {}
            }
        return {
            "ok": False,
            "error": "Health data sync not available - please update garth_sync module"
        }

    def sync_comprehensive(days: int):
        """Fallback comprehensive sync function."""
        activity_result = sync_recent(days)
        health_result = sync_health_data(days)
        return {
            "ok": activity_result.get("ok", False) and health_result.get("ok", False),
            "activities_fetched": activity_result.get("activities_fetched", 0),
            "wellness_synced": health_result.get("wellness_synced", False),
            "msg": f"Activities: {activity_result.get('msg', 'Failed')} | Health: {health_result.get('msg', 'Failed')}"
        }


# -------- Dash layout and callbacks (unchanged) --------
def layout():
    return dbc.Container(
        [
            dbc.Row(
                dbc.Col(
                    [
                        html.H1(
                            [html.I(className="fas fa-user-lock me-3"), "Garmin Connect Integration"], className="mb-2"
                        ),
                        html.P(
                            "Connect to your Garmin Connect account to download and synchronize your activity data automatically.",
                            className="text-muted mb-4",
                        ),
                    ],
                    width=12,
                )
            ),
            dcc.Store(id="garmin-auth-store", storage_type="session"),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H5("Login to Garmin Connect", className="mb-0")),
                            dbc.CardBody(
                                [
                                    html.Div(id="garmin-status-alert"),
                                    html.Div(
                                        id="garmin-login-form",
                                        children=[
                                            dbc.Form(
                                                [
                                                    dbc.Row(
                                                        dbc.Col(
                                                            [
                                                                dbc.Label("Email / Username", html_for="garmin-email"),
                                                                dbc.Input(
                                                                    id="garmin-email",
                                                                    type="text",
                                                                    placeholder="your@email.com",
                                                                    autoComplete="username",
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
                                                                    id="garmin-password",
                                                                    type="password",
                                                                    placeholder="••••••••",
                                                                    autoComplete="current-password",
                                                                ),
                                                            ],
                                                            width=12,
                                                            className="mb-3",
                                                        )
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dbc.Checkbox(
                                                                    id="garmin-remember-me",
                                                                    label="Remember me on this device",
                                                                    value=True,
                                                                ),
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                dbc.Button(
                                                                    "Login",
                                                                    id="garmin-login-btn",
                                                                    color="primary",
                                                                    className="w-100",
                                                                    n_clicks=0,
                                                                ),
                                                                width=6,
                                                            ),
                                                        ],
                                                        className="g-2 mb-1",
                                                    ),
                                                ]
                                            )
                                        ],
                                    ),
                                    html.Div(
                                        id="garmin-mfa-form",
                                        hidden=True,
                                        children=[
                                            html.Hr(),
                                            html.P("Two-factor authentication required (TOTP).", className="mb-1"),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dbc.Input(
                                                            id="garmin-mfa-code",
                                                            type="text",
                                                            placeholder="Enter 6-digit code",
                                                            maxLength=8,
                                                            inputMode="numeric",
                                                        ),
                                                        width=8,
                                                    ),
                                                    dbc.Col(
                                                        dbc.Button(
                                                            "Verify",
                                                            id="garmin-mfa-verify-btn",
                                                            color="secondary",
                                                            className="w-100",
                                                            n_clicks=0,
                                                        ),
                                                        width=4,
                                                    ),
                                                ],
                                                className="g-2",
                                            ),
                                        ],
                                    ),
                                ]
                            ),
                        ]
                    ),
                    width=12,
                )
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H5("Synchronize Health & Activity Data", className="mb-0")),
                            dbc.CardBody(
                                [
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Days to sync"),
                                                            dcc.Dropdown(
                                                                id="garmin-days-dropdown",
                                                                options=[
                                                                    {"label": "7 days", "value": 7},
                                                                    {"label": "14 days", "value": 14},
                                                                    {"label": "30 days", "value": 30},
                                                                    {"label": "90 days", "value": 90},
                                                                ],
                                                                value=7,
                                                                clearable=False,
                                                            ),
                                                        ],
                                                        md=6,
                                                        className="mb-2",
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(" "),
                                                            dbc.Button(
                                                                "Sync Health Data",
                                                                id="garmin-sync-btn",
                                                                color="success",
                                                                className="w-100",
                                                                n_clicks=0,
                                                                disabled=True,
                                                            ),
                                                        ],
                                                        md=6,
                                                        className="mb-2",
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                    html.Div(id="garmin-sync-result"),
                                ]
                            ),
                        ]
                    ),
                    width=12,
                )
            ),
        ],
        className="py-3",
        fluid=True,
    )


def register_callbacks(app):
    @app.callback(
        Output("garmin-auth-store", "data"),
        Output("garmin-status-alert", "children"),
        Input("url", "pathname"),
        prevent_initial_call=False,
    )
    def _bootstrap_auth(_):
        try:
            cli = get_client()
            cli.load_session()
        except Exception as e:
            return (
                {"is_authenticated": False, "username": None, "mfa_required": False},
                dbc.Alert(f"Garmin client error: {e}", color="danger", dismissable=True),
            )
        if getattr(cli, "is_authenticated", False):
            return (
                {"is_authenticated": True, "username": getattr(cli, "username", None), "mfa_required": False},
                dbc.Alert(
                    f"Logged in as {getattr(cli, 'username', 'Garmin User')}.", color="success", dismissable=True
                ),
            )
        return ({"is_authenticated": False, "username": None, "mfa_required": False}, no_update)

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
            cli = get_client()
            result = cli.login(email=email, password=password, remember=bool(remember))
            if result.get("mfa_required"):
                return (
                    {"is_authenticated": False, "username": None, "mfa_required": True},
                    dbc.Alert("Two-factor authentication required. Please enter the code.", color="info"),
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
            cli = get_client()
            result = cli.submit_mfa(code=str(code).strip(), remember=bool(remember))
            return (
                {"is_authenticated": True, "username": result.get("username"), "mfa_required": False},
                dbc.Alert("MFA verified. Logged in successfully.", color="success", dismissable=True),
                True,
            )
        except GarminAuthError as e:
            return no_update, dbc.Alert(f"MFA failed: {e}", color="danger"), False
        except Exception as e:
            return no_update, dbc.Alert(f"MFA error: {e}", color="danger"), False

    @app.callback(
        Output("garmin-sync-btn", "disabled"),
        Input("garmin-auth-store", "data"),
    )
    def _toggle_sync(auth):
        return not (auth and auth.get("is_authenticated"))

    @app.callback(
        Output("garmin-sync-result", "children"),
        Input("garmin-sync-btn", "n_clicks"),
        State("garmin-days-dropdown", "value"),
        State("garmin-auth-store", "data"),
        prevent_initial_call=True,
    )
    def _run_sync(n_clicks, days, auth):
        if not n_clicks:
            raise PreventUpdate
        if not (auth and auth.get("is_authenticated")):
            return dbc.Alert("Please login first to enable data synchronization.", color="warning")
        days = int(days or 7)
        
        # Use comprehensive sync to get both activities and health data
        result = sync_comprehensive(days=days)
        
        if result.get("ok"):
            msg = result.get("msg") or f"Synced last {days} days."
            extra = " (dev mode)" if result.get("dev_mode") else ""
            
            # Show detailed success message for health data
            activities_count = result.get("activities_fetched", 0)
            health_records = result.get("total_health_records", 0)
            wellness_synced = result.get("wellness_synced", False)
            
            if wellness_synced and health_records > 0:
                success_msg = f"✅ Successfully synced {days} days of data:\n"
                success_msg += f"• Activities: {activities_count} records\n"
                success_msg += f"• Health data: {health_records} records (sleep, HRV, steps, stress)"
                success_msg += extra
            else:
                success_msg = msg + extra
            
            return dbc.Alert(success_msg, color="success", dismissable=True, style={"white-space": "pre-line"})
        else:
            error_msg = result.get("error") or result.get("msg") or "unknown error"
            return dbc.Alert(f"Sync failed: {error_msg}", color="danger")
