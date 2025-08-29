# PyQt6 Main Window and Dialog Creation Patterns

## Overview
This guide covers best practices for creating QMainWindow and QDialog components in PyQt6, including proper initialization patterns, layout management, and user interaction handling.

## QMainWindow Creation Patterns

### Best Practice: Subclassing QMainWindow
The recommended approach is to subclass QMainWindow for custom behavior and self-contained window management.

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    
    def initializeUI(self):
        """Set up the main window's GUI"""
        self.setWindowTitle("My Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout and add widgets
        layout = QVBoxLayout()
        button = QPushButton("Click me!")
        button.clicked.connect(self.on_button_clicked)
        layout.addWidget(button)
        
        central_widget.setLayout(layout)
    
    def on_button_clicked(self):
        print("Button clicked!")

# Application entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### QMainWindow Layout Structure
QMainWindow has a predefined layout that includes:
- **Central Widget**: Main content area (required)
- **Menu Bar**: Top horizontal bar for menus
- **Tool Bars**: Customizable toolbars around the window
- **Status Bar**: Bottom information bar
- **Dock Widgets**: Dockable panels on any side

```python
class CompleteMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initializeUI()
        self.create_menu_bar()
        self.create_tool_bar()
        self.create_status_bar()
    
    def initializeUI(self):
        self.setWindowTitle("Complete Main Window")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget is mandatory
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        file_menu.addAction('New', self.new_file)
        file_menu.addAction('Open', self.open_file)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
    
    def create_tool_bar(self):
        toolbar = self.addToolBar('Main')
        toolbar.addAction('New', self.new_file)
        toolbar.addAction('Open', self.open_file)
    
    def create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.showMessage('Ready')
    
    def new_file(self):
        self.status_bar.showMessage('New file created')
    
    def open_file(self):
        self.status_bar.showMessage('File opened')
```

## QDialog Creation Patterns

### Basic Custom Dialog Pattern
QDialog is used for temporary interactions and doesn't have a predefined layout like QMainWindow.

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, 
                            QDialogButtonBox)

class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initializeUI()
    
    def initializeUI(self):
        self.setWindowTitle("Custom Dialog")
        self.setModal(True)  # Make dialog modal
        self.resize(400, 300)
        
        # Create main layout (required for dialogs)
        layout = QVBoxLayout()
        
        # Add content
        label = QLabel("Enter your information:")
        self.name_edit = QLineEdit()
        self.email_edit = QLineEdit()
        
        layout.addWidget(label)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_edit)
        
        # Add button box for standard dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Set layout (crucial for dialogs)
        self.setLayout(layout)
    
    def get_data(self):
        """Return the data entered in the dialog"""
        return {
            'name': self.name_edit.text(),
            'email': self.email_edit.text()
        }

# Using the dialog
class MainWindowWithDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initializeUI()
    
    def initializeUI(self):
        self.setWindowTitle("Main Window with Dialog")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        button = QPushButton("Open Dialog")
        button.clicked.connect(self.open_dialog)
        layout.addWidget(button)
        
        self.result_label = QLabel("No data yet")
        layout.addWidget(self.result_label)
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def open_dialog(self):
        dialog = CustomDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self.result_label.setText(f"Name: {data['name']}, Email: {data['email']}")
```

### Modal vs Modeless Dialogs

#### Modal Dialogs
Block interaction with the parent window until closed:

```python
def open_modal_dialog(self):
    dialog = CustomDialog(self)
    # exec() makes the dialog modal and blocks until closed
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        print("Dialog accepted")
    else:
        print("Dialog rejected")
```

#### Modeless Dialogs
Allow interaction with the parent window:

```python
def open_modeless_dialog(self):
    self.modeless_dialog = CustomDialog(self)
    # show() makes the dialog modeless
    self.modeless_dialog.show()
    # Keep a reference to prevent garbage collection
```

### Dialog Button Box Best Practices
Use QDialogButtonBox for platform-consistent button ordering:

```python
from PyQt6.QtWidgets import QDialogButtonBox

class StandardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        # Content goes here
        content = QLabel("This is a standard dialog")
        layout.addWidget(content)
        
        # Standard button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        
        # Connect standard signals
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_changes)
        
        layout.addWidget(button_box)
        self.setLayout(layout)
    
    def apply_changes(self):
        print("Apply button clicked")
```

## Advanced Dialog Patterns

### Input Dialog Pattern
For simple data collection:

```python
from PyQt6.QtWidgets import QInputDialog

class MainWindowWithInput(QMainWindow):
    def get_user_input(self):
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter your name:')
        if ok and text:
            print(f"User entered: {text}")
        
        number, ok = QInputDialog.getInt(self, 'Number Dialog', 'Enter age:', 25, 0, 120, 1)
        if ok:
            print(f"Age: {number}")
```

### Message Dialog Pattern
For user notifications:

```python
from PyQt6.QtWidgets import QMessageBox

class MainWindowWithMessages(QMainWindow):
    def show_info_message(self):
        QMessageBox.information(self, "Information", "Operation completed successfully!")
    
    def show_warning_message(self):
        QMessageBox.warning(self, "Warning", "Please save your work before continuing.")
    
    def show_question_dialog(self):
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to quit?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
```

## Best Practices Summary

### Window Creation
1. **Always subclass** QMainWindow and QDialog for custom behavior
2. **Call super().__init__()** in the constructor
3. **Separate UI setup** into dedicated methods like `initializeUI()`
4. **Use parent-child relationships** when creating dialogs

### Layout Management
1. **QMainWindow**: Has built-in layout, central widget is required
2. **QDialog**: Must explicitly set a layout using `setLayout()`
3. **Organize content** logically with nested layouts

### Signal Connections
1. **Connect signals in __init__** after widget creation
2. **Use descriptive method names** for slot handlers
3. **Handle dialog results** properly with accept/reject patterns

### Dialog Interaction
1. **Use QDialogButtonBox** for standard buttons
2. **Choose modal vs modeless** based on user workflow
3. **Keep references** to modeless dialogs to prevent garbage collection
4. **Return data** from dialogs using custom methods

### Code Organization
1. **Keep window classes focused** on UI concerns
2. **Separate business logic** from UI code
3. **Use consistent naming** conventions
4. **Document complex interactions** with comments

## Common Patterns Summary

```python
# Main application pattern
class Application:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
    
    def run(self):
        self.main_window.show()
        return self.app.exec()

# Usage
if __name__ == '__main__':
    app = Application()
    sys.exit(app.run())
```

These patterns provide a solid foundation for creating professional PyQt6 desktop applications with proper window and dialog management.