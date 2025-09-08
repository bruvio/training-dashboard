#!/usr/bin/env python3

from datetime import date, timedelta
import json

from garmin_client.client import GarminConnectClient


def display_json(description, data):
    """Display API response in JSON format."""
    print(f"\n{description}")
    print("-" * 60)
    print(json.dumps(data, indent=2, default=str))
    print("-" * 60)


def main():
    """Test specific API endpoints to identify correct field names."""
    client = GarminConnectClient()

    if not client.is_authenticated():
        print("❌ Client not authenticated!")
        return

    today = date.today()
    test_date = today - timedelta(days=1)  # Use yesterday
    date_str = test_date.isoformat()

    print(f"🔍 Testing API responses for date: {date_str}")

    # Test resting heart rate
    try:
        rhr_data = client.api.get_rhr_day(date_str)
        display_json(f"api.get_rhr_day('{date_str}')", rhr_data)
    except Exception as e:
        print(f"❌ RHR Error: {e}")

    # Test steps data
    try:
        steps_data = client.api.get_steps_data(date_str)
        display_json(f"api.get_steps_data('{date_str}')", steps_data)
    except Exception as e:
        print(f"❌ Steps Error: {e}")

    # Test sleep data
    try:
        sleep_data = client.api.get_sleep_data(date_str)
        display_json(f"api.get_sleep_data('{date_str}')", sleep_data)
    except Exception as e:
        print(f"❌ Sleep Error: {e}")

    # Test heart rate zones (working example)
    try:
        hr_data = client.api.get_heart_rates(date_str)
        display_json(f"api.get_heart_rates('{date_str}')", hr_data)
    except Exception as e:
        print(f"❌ HR Error: {e}")


if __name__ == "__main__":
    main()
