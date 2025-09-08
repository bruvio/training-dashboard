#!/usr/bin/env python3
"""
Test the existing WellnessSync class to see what data it can retrieve.
"""

from datetime import date, timedelta
import os
import sys

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from garmin_client.wellness_sync import WellnessSync, get_client


def test_wellness_sync():
    """Test the existing WellnessSync class."""
    print("🔍 Testing existing WellnessSync class...")

    try:
        # Get authenticated client
        client = get_client()
        wellness = WellnessSync(client)

        print("✅ WellnessSync initialized")

        # Test a single day using range
        test_date = date.today() - timedelta(days=7)
        print(f"📅 Testing single day using range: {test_date}")

        single_day_data = wellness.fetch_range(start=test_date, end=test_date, include_extras=True)

        if single_day_data:
            print(f"📊 Single day data type: {type(single_day_data)}")
            if hasattr(single_day_data, "keys"):
                print(f"📊 Keys: {list(single_day_data.keys())}")
            if hasattr(single_day_data, "columns"):
                print(f"📊 Columns: {list(single_day_data.columns)}")
        else:
            print("❌ No single day data returned")

        # Test a range of dates
        start_date = date.today() - timedelta(days=14)
        end_date = date.today() - timedelta(days=1)
        print(f"\n📅 Testing date range: {start_date} to {end_date}")

        range_data = wellness.fetch_range(start=start_date, end=end_date, include_extras=True)

        if range_data:
            print(f"📊 Range data type: {type(range_data)}")

            if isinstance(range_data, dict):
                print(f"📊 Range data keys: {list(range_data.keys())}")

                # Check each data type
                for data_type, data_value in range_data.items():
                    if isinstance(data_value, pd.DataFrame) and not data_value.empty:
                        print(
                            f"  ✅ {data_type}: DataFrame with {data_value.shape[0]} rows, {data_value.shape[1]} columns"
                        )
                        print(f"      Columns: {list(data_value.columns)}")

                        # Show sample values for key columns
                        if data_type == "resting_hr" and "resting_hr" in data_value.columns:
                            non_null = data_value["resting_hr"].notna().sum()
                            print(f"      Resting HR non-null: {non_null}")
                        elif data_type == "body_battery" and len(data_value.columns) > 0:
                            first_col = data_value.columns[0]
                            non_null = data_value[first_col].notna().sum()
                            print(f"      {first_col} non-null: {non_null}")
                        elif data_type == "vo2max" and len(data_value.columns) > 0:
                            first_col = data_value.columns[0]
                            non_null = data_value[first_col].notna().sum()
                            print(f"      {first_col} non-null: {non_null}")

                    elif isinstance(data_value, pd.DataFrame):
                        print(f"  ❌ {data_type}: Empty DataFrame")
                    else:
                        print(f"  ❓ {data_type}: {type(data_value)}")
        else:
            print("❌ No range data returned")

    except Exception as e:
        print(f"❌ Error testing WellnessSync: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_wellness_sync()
