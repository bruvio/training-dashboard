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
                padding: 5px;
                border: 1px solid gray;
                border-radius: 3px;
            }
            
            QPushButton {
                padding: 5px 15px;
                border: 1px solid gray;
                border-radius: 3px;
            }
            
            QPushButton:default {
                background-color: lightblue;
            }
            
            QPushButton:pressed {
                background-color: lightgray;
            }
        """
        )

    def validate_inputs(self):
        """Validate input fields and enable/disable login button."""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()

        # Basic email validation
        has_email = "@" in email and "." in email and len(email) > 5
        has_password = len(password) > 0

        self.login_button.setEnabled(has_email and has_password)

        # Clear status when user types
        if self.status_label.text():
            self.status_label.setText("")

    def attempt_login(self):
        """Attempt login with provided credentials."""
        if not self.login_button.isEnabled():
            return

        # Get credentials
        self.email = self.email_edit.text().strip()
        self.password = self.password_edit.text()
        self.remember_credentials = self.remember_checkbox.isChecked()

        # Basic validation
        if not self.email or not self.password:
            QMessageBox.warning(self, "Invalid Input", "Please enter both email and password.")
            return

        # Email format validation
        if "@" not in self.email or "." not in self.email:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            self.email_edit.setFocus()
            return

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
        """Show error message."""
        self.status_label.setText(f"Error: {message}")
        QMessageBox.critical(self, "Login Error", message)


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
