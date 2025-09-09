#!/usr/bin/env python3
"""Test real MFA authentication with actual credentials."""

import sys

sys.path.insert(0, "/app")

from garmin_client.client import GarminConnectClient


def test_real_mfa():
    """Test MFA authentication with real credentials."""

    client = GarminConnectClient()

    # Real credentials provided by user
    email = "sanpei-caridi@pm.me"
    password = "3u]_-Yb5'~WP\Q"

    print(f"Testing MFA authentication with email: {email}")

    def mfa_callback():
        """MFA callback that should prompt user for code."""
        print("🔐 MFA callback triggered! This means MFA is required.")
        print("   In the web app, this would show the MFA dialog.")
        # For testing without TTY, return a test code
        return "123456"

    try:
        print("\n1. Testing authentication with MFA callback...")
        result = client.authenticate(email, password, mfa_callback=mfa_callback)
        print(f"Authentication result: {result} (type: {type(result)})")

        if result:
            print("✅ Authentication successful!")

            # Test getting some data to verify session works
            print("\n2. Testing data retrieval...")
            try:
                activities = client.get_activities(0, 5)  # Get first 5 activities
                print(f"Retrieved {len(activities)} activities")
                for i, activity in enumerate(activities[:2]):  # Show first 2
                    print(
                        f"  Activity {i+1}: {activity.get('activityName', 'Unknown')} - {activity.get('startTimeLocal', 'No date')}"
                    )
            except Exception as e:
                print(f"Failed to retrieve activities: {e}")
        else:
            print("❌ Authentication failed")

    except Exception as e:
        print(f"Error during authentication: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_real_mfa()
