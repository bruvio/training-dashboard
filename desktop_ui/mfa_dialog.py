"""
MFA (Multi-Factor Authentication) Dialog for Garmin Connect.

Simple dialog for entering MFA codes when Garmin Connect requires 2FA.
"""

import sys
from typing import Optional

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MFADialog(QDialog):
    """Dialog for entering MFA code for Garmin Connect authentication."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mfa_code = ""

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Two-Factor Authentication")
        self.setModal(True)
        self.setFixedSize(400, 200)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Header
        title_label = QLabel("Two-Factor Authentication Required")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        info_label = QLabel("Enter the 6-digit code from your authenticator app")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # MFA code input
        form_layout = QFormLayout()

        self.mfa_edit = QLineEdit()
        self.mfa_edit.setPlaceholderText("123456")
        self.mfa_edit.setMaxLength(6)
        self.mfa_edit.textChanged.connect(self.validate_input)
        form_layout.addRow("MFA Code:", self.mfa_edit)

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

        self.submit_button = QPushButton("Submit")
        self.submit_button.setDefault(True)
        self.submit_button.setEnabled(False)
        self.submit_button.clicked.connect(self.submit_code)
        button_layout.addWidget(self.submit_button)

        layout.addLayout(button_layout)

        # Connect enter key
        self.mfa_edit.returnPressed.connect(self.submit_code)

        # Focus MFA field
        self.mfa_edit.setFocus()

        # Simple styling
        self.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                border: 1px solid gray;
                border-radius: 3px;
                font-size: 16px;
                font-family: monospace;
                text-align: center;
            }
            
            QPushButton {
                padding: 8px 15px;
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

    def validate_input(self):
        """Validate MFA code input."""
        code = self.mfa_edit.text().strip()

        # Enable submit button only for 6-digit codes
        is_valid = len(code) == 6 and code.isdigit()
        self.submit_button.setEnabled(is_valid)

        # Clear status when user types
        if self.status_label.text():
            self.status_label.setText("")

    def submit_code(self):
        """Submit the MFA code."""
        if not self.submit_button.isEnabled():
            return

        code = self.mfa_edit.text().strip()

        # Basic validation
        if len(code) != 6 or not code.isdigit():
            QMessageBox.warning(self, "Invalid Code", "Please enter a 6-digit numeric code.")
            self.mfa_edit.setFocus()
            return

        self.mfa_code = code
        self.accept()

    def get_mfa_code(self) -> str:
        """Get the entered MFA code."""
        return self.mfa_code

    def show_error(self, message: str):
        """Show error message."""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: red;")
        QMessageBox.critical(self, "MFA Error", message)


# For testing
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = MFADialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        code = dialog.get_mfa_code()
        print(f"MFA code entered: {code}")
    else:
        print("MFA cancelled")

    sys.exit(0)
