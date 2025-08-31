"""
MFA (Multi-Factor Authentication) Dialog for Garmin Connect.

Simple dialog for entering MFA codes when Garmin Connect requires 2FA.
"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout


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
                padding: 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 18px;
                font-family: monospace;
                text-align: center;
                font-weight: bold;
                letter-spacing: 2px;
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
                padding: 12px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
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

    def validate_input(self):
        """Validate MFA code input with enhanced feedback."""
        code = self.mfa_edit.text().strip()

        # Clear previous status messages
        if self.status_label.text() and not self.status_label.text().startswith("Error:"):
            self.status_label.setText("")
            self.status_label.setStyleSheet("")

        # Validate code format
        is_valid = len(code) == 6 and code.isdigit()
        self.submit_button.setEnabled(is_valid)

        # Provide real-time feedback
        if code:
            if len(code) < 6:
                if not code.isdigit():
                    self.status_label.setText(f"Code must contain only digits ({len(code)}/6)")
                    self.status_label.setStyleSheet("color: #dc3545;")
                else:
                    self.status_label.setText(f"Enter {6 - len(code)} more digits")
                    self.status_label.setStyleSheet("color: #6c757d;")
            elif len(code) == 6 and not code.isdigit():
                self.status_label.setText("Code must contain only digits")
                self.status_label.setStyleSheet("color: #dc3545;")
            elif is_valid:
                self.status_label.setText("Ready to submit")
                self.status_label.setStyleSheet("color: #28a745;")

    def submit_code(self):
        """Submit the MFA code with enhanced validation."""
        if not self.submit_button.isEnabled():
            return

        code = self.mfa_edit.text().strip()

        # Comprehensive validation
        if not code:
            self.show_validation_error("Please enter your MFA code.")
            return

        if len(code) != 6:
            self.show_validation_error(f"Code must be exactly 6 digits (entered {len(code)}).")
            return

        if not code.isdigit():
            self.show_validation_error("Code must contain only numbers (0-9).")
            return

        # Additional format checks
        if code == "000000" or code == "123456" or len(set(code)) == 1:
            self.show_validation_error("Please enter a valid authentication code.")
            return

        self.mfa_code = code
        self.accept()

    def get_mfa_code(self) -> str:
        """Get the entered MFA code."""
        return self.mfa_code

    def show_error(self, message: str):
        """Show error message with improved styling."""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")

        # Show message box with better formatting
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Authentication Error")
        msg_box.setText("MFA verification failed")
        msg_box.setInformativeText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        # Clear the input and focus for retry
        self.mfa_edit.clear()
        self.mfa_edit.setFocus()

    def show_validation_error(self, message: str):
        """Show validation error without dialog popup."""
        self.status_label.setText(f"Error: {message}")
        self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        self.mfa_edit.selectAll()
        self.mfa_edit.setFocus()


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
