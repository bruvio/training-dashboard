"""
Simple Main Window for Garmin Connect Desktop Dashboard.

Simplified version optimized for macOS compatibility with minimal styling.
"""

import sys
import webbrowser
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QStatusBar,
    QCheckBox,
    QHeaderView,
    QGroupBox,
    QMessageBox,
    QComboBox,
    QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QSettings, QSize
from PyQt6.QtGui import QFont

from garmin_client.client import GarminConnectClient
from .login_dialog_simple import SimpleLoginDialog
from .mfa_dialog import MFADialog
from .settings_dialog import SettingsDialog
from .download_worker import DownloadWorker, BulkDownloadManager


class SimpleGarminDashboardApp(QMainWindow):
    """Simplified PyQt6 application window for Garmin Connect Dashboard."""

    def __init__(self):
        super().__init__()

        # Initialize core components
        self.garmin_client = GarminConnectClient()
        self.settings = QSettings("GarminDashboard", "Settings")
        self.download_manager = BulkDownloadManager(self.garmin_client)

        # State tracking
        self.current_activities = []
        self.active_worker = None
        self.is_authenticated = False

        # Initialize UI
        self.init_ui()
        self.check_authentication_status()

    def init_ui(self):
        """Initialize the user interface with simple layout."""
        self.setWindowTitle("Garmin Connect Dashboard")
        self.setMinimumSize(QSize(800, 600))

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("Garmin Connect Dashboard")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Authentication section
        auth_layout = QHBoxLayout()
        self.auth_status_label = QLabel("Status: Not authenticated")
        self.login_button = QPushButton("Login to Garmin Connect")
        self.login_button.clicked.connect(self.show_login_dialog)

        auth_layout.addWidget(self.auth_status_label)
        auth_layout.addStretch()
        auth_layout.addWidget(self.login_button)
        main_layout.addLayout(auth_layout)

        # Date selection section
        date_group = QGroupBox("Select Date Range")
        date_layout = QHBoxLayout(date_group)

        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)

        main_layout.addWidget(date_group)

        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QHBoxLayout(options_group)

        options_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["fit", "gpx"])
        options_layout.addWidget(self.format_combo)

        self.auto_import_checkbox = QCheckBox("Auto-import to dashboard")
        self.auto_import_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_import_checkbox)

        main_layout.addWidget(options_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.fetch_button = QPushButton("Fetch Activity List")
        self.fetch_button.clicked.connect(self.fetch_activities)
        self.fetch_button.setEnabled(False)
        button_layout.addWidget(self.fetch_button)

        self.download_button = QPushButton("Download Selected Activities")
        self.download_button.clicked.connect(self.download_activities)
        self.download_button.setEnabled(False)
        button_layout.addWidget(self.download_button)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings_dialog)
        button_layout.addWidget(self.settings_button)

        self.dashboard_button = QPushButton("Open Web Dashboard")
        self.dashboard_button.clicked.connect(self.open_web_dashboard)
        button_layout.addWidget(self.dashboard_button)

        main_layout.addLayout(button_layout)

        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Select", "Date", "Activity", "Type"])

        # Make table headers resize to content
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self.activity_table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Please login to Garmin Connect")

        # Apply minimal styling for better macOS compatibility
        self.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 7px;
                padding-top: 5px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QPushButton {
                padding: 5px 10px;
                border: 1px solid gray;
                border-radius: 3px;
            }
            
            QPushButton:pressed {
                background-color: lightgray;
            }
            
            QTableWidget {
                gridline-color: lightgray;
            }
        """
        )

    def check_authentication_status(self):
        """Check if user is authenticated with Garmin Connect."""
        try:
            if self.garmin_client.has_stored_credentials():
                self.auth_status_label.setText("Status: Authenticated ✓")
                self.login_button.setText("Re-authenticate")
                self.fetch_button.setEnabled(True)
                self.is_authenticated = True
                self.status_bar.showMessage("Ready - Authenticated with Garmin Connect")
            else:
                self.auth_status_label.setText("Status: Not authenticated")
                self.login_button.setText("Login to Garmin Connect")
                self.fetch_button.setEnabled(False)
                self.is_authenticated = False
                self.status_bar.showMessage("Please login to Garmin Connect")
        except Exception as e:
            self.auth_status_label.setText(f"Status: Error - {str(e)}")
            self.status_bar.showMessage(f"Authentication error: {str(e)}")

    def show_login_dialog(self):
        """Show the login dialog."""
        dialog = SimpleLoginDialog(self)

        # Pre-fill email if available
        try:
            stored_email = self.garmin_client.get_stored_email()
            if stored_email:
                dialog.set_credentials(stored_email)
        except:
            pass

        if dialog.exec() == SimpleLoginDialog.DialogCode.Accepted:
            email, password = dialog.get_credentials()
            should_remember = dialog.should_remember_credentials()

            self.status_bar.showMessage("Authenticating...")

            # Create MFA callback function
            def mfa_callback():
                mfa_dialog = MFADialog(self)
                if mfa_dialog.exec() == MFADialog.DialogCode.Accepted:
                    return mfa_dialog.get_mfa_code()
                else:
                    return None  # User cancelled MFA

            try:
                # Test authentication with MFA support
                success = self.garmin_client.authenticate(email, password, mfa_callback=mfa_callback)

                if success and should_remember:
                    self.garmin_client.store_credentials(email, password)

                if success:
                    QMessageBox.information(self, "Success", "Authentication successful!")
                    self.check_authentication_status()
                else:
                    QMessageBox.warning(
                        self, "Failed", "Authentication failed. Please check your credentials and try again."
                    )
                    self.status_bar.showMessage("Authentication failed")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Authentication error: {str(e)}")
                self.status_bar.showMessage(f"Authentication error: {str(e)}")

    def fetch_activities(self):
        """Fetch activities list from Garmin Connect."""
        if not self.is_authenticated:
            QMessageBox.warning(self, "Not Authenticated", "Please login first.")
            return

        start_date = self.start_date.date().toPython()
        end_date = self.end_date.date().toPython()

        self.status_bar.showMessage("Fetching activities...")
        self.fetch_button.setEnabled(False)

        try:
            activities = self.garmin_client.get_activities(start_date, end_date)
            self.populate_activity_table(activities)
            self.status_bar.showMessage(f"Found {len(activities)} activities")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch activities: {str(e)}")
            self.status_bar.showMessage(f"Fetch error: {str(e)}")

        finally:
            self.fetch_button.setEnabled(True)

    def populate_activity_table(self, activities):
        """Populate the activity table with fetched activities."""
        self.current_activities = activities
        self.activity_table.setRowCount(len(activities))

        for row, activity in enumerate(activities):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.activity_table.setCellWidget(row, 0, checkbox)

            # Activity date
            date_item = QTableWidgetItem(activity.get("startTimeLocal", "Unknown"))
            self.activity_table.setItem(row, 1, date_item)

            # Activity name
            name_item = QTableWidgetItem(activity.get("activityName", "Unknown"))
            self.activity_table.setItem(row, 2, name_item)

            # Activity type
            type_item = QTableWidgetItem(activity.get("activityType", {}).get("typeKey", "Unknown"))
            self.activity_table.setItem(row, 3, type_item)

        self.download_button.setEnabled(len(activities) > 0)

    def download_activities(self):
        """Download selected activities."""
        if not self.current_activities:
            QMessageBox.warning(self, "No Activities", "Please fetch activities first.")
            return

        # Get selected activities
        selected_activities = []
        for row in range(self.activity_table.rowCount()):
            checkbox = self.activity_table.cellWidget(row, 0)
            if checkbox.isChecked():
                selected_activities.append(self.current_activities[row])

        if not selected_activities:
            QMessageBox.warning(self, "No Selection", "Please select at least one activity.")
            return

        # Get activity IDs
        activity_ids = [activity.get("activityId") for activity in selected_activities if activity.get("activityId")]

        if not activity_ids:
            QMessageBox.warning(self, "Invalid Activities", "No valid activity IDs found.")
            return

        # Start download
        format_type = self.format_combo.currentText()

        self.status_bar.showMessage(f"Starting download of {len(activity_ids)} activities...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(activity_ids))
        self.progress_bar.setValue(0)

        self.download_button.setEnabled(False)

        # Create download worker
        self.active_worker = DownloadWorker(self.garmin_client, activity_ids, format_type, rate_limit_delay=1.0)

        # Connect signals
        self.active_worker.progress_updated.connect(self.update_download_progress)
        self.active_worker.download_completed.connect(self.download_finished)
        self.active_worker.error_occurred.connect(self.download_error)
        self.active_worker.status_updated.connect(self.status_bar.showMessage)

        # Start download
        self.active_worker.start()

    def update_download_progress(self, current, total):
        """Update download progress bar."""
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)

    def download_finished(self, results):
        """Handle download completion."""
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)

        successful = results.get("successful", 0)
        total = results.get("total", 0)

        QMessageBox.information(self, "Download Complete", f"Downloaded {successful}/{total} activities successfully.")

        if successful > 0 and self.auto_import_checkbox.isChecked():
            self.import_to_dashboard()

    def download_error(self, error_message):
        """Handle download errors."""
        self.status_bar.showMessage(f"Download error: {error_message}")

    def import_to_dashboard(self):
        """Import downloaded activities to the dashboard."""
        self.status_bar.showMessage("Importing activities to dashboard...")
        # This would trigger the CLI importer or direct database import
        # For now, just show a message
        QMessageBox.information(
            self,
            "Import",
            "Activities would be imported to the dashboard.\nPlease check the web dashboard for updates.",
        )

    def show_settings_dialog(self):
        """Show the settings dialog."""
        # Create a simple config for the dialog
        config = {
            "default_download_format": self.format_combo.currentText(),
            "auto_import_to_dashboard": self.auto_import_checkbox.isChecked(),
            "download_directory": str(Path.home() / "Downloads"),
            "activities_directory": "./activities",
        }

        dialog = SettingsDialog(config, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            updated_config = dialog.get_config()
            # Apply updated settings
            self.format_combo.setCurrentText(updated_config.get("default_download_format", "fit"))
            self.auto_import_checkbox.setChecked(updated_config.get("auto_import_to_dashboard", True))

    def open_web_dashboard(self):
        """Open the web dashboard in browser."""
        try:
            webbrowser.open("http://localhost:8050")
            self.status_bar.showMessage("Opened web dashboard in browser")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open web dashboard: {str(e)}")


def main():
    """Main entry point for the simplified desktop application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Garmin Connect Dashboard")
    app.setOrganizationName("GarminDashboard")

    # Create and show main window
    window = SimpleGarminDashboardApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
