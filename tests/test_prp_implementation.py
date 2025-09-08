#!/usr/bin/env python3
"""
Test script to validate PRP implementation for fitness data visualization and sync.
"""

import sys

sys.path.append("/app")

from datetime import date, timedelta

from app.data.web_queries import format_personal_record_value, get_activity_statistics
from app.services.garmin_integration_service import GarminIntegrationService
from app.services.wellness_data_service import WellnessDataService


def test_database_tables():
    """Test that all required database tables exist."""
    print("🔍 Testing database tables...")

    try:
        from app.data.create_garmin_tables import list_garmin_tables

        tables = list_garmin_tables()

        expected_tables = [
            "user_profile",
            "daily_sleep",
            "daily_stress",
            "daily_steps",
            "daily_heart_rate",
            "daily_body_battery",
            "daily_training_readiness",
            "daily_spo2",
            "max_metrics",
            "personal_records",
        ]

        missing_tables = [t for t in expected_tables if t not in tables]

        if not missing_tables:
            print("✅ All required database tables exist")
            return True
        else:
            print(f"❌ Missing tables: {missing_tables}")
            return False

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


def test_wellness_data_service():
    """Test the WellnessDataService."""
    print("🔍 Testing WellnessDataService...")

    try:
        service = WellnessDataService()
        summary = service.get_wellness_summary(days=30)

        if isinstance(summary, dict) and "data_availability" in summary:
            print("✅ WellnessDataService working correctly")
            print(f"   Current data summary: {summary.get('total_records', 0)} total records")
            return True
        else:
            print("❌ WellnessDataService not returning expected format")
            return False

    except Exception as e:
        print(f"❌ WellnessDataService test failed: {e}")
        return False


def test_garmin_integration_service():
    """Test the GarminIntegrationService."""
    print("🔍 Testing GarminIntegrationService...")

    try:
        service = GarminIntegrationService()
        status = service.get_sync_status()

        if isinstance(status, dict) and "supported_smoothing" in status:
            print("✅ GarminIntegrationService initialized correctly")
            print(f"   Bruvio-garmin available: {status.get('bruvio_garmin_available', False)}")
            print(f"   Supported smoothing: {status.get('supported_smoothing', [])}")
            return True
        else:
            print("❌ GarminIntegrationService not working correctly")
            return False

    except Exception as e:
        print(f"❌ GarminIntegrationService test failed: {e}")
        return False


def test_personal_records_formatting():
    """Test the improved personal records formatting."""
    print("🔍 Testing personal records formatting...")

    try:
        # Test time formatting
        test_cases = [
            (1800, "5K Time", "30:00"),  # 30 minutes in seconds
            (1800000, "Marathon Time", "30:00"),  # 30 minutes in milliseconds
            (7200, "10K Time", "2:00:00"),  # 2 hours in seconds
            (42.2, "Marathon Distance", "42.20 km"),  # Distance in km
            (5000, "5K Distance", "5.00 km"),  # Distance in meters
            (180, "Max Heart Rate", "180 bpm"),  # Heart rate
        ]

        all_passed = True
        for value, record_type, expected in test_cases:
            result = format_personal_record_value(value, record_type)
            if result == expected:
                print(f"   ✅ {record_type}: {value} → {result}")
            else:
                print(f"   ❌ {record_type}: {value} → {result} (expected {expected})")
                all_passed = False

        if all_passed:
            print("✅ Personal records formatting working correctly")
            return True
        else:
            print("❌ Some personal records formatting tests failed")
            return False

    except Exception as e:
        print(f"❌ Personal records formatting test failed: {e}")
        return False


def test_date_filtering():
    """Test activity statistics with date filtering."""
    print("🔍 Testing date filtering in web queries...")

    try:
        # Test with date range
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        stats = get_activity_statistics(start_date, end_date)

        if isinstance(stats, dict) and "total_activities" in stats:
            print("✅ Date filtering in activity statistics working")
            print(f"   Activities in last 30 days: {stats.get('total_activities', 0)}")
            return True
        else:
            print("❌ Date filtering not working correctly")
            return False

    except Exception as e:
        print(f"❌ Date filtering test failed: {e}")
        return False


def main():
    """Run all tests and report results."""
    print("🧪 Testing PRP Implementation: Fitness Data Visualization & Sync")
    print("=" * 70)

    tests = [
        ("Database Tables", test_database_tables),
        ("WellnessDataService", test_wellness_data_service),
        ("GarminIntegrationService", test_garmin_integration_service),
        ("Personal Records Formatting", test_personal_records_formatting),
        ("Date Filtering", test_date_filtering),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 70)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 70)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1

    print("-" * 70)
    print(f"📊 OVERALL: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 ALL TESTS PASSED! PRP implementation successful.")
        return 0
    else:
        print("⚠️  Some tests failed. Check implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
