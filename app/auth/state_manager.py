"""
Centralized Authentication State Manager.

Singleton pattern to manage authentication state across all Dash callbacks,
eliminating multiple client instances and state conflicts.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class AuthenticationStateManager:
    """Singleton authentication state manager with shared client instance."""

    _instance: Optional["AuthenticationStateManager"] = None
    _client = None
    _state = {
        "authenticated": False,
        "email": None,
        "mfa_required": False,
        "mfa_context": None,
        "session_valid": False,
        "last_check": None,
        "credentials_loaded": False,
    }

    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize singleton instance."""
        if not getattr(self, "_initialized", False):
            self._initialized = True
            logger.info("Authentication State Manager initialized")

    def get_client(self):
        """Get shared client instance - lazy initialization."""
        if self._client is None:
            from garmin_client.client import GarminConnectClient

            self._client = GarminConnectClient()
            logger.info("Shared GarminConnectClient created")
        return self._client

    def update_state(self, **kwargs) -> Dict[str, Any]:
        """Update authentication state atomically."""
        old_state = self._state.copy()
        self._state.update(kwargs)
        self._state["last_check"] = datetime.now().isoformat()

        # Log significant state changes
        if old_state.get("authenticated") != self._state.get("authenticated"):
            logger.info(f"Authentication state changed: {self._state.get('authenticated')}")

        return self._state.copy()

    def get_state(self) -> Dict[str, Any]:
        """Get current authentication state."""
        return self._state.copy()

    def reset_state(self):
        """Reset authentication state to default."""
        logger.info("Resetting authentication state")
        self._state = {
            "authenticated": False,
            "email": None,
            "mfa_required": False,
            "mfa_context": None,
            "session_valid": False,
            "last_check": None,
            "credentials_loaded": False,
        }
        # Don't reset client - keep session files

    def validate_and_restore_session(self) -> Dict[str, Any]:
        """
        Centralized session validation and restoration.

        Returns:
            Dict with status and current state
        """
        try:
            client = self.get_client()

            # Try to restore existing session
            restore_result = client.restore_session()

            if restore_result["status"] == "SUCCESS":
                # Session restored successfully
                credentials = client.load_credentials()
                email = credentials.get("email") if credentials else None

                state_update = {
                    "authenticated": True,
                    "session_valid": True,
                    "email": email,
                    "mfa_required": False,
                    "credentials_loaded": bool(credentials),
                }
                self.update_state(**state_update)
                logger.info("Session restored and validated successfully")
                return {"status": "SUCCESS", "state": self.get_state()}

            elif restore_result["status"] == "NO_SESSION":
                # No session available - check for stored credentials
                credentials = client.load_credentials()
                if credentials:
                    state_update = {
                        "authenticated": False,
                        "session_valid": False,
                        "email": credentials.get("email"),
                        "credentials_loaded": True,
                        "mfa_required": False,
                    }
                    self.update_state(**state_update)
                    logger.info("No session found, but credentials available")
                    return {"status": "CREDENTIALS_AVAILABLE", "state": self.get_state()}
                else:
                    # No session, no credentials
                    self.reset_state()
                    logger.info("No session or credentials found")
                    return {"status": "NO_AUTH", "state": self.get_state()}

            else:
                # Session restore failed
                self.reset_state()
                logger.warning(f"Session restoration failed: {restore_result.get('message')}")
                return {"status": "FAILED", "state": self.get_state()}

        except Exception as e:
            logger.error(f"Error during session validation: {e}")
            self.reset_state()
            return {"status": "ERROR", "state": self.get_state(), "error": str(e)}


# Global function to get singleton instance
def get_auth_manager() -> AuthenticationStateManager:
    """Get singleton authentication manager instance."""
    return AuthenticationStateManager()
