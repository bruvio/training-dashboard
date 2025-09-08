#!/usr/bin/env python3
"""
Test what Garmin API returns for missing metrics.
"""

from datetime import date, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.garmin_integration_service import GarminIntegrationService


def test_missing_metrics():
    """Test what Garmin API returns for heart rate, body battery, etc."""
    print("🔍 Testing missing metrics in Garmin API response...")

    try:
        service = GarminIntegrationService()

        if not service.client.is_authenticated():
            print("❌ Not authenticated with Garmin Connect")
            return

        print("✅ Authenticated with Garmin Connect")

        # Test with a date that should have data
        test_date = date.today() - timedelta(days=10)
        print(f"📅 Testing data for {test_date}")

        # Get raw wellness data
        raw_data = service.client.wellness_summary_for_day(test_date)

        if raw_data:
            print("📋 Raw Garmin API data keys:")
            for key in raw_data.keys():
                print(f"  {key}: {type(raw_data[key])}")

            # Check specific metrics
            metrics_to_check = ["heartRate", "bodyBattery", "readiness", "hrv", "vo2Max"]

            for metric in metrics_to_check:
                if metric in raw_data:
                    data = raw_data[metric]
                    print(f"\n📊 {metric} data structure:")
                    if isinstance(data, dict):
                        for subkey, subvalue in data.items():
                            print(f"  {subkey}: {type(subvalue)} = {subvalue}")
                    else:
                        print(f"  Type: {type(data)} = {data}")
                else:
                    print(f"\n❌ {metric} not found in API response")

            # Check if there are other keys we might be missing
            print(f"\n🔍 All available keys in API response:")
            for key, value in raw_data.items():
                if isinstance(value, dict) and value:
                    print(f"  {key}: {list(value.keys())[:5]}...")
                elif isinstance(value, list) and value:
                    print(f"  {key}: list with {len(value)} items")
                else:
                    print(f"  {key}: {type(value)}")

        else:
            print(f"❌ No data returned for {test_date}")

    except Exception as e:
        print(f"❌ Error testing missing metrics: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_missing_metrics()
