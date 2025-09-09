#!/usr/bin/env python3
"""
Test the corrected wellness sync functions.
"""
import os
import sys
import pytest

sys.path.append("/app")

from datetime import date, timedelta

from garmin_client.client import GarminConnectClient
from garmin_client.wellness_sync import WellnessSyncManager


def is_ci_environment():
    """Check if running in CI environment."""
    return os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.mark.skipif(is_ci_environment(), reason="Garmin authentication not available in CI environment")
def test_corrected_sync():
    """Test the corrected sync functions."""
    try:
        client = GarminConnectClient()
        client.load_session()

        if not client.is_authenticated():
            print("Client not authenticated")
            return

        print("=== Testing Corrected Sync Functions ===")

        wellness_sync = WellnessSyncManager(client)

        # Test with a small date range
        start_date = date.today() - timedelta(days=2)
        end_date = date.today() - timedelta(days=1)

        print(f"Testing date range: {start_date} to {end_date}")

        # Test Body Battery sync
        print("\n1. Testing Body Battery sync...")
        bb_result = wellness_sync.sync_body_battery(start_date, end_date)
        print(f"Body Battery result: {bb_result}")

        # Test Training Readiness sync
        print("\n2. Testing Training Readiness sync...")
        tr_result = wellness_sync.sync_training_readiness(start_date, end_date)
        print(f"Training Readiness result: {tr_result}")

        # Test VO2 Max sync
        print("\n3. Testing Max Metrics (VO2 Max) sync...")
        vm_result = wellness_sync.sync_max_metrics(start_date, end_date)
        print(f"Max Metrics result: {vm_result}")

        # Test Personal Records
        print("\n4. Testing Personal Records sync...")
        pr_result = wellness_sync.sync_personal_records()
        print(f"Personal Records result: {pr_result}")

        print("\n=== Sync Tests Complete ===")

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_corrected_sync()
