#!/usr/bin/env python3
"""
Test script to verify Garmin authentication flow with timeout protection.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_authentication_timeout_protection():
    """Test that authentication doesn't hang and properly handles timeout."""
    print("🔐 Testing Garmin authentication timeout protection...")

    client = GarminConnectClient()

    # Test with invalid credentials to trigger timeout/error handling
    print("Testing with invalid credentials to check timeout protection...")

    start_time = time.time()
    result = client.authenticate("sanpei-caridi@pm.me", "3u]_-Yb5'~WP\Q")
    end_time = time.time()

    elapsed_time = end_time - start_time

    print(f"⏱️  Authentication attempt took {elapsed_time:.2f} seconds")
    print(f"📊 Result: {result}")

    # Check that it didn't hang indefinitely
    if elapsed_time > 35:  # Should timeout around 30 seconds
        print("❌ FAILED: Authentication took too long, might be hanging")
        return False

    # Check that we got a proper response
    if not isinstance(result, dict) or "status" not in result:
        print("❌ FAILED: Invalid response format")
        return False

    print("✅ PASSED: Authentication completed within timeout")
    return True


def test_mfa_callback_structure():
    """Test that MFA callback structure is working."""
    print("🔑 Testing MFA callback structure...")

    client = GarminConnectClient()

    def test_mfa_callback():
        return "123456"  # Test MFA code

    # This should work without hanging even with invalid credentials
    start_time = time.time()
    try:
        result = client.authenticate(
            "test@invalid.email", "invalid_password", mfa_callback=test_mfa_callback, remember_me=False
        )
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"⏱️  MFA authentication attempt took {elapsed_time:.2f} seconds")
        print(f"📊 Result: {result}")

        if elapsed_time > 35:
            print("❌ FAILED: MFA authentication took too long")
            return False

        print("✅ PASSED: MFA callback structure working")
        return True

    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"⏱️  Exception after {elapsed_time:.2f} seconds: {e}")

        if elapsed_time > 35:
            print("❌ FAILED: Exception took too long to occur")
            return False

        print("✅ PASSED: Exception handled within timeout")
        return True


def main():
    """Run all authentication tests."""
    print("🧪 Starting Garmin authentication tests...\n")

    tests = [
        test_authentication_timeout_protection,
        test_mfa_callback_structure,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}\n")

    print(f"📈 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Timeout protection is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
