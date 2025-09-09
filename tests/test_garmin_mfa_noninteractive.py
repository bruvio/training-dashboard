#!/usr/bin/env python3
"""
Non-interactive test script to debug Garmin MFA login issues.
This script tests the login flow without user input, using environment variables.

Usage:
export GARMIN_EMAIL="sanpei-caridi@pm.me"
export GARMIN_PASSWORD="3u]_-Yb5'~WP\Q"
export GARMIN_MFA_CODE="123456"  # Optional, set after first run if MFA is required
python test_garmin_mfa_noninteractive.py
"""

import json
import logging
import os
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
    logger.info(f"Garth version: {getattr(garth, '__version__', 'unknown')}")
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

        # Log garth version and available methods
        logger.info(f"Available garth methods: {[m for m in dir(garth) if not m.startswith('_')]}")

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
                logger.info(f"Context type: {type(ctx)}")

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
                logger.error(f"Exception type: {type(e)}")
                import traceback

                traceback.print_exc()
                return {"error": str(e), "context": "newer_flow"}
        else:
            logger.info("Using older garth MFA flow (Client.login with prompt_mfa callback)")

            class MFAException(Exception):
                pass

            def mfa_prompt():
                logger.info("MFA prompt called by garth")
                raise MFAException("MFA required")

            try:
                c = garth.Client()
                logger.info("Created garth client, attempting login")
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
                logger.error(f"Exception type: {type(e)}")
                import traceback

                traceback.print_exc()
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
                logger.info(f"MFA context type: {type(self._mfa_ctx)}")
                oauth1, oauth2 = garth.resume_login(self._mfa_ctx, code)
                logger.info("MFA verification successful with newer flow")
                logger.info(f"OAuth1 token: {oauth1 is not None}")
                logger.info(f"OAuth2 token: {oauth2 is not None}")
                self._pending_mfa = False
                self._authenticated = True
                self._mfa_ctx = None
                self._username = "Garmin User"
                return {"authenticated": True, "username": self._username, "context": "newer_flow"}

            except Exception as e:
                logger.error(f"MFA verification failed with newer flow: {e}")
                logger.error(f"Exception type: {type(e)}")
                import traceback

                traceback.print_exc()
                return {"error": str(e), "context": "newer_flow"}

        elif self._pending_creds:
            logger.info("Using older garth MFA completion flow")
            email, password = self._pending_creds

            try:
                c = garth.Client()
                logger.info("Created new client, attempting login with MFA code")

                # This is where the error occurs in the original code
                # Let's add detailed logging to see what's happening
                logger.info(f"About to call c.login with email={email}, prompt_mfa=lambda: '{code[:2]}****'")

                c.login(email, password, prompt_mfa=lambda: code)

                logger.info("MFA verification successful with older flow")

                # Adopt tokens to global client
                garth.client.oauth1_token = getattr(c, "oauth1_token", None)
                garth.client.oauth2_token = getattr(c, "oauth2_token", None)
                if hasattr(c, "session"):
                    garth.client.session = c.session

                logger.info(f"OAuth1 token adopted: {garth.client.oauth1_token is not None}")
                logger.info(f"OAuth2 token adopted: {garth.client.oauth2_token is not None}")

                self._pending_mfa = False
                self._authenticated = True
                self._pending_creds = None
                self._username = email

                return {"authenticated": True, "username": self._username, "context": "older_flow"}

            except Exception as e:
                logger.error(f"MFA verification failed with older flow: {e}")
                logger.error(f"Exception type: {type(e)}")
                logger.error(f"Exception args: {e.args}")

                # Additional debugging for the specific error we're seeing
                if "Unexpected title" in str(e):
                    logger.error("This is the 'Unexpected title' error we're debugging!")
                    logger.error("The garth library is receiving an unexpected page title during MFA verification")
                    logger.error("This typically happens when Garmin's SSO flow has changed or there's a timing issue")

                import traceback

                traceback.print_exc()
                return {"error": str(e), "context": "older_flow", "exception_type": str(type(e))}
        else:
            return {"error": "Invalid MFA state - no context or credentials available"}

    def save_tokens(self):
        """Save authentication tokens for future use."""
        if not self._authenticated:
            logger.warning("Not authenticated - cannot save tokens")
            return False

        try:
            # Try the newer API first
            if hasattr(garth.client, "dump_tokens"):
                data = garth.client.dump_tokens()
            else:
                # Fallback for older versions - manually extract tokens
                data = {
                    "oauth1_token": getattr(garth.client, "oauth1_token", None),
                    "oauth2_token": getattr(garth.client, "oauth2_token", None),
                }
            self.token_file.write_text(json.dumps(data, default=str))
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
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days)

            logger.info(f"Requesting activities from {start.date()} to {end.date()}")

            # Use the correct API for garth 0.5.17
            try:
                # Method 1: Direct connectapi call
                from garth import connectapi

                activities = connectapi(
                    f"/activitylist-service/activities/search/activities?start=0&limit=500&startDate={start.date()}&endDate={end.date()}"
                )
            except Exception as e1:
                logger.warning(f"Method 1 failed: {e1}")
                try:
                    # Method 2: Using garth.client
                    activities_data = garth.client.get(
                        "connectapi",
                        f"/activitylist-service/activities/search/activities?start=0&limit=500&startDate={start.date()}&endDate={end.date()}",
                    )
                    activities = (
                        activities_data if isinstance(activities_data, list) else activities_data.get("activities", [])
                    )
                except Exception as e2:
                    logger.warning(f"Method 2 failed: {e2}")
                    # Method 3: Try garth.data module
                    activities_data = garth.data.activities(start=start.date(), end=end.date())
                    activities = (
                        activities_data if isinstance(activities_data, list) else activities_data.get("activities", [])
                    )
            count = 0

            logger.info("Fetching activities...")
            for activity in activities:
                count += 1
                activity_name = activity.get("activityName", "Unknown")
                start_time = activity.get("startTimeLocal", "No date")
                logger.info(f"Activity {count}: {activity_name} - {start_time}")
                if count >= 5:  # Limit output for debugging
                    logger.info("... (showing first 5 activities)")
                    break

            logger.info(f"Total activities found: {count}")
            return {
                "ok": True,
                "activities_fetched": count,
                "msg": f"Successfully synced {count} activities from the last {days} days.",
            }

        except Exception as e:
            logger.error(f"Activity sync failed: {e}")
            import traceback

            traceback.print_exc()
            return {"error": str(e)}


