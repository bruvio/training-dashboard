"""
Main Window for Garmin Connect Desktop Dashboard.

PyQt6-based desktop application providing authentication, calendar selection,
activity management, and integration with the web dashboard.
Research-validated implementation following enhanced PRP specifications.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
import subprocess
import sys
from typing import Dict, List
import webbrowser

from PyQt6.QtCore import QDate, QSettings, QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from garmin_client.client import GarminConnectClient

from .download_worker import BulkDownloadManager, DownloadWorker
from .login_dialog import LoginDialog
from .settings_dialog import SettingsDialog


class GarminDashboardApp(QMainWindow):
    """Main PyQt6 application window for Garmin Connect Dashboard."""

    def __init__(self):
        super().__init__()

        # Initialize core components
        self.garmin_client = GarminConnectClient()
        self.settings = QSettings("GarminDashboard", "Settings")
        self.download_manager = BulkDownloadManager(self.garmin_client)

        # State tracking
        self.current_activities = []
        self.active_worker = None

        # Initialize UI
        self.init_ui()
        self.init_connections()

        # Load settings and check authentication
        self.restore_window_state()
        self.check_authentication_status()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Garmin Connect Dashboard")
        self.setMinimumSize(QSize(1200, 800))

        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)

        # Right panel - Data view
        right_panel = self.create_data_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([400, 800])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Please login to Garmin Connect")

        # Menu bar
        self.create_menu_bar()

        # Apply styling
        self.apply_styling()

    def create_control_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Authentication section
        auth_group = QGroupBox("Authentication")
        auth_layout = QVBoxLayout(auth_group)

        self.login_status_label = QLabel("Not logged in")
        self.login_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        auth_layout.addWidget(self.login_status_label)

        self.login_button = QPushButton("Login to Garmin Connect")
        self.login_button.clicked.connect(self.show_login_dialog)
        auth_layout.addWidget(self.login_button)

        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        self.logout_button.setEnabled(False)
        auth_layout.addWidget(self.logout_button)

        layout.addWidget(auth_group)

        # Date selection section
        date_group = QGroupBox("Select Date Range")
        date_layout = QVBoxLayout(date_group)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setSelectionMode(QCalendarWidget.SelectionMode.SingleSelection)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        date_layout.addWidget(self.calendar)

        # Quick date buttons
        quick_dates_layout = QHBoxLayout()

        self.last_week_btn = QPushButton("Last Week")
        self.last_week_btn.clicked.connect(lambda: self.set_date_range(-7))
        quick_dates_layout.addWidget(self.last_week_btn)

        self.last_month_btn = QPushButton("Last Month")
        self.last_month_btn.clicked.connect(lambda: self.set_date_range(-30))
        quick_dates_layout.addWidget(self.last_month_btn)

        date_layout.addLayout(quick_dates_layout)

        # Date range display
        self.date_range_label = QLabel("Select date range")
        self.date_range_label.setWordWrap(True)
        date_layout.addWidget(self.date_range_label)

        layout.addWidget(date_group)

        # Download section
        download_group = QGroupBox("Download Activities")
        download_layout = QVBoxLayout(download_group)

        self.refresh_button = QPushButton("Refresh Activities")
        self.refresh_button.clicked.connect(self.refresh_activities)
        self.refresh_button.setEnabled(False)
        download_layout.addWidget(self.refresh_button)

        self.download_selected_button = QPushButton("Download Selected")
        self.download_selected_button.clicked.connect(self.download_selected_activities)
        self.download_selected_button.setEnabled(False)
        download_layout.addWidget(self.download_selected_button)

        self.download_all_button = QPushButton("Download All Visible")
        self.download_all_button.clicked.connect(self.download_all_activities)
        self.download_all_button.setEnabled(False)
        download_layout.addWidget(self.download_all_button)

        # Download progress
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        download_layout.addWidget(self.download_progress)

        self.download_status = QLabel("")
        self.download_status.setWordWrap(True)
        download_layout.addWidget(self.download_status)

        layout.addWidget(download_group)

        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings_dialog)
        actions_layout.addWidget(self.settings_button)

        self.web_dashboard_button = QPushButton("Open Web Dashboard")
        self.web_dashboard_button.clicked.connect(self.open_web_dashboard)
        actions_layout.addWidget(self.web_dashboard_button)

        layout.addWidget(actions_group)

        layout.addStretch()
        return panel

    def create_data_panel(self) -> QWidget:
        """Create the right data panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Activities table header
        header_layout = QHBoxLayout()

        activities_label = QLabel("Activities")
        activities_font = QFont()
        activities_font.setPointSize(14)
        activities_font.setBold(True)
        activities_label.setFont(activities_font)
        header_layout.addWidget(activities_label)

        header_layout.addStretch()

        # Select all/none buttons
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_activities)
        self.select_all_button.setEnabled(False)
        header_layout.addWidget(self.select_all_button)

        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self.select_no_activities)
        self.select_none_button.setEnabled(False)
        header_layout.addWidget(self.select_none_button)

        layout.addLayout(header_layout)

        # Activities table
        self.activities_table = QTableWidget()
        self.activities_table.setColumnCount(7)
        self.activities_table.setHorizontalHeaderLabels(
            ["Select", "Date", "Activity", "Distance", "Duration", "Type", "Status"]
        )

        # Configure table
        header = self.activities_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.activities_table.setAlternatingRowColors(True)
        self.activities_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.activities_table.setSortingEnabled(True)

        layout.addWidget(self.activities_table)

        return panel

    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        login_action = QAction("Login", self)
        login_action.setShortcut("Ctrl+L")
        login_action.triggered.connect(self.show_login_dialog)
        file_menu.addAction(login_action)

        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        refresh_action = QAction("Refresh Activities", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_activities)
        edit_menu.addAction(refresh_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.select_all_activities)
        edit_menu.addAction(select_all_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings_dialog)
        tools_menu.addAction(settings_action)

        web_dashboard_action = QAction("Open Web Dashboard", self)
        web_dashboard_action.setShortcut("Ctrl+W")
        web_dashboard_action.triggered.connect(self.open_web_dashboard)
        tools_menu.addAction(web_dashboard_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def apply_styling(self):
        """Apply modern styling to the application."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
            
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
            
            QCalendarWidget QTableView {
                background-color: white;
                selection-background-color: #0078d4;
            }
            
            QCalendarWidget QToolButton {
                color: #495057;
                font-size: 13px;
                font-weight: bold;
            }
            
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                font-size: 12px;
                font-weight: bold;
            }
            
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
            
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                font-size: 12px;
                padding: 2px;
            }
        """
        )

    def init_connections(self):
        """Initialize additional signal connections."""
        # Connect table selection changes
        self.activities_table.itemSelectionChanged.connect(self.on_selection_changed)

    def restore_window_state(self):
        """Restore window size and position from settings."""
        if geometry := self.settings.value("geometry"):
            self.restoreGeometry(geometry)

        if window_state := self.settings.value("windowState"):
            self.restoreState(window_state)

    def save_window_state(self):
        """Save window size and position to settings."""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def closeEvent(self, event):
        """Handle application close event."""
        # Stop any active downloads
        if self.active_worker and self.active_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "A download is currently in progress. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.active_worker.stop_download()
                self.active_worker.wait(3000)  # Wait up to 3 seconds
            else:
                event.ignore()
                return

        # Save settings
        self.save_window_state()
        event.accept()

    # Authentication methods
    def check_authentication_status(self):
        """Check if user has stored credentials and attempt auto-login."""
        if credentials := self.garmin_client.load_credentials():
            email = credentials.get("email", "")
            self.login_status_label.setText(f"Auto-authenticating as {email}...")
            self.login_status_label.setStyleSheet("color: #ffc107; font-weight: bold;")

            # Attempt authentication in background
            QTimer.singleShot(1000, self.attempt_auto_login)

    def attempt_auto_login(self):
        """Attempt automatic login with stored credentials."""
        if self.garmin_client.authenticate():
            self.on_authentication_success()
        else:
            self.login_status_label.setText("Auto-login failed - Please login manually")
            self.login_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")

    def show_login_dialog(self):
        """Show login dialog."""
        # Pre-fill with stored credentials if available
        credentials = self.garmin_client.load_credentials()

        dialog = LoginDialog(self)
        if credentials:
            dialog.set_credentials(credentials.get("email", ""))

        if dialog.exec() == LoginDialog.DialogCode.Accepted:
            email, password = dialog.get_credentials()
            dialog.should_remember_credentials()

            # Show progress
            self.login_status_label.setText("Authenticating...")
            self.login_status_label.setStyleSheet("color: #ffc107; font-weight: bold;")

            # Attempt authentication
            if self.garmin_client.authenticate(email, password):
                self.on_authentication_success()
            else:
                self.login_status_label.setText("Authentication failed")
                self.login_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
                QMessageBox.critical(
                    self,
                    "Login Failed",
                    "Failed to authenticate with Garmin Connect.\n" "Please check your credentials and try again.",
                )

    def on_authentication_success(self):
        """Handle successful authentication."""
        session_info = self.garmin_client.get_session_info()
        email = session_info.get("email", "Unknown") if session_info else "Unknown"

        self.login_status_label.setText(f"Logged in as {email}")
        self.login_status_label.setStyleSheet("color: #28a745; font-weight: bold;")

        # Enable UI elements
        self.login_button.setEnabled(False)
        self.logout_button.setEnabled(True)
        self.refresh_button.setEnabled(True)

        self.status_bar.showMessage("Successfully authenticated with Garmin Connect")

        # Auto-refresh activities for current month
        self.set_date_range(-30)
        QTimer.singleShot(500, self.refresh_activities)

    def logout(self):
        """Logout from Garmin Connect."""
        self.garmin_client.logout()

        self.login_status_label.setText("Not logged in")
        self.login_status_label.setStyleSheet("color: #dc3545; font-weight: bold;")

        # Disable UI elements
        self.login_button.setEnabled(True)
        self.logout_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.download_selected_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.select_none_button.setEnabled(False)

        # Clear activities table
        self.activities_table.setRowCount(0)
        self.current_activities.clear()

        self.status_bar.showMessage("Logged out from Garmin Connect")

    # Date selection methods
    def on_date_selected(self):
        """Handle calendar date selection."""
        selected_date = self.calendar.selectedDate().toPython()
        self.date_range_label.setText(f"Selected: {selected_date.strftime('%Y-%m-%d')}")

    def set_date_range(self, days_back: int):
        """Set date range relative to today."""
        end_date = date.today()
        start_date = end_date + timedelta(days=days_back)

        # Update calendar selection
        self.calendar.setSelectedDate(QDate.fromString(start_date.isoformat(), Qt.DateFormat.ISODate))

        self.date_range_label.setText(f"Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

        # Store the date range for refreshing activities
        self.current_start_date = start_date
        self.current_end_date = end_date

    # Activity management methods
    def refresh_activities(self):
        """Refresh activities from Garmin Connect."""
        if not self.garmin_client.is_authenticated():
            QMessageBox.warning(self, "Not Authenticated", "Please login first.")
            return

        self.status_bar.showMessage("Refreshing activities from Garmin Connect...")
        self.refresh_button.setEnabled(False)

        # Get date range
        if not hasattr(self, "current_start_date"):
            self.set_date_range(-30)  # Default to last 30 days

        try:
            if activities := self.garmin_client.get_activities(
                self.current_start_date, self.current_end_date, limit=200
            ):
                self.current_activities = activities
                self.populate_activities_table(activities)
                self.status_bar.showMessage(f"Found {len(activities)} activities")
            else:
                self.current_activities = []
                self.activities_table.setRowCount(0)
                self.status_bar.showMessage("No activities found for selected date range")
                QMessageBox.information(self, "No Activities", "No activities found for the selected date range.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to retrieve activities:\n{str(e)}")
            self.status_bar.showMessage("Failed to retrieve activities")

        finally:
            self.refresh_button.setEnabled(True)

    def populate_activities_table(self, activities: List[Dict]):
        """Populate the activities table with data."""
        self.activities_table.setRowCount(len(activities))

        for row, activity in enumerate(activities):
            # Checkbox for selection
            checkbox = QCheckBox()
            self.activities_table.setCellWidget(row, 0, checkbox)

            if start_time_local := activity.get("startTimeLocal", ""):
                try:
                    dt = datetime.fromisoformat(start_time_local.replace("Z", ""))
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = start_time_local
            else:
                date_str = "Unknown"

            activity_name = activity.get("activityName", "Unnamed Activity")
            distance = activity.get("distance", 0)
            duration = activity.get("duration", 0) or activity.get("elapsedDuration", 0)
            activity_type = activity.get("activityType", {}).get("typeKey", "unknown")

            # Create table items
            self.activities_table.setItem(row, 1, QTableWidgetItem(date_str))
            self.activities_table.setItem(row, 2, QTableWidgetItem(activity_name))

            # Format distance
            if distance and distance > 0:
                distance_str = f"{distance/1000:.2f} km"
            else:
                distance_str = "N/A"
            self.activities_table.setItem(row, 3, QTableWidgetItem(distance_str))

            # Format duration
            if duration and duration > 0:
                hours = int(duration // 3600)
                minutes = int((duration % 3600) // 60)
                duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            else:
                duration_str = "N/A"
            self.activities_table.setItem(row, 4, QTableWidgetItem(duration_str))

            # Activity type with emoji
            type_display = self.get_activity_type_display(activity_type)
            self.activities_table.setItem(row, 5, QTableWidgetItem(type_display))

            self.activities_table.setItem(row, 6, QTableWidgetItem("Not Downloaded"))

            # Store activity ID and data for downloading
            activity_id = activity.get("activityId")
            self.activities_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, activity_id)
            self.activities_table.item(row, 2).setData(Qt.ItemDataRole.UserRole, activity)

        # Enable selection buttons
        self.select_all_button.setEnabled(True)
        self.select_none_button.setEnabled(True)
        self.download_selected_button.setEnabled(False)
        self.download_all_button.setEnabled(True)

    def get_activity_type_display(self, activity_type: str) -> str:
        """Get display string for activity type with emoji."""
        type_map = {
            "running": "🏃 Running",
            "cycling": "🚴 Cycling",
            "swimming": "🏊 Swimming",
            "walking": "🚶 Walking",
            "hiking": "🥾 Hiking",
            "strength_training": "💪 Strength",
            "cardio": "💓 Cardio",
            "yoga": "🧘 Yoga",
            "golf": "🏌️ Golf",
            "tennis": "🎾 Tennis",
        }

        return type_map.get(activity_type.lower(), f"⚽ {activity_type.title()}")

    def on_selection_changed(self):
        """Handle activity table selection changes."""
        selected_count = len(self.get_selected_activities())
        self.download_selected_button.setEnabled(selected_count > 0)

        if selected_count > 0:
            self.download_selected_button.setText(f"Download Selected ({selected_count})")
        else:
            self.download_selected_button.setText("Download Selected")

    def get_selected_activities(self) -> List[int]:
        """Get list of selected activity IDs."""
        selected_activities = []

        for row in range(self.activities_table.rowCount()):
            checkbox = self.activities_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                if activity_id := self.activities_table.item(row, 1).data(Qt.ItemDataRole.UserRole):
                    selected_activities.append(activity_id)

        return selected_activities

    def select_all_activities(self):
        """Select all activities in the table."""
        for row in range(self.activities_table.rowCount()):
            if checkbox := self.activities_table.cellWidget(row, 0):
                checkbox.setChecked(True)

    def select_no_activities(self):
        """Deselect all activities in the table."""
        for row in range(self.activities_table.rowCount()):
            if checkbox := self.activities_table.cellWidget(row, 0):
                checkbox.setChecked(False)

    def download_selected_activities(self):
        """Download selected activities."""
        selected_activities = self.get_selected_activities()

        if not selected_activities:
            QMessageBox.information(self, "No Selection", "Please select activities to download.")
            return

        self.start_download(selected_activities)

    def download_all_activities(self):
        """Download all visible activities."""
        all_activities = []

        for row in range(self.activities_table.rowCount()):
            if activity_id := self.activities_table.item(row, 1).data(Qt.ItemDataRole.UserRole):
                all_activities.append(activity_id)

        if not all_activities:
            QMessageBox.information(self, "No Activities", "No activities available for download.")
            return

        self.start_download(all_activities)

    def start_download(self, activity_ids: List[int]):
        """Start downloading activities in background."""
        if self.active_worker and self.active_worker.isRunning():
            QMessageBox.warning(
                self, "Download in Progress", "A download is already in progress. Please wait for it to complete."
            )
            return

        # Get configuration
        config = self.garmin_client.get_config()
        format_type = config.get("default_download_format", "fit")
        rate_limit = config.get("rate_limit_delay", 1.0)

        # Create download worker
        self.active_worker = DownloadWorker(self.garmin_client, activity_ids, format_type, rate_limit_delay=rate_limit)

        # Connect signals
        self.active_worker.progress_updated.connect(self.update_download_progress)
        self.active_worker.status_updated.connect(self.update_download_status)
        self.active_worker.activity_downloaded.connect(self.on_activity_downloaded)
        self.active_worker.download_completed.connect(self.on_download_completed)
        self.active_worker.error_occurred.connect(self.on_download_error)

        # Update UI for download
        self.download_progress.setVisible(True)
        self.download_progress.setMaximum(len(activity_ids))
        self.download_progress.setValue(0)

        # Disable buttons during download
        self.download_selected_button.setEnabled(False)
        self.download_all_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

        # Start download
        self.active_worker.start()

        self.status_bar.showMessage(f"Starting download of {len(activity_ids)} activities...")

    def update_download_progress(self, current: int, total: int):
        """Update download progress bar."""
        self.download_progress.setMaximum(total)
        self.download_progress.setValue(current)

        self.status_bar.showMessage(f"Downloaded {current}/{total} activities...")

    def update_download_status(self, message: str):
        """Update download status message."""
        self.download_status.setText(message)

    def on_activity_downloaded(self, activity_id: int, filename: str, success: bool):
        """Handle individual activity download completion."""
        # Update table status
        for row in range(self.activities_table.rowCount()):
            row_activity_id = self.activities_table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            if row_activity_id == activity_id:
                status_text = "Downloaded" if success else "Failed"
                self.activities_table.setItem(row, 6, QTableWidgetItem(status_text))
                break

    def on_download_completed(self, results: Dict):
        """Handle download completion."""
        # Hide progress
        self.download_progress.setVisible(False)

        # Re-enable buttons
        self.download_selected_button.setEnabled(False)  # Will be updated by selection
        self.download_all_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.on_selection_changed()  # Update selected button state

        # Show completion message
        total = results["total"]
        successful = results["successful"]
        failed = results["failed"]

        self.download_status.setText(f"Download complete: {successful}/{total} successful, {failed} failed")

        self.status_bar.showMessage(f"Download complete: {successful}/{total} successful")

        # Show summary dialog
        if failed > 0:
            QMessageBox.warning(
                self,
                "Download Complete with Errors",
                f"Downloaded {successful} out of {total} activities.\n" f"{failed} downloads failed.",
            )
        else:
            QMessageBox.information(self, "Download Complete", f"Successfully downloaded all {successful} activities!")

    def on_download_error(self, error_message: str):
        """Handle download error."""
        self.status_bar.showMessage(f"Download error: {error_message}")

    # Settings and utility methods
    def show_settings_dialog(self):
        """Show settings dialog."""
        config = self.garmin_client.get_config()
        dialog = SettingsDialog(config, self)

        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            new_config = dialog.get_config()
            self.garmin_client.save_config(new_config)
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")

    def open_web_dashboard(self):
        """Open web dashboard in browser."""
        try:
            # First try to check if the dashboard is running
            import requests

            response = requests.get("http://localhost:8050", timeout=2)
            if response.status_code == 200:
                webbrowser.open("http://localhost:8050")
                self.status_bar.showMessage("Opened web dashboard in browser")
            else:
                self.start_web_dashboard_and_open()
        except Exception:
            self.start_web_dashboard_and_open()

    def start_web_dashboard_and_open(self):
        """Start web dashboard and open in browser."""
        reply = QMessageBox.question(
            self,
            "Start Web Dashboard",
            "The web dashboard doesn't appear to be running.\n" "Would you like to start it using Docker?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Start docker-compose
                self.status_bar.showMessage("Starting web dashboard...")
                subprocess.Popen(["docker-compose", "up", "-d"], cwd=Path(__file__).parent.parent)

                # Wait a moment then open browser
                QTimer.singleShot(5000, lambda: webbrowser.open("http://localhost:8050"))
                QMessageBox.information(
                    self,
                    "Starting Dashboard",
                    "Web dashboard is starting up.\n" "It will open in your browser in a few seconds.",
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start web dashboard:\n{str(e)}")

    def show_about_dialog(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Garmin Dashboard",
            "<h3>Garmin Connect Desktop Dashboard</h3>"
            "<p>A comprehensive tool for downloading and analyzing your Garmin Connect activities.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Secure Garmin Connect authentication</li>"
            "<li>Calendar-based activity selection</li>"
            "<li>Bulk activity downloads</li>"
            "<li>Web dashboard integration</li>"
            "</ul>"
            "<p><b>Built with:</b> PyQt6, Python, and Dash</p>"
            "<p><b>Version:</b> 1.0.0</p>",
        )


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Garmin Connect Dashboard")
    app.setOrganizationName("Garmin Dashboard")
    app.setApplicationVersion("1.0.0")

    # Set application icon if available
    # app.setWindowIcon(QIcon("icon.png"))

    # Create and show main window
    window = GarminDashboardApp()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
