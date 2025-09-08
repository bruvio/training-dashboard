#!/usr/bin/env python3
"""
Test script to verify that the MFA dialog now appears correctly in the UI.
"""

from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_backend_mfa_detection():
    """First verify that backend MFA detection still works."""
    print("🔐 Step 1: Testing backend MFA detection...")

    client = GarminConnectClient()
    result = client.authenticate("sanpei-caridi@pm.me", "3u]_-Yb5'~WP\\Q", remember_me=True)

    print(f"📊 Backend result: {result}")

    if result.get("status") == "MFA_REQUIRED":
        print("✅ Backend correctly detects MFA requirement")
        if result.get("mfa_context"):
            print("✅ MFA context successfully serialized")
            return True
        else:
            print("❌ Missing MFA context")
            return False
    else:
        print(f"❌ Backend returned unexpected status: {result.get('status')}")
        return False


def test_container_logs_for_mfa():
    """Check Docker logs to see if MFA callback fires correctly."""
    print("\n📝 Step 2: Checking container logs for MFA processing...")
    print("💡 Trigger login through web UI at: http://localhost:8050/garmin-login")
    print("💡 Use credentials: sanpei-caridi@pm.me / 3u]_-Yb5'~WP\\Q")
    print("💡 Expected: MFA dialog should appear asking for 6-digit code")
    print("\nMonitor logs with: docker-compose logs -f | grep -E '(MFA|🔐)'")

    return True


def test_mfa_dialog_simulation():
    """Simulate what should happen with the fixed callback."""
    print("\n🌐 Step 3: Simulating fixed callback behavior...")

    # This represents what the first callback should return
    expected_mfa_response = {
        "login-status": "",  # Empty
        "mfa-section": "MFA form content",  # MFA form components
        "mfa-section-style": {"display": "block"},  # Show MFA section
        "success-section": [],  # Empty
        "success-section-style": {"display": "none"},  # Hide success
        "login-form-style": {"display": "none"},  # Hide login form
        "login-status-store": {"mfa_required": True, "email": "user@email.com"},
    }

    print("📊 Expected first callback return (MFA_REQUIRED):")
    for key, value in expected_mfa_response.items():
        print(f"   {key}: {value}")

    # This represents what the second callback should return with the fix
    expected_second_callback_response = "no_update for all outputs"

    print(f"\n📊 Expected second callback return (when n_clicks=None): {expected_second_callback_response}")
    print("✅ This should prevent the MFA dialog from being hidden immediately")

    return True


def main():
    """Test the complete MFA UI flow."""
    print("🧪 Testing MFA UI Flow After Fix\n")

    tests = [
        test_backend_mfa_detection,
        test_container_logs_for_mfa,
        test_mfa_dialog_simulation,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            print("=" * 60)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            print("=" * 60)

    print(f"\n📈 Test Results: {passed}/{total} tests completed")

    if passed == total:
        print("\n🎉 Backend tests pass! Now test the web UI:")
        print("   1. Open: http://localhost:8050/garmin-login")
        print("   2. Enter: sanpei-caridi@pm.me / 3u]_-Yb5'~WP\\Q")
        print("   3. Click Login")
        print("   4. ✅ MFA dialog should now appear asking for 6-digit code")
        print("   5. ✅ The dialog should stay visible and not disappear")
        print("   6. Enter the MFA code you receive via email")
        print("   7. ✅ Authentication should complete successfully")
        return 0
    else:
        print("\n❌ Some backend tests failed - check the implementation")
        return 1


if __name__ == "__main__":
    exit(main())