def main():
    """Main test function using environment variables."""
    print("=== Garmin MFA Debug Tool (Non-Interactive) ===")
    print()

    # Get credentials from environment
    email = os.getenv("GARMIN_EMAIL", "").strip()
    password = os.getenv("GARMIN_PASSWORD", "").strip()
    mfa_code = os.getenv("GARMIN_MFA_CODE", "").strip()

    if not email:
        print("✗ GARMIN_EMAIL environment variable is required!")
        print("Usage: export GARMIN_EMAIL='your@email.com'")
        return False

    if not password:
        print("✗ GARMIN_PASSWORD environment variable is required!")
        print("Usage: export GARMIN_PASSWORD='yourpassword'")
        return False

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

        if not mfa_code:
            print("✗ GARMIN_MFA_CODE environment variable is required for MFA!")
            print("Usage: export GARMIN_MFA_CODE='123456'")
            print("Run this script again after setting the MFA code.")
            return False

        # Step 2: Submit MFA
        mfa_result = debugger.submit_mfa_code(mfa_code)

        if mfa_result.get("error"):
            print(f"✗ MFA verification failed: {mfa_result['error']}")
            print(f"Context: {mfa_result.get('context', 'unknown')}")
            print(f"Exception type: {mfa_result.get('exception_type', 'unknown')}")

            # Provide specific guidance for the error we're debugging
            if "Unexpected title" in mfa_result["error"]:
                print()
                print("=== DEBUG ANALYSIS ===")
                print("This error occurs when garth receives an unexpected page title during MFA verification.")
                print("Possible causes:")
                print("1. Garmin's SSO flow has changed and garth needs to be updated")
                print("2. MFA code was entered too late (codes typically expire in 30 seconds)")
                print("3. Network or timing issues during the SSO handshake")
                print("4. The MFA code was incorrect")
                print()
                print("Suggested fixes:")
                print("1. Try with a fresh MFA code immediately after generation")
                print("2. Check if garth library needs updating: pip install --upgrade garth")
                print("3. Check Garmin Connect status at https://status.garmin.com/")

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

    success = main()
    sys.exit(0 if success else 1)
