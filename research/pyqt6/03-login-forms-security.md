# PyQt6 Login Forms with Secure Password Handling

## Overview
This guide covers creating secure login forms in PyQt6 using QLineEdit password fields, input validation, and authentication best practices. Focus is on client-side security measures and proper UI design patterns.

## Password Field Implementation

### Basic Password Field Setup
Use `QLineEdit.EchoMode.Password` to mask password input:

```python
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout)
from PyQt6.QtCore import Qt

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    
    def initializeUI(self):
        self.setWindowTitle("Secure Login Form")
        self.setGeometry(200, 200, 350, 200)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Form layout for organized input fields
        form_layout = QFormLayout()
        
        # Username field
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Enter username")
        
        # Password field with security settings
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("Enter password")
        
        # Add fields to form
        form_layout.addRow(QLabel("Username:"), self.username_field)
        form_layout.addRow(QLabel("Password:"), self.password_field)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setDefault(True)  # Enter key triggers login
        
        # Assembly layout
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.login_button)
        main_layout.addStretch()  # Add space at bottom
        
        self.setLayout(main_layout)
    
    def handle_login(self):
        username = self.username_field.text().strip()
        password = self.password_field.text()
        
        if self.validate_input(username, password):
            if self.authenticate(username, password):
                self.login_successful()
            else:
                self.login_failed()
    
    def validate_input(self, username, password):
        """Client-side input validation"""
        if not username:
            QMessageBox.warning(self, "Input Error", "Username cannot be empty")
            self.username_field.setFocus()
            return False
        
        if not password:
            QMessageBox.warning(self, "Input Error", "Password cannot be empty")
            self.password_field.setFocus()
            return False
        
        if len(username) < 3:
            QMessageBox.warning(self, "Input Error", "Username must be at least 3 characters")
            self.username_field.setFocus()
            return False
        
        return True
    
    def authenticate(self, username, password):
        """Replace with actual authentication logic"""
        # This is a placeholder - implement proper authentication
        valid_credentials = {
            "admin": "securepassword123",
            "user": "userpass456"
        }
        return valid_credentials.get(username) == password
    
    def login_successful(self):
        QMessageBox.information(self, "Success", "Login successful!")
        self.clear_form()
        # Proceed to main application
    
    def login_failed(self):
        QMessageBox.warning(self, "Error", "Invalid username or password")
        self.password_field.clear()  # Clear password on failure
        self.password_field.setFocus()
    
    def clear_form(self):
        self.username_field.clear()
        self.password_field.clear()
```

### Echo Mode Options
QLineEdit provides several echo modes for different security levels:

```python
class PasswordFieldDemo(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        
        # Normal mode (default)
        normal_field = QLineEdit()
        normal_field.setEchoMode(QLineEdit.EchoMode.Normal)
        layout.addRow("Normal:", normal_field)
        
        # Password mode (most common)
        password_field = QLineEdit()
        password_field.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Password:", password_field)
        
        # No echo mode (maximum security)
        no_echo_field = QLineEdit()
        no_echo_field.setEchoMode(QLineEdit.EchoMode.NoEcho)
        layout.addRow("No Echo:", no_echo_field)
        
        # Password echo on edit
        edit_echo_field = QLineEdit()
        edit_echo_field.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        layout.addRow("Echo on Edit:", edit_echo_field)
        
        self.setLayout(layout)
```

## Advanced Security Features

### Enhanced Password Field Configuration
Additional security settings for password fields:

```python
def setup_secure_password_field(self):
    """Configure password field with enhanced security"""
    self.password_field = QLineEdit()
    
    # Basic password masking
    self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
    
    # Disable input method features for security
    self.password_field.setInputMethodHints(
        Qt.InputMethodHint.ImhHiddenText |
        Qt.InputMethodHint.ImhNoPredictiveText |
        Qt.InputMethodHint.ImhNoAutoUppercase
    )
    
    # Set maximum length
    self.password_field.setMaxLength(128)
    
    # Disable context menu to prevent copy/paste
    self.password_field.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
    
    return self.password_field
```

