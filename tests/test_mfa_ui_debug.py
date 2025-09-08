#!/usr/bin/env python3
"""
Test script to simulate MFA authentication and check if debug logging reveals
why the MFA dialog is not appearing in the UI.
"""

import json
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_mfa_response_structure():
    """Test the MFA response structure that would be sent to the UI."""
    print("🧪 Testing MFA response structure for UI...")

    client = GarminConnectClient()

    # Test with invalid credentials to see what response is generated
    result = client.authenticate("test@invalid.com", "invalid_password")

    print(f"📊 Backend MFA Response: {result}")
    print(f"📊 Response Type: {type(result)}")

    if isinstance(result, dict):
        print(f"📊 Response Keys: {list(result.keys())}")
        print(f"📊 Status: {result.get('status')}")

        if result.get("status") == "MFA_REQUIRED":
            print("✅ Backend correctly returns MFA_REQUIRED")
            print(f"📊 MFA Context Present: {'mfa_context' in result}")
            if "mfa_context" in result:
                print(f"📊 MFA Context Type: {type(result['mfa_context'])}")
                print(f"📊 MFA Context Length: {len(str(result['mfa_context'])) if result['mfa_context'] else 'None'}")
        else:
            print(f"⚠️ Backend returned status: {result.get('status')}")

    return result


def test_dash_callback_simulation():
    """Simulate what the Dash callback should receive and return."""
    print("\n🌐 Simulating Dash callback behavior...")

    # This simulates what the callback receives
    test_result = {"status": "MFA_REQUIRED", "mfa_context": "dGVzdF9jb250ZXh0XzEyMzQ1"}  # base64 encoded test context

    # Simulate the callback logic from app/pages/garmin_login.py
    print(f"📊 Simulated callback input: {test_result}")

    if test_result["status"] == "MFA_REQUIRED":
        print("🔐 MFA_REQUIRED status detected in callback")

        # This is what should be created for the MFA dialog
        mfa_content_structure = {
            "alert": "Multi-Factor Authentication required. Please enter your MFA code.",
            "form_elements": [
                "dbc.Label('MFA Code', html_for='mfa-code')",
                "dbc.Input(type='text', id='mfa-code', placeholder='Enter 6-digit MFA code')",
                "dbc.Button([html.I(className='fas fa-key me-2'), 'Verify MFA'])",
            ],
        }

        print(f"📊 Expected MFA dialog structure: {json.dumps(mfa_content_structure, indent=2)}")

        # This is what should be returned by the callback
        expected_callback_return = {
            "login-status": "",
            "mfa-section": "mfa_content",  # Should contain the MFA form
            "mfa-section-style": {"display": "block"},  # Should show the MFA section
            "success-section": [],
            "success-section-style": {"display": "none"},
            "login-form-style": {"display": "none"},  # Should hide the login form
            "login-status-store": {
                "mfa_required": True,
                "email": "test@invalid.com",
                "password": "invalid_password",
                "remember_me": False,
                "mfa_context": test_result["mfa_context"],
                "mfa_content": "mfa_content",
            },
        }

        print(f"📊 Expected callback return: {json.dumps(expected_callback_return, indent=2)}")
        return True

    return False


def test_container_logs():
    """Check what the actual logs show when authentication happens."""
    print("\n📝 Testing with actual container to see debug logs...")

    # Use curl to simulate the login form submission
    login_data = {
        "garmin-email": "test@invalid.com",
        "garmin-password": "invalid_password",
        "remember-me-checkbox": False,
    }

    print(f"📤 Simulating login request with data: {login_data}")

    # We can't easily simulate the Dash callback through curl,
    # but we can check the container logs to see what's happening
    print("💡 Check Docker logs for debug output:")
    print("   docker-compose logs -f | grep -E '(MFA|Authentication|login)'")

    return True


def main():
    """Run all MFA UI debug tests."""
    print("🔍 Starting MFA UI Debug Tests...\n")

    tests = [
        test_mfa_response_structure,
        test_dash_callback_simulation,
        test_container_logs,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            print(f"🧪 Running {test.__name__}...")
            if test():
                passed += 1
            print("=" * 60)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            print("=" * 60)

    print(f"\n📈 Test Results: {passed}/{total} tests completed")
    print("\n💡 Next steps:")
    print("1. Check Docker logs for the debug output from authentication")
    print("2. Verify that the Dash callback is receiving the correct response structure")
    print("3. Check if there are any JavaScript console errors preventing the UI update")

    return 0


if __name__ == "__main__":
    exit(main())
