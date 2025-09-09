#!/usr/bin/env python3
"""
Test complete data sync with all missing metrics over a larger date range.
"""

from datetime import date, timedelta
import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.garmin_integration_service import GarminIntegrationService


def is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.mark.skipif(is_ci_environment(), reason="Garmin authentication not available in CI environment")
def test_complete_sync():
    """Test complete sync with all metrics over 2 weeks."""
    print("🧪 Testing complete sync with all metrics...")

    try:
        service = GarminIntegrationService()

        if not service.client.is_authenticated():
            print("❌ Not authenticated with Garmin Connect")
            return

        print("✅ Authenticated with Garmin Connect")

        # Test with 2 weeks of data to fill gaps
        start_date = date.today() - timedelta(days=14)
        end_date = date.today() - timedelta(days=1)

        print(f"📅 Testing complete sync for {start_date} to {end_date} (14 days)")

        # Run complete sync
        result = service.sync_wellness_data_range(start_date=start_date, end_date=end_date, smoothing="none")

        if result.get("success"):
            print(f"✅ Sync completed successfully!")
            print(f"📊 Days synced: {result.get('days_synced', 0)}")
            print(f"📊 Records synced: {result.get('records_synced', 0)}")
            print(f"📊 Data types synced: {result.get('data_types_synced', 0)}")

            persistence = result.get("persistence", {})
            print(f"\n📋 Persistence Results:")
            for data_type, success in persistence.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"  {status} {data_type}")

        else:
            print(f"❌ Sync failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error testing complete sync: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_complete_sync()
