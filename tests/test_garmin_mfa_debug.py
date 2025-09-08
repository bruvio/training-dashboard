#!/usr/bin/env python3
"""
Independent test script to debug Garmin MFA login issues.
This script tests the login flow without the Dash application.
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Try to import garth
try:
    import garth

    GARTH_AVAILABLE = True
    logger.info("Garth library is available")
except ImportError:
    logger.error("Garth library not available. Please install it with: pip install garth")
    GARTH_AVAILABLE = False
    sys.exit(1)

# Default token path
DEFAULT_TOKEN_PATH = Path.home() / ".garmin" / "tokens.json"


class GarminMFADebugger:
    """Debug Garmin MFA login process independently from the main app."""

    def __init__(self, token_file: Path = DEFAULT_TOKEN_PATH):
        self.token_file = token_file
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._authenticated = False
        self._pending_mfa = False
        self._username: Optional[str] = None
        self._mfa_ctx: Optional[Any] = None
        self._pending_creds: Optional[tuple[str, str]] = None

    def check_existing_session(self) -> bool:
        """Check if there's an existing valid session."""
        if not self.token_file.exists():
            logger.info("No existing tokens found")
            return False

        try:
            data = json.loads(self.token_file.read_text())
            garth.client.load_tokens(data)
            garth.client.refresh_oauth_token()
            logger.info("Successfully loaded existing tokens")
            self._authenticated = True
            return True
        except Exception as e:
            logger.warning(f"Existing tokens invalid or expired: {e}")
            return False

    def login_step1(self, email: str, password: str) -> Dict:
        """First step of login - may trigger MFA."""
        logger.info(f"Starting login for {email}")

        # Check if garth supports the newer MFA flow
        if hasattr(garth, "resume_login"):
            logger.info("Using newer garth MFA flow (garth.login with return_on_mfa=True)")
            try:
                result, ctx = garth.login(email, password, return_on_mfa=True)
                logger.info(f"Login step 1 result: {result}")

                if result == "needs_mfa":
                    logger.info("MFA is required")
                    self._pending_mfa = True
                    self._mfa_ctx = ctx
                    return {"mfa_required": True, "context": "newer_flow"}
                else:
                    logger.info("Login successful without MFA")
                    self._authenticated = True
                    self._username = email
                    return {"authenticated": True, "username": self._username, "context": "newer_flow"}

            except Exception as e:
                logger.error(f"Login failed with newer flow: {e}")
                return {"error": str(e), "context": "newer_flow"}
        else:
            logger.info("Using older garth MFA flow (Client.login with prompt_mfa callback)")

            class MFAException(Exception):
                pass

            def mfa_prompt():
                raise MFAException("MFA required")

            try:
                c = garth.Client()
                c.login(email, password, prompt_mfa=mfa_prompt)

                # If we get here, login was successful without MFA
                logger.info("Login successful without MFA (older flow)")
                self._authenticated = True
                self._username = email

                # Adopt tokens to global client
                garth.client.oauth1_token = getattr(c, "oauth1_token", None)
                garth.client.oauth2_token = getattr(c, "oauth2_token", None)
                if hasattr(c, "session"):
                    garth.client.session = c.session

                return {"authenticated": True, "username": self._username, "context": "older_flow"}

            except MFAException:
                logger.info("MFA is required (older flow)")
                self._pending_mfa = True
                self._pending_creds = (email, password)
                return {"mfa_required": True, "context": "older_flow"}
            except Exception as e:
                logger.error(f"Login failed with older flow: {e}")
                return {"error": str(e), "context": "older_flow"}

    def submit_mfa_code(self, code: str) -> Dict:
        """Submit MFA code to complete authentication."""
        if not self._pending_mfa:
            return {"error": "No MFA pending. Call login_step1 first."}

        logger.info(f"Submitting MFA code: {code[:2]}****")

        # Check which flow we're using
        if hasattr(garth, "resume_login") and self._mfa_ctx:
            logger.info("Using newer garth MFA completion flow")
            try:
                oauth1, oauth2 = garth.resume_login(self._mfa_ctx, code)
                logger.info("MFA verification successful with newer flow")
                self._pending_mfa = False
                self._authenticated = True
                self._mfa_ctx = None
                self._username = "Garmin User"
                return {"authenticated": True, "username": self._username, "context": "newer_flow"}

            except Exception as e:
                logger.error(f"MFA verification failed with newer flow: {e}")
                return {"error": str(e), "context": "newer_flow"}

        elif self._pending_creds:
            logger.info("Using older garth MFA completion flow")
            email, password = self._pending_creds

            try:
                c = garth.Client()
                logger.info("Created new client, attempting login with MFA code")

                # This is where the error occurs in the original code
                c.login(email, password, prompt_mfa=lambda: code)

                logger.info("MFA verification successful with older flow")

                # Adopt tokens to global client
                garth.client.oauth1_token = getattr(c, "oauth1_token", None)
                garth.client.oauth2_token = getattr(c, "oauth2_token", None)
                if hasattr(c, "session"):
                    garth.client.session = c.session

                self._pending_mfa = False
                self._authenticated = True
                self._pending_creds = None
                self._username = email

                return {"authenticated": True, "username": self._username, "context": "older_flow"}

            except Exception as e:
                logger.error(f"MFA verification failed with older flow: {e}")
                logger.error(f"Exception type: {type(e)}")
                logger.error(f"Exception args: {e.args}")
                return {"error": str(e), "context": "older_flow", "exception_type": str(type(e))}
        else:
            return {"error": "Invalid MFA state - no context or credentials available"}

    def save_tokens(self):
        """Save authentication tokens for future use."""
        if not self._authenticated:
            logger.warning("Not authenticated - cannot save tokens")
            return False

        try:
            data = garth.client.dump_tokens()
            self.token_file.write_text(json.dumps(data))
            logger.info(f"Tokens saved to {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            return False

    def test_activities_sync(self, days: int = 7) -> Dict:
        """Test syncing activities after successful authentication."""
        if not self._authenticated:
            return {"error": "Not authenticated. Login first."}

        try:
            from datetime import datetime, timedelta, timezone

            logger.info(f"Testing activity sync for last {days} days")
            c = garth.client
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days)

            activities = c.activities(start=start.date(), limit=500)
            count = 0

            logger.info("Fetching activities...")
            for activity in activities:
                count += 1
                logger.info(
                    f"Activity {count}: {activity.get('activityName', 'Unknown')} - {activity.get('startTimeLocal', 'No date')}"
                )
                if count >= 10:  # Limit output for debugging
                    logger.info("... (showing first 10 activities)")
                    break

            return {
                "ok": True,
                "activities_fetched": count,
                "msg": f"Successfully synced {count} activities from the last {days} days.",
            }

        except Exception as e:
            logger.error(f"Activity sync failed: {e}")
            return {"error": str(e)}