### Input Validation and Sanitization
Comprehensive input validation:

```python
import re

class SecureLoginValidator:
    def __init__(self):
        # Define validation patterns
        self.username_pattern = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def validate_username(self, username):
        """Validate username format and content"""
        if not username:
            return False, "Username is required"
        
        if not self.username_pattern.match(username):
            return False, "Username must be 3-20 characters, letters, numbers, and underscores only"
        
        # Check for common injection attempts
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
        if any(char in username for char in dangerous_chars):
            return False, "Username contains invalid characters"
        
        return True, ""
    
    def validate_email(self, email):
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        if not self.email_pattern.match(email):
            return False, "Invalid email format"
        
        return True, ""
    
    def validate_password_strength(self, password):
        """Check password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        checks = {
            'uppercase': re.search(r'[A-Z]', password),
            'lowercase': re.search(r'[a-z]', password),
            'digit': re.search(r'\d', password),
            'special': re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)
        }
        
        missing = [name for name, check in checks.items() if not check]
        
        if len(missing) > 1:
            return False, f"Password must contain {', '.join(missing)} characters"
        
        return True, ""

# Usage in login form
class SecureLoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.validator = SecureLoginValidator()
        self.initializeUI()
    
    def validate_input(self, username, password):
        # Validate username
        valid, message = self.validator.validate_username(username)
        if not valid:
            QMessageBox.warning(self, "Validation Error", message)
            return False
        
        # Validate password strength (optional for login, required for registration)
        # valid, message = self.validator.validate_password_strength(password)
        # if not valid:
        #     QMessageBox.warning(self, "Validation Error", message)
        #     return False
        
        return True
```

## Complete Login Dialog Implementation

### Professional Login Dialog
A complete, production-ready login dialog:

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QPushButton, QCheckBox,
                            QDialogButtonBox, QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont

class LoginDialog(QDialog):
    login_successful = pyqtSignal(str)  # Signal emitted on successful login
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = SecureLoginValidator()
        self.initializeUI()
    
    def initializeUI(self):
        self.setWindowTitle("Login Required")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        # Header section
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)
        
        # Login form section
        form_layout = self.create_login_form()
        main_layout.addLayout(form_layout)
        
        # Options section
        options_layout = self.create_options()
        main_layout.addLayout(options_layout)
        
        # Button section
        button_layout = self.create_buttons()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Set initial focus
        self.username_field.setFocus()
    
    def create_header(self):
        """Create the header section with title"""
        header_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Sign In")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(title_label)
        return header_layout
    
    def create_login_form(self):
        """Create the login form fields"""
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Username field
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Username or Email")
        self.username_field.returnPressed.connect(self.handle_login)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("Password")
        self.password_field.returnPressed.connect(self.handle_login)
        
        # Enhance password field security
        self.password_field.setInputMethodHints(
            Qt.InputMethodHint.ImhHiddenText |
            Qt.InputMethodHint.ImhNoPredictiveText |
            Qt.InputMethodHint.ImhNoAutoUppercase
        )
        
        form_layout.addRow("Username:", self.username_field)
        form_layout.addRow("Password:", self.password_field)
        
        return form_layout
    
    def create_options(self):
        """Create options section"""
        options_layout = QHBoxLayout()
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        options_layout.addWidget(self.remember_checkbox)
        
        # Spacer
        options_layout.addStretch()
        
        # Forgot password link (styled as button)
        forgot_button = QPushButton("Forgot Password?")
        forgot_button.setFlat(True)
        forgot_button.setStyleSheet("QPushButton { color: #0066cc; border: none; }")
        forgot_button.clicked.connect(self.forgot_password)
        options_layout.addWidget(forgot_button)
        
        return options_layout
    
    def create_buttons(self):
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.handle_login)
        
        # Style the login button
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.login_button)
        
        return button_layout
    
    def handle_login(self):
        """Handle login attempt"""
        username = self.username_field.text().strip()
        password = self.password_field.text()
        
        # Validate input
        if not self.validate_input(username, password):
            return
        
        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("Signing in...")
        
        # Simulate authentication (replace with actual authentication)
        try:
            if self.authenticate(username, password):
                self.login_successful.emit(username)
                self.accept()
            else:
                self.show_error("Invalid username or password")
        finally:
            # Re-enable login button
            self.login_button.setEnabled(True)
            self.login_button.setText("Sign In")
    
    def validate_input(self, username, password):
        """Validate user input"""
        if not username:
            self.show_error("Username is required")
            self.username_field.setFocus()
            return False
        
        if not password:
            self.show_error("Password is required")
            self.password_field.setFocus()
            return False
        
        # Additional validation
        valid, message = self.validator.validate_username(username)
        if not valid:
            self.show_error(message)
            self.username_field.setFocus()
            return False
        
        return True
    
    def authenticate(self, username, password):
        """Authenticate user credentials (placeholder)"""
        # Replace with actual authentication logic
        # This could involve API calls, database queries, etc.
        return username == "admin" and password == "password123"
    
    def show_error(self, message):
        """Show error message"""
        error_label = QLabel(message)
        error_label.setStyleSheet("color: red; font-size: 12px;")
        # You could also use QMessageBox for errors
        # QMessageBox.warning(self, "Login Error", message)
    
    def forgot_password(self):
        """Handle forgot password"""
        # Implement forgot password functionality
        QMessageBox.information(self, "Forgot Password", 
                              "Password reset functionality would go here.")

