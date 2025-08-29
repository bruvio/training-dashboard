# PyQt6 Installation and Setup Requirements

## Overview
PyQt6 is a comprehensive set of Python bindings for Qt6, enabling the development of cross-platform desktop applications. This guide covers installation requirements and setup procedures for 2024-2025.

## Python Requirements

### Minimum Version
- **Required**: Python 3.9 or later (recommended for 2024-2025)
- **Legacy Support**: Some sources mention Python 3.6.1+ but Python 3.9+ is recommended for best compatibility

## Installation Methods

### Standard Installation via pip
The most straightforward approach is using pip:

```bash
pip install PyQt6
```

This command automatically installs PyQt6 along with the necessary Qt libraries bundled in the PyQt6-Qt6 package.

### Virtual Environment Setup (Recommended)
Best practice is to use a Python virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install PyQt6
pip install PyQt6
```

### Platform-Specific Considerations

#### Windows
- Binary wheels are available for Windows 64-bit
- Qt libraries are included automatically
- No additional system dependencies required

#### macOS
- Binary wheels available
- Compatible with Intel and Apple Silicon Macs
- Qt libraries bundled automatically

#### Linux (Ubuntu/Debian)
For Ubuntu, you may need to install Python development tools first:

```bash
sudo apt install python3-venv python3-pip
```

Alternative package manager installation:
```bash
sudo apt install python3-pyqt6
```

## Current Version Information
- **Latest Version**: PyQt6 6.9.1 (as of June 2025)
- **Regular Updates**: Maintained with frequent releases throughout 2024-2025
- **Long-term Support**: Stable API with backward compatibility

## Additional Dependencies

### Core Package Structure
The PyQt6 installation includes:
- **PyQt6**: Main GUI framework
- **PyQt6-Qt6**: Subset of Qt installation required by PyQt6
- **PyQt6-sip**: SIP binding generator (installed automatically)

### Optional Development Tools
For advanced development, consider installing:

```bash
# Qt Designer and development tools (optional)
pip install pyqt6-tools

# For custom widgets and advanced features
pip install pyqt6-plugins
```

Note: Qt Designer and Qt Creator must be downloaded separately from the Qt website if needed for GUI design.

## System Dependencies

### Source Installation Requirements
If installing from source (not recommended for most users):
- Qt6 development libraries
- CMake
- C++ compiler
- Qt's qmake tool must be on PATH

### Runtime Dependencies
For binary wheel installations, all necessary Qt libraries are bundled automatically. No additional system Qt installation is required.

## Licensing Considerations

### License Options
- **GPL v3**: Free for open-source projects
- **Commercial License**: Required for proprietary applications
- **Compatibility**: Your PyQt6 license must be compatible with your Qt license

### Important Notes
- GPL license requires your code to also use a GPL-compatible license
- Commercial applications require a commercial license
- Choose license type before beginning development

## Verification of Installation

Test your PyQt6 installation with this simple script:

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton

def test_installation():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PyQt6 Test")
    window.setGeometry(100, 100, 300, 200)
    
    button = QPushButton("Hello PyQt6!")
    window.setCentralWidget(button)
    
    print("PyQt6 installation successful!")
    window.show()
    
    # Show window briefly then exit
    app.exec()

if __name__ == "__main__":
    test_installation()
```

## Troubleshooting Common Issues

### Import Errors
If you encounter import errors:
1. Ensure virtual environment is activated
2. Verify Python version compatibility
3. Reinstall PyQt6: `pip uninstall PyQt6 && pip install PyQt6`

### Platform-Specific Issues
- **macOS**: May need Xcode command line tools: `xcode-select --install`
- **Linux**: Ensure display server is available for GUI applications
- **Windows**: Ensure Microsoft Visual C++ Redistributable is installed

## Best Practices

### Development Environment
1. Always use virtual environments for project isolation
2. Pin PyQt6 version in requirements.txt for reproducible builds
3. Test installation early in development cycle
4. Use package managers appropriate for your platform

### Production Deployment
1. Document exact Python and PyQt6 versions used
2. Test on target deployment platforms
3. Consider packaging tools like PyInstaller for distribution
4. Ensure license compliance for your use case

## Next Steps
After successful installation, proceed to:
1. Main window and dialog creation patterns
2. Basic widget usage and layout management
3. Signal/slot connections for event handling
4. UI styling and theming options

## Resources
- [Official PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt for Python Documentation](https://doc.qt.io/qtforpython-6/)
- [PyQt6 Tutorial Series](https://www.pythonguis.com/pyqt6-tutorial/)
- [PyQt6 on PyPI](https://pypi.org/project/PyQt6/)