def interactive_test():
    """Interactive test function."""
    print("=== Garmin MFA Debug Tool ===")
    print()

    debugger = GarminMFADebugger()

    # Check for existing session
    if debugger.check_existing_session():
        print("✓ Found valid existing session!")

        # Test activities sync
        result = debugger.test_activities_sync(7)
        if result.get("ok"):
            print(f"✓ {result['msg']}")
            return True
        else:
            print(f"✗ Activity sync failed: {result.get('error')}")
            return False

    # Get credentials
    email = input("Garmin email: ").strip()
    if not email:
        print("Email is required!")
        return False

    import getpass

    password = getpass.getpass("Garmin password: ").strip()
    if not password:
        print("Password is required!")
        return False

    # Step 1: Login
    result = debugger.login_step1(email, password)

    if result.get("error"):
        print(f"✗ Login failed: {result['error']}")
        print(f"Context: {result.get('context', 'unknown')}")
        return False

    if result.get("authenticated"):
        print(f"✓ Login successful! Welcome {result['username']}")

        # Save tokens
        if debugger.save_tokens():
            print("✓ Tokens saved for future use")

        # Test activities sync
        result = debugger.test_activities_sync(7)
        if result.get("ok"):
            print(f"✓ {result['msg']}")
            return True
        else:
            print(f"✗ Activity sync failed: {result.get('error')}")
            return False

    if result.get("mfa_required"):
        print(f"⚠ MFA required (using {result.get('context', 'unknown')} flow)")

        # Get MFA code
        mfa_code = input("Enter MFA code (6 digits): ").strip()
        if not mfa_code:
            print("MFA code is required!")
            return False

        # Step 2: Submit MFA
        mfa_result = debugger.submit_mfa_code(mfa_code)

        if mfa_result.get("error"):
            print(f"✗ MFA verification failed: {mfa_result['error']}")
            print(f"Context: {mfa_result.get('context', 'unknown')}")
            print(f"Exception type: {mfa_result.get('exception_type', 'unknown')}")
            return False

        if mfa_result.get("authenticated"):
            print(f"✓ MFA verification successful! Welcome {mfa_result['username']}")

            # Save tokens
            if debugger.save_tokens():
                print("✓ Tokens saved for future use")

            # Test activities sync
            sync_result = debugger.test_activities_sync(7)
            if sync_result.get("ok"):
                print(f"✓ {sync_result['msg']}")
                return True
            else:
                print(f"✗ Activity sync failed: {sync_result.get('error')}")
                return False

    print("✗ Unexpected result from login")
    return False


if __name__ == "__main__":
    if not GARTH_AVAILABLE:
        sys.exit(1)

    success = interactive_test()
    sys.exit(0 if success else 1)
