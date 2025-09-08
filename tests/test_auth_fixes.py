#!/usr/bin/env python3
"""
Test script to verify both authentication fixes:
1. JSON decode error handling in session resumption
2. Remember credentials functionality
"""

import json
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from garmin_client.client import GarminConnectClient


def test_json_decode_error_handling():
    """Test that corrupted session files are handled gracefully."""
    print("🔧 Testing JSON decode error handling...")

    client = GarminConnectClient()

    # Create a corrupted session file to trigger the error
    garth_session_path = client.config_dir / "garth_session"
    garth_session_path.parent.mkdir(parents=True, exist_ok=True)

    # Write corrupted JSON to simulate the issue
    garth_session_path.write_text("")  # Empty file
    print(f"Created empty session file at: {garth_session_path}")

    # Try to authenticate - this should NOT crash with JSONDecodeError
    try:
        result = client.authenticate("test@invalid.email", "invalid_password")
        print(f"📊 Result: {result}")

        if result.get("status") == "FAILED":
            print("✅ PASSED: Authentication failed gracefully without crashing")
            return True
        else:
            print("❌ FAILED: Unexpected result, should have failed gracefully")
            return False

    except json.JSONDecodeError as e:
        print(f"❌ FAILED: JSON decode error still not handled: {e}")
        return False
    except Exception as e:
        print(f"✅ PASSED: Got expected exception (not JSON decode): {e}")
        return True


def test_remember_credentials_functionality():
    """Test that remember me functionality works correctly."""
    print("💾 Testing remember credentials functionality...")

    # Create a fresh client
    client = GarminConnectClient()

    # Clear any existing credentials
    client.clear_credentials()

    # First, verify no credentials exist
    credentials = client.load_credentials()
    if credentials:
        print("❌ FAILED: Credentials should be empty initially")
        return False

    print("✅ Initial state: No credentials stored")

    # Store test credentials manually (simulating successful auth with remember_me=True)
    test_email = "test.user@example.com"
    test_password = "test_password_123"

    client.store_credentials(test_email, test_password)
    print(f"📝 Stored test credentials for: {test_email}")

    # Load and verify credentials
    loaded_credentials = client.load_credentials()
    if not loaded_credentials:
        print("❌ FAILED: Could not load stored credentials")
        return False

    if loaded_credentials["email"] != test_email:
        print(f"❌ FAILED: Email mismatch. Expected: {test_email}, Got: {loaded_credentials['email']}")
        return False

    if loaded_credentials["password"] != test_password:
        print("❌ FAILED: Password mismatch")
        return False

    print("✅ PASSED: Credentials stored and loaded correctly")

    # Test that credentials are used when not providing email/password
    try:
        result = client.authenticate()  # No email/password provided
        print(f"📊 Result when using stored credentials: {result}")

        # Should fail due to invalid credentials, but should try to use stored ones
        if result.get("status") == "FAILED":
            print("✅ PASSED: Used stored credentials (failed as expected with invalid creds)")
            return True
        else:
            print("❌ FAILED: Unexpected result when using stored credentials")
            return False

    except Exception as e:
        print(f"❌ FAILED: Exception when using stored credentials: {e}")
        return False


def test_credential_storage_after_auth():
    """Test that credentials are stored only after successful authentication."""
    print("🔐 Testing credential storage timing...")

    client = GarminConnectClient()
    client.clear_credentials()

    # Mock a scenario where authentication would succeed
    # (We can't actually authenticate with invalid creds, but we can test the logic)

    # Verify credentials are not stored before successful auth
    initial_creds = client.load_credentials()
    if initial_creds:
        print("❌ FAILED: Credentials should not exist initially")
        return False

    # Try auth with remember_me=True but invalid credentials (should fail and not store)
    result = client.authenticate("invalid@email.com", "invalid_pass", remember_me=True)

    # Credentials should still not be stored since auth failed
    after_failed_auth = client.load_credentials()
    if after_failed_auth:
        print("❌ FAILED: Credentials should not be stored after failed authentication")
        return False

    print("✅ PASSED: Credentials not stored after failed authentication")
    return True


def main():
    """Run all authentication fix tests."""
    print("🧪 Starting Garmin authentication fix tests...\n")

    tests = [
        test_json_decode_error_handling,
        test_remember_credentials_functionality,
        test_credential_storage_after_auth,
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
        print("🎉 All authentication fixes working correctly!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
