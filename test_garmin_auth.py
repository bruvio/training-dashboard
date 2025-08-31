#!/usr/bin/env python3
"""
Simple test script for Garmin Connect authentication with MFA handling.
"""

import sys
import getpass
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_garmin_authentication():
    """Test Garmin Connect authentication with proper MFA handling."""
    print("🏃 Testing Garmin Connect Authentication")
    print("=" * 50)

    try:
        # Create client
        client = GarminConnectClient()

        # Get credentials
        print("\nPlease provide your Garmin Connect credentials:")
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ")

        if not email or not password:
            print("❌ Email and password are required")
            return False

        print(f"\n🔑 Attempting to authenticate as {email}...")

        # Test authentication
        success = client.authenticate(email, password)

        if success:
            print("✅ Authentication successful!")

            # Test getting recent activities
            print("\n🏃 Getting recent activities...")
            try:
                from datetime import date, timedelta

                start_date = date.today() - timedelta(days=30)
                end_date = date.today()

                activities = client.get_activities(start_date, end_date, limit=5)
                if activities:
                    print(f"📈 Found {len(activities)} recent activities:")
                    for i, activity in enumerate(activities[:3], 1):
                        print(
                            f"  {i}. {activity.get('activityName', 'Unknown')} - {activity.get('startTimeGMT', 'Unknown date')}"
                        )
                else:
                    print("📭 No activities found")
            except Exception as e:
                print(f"⚠️  Error getting activities: {e}")

            return True
        else:
            print("❌ Authentication failed")
            return False

    except Exception as e:
        print(f"💥 Error during authentication: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    success = test_garmin_authentication()
    sys.exit(0 if success else 1)
