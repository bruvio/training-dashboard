"""
garmin_client/client.py

Thin wrapper around `python-garminconnect` with token restore, MFA and helpers.
"""

from __future__ import annotations

import os
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError  # type: ignore
    from garth.exc import GarthHTTPError  # type: ignore
except Exception:  # pragma: no cover
    Garmin = None  # type: ignore
    GarminConnectAuthenticationError = Exception  # type: ignore
    GarminConnectConnectionError = Exception  # type: ignore
    GarminConnectTooManyRequestsError = Exception  # type: ignore
    GarthHTTPError = Exception  # type: ignore

logger = logging.getLogger(__name__)


def _to_iso(d: Union[str, date, datetime]) -> str:
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


class GarminAuthError(RuntimeError):
    pass


class GarminConnectClient:
    """
    Wrapper around cyberjunky/python-garminconnect.
    """

    def __init__(
        self,
        token_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        token_env = os.getenv("GARMINTOKENS")
        if token_dir is None:
            token_dir = token_env or "~/.garminconnect"
        self.token_dir = Path(os.path.expanduser(str(token_dir)))
        self.api: Optional[Garmin] = None
        self._pending_mfa_ctx: Optional[Any] = None
        self._pending_remember: bool = False
        self._username: Optional[str] = None

    def is_authenticated(self) -> bool:
        return self.api is not None

    def username(self) -> Optional[str]:
        return self._username

    def load_session(self) -> Dict[str, Any]:
        try:
            if Garmin is None:
                raise GarminAuthError("garminconnect library not installed")
            g = Garmin()
            g.login(str(self.token_dir))
            self.api = g
            try:
                self._username = (self.api.get_full_name() or "").split(" ")[0] or "garmin"
            except Exception:
                self._username = "garmin"
            logger.info("Loaded Garmin tokens from %s", self.token_dir)
            return {"is_authenticated": True, "username": self._username, "mfa_required": False}
        except (FileNotFoundError, GarminConnectAuthenticationError, GarminConnectConnectionError, GarthHTTPError) as e:
            logger.info("No valid Garmin session in %s: %s", self.token_dir, e)
            self.api = None
            self._username = None
            return {"is_authenticated": False, "username": None, "mfa_required": False}

    def login(self, email: str, password: str, remember: bool = True) -> Dict[str, Any]:
        if Garmin is None:
            raise GarminAuthError("garminconnect library not installed")
        try:
            g = Garmin(email=email, password=password, return_on_mfa=True)
            result1, ctx = g.login()
            if result1 == "needs_mfa":
                self.api = g
                self._pending_mfa_ctx = ctx
                self._pending_remember = bool(remember)
                return {"success": True, "mfa_required": True, "username": None}
            self.api = g
            self._username = (self.api.get_full_name() or "").split(" ")[0]
            if remember:
                self.api.garth.dump(str(self.token_dir))
            return {"success": True, "mfa_required": False, "username": self._username}
        except (GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarthHTTPError) as e:
            raise GarminAuthError(str(e)) from e

    def submit_mfa(self, code: str, remember: Optional[bool] = None) -> Dict[str, Any]:
        if self.api is None or self._pending_mfa_ctx is None:
            raise GarminAuthError("No MFA challenge in progress")
        try:
            self.api.resume_login(self._pending_mfa_ctx, str(code).strip())
            self._pending_mfa_ctx = None
            self._username = (self.api.get_full_name() or "").split(" ")[0]
            if remember if remember is not None else self._pending_remember:
                self.api.garth.dump(str(self.token_dir))
            return {"success": True, "username": self._username}
        except (GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError, GarthHTTPError) as e:
            raise GarminAuthError(str(e)) from e

    # Data helpers

    def get_activities_by_date(self, start: Union[str, date, datetime], end: Union[str, date, datetime], activity_type: str = "") -> List[Dict[str, Any]]:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        return self.api.get_activities_by_date(_to_iso(start), _to_iso(end), activity_type)

    def get_activities(self, start: int = 0, limit: int = 100, activity_type: str = "") -> List[Dict[str, Any]]:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        return self.api.get_activities(start, limit, activity_type)

    def download_activity_fit(self, activity_id: Union[int, str], dest_dir: Union[str, Path]) -> Path:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        content = self.api.download_activity(activity_id, dl_fmt="fit")
        out = dest_dir / f"{activity_id}.fit"
        out.write_bytes(content)
        return out

    def wellness_summary_for_day(self, d: Union[str, date, datetime]) -> Dict[str, Any]:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        d_iso = _to_iso(d)
        out: Dict[str, Any] = {}
        try:
            out["steps"] = self.api.get_steps_data(d_iso)
        except Exception:
            pass
        try:
            out["stress"] = self.api.get_stress_data(d_iso)
        except Exception:
            pass
        try:
            out["sleep"] = self.api.get_sleep_data(d_iso)
        except Exception:
            pass
        try:
            out["hrv"] = self.api.get_hrv_data(d_iso)
        except Exception:
            pass
        return out