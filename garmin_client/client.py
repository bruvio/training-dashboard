

"""
Garmin Connect Client — ultra-compatible with old/new `garth`.

- MFA: supports both new (resume_login) and old (prompt_mfa) flows.
- Token persistence: works even when `garth.client.dump_tokens()` is missing by
  saving a minimal structure (oauth1_token, oauth2_token) if present; otherwise no-op.
- Never calls API during MFA completion (avoids OAuth1 assertion).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

try:
    import garth  # type: ignore
except Exception:
    garth = None
    logger.warning("garth not available. Client will run in 'dev' mode (no real login).")

DEFAULT_TOKEN_PATH = Path.home() / ".garmin" / "tokens.json"


class GarminAuthError(Exception):
    pass


class _MFAKick(Exception):
    """Internal sentinel to signal MFA is required without prompting."""


def _adopt_tokens(src):
    """
    Copy auth tokens/session from a temporary client instance into garth.client.
    Compatible with older garth that lacks helpers.
    """
    try:
        if hasattr(garth, "client"):
            if hasattr(src, "oauth1_token"):
                setattr(garth.client, "oauth1_token", getattr(src, "oauth1_token"))
            if hasattr(src, "oauth2_token"):
                setattr(garth.client, "oauth2_token", getattr(src, "oauth2_token"))
            if hasattr(src, "session"):
                garth.client.session = src.session
    except Exception as e:
        logger.debug("Token adoption warning: %s", e)


def _dump_tokens_fallback():
    """
    Return a minimal token snapshot even if dump_tokens doesn't exist.
    """
    data = {}
    c = getattr(garth, "client", None)
    if c is None:
        return data
    for key in ("oauth1_token", "oauth2_token"):
        val = getattr(c, key, None)
        # Some garth builds store tokens as objects with .to_dict()
        if hasattr(val, "to_dict"):
            try:
                val = val.to_dict()
            except Exception:
                pass
        data[key] = val
    return data


def _load_tokens_fallback(data: dict):
    """
    Load minimal token snapshot back into garth.client if possible.
    """
    c = getattr(garth, "client", None)
    if c is None:
        return False
    try:
        for key in ("oauth1_token", "oauth2_token"):
            if key in data and data[key]:
                setattr(c, key, data[key])
        return True
    except Exception:
        return False


class GarminClient:
    def __init__(self, token_file: Path = DEFAULT_TOKEN_PATH):
        self.token_file = token_file
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._authenticated = False
        self._pending_mfa = False
        self._username: Optional[str] = None

        # For newer garth (resume_login)
        self._mfa_ctx: Optional[Any] = None

        # For older garth (prompt_mfa two-step)
        self._pending_creds: Optional[Tuple[str, str]] = None
        self._remember_after_mfa: bool = False

        self.load_session()

    # ------------- properties -------------
    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    @property
    def username(self) -> Optional[str]:
        return self._username

    # ------------- token utils -------------
    def _save_tokens(self):
        if garth is None:
            return
        try:
            if hasattr(garth.client, "dump_tokens"):
                data = garth.client.dump_tokens()
            else:
                data = _dump_tokens_fallback()
            if data:
                self.token_file.write_text(json.dumps(data))
        except Exception as e:
            # Log at INFO to avoid alarming noise; not fatal
            logger.info("Skipping token save (not supported on this garth): %s", e)

    def _load_tokens(self) -> bool:
        if garth is None or not self.token_file.exists():
            return False
        try:
            data = json.loads(self.token_file.read_text())
            if hasattr(garth.client, "load_tokens"):
                garth.client.load_tokens(data)
            else:
                _load_tokens_fallback(data)
            # Try to validate if method exists
            if hasattr(garth.client, "refresh_oauth_token"):
                garth.client.refresh_oauth_token()
            return True
        except Exception as e:
            logger.info("Token load/refresh not supported or invalid; proceeding unauthenticated: %s", e)
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
            # Avoid API calls here
            self._username = getattr(garth.client, "username", None) or "Garmin User"
        return self._authenticated

    # ------------- auth -------------
    def login(self, email: str, password: str, remember: bool = False) -> Dict:
        if garth is None:
            self._authenticated = True
            self._username = email.split("@")[0] if "@" in email else email
            self._pending_mfa = False
            return {"authenticated": True, "username": self._username, "dev_mode": True}

        # Path A: newer garth with resume_login available
        if hasattr(garth, "resume_login"):
            try:
                result1, ctx = garth.login(email, password, return_on_mfa=True)
                if result1 == "needs_mfa":
                    self._pending_mfa = True
                    self._mfa_ctx = ctx
                    self._remember_after_mfa = bool(remember)
                    return {"mfa_required": True}
                # Success without MFA; tokens are on garth.client
                self._pending_mfa = False
                self._authenticated = True
                self._mfa_ctx = None
                self._username = getattr(garth.client, "username", None) or email
                if remember:
                    self._save_tokens()
                return {"authenticated": True, "username": self._username}
            except Exception as e:
                logger.exception("Login failed: %s", e)
                raise GarminAuthError(str(e)) from e

        # Path B: older garth - use two-step with prompt_mfa
        try:
            c = garth.Client()

            def _kick():
                raise _MFAKick()

            # If MFA is needed, _kick is called by garth and we raise _MFAKick
            c.login(email, password, prompt_mfa=_kick)
            # Success without MFA
            _adopt_tokens(c)
            self._pending_mfa = False
            self._authenticated = True
            self._pending_creds = None
            self._username = email  # avoid early API hit
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

        # Path A: newer garth
        if hasattr(garth, "resume_login"):
            if not self._mfa_ctx:
                raise GarminAuthError("No MFA context. Start login first.")
            try:
                _oauth1, _oauth2 = garth.resume_login(self._mfa_ctx, code)
                self._pending_mfa = False
                self._authenticated = True
                self._mfa_ctx = None
                self._username = getattr(garth.client, "username", None) or "Garmin User"
                if self._remember_after_mfa or remember:
                    self._save_tokens()
                return {"authenticated": True, "username": self._username}
            except Exception as e:
                logger.exception("MFA verification failed: %s", e)
                raise GarminAuthError(str(e)) from e

        # Path B: older garth - retry full login supplying code via prompt_mfa
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

    def logout(self):
        self._authenticated = False
        self._pending_mfa = False
        self._username = None
        self._mfa_ctx = None
        self._pending_creds = None
        self._remember_after_mfa = False
        if self.token_file.exists():
            try:
                self.token_file.unlink()
            except Exception:
                pass


# Singleton
_client_singleton: Optional[GarminClient] = None


def get_client() -> GarminClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = GarminClient()
    return _client_singleton

