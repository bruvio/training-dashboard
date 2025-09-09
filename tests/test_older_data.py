#!/usr/bin/env python3
"""
Test Garmin data transformation with older dates that should have data.
"""

from datetime import date, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.garmin_integration_service import GarminIntegrationService


def test_older_garmin_data():
    """Test with older dates that should have data."""
    print("🔍 Testing Garmin data with older dates...")

    try:
        service = GarminIntegrationService()

        if not service.client.is_authenticated():
            print("❌ Not authenticated with Garmin Connect")
            return

        print("✅ Authenticated with Garmin Connect")

        # Test with dates from 1 week ago to 30 days ago
        today = date.today()
        test_dates = [
            today - timedelta(days=7),  # 1 week ago
            today - timedelta(days=14),  # 2 weeks ago
            today - timedelta(days=30),  # 30 days ago
        ]

        for test_date in test_dates:
            print(f"\n📅 Testing data for {test_date}")

            # Get raw wellness data
            raw_data = service.client.wellness_summary_for_day(test_date)

            if raw_data:
                # Check sleep data specifically
                if "sleep" in raw_data and raw_data["sleep"]:
                    sleep_data = raw_data["sleep"]
                    if "dailySleepDTO" in sleep_data and sleep_data["dailySleepDTO"]:
                        daily_sleep = sleep_data["dailySleepDTO"]
                        sleep_seconds = daily_sleep.get("sleepTimeSeconds")
                        deep_seconds = daily_sleep.get("deepSleepSeconds")
                        light_seconds = daily_sleep.get("lightSleepSeconds")
                        rem_seconds = daily_sleep.get("remSleepSeconds")

                        print(
                            f"  Sleep data: {sleep_seconds}s total, {deep_seconds}s deep, {light_seconds}s light, {rem_seconds}s REM"
                        )

                        if sleep_seconds and sleep_seconds > 0:
                            print(f"  ✅ Found meaningful sleep data for {test_date}")

                            # Test transformation
                            transformed = service._transform_garmin_data(raw_data, test_date)

                            if "sleep" in transformed:
                                print(f"  🔄 Transformed sleep: {transformed['sleep']}")
                                break
                            else:
                                print(f"  ❌ Transformation failed to create sleep data")
                        else:
                            print(f"  ⚠️ No sleep data for {test_date}")
                    else:
                        print(f"  ⚠️ No dailySleepDTO for {test_date}")
                else:
                    print(f"  ⚠️ No sleep section for {test_date}")

                # Check stress data
                if "stress" in raw_data and raw_data["stress"]:
                    stress_data = raw_data["stress"]
                    avg_stress = stress_data.get("avgStressLevel")
                    max_stress = stress_data.get("maxStressLevel")
                    print(f"  Stress data: avg={avg_stress}, max={max_stress}")

                # Check steps data
                if "steps" in raw_data and raw_data["steps"]:
                    steps_list = raw_data["steps"]
                    if steps_list:
                        total_steps = sum(item.get("steps", 0) for item in steps_list if isinstance(item, dict))
                        print(f"  Steps data: {total_steps} total steps")
                    else:
                        print(f"  ⚠️ Empty steps list for {test_date}")
            else:
                print(f"  ❌ No data returned for {test_date}")

    except Exception as e:
        print(f"❌ Error testing older data: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_older_garmin_data()
