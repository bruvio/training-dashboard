#!/usr/bin/env python3
"""
Test script for GUI MFA handling with Garmin Connect.
"""

from pathlib import Path
import sys

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMessageBox
from desktop_ui.login_dialog_simple import SimpleLoginDialog
from desktop_ui.mfa_dialog import MFADialog

from garmin_client.client import GarminConnectClient


def test_mfa_gui():
    """Test the GUI MFA flow."""
    QApplication(sys.argv)

    try:
        print("🖥️  Testing GUI MFA Authentication Flow")
        print("=" * 50)

        # Step 1: Get login credentials
        login_dialog = SimpleLoginDialog()
        if login_dialog.exec() != SimpleLoginDialog.DialogCode.Accepted:
            print("❌ Login cancelled by user")
            return False

        email, password = login_dialog.get_credentials()
        print(f"📧 Email: {email}")

        # Step 2: Create client and attempt authentication
        client = GarminConnectClient()

        # Define MFA callback that uses our GUI dialog
        def mfa_callback():
            print("🔐 MFA required - showing MFA dialog")
            mfa_dialog = MFADialog()
            if mfa_dialog.exec() == MFADialog.DialogCode.Accepted:
                mfa_code = mfa_dialog.get_mfa_code()
                print(f"🔑 MFA code entered: {mfa_code}")
                return mfa_code
            else:
                print("❌ MFA cancelled by user")
                return None

        print("🔑 Attempting authentication...")
        success = client.authenticate(email, password, mfa_callback=mfa_callback)

        if success:
            print("✅ Authentication successful!")

            # Show success message
            QMessageBox.information(
                None, "Success", f"Successfully authenticated with Garmin Connect!\n\n" f"Email: {email}"
            )

            # Test getting activities
            print("\n🏃 Testing activity retrieval...")
            try:
                from datetime import date, timedelta

                start_date = date.today() - timedelta(days=7)
                end_date = date.today()

                activities = client.get_activities(start_date, end_date, limit=3)
                if activities:
                    print(f"📈 Found {len(activities)} recent activities")
                    activity_list = "\\n".join(
                        [
                            f"• {activity.get('activityName', 'Unknown')} - {activity.get('startTimeGMT', 'Unknown date')[:10]}"
                            for activity in activities[:3]
                        ]
                    )
                    QMessageBox.information(
                        None, "Recent Activities", f"Found {len(activities)} recent activities:\\n\\n{activity_list}"
                    )
                else:
                    print("📭 No activities found")
                    QMessageBox.information(None, "No Activities", "No recent activities found.")

            except Exception as e:
                error_msg = f"Error getting activities: {e}"
                print(f"⚠️  {error_msg}")
                QMessageBox.warning(None, "Activity Error", error_msg)

            return True
        else:
            print("❌ Authentication failed")
            QMessageBox.critical(
                None,
                "Authentication Failed",
                "Failed to authenticate with Garmin Connect.\\n" "Please check your credentials and try again.",
            )
            return False

    except Exception as e:
        error_msg = f"Error during authentication: {e}"
        print(f"💥 {error_msg}")
        print(f"Error type: {type(e).__name__}")
        QMessageBox.critical(None, "Error", error_msg)
        return False


if __name__ == "__main__":
    success = test_mfa_gui()
    print(f"\\n{'✅ Test completed successfully' if success else '❌ Test failed'}")
    sys.exit(0 if success else 1)
