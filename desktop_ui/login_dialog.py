"""
Login Dialog for Garmin Connect Authentication.

Secure login dialog with credential validation and user-friendly interface.
Research-validated PyQt6 implementation following PRP specifications.
"""

import sys
from typing import Tuple

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class LoginDialog(QDialog):
    """Secure login dialog for Garmin Connect authentication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email = ""
        self.password = ""
        self.remember_credentials = False

        self.init_ui()
        self.init_connections()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Login to Garmin Connect")
        self.setModal(True)
        self.setFixedSize(400, 300)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header_layout = QVBoxLayout()

        title_label = QLabel("Garmin Connect Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Enter your Garmin Connect credentials")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(subtitle_label)

        layout.addLayout(header_layout)

        # Login form
        form_group = QGroupBox("Credentials")
        form_layout = QFormLayout(form_group)

        # Email field
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("your.email@example.com")
        self.email_edit.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Email:", self.email_edit)

        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Your Garmin Connect password")
        self.password_edit.textChanged.connect(self.validate_inputs)
        form_layout.addRow("Password:", self.password_edit)

        # Remember credentials checkbox
        self.remember_checkbox = QCheckBox("Remember credentials (encrypted)")
        self.remember_checkbox.setChecked(True)
        form_layout.addRow("", self.remember_checkbox)

        layout.addWidget(form_group)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666666;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.setEnabled(False)
        self.login_button.clicked.connect(self.attempt_login)
        button_layout.addWidget(self.login_button)

        layout.addLayout(button_layout)

        # Apply styling
        self.apply_styling()

    def init_connections(self):
        """Initialize signal connections."""
        # Enter key in password field should attempt login
        self.password_edit.returnPressed.connect(self.attempt_login)

        # Auto-focus email field
        self.email_edit.setFocus()

    def apply_styling(self):
        """Apply modern styling to the dialog."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #f8f9fa;
                font-family: system-ui, -apple-system, sans-serif;
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
            
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border-color: #0078d4;
                outline: none;
                background-color: #f8f9fa;
            }
            
            QLineEdit:invalid {
                border-color: #dc3545;
                background-color: #fff5f5;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
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
            
            QPushButton#cancel_button {
                background-color: #6c757d;
                color: white;
            }
            
            QPushButton#cancel_button:hover {
                background-color: #5a6268;
            }
            
            QCheckBox {
                font-size: 12px;
                color: #495057;
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
            
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                font-size: 12px;
            }
            
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
        """
        )

        # Set object names for specific styling
        self.cancel_button.setObjectName("cancel_button")

    def validate_inputs(self):
        """Validate input fields with enhanced feedback."""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        # Clear previous error messages when user types
        if (
            self.status_label.text()
            and not self.progress_bar.isVisible()
            and not self.status_label.text().startswith("Error:")
        ):
            self.status_label.setText("")
            self.status_label.setStyleSheet("color: #666666;")

        # Enhanced validation
        has_valid_email = self._is_valid_email(email)
        has_password = len(password) >= 6  # Minimum password length

        self.login_button.setEnabled(has_valid_email and has_password)

        # Provide real-time feedback
        if not self.progress_bar.isVisible():
            if email and not has_valid_email:
                self.status_label.setText("Please enter a valid email address")
                self.status_label.setStyleSheet("color: #dc3545;")
            elif password and len(password) < 6:
                self.status_label.setText("Password must be at least 6 characters")
                self.status_label.setStyleSheet("color: #dc3545;")
            elif has_valid_email and has_password:
                self.status_label.setText("Ready to login")
                self.status_label.setStyleSheet("color: #28a745;")

    def _is_valid_email(self, email: str) -> bool:
        """Enhanced email validation."""
        if not email or len(email) < 5:
            return False

        # Check for @ and . in correct positions
        if "@" not in email or "." not in email:
            return False

        at_pos = email.find("@")
        dot_pos = email.rfind(".")

        # Basic structure: something@domain.tld
        return (
            at_pos > 0  # @ not at start
            and dot_pos > at_pos + 1  # . after @ with at least 1 char
            and len(email) > dot_pos + 1  # something after final .
            and email.count("@") == 1
        )  # exactly one @

    def attempt_login(self):
        """Attempt login with comprehensive validation."""
        if not self.login_button.isEnabled():
            return

        # Get credentials
        self.email = self.email_edit.text().strip()
        self.password = self.password_edit.text()
        self.remember_credentials = self.remember_checkbox.isChecked()

        # Comprehensive validation
        if not self.email or not self.password:
            self.show_validation_error("Please enter both email and password.")
            return

        if not self._is_valid_email(self.email):
            self.show_validation_error("Please enter a valid email address.")
            self.email_edit.setFocus()
            self.email_edit.selectAll()
            return

        if len(self.password) < 6:
            self.show_validation_error("Password must be at least 6 characters long.")
            self.password_edit.setFocus()
            self.password_edit.selectAll()
            return

        # Show progress and disable inputs
        self.show_login_progress("Connecting to Garmin Connect...")

        # In a real implementation, this would be done in a separate thread
        # For now, simulate the login process
        QTimer.singleShot(2000, self.simulate_login_result)

    def show_login_progress(self, message: str):
        """Show login progress UI."""
        self.status_label.setText(message)
        self.progress_bar.setVisible(True)

        # Disable inputs
        self.email_edit.setEnabled(False)
        self.password_edit.setEnabled(False)
        self.remember_checkbox.setEnabled(False)
        self.login_button.setEnabled(False)
        self.cancel_button.setText("Cancel")

    def hide_login_progress(self):
        """Hide login progress UI."""
        self.progress_bar.setVisible(False)

        # Re-enable inputs
        self.email_edit.setEnabled(True)
        self.password_edit.setEnabled(True)
        self.remember_checkbox.setEnabled(True)
        self.validate_inputs()  # Re-validate to enable/disable login button
        self.cancel_button.setText("Cancel")

    def simulate_login_result(self):
        """Simulate login result (replace with real authentication)."""
        # For demonstration, accept any credentials
        # In real implementation, this would call the GarminConnectClient

        self.hide_login_progress()

        # Simulate successful login
        if len(self.password) >= 6:  # Simple validation
            self.status_label.setText("Login successful!")
            self.status_label.setStyleSheet("color: #28a745;")
            QTimer.singleShot(1000, self.accept)
        else:
            self.status_label.setText("Login failed: Password too short")
            self.status_label.setStyleSheet("color: #dc3545;")

    def get_credentials(self) -> Tuple[str, str]:
        """
        Get entered credentials.

        Returns:
            Tuple of (email, password)
        """
        return self.email, self.password

    def should_remember_credentials(self) -> bool:
        """
        Check if credentials should be remembered.

        Returns:
            True if credentials should be stored
        """
        return self.remember_credentials

    def set_credentials(self, email: str, password: str = ""):
        """
        Pre-fill credentials (for example, from stored credentials).

        Args:
            email: Email to pre-fill
            password: Password to pre-fill (usually empty for security)
        """
        self.email_edit.setText(email)
        if password:
            self.password_edit.setText(password)
        self.validate_inputs()

    def show_error(self, message: str):
        """
        Show error message with improved formatting.

        Args:
            message: Error message to display
        """
        self.hide_login_progress()
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")

        # Show detailed error dialog
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Login Failed")
        msg_box.setText("Authentication Error")
        msg_box.setInformativeText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        # Focus password field for retry
        self.password_edit.clear()
        self.password_edit.setFocus()

    def show_validation_error(self, message: str):
        """Show validation error without dialog popup."""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")


# Standalone testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = LoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        email, password = dialog.get_credentials()
        print(f"Login successful: {email}")
    else:
        print("Login cancelled")

    sys.exit(0)
