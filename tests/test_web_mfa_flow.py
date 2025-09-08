#!/usr/bin/env python3
"""
Test script to verify that the web interface properly handles MFA flow.
This tests the complete flow from login attempt to MFA dialog display.
"""

from pathlib import Path
import sys
import time
from unittest.mock import patch

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_mfa_required_response():
    """Test that MFA required response is properly formatted."""
    print("🔐 Testing MFA required response formatting...")

    client = GarminConnectClient()

    # Mock garth.login to simulate MFA requirement
    with patch("garmin_client.client.garth.login") as mock_login:
        # Simulate MFA requirement
        mock_mfa_context = {"mfa_token": "test_token_12345", "session_data": "encrypted_data"}
        mock_login.return_value = ("needs_mfa", mock_mfa_context)

        result = client.authenticate("test@example.com", "test_password")

        print(f"📊 Result: {result}")

        # Verify the response structure
        if result.get("status") != "MFA_REQUIRED":
            print("❌ FAILED: Expected MFA_REQUIRED status")
            return False

        if "mfa_context" not in result:
            print("❌ FAILED: Missing mfa_context in response")
            return False

        print("✅ PASSED: MFA required response properly formatted")
        return True


def test_mfa_context_serialization():
    """Test that MFA context is properly serialized and can be deserialized."""
    print("🔑 Testing MFA context serialization/deserialization...")

    client = GarminConnectClient()

    with patch("garmin_client.client.garth.login") as mock_login:
        # Simulate MFA requirement with complex context
        mock_mfa_context = {
            "mfa_token": "test_token_12345",
            "session_data": "encrypted_session_data",
            "cookies": {"session_id": "abc123", "csrf_token": "xyz789"},
        }
        mock_login.return_value = ("needs_mfa", mock_mfa_context)

        result = client.authenticate("test@example.com", "test_password")

        if result.get("status") != "MFA_REQUIRED":
            print("❌ FAILED: Expected MFA_REQUIRED status")
            return False

        # Test that we can deserialize the mfa_context
        import base64
        import pickle

        try:
            serialized_context = result["mfa_context"]
            deserialized_context = pickle.loads(base64.b64decode(serialized_context))

            if deserialized_context != mock_mfa_context:
                print("❌ FAILED: Deserialized context doesn't match original")
                return False

            print("✅ PASSED: MFA context serialization working correctly")
            return True

        except Exception as e:
            print(f"❌ FAILED: Context deserialization failed: {e}")
            return False


def test_timeout_behavior_with_mfa():
    """Test that timeout protection works even when MFA is involved."""
    print("⏱️  Testing timeout behavior with MFA flow...")

    client = GarminConnectClient()

    # Mock garth.login to simulate a hanging call that times out
    with patch("garmin_client.client.garth.login") as mock_login:

        def hanging_login(*args, **kwargs):
            time.sleep(35)  # Simulate hanging longer than timeout
            return ("needs_mfa", {"token": "test"})

        mock_login.side_effect = hanging_login

        start_time = time.time()
        result = client.authenticate("test@example.com", "test_password")
        end_time = time.time()

        elapsed_time = end_time - start_time

        print(f"⏱️  Authentication took {elapsed_time:.2f} seconds")
        print(f"📊 Result: {result}")

        # Should timeout around 30 seconds
        if elapsed_time > 35:
            print("❌ FAILED: Authentication didn't timeout properly")
            return False

        if elapsed_time < 25:
            print("❌ FAILED: Authentication finished too quickly (timeout not working)")
            return False

        if result.get("status") != "FAILED":
            print("❌ FAILED: Expected FAILED status for timeout")
            return False

        print("✅ PASSED: Timeout protection working with MFA flow")
        return True


def test_web_callback_structure():
    """Test that the web callback structure is compatible."""
    print("🌐 Testing web callback structure compatibility...")

    # Test the web MFA callback format
    def web_mfa_callback():
        return "123456"  # Simulates user input

    # Verify callback returns expected format
    mfa_code = web_mfa_callback()

    if not isinstance(mfa_code, str):
        print("❌ FAILED: MFA callback should return string")
        return False

    if len(mfa_code) != 6:
        print("❌ FAILED: MFA code should be 6 digits")
        return False

    # Test with client using callback
    client = GarminConnectClient()

    with patch("garmin_client.client.garth.login") as mock_login, patch(
        "garmin_client.client.garth_sso.resume_login"
    ) as mock_resume:
        # First call returns MFA requirement
        mock_context = {"token": "test_token"}
        mock_login.return_value = ("needs_mfa", mock_context)

        # Resume login should succeed
        mock_resume.return_value = None  # Success

        result = client.authenticate("test@example.com", "test_password", mfa_callback=web_mfa_callback)

        print(f"📊 Result: {result}")

        # Should succeed with the callback
        if result.get("status") != "SUCCESS":
            print("❌ FAILED: Expected SUCCESS with MFA callback")
            return False

        # Verify resume_login was called with correct parameters
        mock_resume.assert_called_once_with(mock_context, "123456")

        print("✅ PASSED: Web callback structure compatible")
        return True


def main():
    """Run all MFA web flow tests."""
    print("🧪 Starting Garmin MFA web flow tests...\n")

    tests = [
        test_mfa_required_response,
        test_mfa_context_serialization,
        test_timeout_behavior_with_mfa,
        test_web_callback_structure,
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
        print("🎉 All MFA web flow tests passed! Ready for production use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the MFA implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
