#!/usr/bin/env python3
"""
Fixed Garmin login test script that handles MFA properly.
This script addresses the "Unexpected title" error by implementing proper MFA handling.
"""

import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    import garth

    GARTH_AVAILABLE = True
    logger.info(f"Garth library available, version: {getattr(garth, '__version__', 'unknown')}")
except ImportError:
    logger.error("Garth library not available. Please install it with: pip install garth")
    GARTH_AVAILABLE = False
    sys.exit(1)

DEFAULT_TOKEN_PATH = Path.home() / ".garmin" / "tokens.json"


class ImprovedGarminClient:
    """
    Improved Garmin client that fixes MFA handling issues.
    """

    def __init__(self, token_file: Path = DEFAULT_TOKEN_PATH):
        self.token_file = token_file
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self._authenticated = False
        self._username: Optional[str] = None

    def _save_tokens(self) -> bool:
        """Save authentication tokens."""
        try:
            data = garth.client.dump_tokens()
            self.token_file.write_text(json.dumps(data))
            logger.info(f"Tokens saved to {self.token_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            return False

    def _load_tokens(self) -> bool:
        """Load existing tokens."""
        if not self.token_file.exists():
            logger.info("No existing tokens found")
            return False

        try:
            data = json.loads(self.token_file.read_text())
            garth.client.load_tokens(data)
            garth.client.refresh_oauth_token()
            logger.info("Successfully loaded existing tokens")
            return True
        except Exception as e:
            logger.warning(f"Existing tokens invalid or expired: {e}")
            return False

    def check_existing_session(self) -> bool:
        """Check for valid existing session."""
        if self._load_tokens():
            self._authenticated = True
            self._username = "Existing User"
            return True
        return False

    def login_with_mfa(self, email: str, password: str, mfa_callback: Callable[[], str]) -> Dict[str, Any]:
        """
        Enhanced login that properly handles MFA.

        Args:
            email: Garmin email
            password: Garmin password
            mfa_callback: Function that returns MFA code when called
        """
        logger.info(f"Starting login for {email}")

        # Check if we have the newer MFA flow available
        if hasattr(garth, "resume_login"):
            logger.info("Using newer garth MFA flow")
            return self._login_newer_flow(email, password, mfa_callback)
        else:
            logger.info("Using older garth MFA flow with improvements")
            return self._login_older_flow_fixed(email, password, mfa_callback)

    def _login_newer_flow(self, email: str, password: str, mfa_callback: Callable[[], str]) -> Dict[str, Any]:
        """Use the newer garth MFA flow (recommended)."""
        try:
            result, ctx = garth.login(email, password, return_on_mfa=True)

            if result == "needs_mfa":
                logger.info("MFA required - getting code")
                mfa_code = mfa_callback()
                logger.info(f"Submitting MFA code: {mfa_code[:2]}****")

                oauth1, oauth2 = garth.resume_login(ctx, mfa_code)

                logger.info("MFA authentication successful")
                self._authenticated = True
                self._username = email

                return {"success": True, "authenticated": True, "username": self._username, "method": "newer_flow"}
            else:
                logger.info("Login successful without MFA")
                self._authenticated = True
                self._username = email

                return {
                    "success": True,
                    "authenticated": True,
                    "username": self._username,
                    "method": "newer_flow_no_mfa",
                }

        except Exception as e:
            logger.error(f"Newer flow login failed: {e}")
            return {"success": False, "error": str(e), "method": "newer_flow"}

    def _login_older_flow_fixed(self, email: str, password: str, mfa_callback: Callable[[], str]) -> Dict[str, Any]:
        """
        Use the older garth MFA flow with fixes for the "Unexpected title" error.
        """

        # Step 1: Try login without MFA first to trigger MFA requirement
        logger.info("Step 1: Testing if MFA is required")

        class MFARequiredException(Exception):
            pass

        def mfa_detector():
            logger.info("MFA is required")
            raise MFARequiredException("MFA needed")

        try:
            c = garth.Client()
            c.login(email, password, prompt_mfa=mfa_detector)

            # If we get here, no MFA was needed
            logger.info("Login successful without MFA")
            self._adopt_client_tokens(c)
            self._authenticated = True
            self._username = email

            return {"success": True, "authenticated": True, "username": self._username, "method": "older_flow_no_mfa"}

        except MFARequiredException:
            logger.info("Step 2: MFA is required, proceeding with MFA authentication")

            # Step 2: Perform MFA authentication
            return self._perform_mfa_authentication(email, password, mfa_callback)

        except Exception as e:
            logger.error(f"Initial login failed: {e}")
            return {"success": False, "error": str(e), "method": "older_flow_initial"}

    def _perform_mfa_authentication(self, email: str, password: str, mfa_callback: Callable[[], str]) -> Dict[str, Any]:
        """
        Perform MFA authentication with retry logic and proper error handling.
        """
        max_retries = 3

        for attempt in range(max_retries):
            logger.info(f"MFA attempt {attempt + 1}/{max_retries}")

            try:
                # Get a fresh MFA code
                mfa_code = mfa_callback()
                logger.info(f"Got MFA code: {mfa_code[:2]}****")

                # Create a new client for each attempt
                c = garth.Client()

                # Create a proper MFA callback that handles multiple calls
                mfa_call_count = 0

                def mfa_provider():
                    nonlocal mfa_call_count
                    mfa_call_count += 1
                    logger.info(f"MFA provider called (call #{mfa_call_count})")

                    if mfa_call_count > 3:
                        logger.warning("MFA provider called too many times, code may be invalid")

                    return mfa_code

                # Attempt login with MFA
                c.login(email, password, prompt_mfa=mfa_provider)

                logger.info(f"MFA authentication successful on attempt {attempt + 1}")
                self._adopt_client_tokens(c)
                self._authenticated = True
                self._username = email

                return {
                    "success": True,
                    "authenticated": True,
                    "username": self._username,
                    "method": "older_flow_mfa",
                    "attempts": attempt + 1,
                }

            except Exception as e:
                error_str = str(e)
                logger.error(f"MFA attempt {attempt + 1} failed: {error_str}")

                # Check for specific errors that indicate we should retry
                if "Unexpected title" in error_str or "Enter MFA code" in error_str:
                    logger.info("Got 'Unexpected title' or 'Enter MFA code' error")

                    if attempt < max_retries - 1:
                        logger.info(f"Retrying with fresh MFA code (attempt {attempt + 2}/{max_retries})")
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        logger.error("Max retries reached for MFA authentication")
                        return {
                            "success": False,
                            "error": f"MFA failed after {max_retries} attempts: {error_str}",
                            "method": "older_flow_mfa",
                            "attempts": max_retries,
                            "fix_suggestion": (
                                "This error typically occurs when:\n"
                                "1. MFA code expired (codes are valid for ~30 seconds)\n"
                                "2. MFA code was already used\n"
                                "3. Network timing issues\n"
                                "Try getting a fresh MFA code immediately before authentication."
                            ),
                        }
                else:
                    # Non-recoverable error
                    return {"success": False, "error": error_str, "method": "older_flow_mfa", "attempts": attempt + 1}

        # Should never reach here
        return {"success": False, "error": "Unexpected end of MFA authentication", "method": "older_flow_mfa"}

    def _adopt_client_tokens(self, client):
        """Adopt tokens from a client instance to the global garth client."""
        try:
            garth.client.oauth1_token = getattr(client, "oauth1_token", None)
            garth.client.oauth2_token = getattr(client, "oauth2_token", None)
            if hasattr(client, "session"):
                garth.client.session = client.session
            logger.info("Successfully adopted client tokens")
        except Exception as e:
            logger.warning(f"Token adoption warning: {e}")

    def save_session(self) -> bool:
        """Save the current session."""
        if self._authenticated:
            return self._save_tokens()
        return False

    def sync_activities(self, days: int = 7) -> Dict[str, Any]:
        """Test activity synchronization."""
        if not self._authenticated:
            return {"success": False, "error": "Not authenticated"}

        try:
            from datetime import datetime, timedelta, timezone

            logger.info(f"Syncing activities for last {days} days")

            end = datetime.now(timezone.utc)
            start = end - timedelta(days=days)

            activities = garth.client.activities(start=start.date(), limit=100)

            count = 0
            activity_list = []

            for activity in activities:
                count += 1
                activity_info = {
                    "name": activity.get("activityName", "Unknown"),
                    "start_time": activity.get("startTimeLocal", "No date"),
                    "activity_type": activity.get("activityType", {}).get("typeKey", "Unknown"),
                    "distance": activity.get("distance", 0),
                    "duration": activity.get("duration", 0),
                }
                activity_list.append(activity_info)

                if count <= 3:  # Log first few activities
                    logger.info(
                        f"Activity {count}: {activity_info['name']} ({activity_info['activity_type']}) - {activity_info['start_time']}"
                    )

            if count > 3:
                logger.info(f"... and {count - 3} more activities")

            return {
                "success": True,
                "activities_count": count,
                "activities": activity_list[:10],  # Return first 10 for display
                "message": f"Successfully retrieved {count} activities from last {days} days",
            }

        except Exception as e:
            logger.error(f"Activity sync failed: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": str(e)}


def main():
    """Main test function."""
    print("=== Improved Garmin Login Test ===")

    # Get credentials from environment
    email = os.getenv("GARMIN_EMAIL", "").strip()
    password = os.getenv("GARMIN_PASSWORD", "").strip()

    if not email or not password:
        print("Please set GARMIN_EMAIL and GARMIN_PASSWORD environment variables")
        return False

    client = ImprovedGarminClient()

    # Check existing session
    if client.check_existing_session():
        print("✓ Found valid existing session!")
    else:
        print("No existing session found, performing fresh login...")

        # Define MFA callback function
        def get_mfa_code() -> str:
            # Try environment variable first
            env_code = os.getenv("GARMIN_MFA_CODE", "").strip()
            if env_code:
                print(f"Using MFA code from environment: {env_code[:2]}****")
                return env_code

            # Interactive fallback
            import sys

            if sys.stdin.isatty():
                return input("Enter MFA code: ").strip()
            else:
                raise ValueError("MFA code required but not available (set GARMIN_MFA_CODE environment variable)")

        # Perform login
        result = client.login_with_mfa(email, password, get_mfa_code)

        if result["success"]:
            print(f"✓ Login successful! Method: {result['method']}")
            print(f"  Username: {result['username']}")

            if "attempts" in result:
                print(f"  MFA attempts: {result['attempts']}")

            # Save session
            if client.save_session():
                print("✓ Session saved for future use")
        else:
            print(f"✗ Login failed: {result['error']}")
            if "fix_suggestion" in result:
                print(f"\nSuggested fix:\n{result['fix_suggestion']}")
            return False

    # Test activity sync
    print("\nTesting activity synchronization...")
    sync_result = client.sync_activities(7)

    if sync_result["success"]:
        print(f"✓ {sync_result['message']}")

        if sync_result["activities"]:
            print("\nRecent activities:")
            for i, activity in enumerate(sync_result["activities"][:5], 1):
                print(f"  {i}. {activity['name']} ({activity['activity_type']}) - {activity['start_time']}")
    else:
        print(f"✗ Activity sync failed: {sync_result['error']}")
        return False

    print("\n✓ All tests completed successfully!")
    return True


if __name__ == "__main__":
    if not GARTH_AVAILABLE:
        sys.exit(1)

    success = main()
    sys.exit(0 if success else 1)
