#!/usr/bin/env python3

from datetime import date, timedelta
import json
import sys

# Add the app directory to the Python path
sys.path.append("/app")

from garmin_client.client import GarminConnectClient
from garmin_client.wellness_sync import WellnessSyncManager


def display_json(description, data):
    """Display API response in JSON format."""
    print(f"\n{description}")
    print("=" * 80)
    print(json.dumps(data, indent=2, default=str))
    print("=" * 80)


def test_individual_apis():
    """Test individual API calls to see actual field structures."""
    client = GarminConnectClient()
    wellness_sync = WellnessSyncManager(client)

    # Check if authenticated
    if not wellness_sync.client.is_authenticated():
        print("❌ Client not authenticated!")
        return

    today = date.today()
    test_date = today - timedelta(days=1)  # Use yesterday for stable data
    date_str = test_date.isoformat()

    print(f"🔍 Testing individual API calls for: {date_str}")

    # Test each API individually to see the raw response structure

    print("\n" + "=" * 80)
    print("1. RESTING HEART RATE API")
    print("=" * 80)
    try:
        rhr_data = wellness_sync.client.api.get_rhr_day(date_str)
        display_json(f"get_rhr_day('{date_str}')", rhr_data)

        # Show what our current code tries to extract
        print(f"Current code looks for: rhr_data.get('value') = {rhr_data.get('value') if rhr_data else 'None'}")
        print(
            f"Old code looked for: rhr_data.get('restingHeartRate') = {rhr_data.get('restingHeartRate') if rhr_data else 'None'}"
        )

    except Exception as e:
        print(f"❌ RHR API Error: {e}")

    print("\n" + "=" * 80)
    print("2. STEPS DATA API")
    print("=" * 80)
    try:
        steps_data = wellness_sync.client.api.get_steps_data(date_str)
        display_json(f"get_steps_data('{date_str}')", steps_data)

        # Handle list response
        if isinstance(steps_data, list) and steps_data:
            steps_item = steps_data[0]
            print(f"\nAnalyzing first item in list:")
            print(f"Current code looks for: steps_item.get('steps') = {steps_item.get('steps')}")
            print(f"Current code looks for: steps_item.get('totalSteps') = {steps_item.get('totalSteps')}")
            print(f"Available keys: {list(steps_item.keys()) if isinstance(steps_item, dict) else 'Not a dict'}")
        elif isinstance(steps_data, dict):
            print(f"\nAnalyzing dict response:")
            print(f"Current code looks for: steps_data.get('steps') = {steps_data.get('steps')}")
            print(f"Current code looks for: steps_data.get('totalSteps') = {steps_data.get('totalSteps')}")
            print(f"Available keys: {list(steps_data.keys())}")

    except Exception as e:
        print(f"❌ Steps API Error: {e}")

    print("\n" + "=" * 80)
    print("3. SLEEP DATA API")
    print("=" * 80)
    try:
        sleep_data = wellness_sync.client.api.get_sleep_data(date_str)
        display_json(f"get_sleep_data('{date_str}')", sleep_data)

        if sleep_data:
            print(f"\nAnalyzing sleep data:")
            print(f"Current code looks for: sleep_data.get('sleepTimeSeconds') = {sleep_data.get('sleepTimeSeconds')}")
            print(
                f"Current code looks for: sleep_data.get('overallSleepScore') = {sleep_data.get('overallSleepScore')}"
            )
            print(f"Available keys: {list(sleep_data.keys()) if isinstance(sleep_data, dict) else 'Not a dict'}")

    except Exception as e:
        print(f"❌ Sleep API Error: {e}")

    print("\n" + "=" * 80)
    print("4. HEART RATE ZONES (WORKING EXAMPLE)")
    print("=" * 80)
    try:
        hr_data = wellness_sync.client.api.get_heart_rates(date_str)
        display_json(f"get_heart_rates('{date_str}')", hr_data)

        if hr_data:
            print(f"\nThis API is working - analyzing structure:")
            print(f"Current code looks for: hr_data.get('maxHeartRate') = {hr_data.get('maxHeartRate')}")
            print(f"Available keys: {list(hr_data.keys()) if isinstance(hr_data, dict) else 'Not a dict'}")

    except Exception as e:
        print(f"❌ HR API Error: {e}")


if __name__ == "__main__":
    test_individual_apis()
