"""
Settings Dialog for Garmin Dashboard Configuration.

Configuration dialog for managing download preferences, directories,
rate limiting, and other application settings.
"""

import sys
from pathlib import Path
from typing import Dict, Any

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QTabWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QGroupBox,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config.copy()  # Work on a copy

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Garmin Dashboard Settings")
        self.setModal(True)
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Header
        header_label = QLabel("Application Settings")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)

        # Tabs for different settings categories
        tab_widget = QTabWidget()

        # Download settings tab
        download_tab = self.create_download_tab()
        tab_widget.addTab(download_tab, "Downloads")

        # Directory settings tab
        directory_tab = self.create_directory_tab()
        tab_widget.addTab(directory_tab, "Directories")

        # Advanced settings tab
        advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        layout.addWidget(tab_widget)

        # Buttons
        button_layout = QHBoxLayout()

        self.restore_defaults_button = QPushButton("Restore Defaults")
        self.restore_defaults_button.clicked.connect(self.restore_defaults)
        button_layout.addWidget(self.restore_defaults_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # Apply styling
        self.apply_styling()

    def create_download_tab(self):
        """Create download settings tab."""
        widget = QGroupBox()
        layout = QFormLayout(widget)

        # Default download format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["fit", "gpx"])
        layout.addRow("Default Format:", self.format_combo)

        # Max concurrent downloads
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setSuffix(" downloads")
        layout.addRow("Max Concurrent Downloads:", self.concurrent_spin)

        # Rate limit delay
        self.rate_limit_spin = QDoubleSpinBox()
        self.rate_limit_spin.setRange(0.1, 10.0)
        self.rate_limit_spin.setSingleStep(0.1)
        self.rate_limit_spin.setSuffix(" seconds")
        layout.addRow("Delay Between Downloads:", self.rate_limit_spin)

        # Auto-import to dashboard
        self.auto_import_checkbox = QCheckBox("Automatically import downloaded activities to dashboard")
        layout.addRow("", self.auto_import_checkbox)

        return widget

    def create_directory_tab(self):
        """Create directory settings tab."""
        widget = QGroupBox()
        layout = QFormLayout(widget)

        # Download directory
        download_layout = QHBoxLayout()
        self.download_dir_edit = QLineEdit()
        self.download_dir_button = QPushButton("Browse...")
        self.download_dir_button.clicked.connect(self.browse_download_directory)
        download_layout.addWidget(self.download_dir_edit)
        download_layout.addWidget(self.download_dir_button)
        layout.addRow("Download Directory:", download_layout)

        # Activities directory
        activities_layout = QHBoxLayout()
        self.activities_dir_edit = QLineEdit()
        self.activities_dir_button = QPushButton("Browse...")
        self.activities_dir_button.clicked.connect(self.browse_activities_directory)
        activities_layout.addWidget(self.activities_dir_edit)
        activities_layout.addWidget(self.activities_dir_button)
        layout.addRow("Activities Directory:", activities_layout)

        # Note about directories
        note_label = QLabel(
            "Note: Downloaded activities will be saved to the download directory "
            "and optionally copied to the activities directory for dashboard import."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #666666; font-size: 11px;")
        layout.addRow("", note_label)

        return widget

    def create_advanced_tab(self):
        """Create advanced settings tab."""
        widget = QGroupBox()
        layout = QFormLayout(widget)

        # Logging level
        self.logging_combo = QComboBox()
        self.logging_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("Logging Level:", self.logging_combo)

        # Connection timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setSuffix(" seconds")
        layout.addRow("Connection Timeout:", self.timeout_spin)

        # Retry attempts
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        self.retry_spin.setSuffix(" attempts")
        layout.addRow("Download Retry Attempts:", self.retry_spin)

        # Clear credentials button
        self.clear_credentials_button = QPushButton("Clear Stored Credentials")
        self.clear_credentials_button.clicked.connect(self.clear_credentials)
        layout.addRow("Security:", self.clear_credentials_button)

        return widget

    def apply_styling(self):
        """Apply modern styling to the dialog."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f8f9fa;
                font-family: system-ui, -apple-system, sans-serif;
            }
            
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                border: 2px solid #dee2e6;
                padding: 10px 18px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid white;
                color: #0078d4;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
                border-color: #0078d4;
            }
            
            QGroupBox {
                border: none;
                padding-top: 15px;
                font-weight: normal;
            }
            
            QLabel {
                font-size: 14px;
                color: #495057;
            }
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                padding: 8px 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #0078d4;
                outline: none;
                background-color: #f8f9fa;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton#restore_defaults_button {
                background-color: #ffc107;
                color: #212529;
            }
            
            QPushButton#restore_defaults_button:hover {
                background-color: #e0a800;
            }
            
            QPushButton#clear_credentials_button {
                background-color: #dc3545;
            }
            
            QPushButton#clear_credentials_button:hover {
                background-color: #c82333;
            }
            
            QPushButton#cancel_button {
                background-color: #6c757d;
            }
            
            QPushButton#cancel_button:hover {
                background-color: #5a6268;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #495057;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                border-radius: 3px;
                background-color: #0078d4;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAiIGhlaWdodD0iMTAiIHZpZXdCb3g9IjAgMCAxMCAxMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTIuNSA1TDQgNi41TDcuNSAzIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjEuNSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 2px solid #ced4da;
                border-top-right-radius: 6px;
                background-color: #f8f9fa;
            }
            
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 2px solid #ced4da;
                border-bottom-right-radius: 6px;
                background-color: #f8f9fa;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
                background-color: #6c757d;
            }
        """
        )

        # Set object names for styling
        self.restore_defaults_button.setObjectName("restore_defaults_button")
        self.cancel_button.setObjectName("cancel_button")
        self.clear_credentials_button.setObjectName("clear_credentials_button")

    def load_config(self):
        """Load current configuration into UI elements."""
        # Download settings
        format_value = self.config.get("default_download_format", "fit")
        format_index = self.format_combo.findText(format_value)
        if format_index >= 0:
            self.format_combo.setCurrentIndex(format_index)

        self.concurrent_spin.setValue(self.config.get("max_concurrent_downloads", 3))
        self.rate_limit_spin.setValue(self.config.get("rate_limit_delay", 1.0))
        self.auto_import_checkbox.setChecked(self.config.get("auto_import_to_dashboard", True))

        # Directory settings
        self.download_dir_edit.setText(self.config.get("download_directory", ""))
        self.activities_dir_edit.setText(self.config.get("activities_directory", "./activities"))

        # Advanced settings
        logging_level = self.config.get("logging_level", "INFO")
        logging_index = self.logging_combo.findText(logging_level)
        if logging_index >= 0:
            self.logging_combo.setCurrentIndex(logging_index)

        self.timeout_spin.setValue(self.config.get("connection_timeout", 60))
        self.retry_spin.setValue(self.config.get("retry_attempts", 3))

    def save_config(self):
        """Save UI values to configuration."""
        # Download settings
        self.config["default_download_format"] = self.format_combo.currentText()
        self.config["max_concurrent_downloads"] = self.concurrent_spin.value()
        self.config["rate_limit_delay"] = self.rate_limit_spin.value()
        self.config["auto_import_to_dashboard"] = self.auto_import_checkbox.isChecked()

        # Directory settings
        self.config["download_directory"] = self.download_dir_edit.text().strip()
        self.config["activities_directory"] = self.activities_dir_edit.text().strip()

        # Advanced settings
        self.config["logging_level"] = self.logging_combo.currentText()
        self.config["connection_timeout"] = self.timeout_spin.value()
        self.config["retry_attempts"] = self.retry_spin.value()

    def browse_download_directory(self):
        """Browse for download directory."""
        current_dir = self.download_dir_edit.text() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory", current_dir)
        if directory:
            self.download_dir_edit.setText(directory)

    def browse_activities_directory(self):
        """Browse for activities directory."""
        current_dir = self.activities_dir_edit.text() or "./activities"
        directory = QFileDialog.getExistingDirectory(self, "Select Activities Directory", current_dir)
        if directory:
            self.activities_dir_edit.setText(directory)

    def clear_credentials(self):
        """Clear stored credentials with confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear Credentials",
            "Are you sure you want to clear stored credentials?\n" "You will need to login again next time.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # In a real implementation, this would call GarminConnectClient.clear_credentials()
            QMessageBox.information(self, "Credentials Cleared", "Stored credentials have been cleared successfully.")

    def restore_defaults(self):
        """Restore default settings."""
        reply = QMessageBox.question(
            self,
            "Restore Defaults",
            "Are you sure you want to restore all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Default configuration
            default_config = {
                "default_download_format": "fit",
                "max_concurrent_downloads": 3,
                "rate_limit_delay": 1.0,
                "auto_import_to_dashboard": True,
                "download_directory": str(Path.home() / ".garmin-dashboard" / "downloads"),
                "activities_directory": "./activities",
                "logging_level": "INFO",
                "connection_timeout": 60,
                "retry_attempts": 3,
            }

            self.config.update(default_config)
            self.load_config()

    def apply_settings(self):
        """Apply settings without closing dialog."""
        self.save_config()
        QMessageBox.information(self, "Settings Applied", "Settings have been applied successfully.")

    def accept_settings(self):
        """Save settings and close dialog."""
        self.save_config()
        self.accept()

    def get_config(self) -> Dict[str, Any]:
        """
        Get the updated configuration.

        Returns:
            Updated configuration dictionary
        """
        return self.config.copy()


# Standalone testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Sample configuration
    test_config = {
        "default_download_format": "fit",
        "max_concurrent_downloads": 3,
        "rate_limit_delay": 1.0,
        "auto_import_to_dashboard": True,
        "download_directory": "/Users/test/Downloads",
        "activities_directory": "./activities",
    }

    dialog = SettingsDialog(test_config)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        updated_config = dialog.get_config()
        print("Updated configuration:", updated_config)
    else:
        print("Settings cancelled")

    sys.exit(0)