# Usage example
class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.show_login()
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self)
        login_dialog.login_successful.connect(self.on_login_successful)
        
        if login_dialog.exec() != QDialog.DialogCode.Accepted:
            # User cancelled login
            sys.exit()
    
    def on_login_successful(self, username):
        """Handle successful login"""
        self.current_user = username
        self.setWindowTitle(f"Application - Welcome {username}")
        self.show()
```

## Security Best Practices

### 1. Password Field Security
- Use `QLineEdit.EchoMode.Password` for standard password masking
- Use `QLineEdit.EchoMode.NoEcho` for maximum security (PIN entries)
- Disable predictive text and autocorrect
- Consider disabling context menus to prevent copy/paste

### 2. Input Validation
- Always validate on client-side AND server-side
- Sanitize inputs to prevent injection attacks
- Use regex patterns for format validation
- Implement rate limiting for login attempts

### 3. Authentication Security
- Never store passwords in plain text
- Use secure hashing algorithms (bcrypt, Argon2)
- Implement session management
- Use HTTPS for network communication
- Implement proper error handling without revealing system details

### 4. UI Security Considerations
- Clear password fields on login failure
- Provide clear but non-specific error messages
- Implement lockout mechanisms after failed attempts
- Use secure memory handling for sensitive data

### 5. Additional Security Measures
```python
# Example of secure password handling
import hashlib
import secrets

class PasswordSecurity:
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use a strong hashing algorithm
        pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
        return salt + pwd_hash.hex()
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        salt = hashed[:32]
        stored_hash = hashed[32:]
        pwd_hash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
        return pwd_hash.hex() == stored_hash
```

## Testing Login Forms

### Unit Testing
```python
import unittest
from unittest.mock import patch

class TestLoginForm(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.login_form = LoginForm()
    
    def test_empty_username_validation(self):
        self.login_form.username_field.setText("")
        self.login_form.password_field.setText("password")
        result = self.login_form.validate_input("", "password")
        self.assertFalse(result)
    
    def test_empty_password_validation(self):
        self.login_form.username_field.setText("user")
        self.login_form.password_field.setText("")
        result = self.login_form.validate_input("user", "")
        self.assertFalse(result)
    
    def tearDown(self):
        self.app.quit()
```

This comprehensive guide provides the foundation for creating secure, user-friendly login forms in PyQt6 applications with proper password handling and validation.