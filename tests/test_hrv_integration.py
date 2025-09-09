#!/usr/bin/env python3
"""
Test HRV integration with GarminIntegrationService.
"""

from datetime import date, timedelta
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.garmin_integration_service import GarminIntegrationService


def test_hrv_integration():
    """Test HRV integration in GarminIntegrationService."""
    print("🧪 Testing HRV integration with GarminIntegrationService...")

    try:
        service = GarminIntegrationService()

        if not service.client.is_authenticated():
            print("❌ Not authenticated with Garmin Connect")
            return

        print("✅ Authenticated with Garmin Connect")

        # Test with a single day that should have HRV data
        test_date = date.today() - timedelta(days=10)
        end_date = test_date

        print(f"📅 Testing HRV integration for {test_date}")

        # Run a sync for just one day to test HRV integration
        result = service.sync_wellness_data_range(start_date=test_date, end_date=end_date, smoothing="none")

        if result.get("success"):
            print(f"✅ Sync completed successfully!")
            print(f"📊 Days synced: {result.get('days_synced', 0)}")
            print(f"📊 Records synced: {result.get('records_synced', 0)}")
            print(f"📊 Data types synced: {result.get('data_types_synced', 0)}")

            persistence = result.get("persistence", {})
            for data_type, success in persistence.items():
                if success:
                    print(f"  ✅ {data_type}: persisted successfully")
                else:
                    print(f"  ❌ {data_type}: failed to persist")

            # Check specifically for HRV
            if "hrv" in persistence:
                print(f"🎯 HRV data processing: {'✅ SUCCESS' if persistence['hrv'] else '❌ FAILED'}")
            else:
                print("🔍 HRV not found in persistence results")

        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error testing HRV integration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_hrv_integration()
