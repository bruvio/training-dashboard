#!/usr/bin/env python3
"""
Test and fix the Garmin data transformation issue.
"""

from datetime import date, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.garmin_integration_service import GarminIntegrationService


def test_garmin_data_transformation():
    """Test what actual Garmin API data looks like."""
    print("🔍 Testing Garmin data transformation...")

    try:
        # Create service
        service = GarminIntegrationService()

        # Check if authenticated
        if not service.client.is_authenticated():
            print("❌ Not authenticated with Garmin Connect")
            return

        print("✅ Authenticated with Garmin Connect")

        # Get raw data for today
        today = date.today()
        yesterday = today - timedelta(days=1)

        print(f"📅 Testing data for {yesterday}")

        # Get raw wellness data from Garmin API
        raw_data = service.client.wellness_summary_for_day(yesterday)

        print("📋 Raw Garmin API data structure:")
        if raw_data:
            # Show the structure of what we get from Garmin
            for key, value in raw_data.items():
                if isinstance(value, dict):
                    print(f"  {key}: {{...}} (dict with {len(value)} keys)")
                    # Show first few keys of nested dicts
                    if len(value) < 10:
                        for subkey, subvalue in value.items():
                            print(f"    {subkey}: {type(subvalue)} = {subvalue}")
                    else:
                        sample_keys = list(value.keys())[:5]
                        for subkey in sample_keys:
                            print(f"    {subkey}: {type(value[subkey])} = {value[subkey]}")
                        print(f"    ... and {len(value) - 5} more keys")
                elif isinstance(value, list):
                    print(f"  {key}: [...] (list with {len(value)} items)")
                    if value and len(value) > 0:
                        print(f"    First item: {type(value[0])} = {value[0]}")
                else:
                    print(f"  {key}: {type(value)} = {value}")
        else:
            print("❌ No raw data returned from Garmin API")
            return

        # Test our transformation
        print(f"\n🔄 Testing transformation...")
        transformed = service._transform_garmin_data(raw_data, yesterday)

        print("📊 Transformed data:")
        for data_type, data_value in transformed.items():
            print(f"  {data_type}: {data_value}")

        # Check if we get meaningful values
        has_meaningful_data = False
        for data_type, data_value in transformed.items():
            if data_value and isinstance(data_value, dict):
                for key, value in data_value.items():
                    if value not in [None, 0, "", "0"]:
                        has_meaningful_data = True
                        print(f"  ✅ Found meaningful value: {key} = {value}")

        if not has_meaningful_data:
            print("❌ No meaningful values found in transformation")
            print("💡 The transformation logic needs to be fixed")
        else:
            print("✅ Transformation produced meaningful values")

    except Exception as e:
        print(f"❌ Error testing transformation: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_garmin_data_transformation()
