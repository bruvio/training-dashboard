"""
garmin_client/client.py

Thin wrapper around `python-garminconnect` with token restore, MFA and helpers.

Hardened for Docker & first-run:
- Uses ONLY python-garminconnect (no direct garth.* calls).
- Never creates placeholder token files.
- Restores session ONLY when both token files exist AND look valid.
- On first credential login/MFA, temporarily unsets env that can trigger token reads
  (GARMINTOKENS/GARTH_HOME), then saves tokens afterward.
- Quarantines invalid token files to avoid Pydantic validation errors.
- Falls back to writable locations (/data/garmin_tokens, /tmp/garmin_tokens) if the
  primary token dir cannot be written.
"""

from __future__ import annotations

import os
import json
import time
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager

try:
    from garminconnect import (  # type: ignore
        Garmin,
        GarminConnectAuthenticationError,
        GarminConnectConnectionError,
        GarminConnectTooManyRequestsError,
    )

    # Import the enum for proper type hints
    from garminconnect import Garmin as GarminAPI
except Exception:  # pragma: no cover
    Garmin = None  # type: ignore
    GarminConnectAuthenticationError = Exception  # type: ignore
    GarminConnectConnectionError = Exception  # type: ignore
    GarminConnectTooManyRequestsError = Exception  # type: ignore

logger = logging.getLogger(__name__)


def _to_iso(d: Union[str, date, datetime]) -> str:
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    return str(d)


class GarminAuthError(RuntimeError):
    pass


# ---------------- Token store utilities ----------------


def _fallback_token_dirs() -> List[Path]:
    """Writable fallbacks commonly mounted in Docker images (order matters)."""
    return [Path("/data/garmin_tokens"), Path("/tmp/garmin_tokens")]


def _read_json(fp: Path) -> Dict[str, Any]:
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _looks_like_oauth1(fp: Path) -> bool:
    d = _read_json(fp)
    return all(isinstance(d.get(k), str) and d[k] for k in ("oauth_token", "oauth_token_secret"))


def _looks_like_oauth2(fp: Path) -> bool:
    d = _read_json(fp)
    return all(isinstance(d.get(k), str) and d[k] for k in ("access_token", "refresh_token"))


def _has_valid_token_store(dirpath: Path) -> bool:
    """True iff both token files exist and appear valid (avoid Pydantic errors)."""
    o1 = dirpath / "oauth1_token.json"
    o2 = dirpath / "oauth2_token.json"
    if not (o1.exists() and o2.exists()):
        return False
    return _looks_like_oauth1(o1) and _looks_like_oauth2(o2)


def _sanitize_token_store(dirpath: Path) -> None:
    """
    If token files exist but fail validation, rename them with a .corrupt.<ts> suffix
    so the library won't try to parse them and bail.
    """
    o1 = dirpath / "oauth1_token.json"
    o2 = dirpath / "oauth2_token.json"
    ts = time.strftime("%Y%m%d-%H%M%S")

    if o1.exists() and not _looks_like_oauth1(o1):
        new = o1.with_suffix(o1.suffix + f".corrupt.{ts}")
        try:
            o1.rename(new)
            logger.warning("Quarantined invalid token file: %s -> %s", o1, new)
        except Exception as e:
            logger.warning("Failed to quarantine %s: %s", o1, e)

    if o2.exists() and not _looks_like_oauth2(o2):
        new = o2.with_suffix(o2.suffix + f".corrupt.{ts}")
        try:
            o2.rename(new)
            logger.warning("Quarantined invalid token file: %s -> %s", o2, new)
        except Exception as e:
            logger.warning("Failed to quarantine %s: %s", o2, e)


def _ensure_writable_dir_or_fallback(primary: Path) -> Path:
    """
    Ensure we can write tokens somewhere.
    Try primary, then fallbacks; return the chosen dir.
    """
    try:
        primary.mkdir(parents=True, exist_ok=True)
        (primary / ".writable.check").write_text("ok", encoding="utf-8")
        (primary / ".writable.check").unlink(missing_ok=True)
        return primary
    except Exception as e:
        logger.warning("Primary token dir %s not writable (%s). Trying fallbacks...", primary, e)

    for fb in _fallback_token_dirs():
        try:
            fb.mkdir(parents=True, exist_ok=True)
            (fb / ".writable.check").write_text("ok", encoding="utf-8")
            (fb / ".writable.check").unlink(missing_ok=True)
            logger.info("Using fallback token directory %s. Set GARMINTOKENS=%s to persist here.", fb, fb)
            return fb
        except Exception as e2:
            logger.warning("Fallback token dir %s not usable: %s", fb, e2)

    raise GarminAuthError(
        f"No writable token directory available. "
        f"Check permissions for {primary} or bind-mount a writable dir "
        f"(e.g. ./data/garmin_tokens:/home/garmin/.garminconnect) and/or set GARMINTOKENS."
    )


@contextmanager
def _temporarily_unset_env(keys: List[str]):
    """
    Temporarily remove environment variables (e.g., GARMINTOKENS/GARTH_HOME)
    so first-run credential login doesn't try to read empty token stores.
    """
    old: Dict[str, Optional[str]] = {k: os.environ.pop(k, None) for k in keys}
    try:
        yield
    finally:
        for k, v in old.items():
            if v is not None:
                os.environ[k] = v


