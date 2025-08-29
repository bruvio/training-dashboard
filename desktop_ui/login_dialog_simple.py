"""
Simple Login Dialog for Garmin Connect Authentication.

Simplified version optimized for macOS compatibility.
"""

import sys
from typing import Tuple

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SimpleLoginDialog(QDialog):
    """Simplified login dialog for Garmin Connect authentication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.email = ""
        self.password = ""
        self.remember_credentials = False

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Login to Garmin Connect")
        self.setModal(True)
        self.setFixedSize(400, 250)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        title_label = QLabel("Garmin Connect Login")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Enter your Garmin Connect credentials")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Login form
        form_layout = QFormLayout()

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

        layout.addLayout(form_layout)

        # Status label
        self.status_label = QLabel("")
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

        # Connect enter key
        self.password_edit.returnPressed.connect(self.attempt_login)

        # Focus email field
        self.email_edit.setFocus()

        # Simple styling
        self.setStyleSheet(
            """
            QLineEdit {
                padding: 10px;
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
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #5a6268;
            }
            
            QPushButton:pressed {
                background-color: #495057;
            }
            
            QPushButton:default {
                background-color: #0078d4;
            }
            
            QPushButton:default:hover {
                background-color: #106ebe;
            }
            
            QPushButton:default:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
            }
        """
        )

    def validate_inputs(self):
        """Validate input fields with enhanced feedback."""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        # Clear previous error messages when user types
        if self.status_label.text() and not self.status_label.text().startswith("Error:"):
            self.status_label.setText("")
            self.status_label.setStyleSheet("")

        # Enhanced email validation
        has_valid_email = self._is_valid_email(email)
        has_password = len(password) >= 6  # Minimum password length

        self.login_button.setEnabled(has_valid_email and has_password)

        # Provide real-time feedback
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

        # Clear any previous error messages
        self.status_label.setText("")
        self.status_label.setStyleSheet("")

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

        # Visual feedback for login attempt
        self.status_label.setText("Attempting login...")
        self.status_label.setStyleSheet("color: #0078d4;")

        # Accept the dialog (parent will handle authentication)
        self.accept()

    def get_credentials(self) -> Tuple[str, str]:
        """Get entered credentials."""
        return self.email, self.password

    def should_remember_credentials(self) -> bool:
        """Check if credentials should be remembered."""
        return self.remember_credentials

    def set_credentials(self, email: str, password: str = ""):
        """Pre-fill credentials."""
        self.email_edit.setText(email)
        if password:
            self.password_edit.setText(password)
        self.validate_inputs()

    def show_error(self, message: str):
        """Show error message with improved formatting."""
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


# For testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = SimpleLoginDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        email, password = dialog.get_credentials()
        print(f"Login successful: {email}")
    else:
        print("Login cancelled")

    sys.exit(0)