# ---------------- Client ----------------


class GarminConnectClient:
    """
    Wrapper around cyberjunky/python-garminconnect with a resilient token store.
    """

    def __init__(self, token_dir: Optional[Union[str, Path]] = None) -> None:
        token_env = os.getenv("GARMINTOKENS")
        if token_dir is None:
            token_dir = token_env or "~/.garminconnect"
        self.token_dir = Path(os.path.expanduser(str(token_dir)))
        self.api: Optional[Garmin] = None
        self._pending_mfa_ctx: Optional[Any] = None
        self._pending_remember: bool = False
        self._username: Optional[str] = None

    # -------- Session helpers

    def is_authenticated(self) -> bool:
        return self.api is not None

    def username(self) -> Optional[str]:
        return self._username

    # -------- Internals

    def _boot_api_from_tokens(self, dirpath: Path) -> bool:
        """Attempt to boot a Garmin() client from a token directory."""
        if Garmin is None:
            raise GarminAuthError("garminconnect library not installed")
        try:
            g = Garmin()
            g.login(str(dirpath))  # loads OAuth token store
            self.api = g
            try:
                self._username = (self.api.get_full_name() or "").split(" ")[0] or "garmin"
            except Exception:
                self._username = "garmin"
            logger.info("Loaded Garmin tokens from %s", dirpath)
            self.token_dir = dirpath  # adopt the working token dir
            return True
        except Exception as e:
            logger.info("No valid Garmin session in %s: %s", dirpath, e)
            return False

    def _save_tokens_with_fallback(self) -> None:
        """
        Persist tokens using the API's internal garth client to the primary dir,
        else fall back to a writable location.
        """
        if self.api is None:
            raise GarminAuthError("Not authenticated; cannot persist tokens")

        # Try primary
        try:
            chosen = _ensure_writable_dir_or_fallback(self.token_dir)
            # .garth.dump writes oauth1/2 json files
            self.api.garth.dump(str(chosen))
            self.token_dir = chosen
            return
        except PermissionError as e:
            logger.warning("Cannot write tokens to %s: %s. Trying fallbacks...", self.token_dir, e)
        except Exception as e:
            logger.warning("Failed to write tokens to %s: %s. Trying fallbacks...", self.token_dir, e)

        # Try fallbacks
        for fb in _fallback_token_dirs():
            try:
                fb.mkdir(parents=True, exist_ok=True)
                self.api.garth.dump(str(fb))
                logger.info("Saved tokens to fallback dir %s. Consider setting GARMINTOKENS=%s", fb, fb)
                self.token_dir = fb
                return
            except Exception as e2:
                logger.warning("Fallback %s also failed: %s", fb, e2)

        raise GarminAuthError(
            f"Failed to save Garmin tokens; check permissions for {self.token_dir} "
            f"or mount a writable dir via GARMINTOKENS or /data/garmin_tokens."
        )

    # -------- Bootstrap session

    def load_session(self) -> Dict[str, Any]:
        """
        Try loading a previous session from token directory or fallbacks.
        Only attempt restore if token files exist and look valid.
        """
        try:
            if Garmin is None:
                raise GarminAuthError("garminconnect library not installed")

            # Primary location first
            if self.token_dir.exists():
                if _has_valid_token_store(self.token_dir) and self._boot_api_from_tokens(self.token_dir):
                    return {"is_authenticated": True, "username": self._username, "mfa_required": False}
                else:
                    logger.info("Token directory %s exists but has no valid tokens yet.", self.token_dir)
            else:
                logger.info(
                    "Token directory %s does not exist yet; it will be created on first successful login.",
                    self.token_dir,
                )

            # Fallbacks (only if they have valid tokens)
            for fb in _fallback_token_dirs():
                if fb.exists() and _has_valid_token_store(fb) and self._boot_api_from_tokens(fb):
                    return {"is_authenticated": True, "username": self._username, "mfa_required": False}

            # None worked
            self.api = None
            self._username = None
            return {"is_authenticated": False, "username": None, "mfa_required": False}

        except (GarminConnectAuthenticationError, GarminConnectConnectionError) as e:
            logger.info("Error while loading session: %s", e)
            self.api = None
            self._username = None
            return {"is_authenticated": False, "username": None, "mfa_required": False}

    # -------- Interactive login (python-garminconnect only)

    def login(self, email: str, password: str, remember: bool = True) -> Dict[str, Any]:
        """
        Start a credential login with python-garminconnect.
        - Ensure token dir is writable (choose fallback if needed).
        - Temporarily unset env (GARMINTOKENS/GARTH_HOME) to prevent first-run token reads.
        - Proceed with credential login; persist tokens if requested.
        """
        if Garmin is None:
            raise GarminAuthError("garminconnect library not installed")
        try:
            # Choose a writable target dir up front (but do not create any token files)
            self.token_dir = _ensure_writable_dir_or_fallback(self.token_dir)

            # Ensure bad files (if any) don't poison the flow
            _sanitize_token_store(self.token_dir)

            g = Garmin(email=email, password=password, return_on_mfa=True)

            # On some stacks, env vars can make the underlying auth try to read tokens
            with _temporarily_unset_env(["GARMINTOKENS", "GARTH_HOME"]):
                result1, ctx = g.login()  # credential login flow

            if result1 == "needs_mfa":
                self.api = g
                self._pending_mfa_ctx = ctx
                self._pending_remember = bool(remember)
                return {"success": True, "mfa_required": True, "username": None}

            # Logged in without MFA
            self.api = g
            try:
                self._username = (self.api.get_full_name() or "").split(" ")[0]
            except Exception:
                self._username = "garmin"
            if remember:
                self._save_tokens_with_fallback()

            return {"success": True, "mfa_required": False, "username": self._username}

        except (GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            raise GarminAuthError(str(e)) from e
        except FileNotFoundError as e:
            # If any lib attempts to read token files mid-flow, treat as first-run and retry once
            logger.warning("First-run token read attempt failed (%s). Retrying login fresh.", e)
            try:
                with _temporarily_unset_env(["GARMINTOKENS", "GARTH_HOME"]):
                    result1, ctx = g.login()
                if result1 == "needs_mfa":
                    self.api = g
                    self._pending_mfa_ctx = ctx
                    self._pending_remember = bool(remember)
                    return {"success": True, "mfa_required": True, "username": None}
                self.api = g
                if remember:
                    self._save_tokens_with_fallback()
                self._username = (self.api.get_full_name() or "garmin").split(" ")[0]
                return {"success": True, "mfa_required": False, "username": self._username}
            except Exception as e2:
                raise GarminAuthError(str(e2)) from e2

    def submit_mfa(self, code: str, remember: Optional[bool] = None) -> Dict[str, Any]:
        """
        Complete the MFA challenge that was initiated during login().
        """
        if self.api is None or self._pending_mfa_ctx is None:
            raise GarminAuthError("No MFA challenge in progress")
        try:
            # Ensure token dir is sane & env doesn't force token reads mid-resume
            self.token_dir = _ensure_writable_dir_or_fallback(self.token_dir)
            _sanitize_token_store(self.token_dir)

            with _temporarily_unset_env(["GARMINTOKENS", "GARTH_HOME"]):
                self.api.resume_login(self._pending_mfa_ctx, str(code).strip())

            self._pending_mfa_ctx = None

            try:
                self._username = (self.api.get_full_name() or "").split(" ")[0]
            except Exception:
                self._username = "garmin"
            if remember if remember is not None else self._pending_remember:
                self._save_tokens_with_fallback()

            return {"success": True, "username": self._username}

        except (GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError) as e:
            raise GarminAuthError(str(e)) from e
        except FileNotFoundError as e:
            # Retry once without env pointing at a token dir
            logger.warning("First-run token read attempt during MFA failed (%s). Retrying once.", e)
            try:
                with _temporarily_unset_env(["GARMINTOKENS", "GARTH_HOME"]):
                    self.api.resume_login(self._pending_mfa_ctx, str(code).strip())
                self._pending_mfa_ctx = None
                if remember if remember is not None else self._pending_remember:
                    self._save_tokens_with_fallback()
                self._username = (self.api.get_full_name() or "garmin").split(" ")[0]
                return {"success": True, "username": self._username}
            except Exception as e2:
                raise GarminAuthError(str(e2)) from e2

    # -------- Data helpers used by sync page

    def get_activities_by_date(
        self,
        start: Union[str, date, datetime],
        end: Union[str, date, datetime],
        activity_type: str = "",
    ) -> List[Dict[str, Any]]:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        return self.api.get_activities_by_date(_to_iso(start), _to_iso(end), activity_type)

    def get_activities(self, start: int = 0, limit: int = 100, activity_type: str = "") -> List[Dict[str, Any]]:
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        return self.api.get_activities(start, limit, activity_type)

    def download_activity_fit(self, activity_id: Union[int, str], dest_dir: Union[str, Path]) -> Path:
        """Download a single activity as .FIT file and return the path."""
        if self.api is None:
            raise GarminAuthError("Not authenticated")
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)

        # Download the original format (usually a ZIP containing the FIT file)
        content = self.api.download_activity(activity_id, dl_fmt=GarminAPI.ActivityDownloadFormat.ORIGINAL)

        # Check if it's a ZIP file
        if content.startswith(b"PK"):
            # It's a ZIP file, extract the FIT file
            import zipfile
            import io

            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                # Look for .FIT files in the ZIP
                fit_files = [name for name in zip_file.namelist() if name.lower().endswith(".fit")]
                if not fit_files:
                    raise ValueError(f"No .FIT file found in downloaded ZIP for activity {activity_id}")

                # Extract the first FIT file
                fit_filename = fit_files[0]
                fit_content = zip_file.read(fit_filename)

                out = dest / f"{activity_id}.fit"
                out.write_bytes(fit_content)
                return out
        else:
            # It's already a FIT file
            out = dest / f"{activity_id}.fit"
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
