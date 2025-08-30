# Garmin Dashboard

A comprehensive fitness activity dashboard for Garmin Connect users, featuring web-based visualization with direct Garmin Connect integration and optional desktop application for advanced functionality.

## Features

### 🌐 Web Dashboard
- **Professional Landing Page**: Enhanced interface with quick action cards and navigation
- **Direct Garmin Connect Integration**: Login directly through web interface with MFA support
- **Activity Synchronization**: Download activities directly from Garmin Connect to database
- **Interactive Visualizations**: Real-time charts for heart rate, speed, elevation, and power data
- **GPS Route Mapping**: Interactive maps with start/end markers and route visualization
- **Activity Analytics**: Comprehensive metrics including pace, distance, duration, and performance
- **Multi-page Navigation**: Professional Bootstrap UI with responsive design
- **Activity Detail Views**: Detailed analysis with charts, maps, and comprehensive metrics

### 🖥️ Desktop Application
- **Secure Login**: Encrypted credential storage for Garmin Connect
- **Activity Downloads**: Bulk download activities in FIT or GPX format
- **Calendar Selection**: Interactive date range picker for activity selection
- **Background Processing**: Non-blocking downloads with progress tracking
- **Configuration Management**: Customizable settings for downloads and directories

### 🔧 Technical Features
- Docker deployment with health checks
- SQLite database with SQLAlchemy ORM
- Support for FIT, GPX, and TCX file formats
- Secure credential encryption using Fernet
- Rate-limited API calls to respect Garmin Connect limits
- Comprehensive error handling and logging

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.9+** (for local development)
- **Garmin Connect account** (for activity downloads)

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd fit-dashboard
mkdir -p data activities
```

### 2. Start with Docker (Recommended)
```bash
# Set the dashboard port and start services
export DASHBOARD_PORT=8050
docker-compose up -d --build

# View the dashboard
open http://localhost:8050
```

The web dashboard provides:
- **Main Dashboard**: Activity overview and statistics at `/`
- **Activity Details**: Individual activity analysis at `/activity/{id}`
- **Garmin Connect**: Login and sync interface at `/garmin`

### 3. Use Desktop Application
```bash
# Install dependencies
pip install -r requirements.txt

# Launch desktop app (simplified version for better macOS compatibility)
python run_desktop_app.py

# Or with virtual environment:
source venv/bin/activate
python -m desktop_ui.main_window_simple
```

## Docker Deployment

### Standard Deployment
```bash
# Create required directories
mkdir -p data activities

# Start services with proper port configuration
export DASHBOARD_PORT=8050
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f garmin-dashboard-web
```

#### Web Dashboard Usage
1. **Access Dashboard**: Navigate to `http://localhost:8050`
2. **Connect to Garmin**: Click "Connect Now" or visit `/garmin`
3. **Login to Garmin Connect**: Enter your credentials (supports MFA)
4. **Sync Activities**: Choose date range and sync your activities
5. **View Activities**: Browse activities from the main dashboard
6. **Analyze Details**: Click "View Details" for comprehensive activity analysis

### Development Mode
```bash
# Start with hot reload
docker-compose --profile dev up

# Dashboard available at http://localhost:8050
```

### Import Activities
```bash
# Place FIT/GPX files in ./activities directory
cp your-activities/*.fit ./activities/

# Run importer
docker-compose --profile tools run garmin-importer
```

## Desktop Application Usage

### First Time Setup
1. Launch the desktop application:
   ```bash
   python -m desktop_ui.main_window
   ```
2. Click "Login" to configure Garmin Connect credentials
3. Enter your Garmin Connect email and password
4. Credentials are encrypted and stored locally

### Downloading Activities
1. **Select Date Range**: Use the calendar to choose start and end dates
2. **Choose Format**: Select FIT (recommended) or GPX format
3. **Start Download**: Click "Download Activities" to begin
4. **Monitor Progress**: Watch the progress bar and status updates
5. **View Results**: Downloaded files are saved to your configured directory

### Settings Configuration
Access **Settings** to configure:
- **Download Directory**: Where activities are saved
- **Activity Directory**: Directory for dashboard import
- **Download Format**: Default format (FIT/GPX)
- **Rate Limiting**: Delay between downloads
- **Concurrent Downloads**: Maximum simultaneous downloads

## Local Development

### Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python -c "from app.data.db import create_tables; create_tables()"
```

### Run Web Dashboard
```bash
# Start development server
python -m app.dash_app

# Dashboard available at http://localhost:8050
```

### Run Desktop Application
```bash
# Launch desktop UI (simplified version)
python run_desktop_app.py

# Or directly with module:
python -m desktop_ui.main_window_simple
```

### Import Activities Manually
```bash
# Import from directory
python -m cli.gd_import ./activities --verbose

# Import single file
python -m cli.gd_import ./activities/activity.fit
```

## Configuration

### Environment Variables
```bash
# Web Dashboard
DASHBOARD_PORT=8050          # Port for web dashboard
DASH_DEBUG=False            # Enable debug mode
DATABASE_URL=sqlite:///data/garmin_dashboard.db

# Docker
COMPOSE_PROJECT_NAME=garmin-dashboard
```

### Desktop Application Settings
Settings are stored in `~/.garmin-dashboard/`:
- `config.json`: Application preferences
- `credentials.enc`: Encrypted Garmin Connect credentials
- `encryption.key`: Encryption key (keep secure!)

## Web Dashboard Features

### Garmin Connect Integration
The web dashboard now includes comprehensive Garmin Connect integration:

#### Authentication
- **Email/Password Login**: Secure authentication with your Garmin Connect account
- **MFA Support**: Full support for accounts with two-factor authentication enabled
- **Session Management**: Secure session handling with encrypted credentials
- **Auto-Login Detection**: Seamless re-authentication for returning users

#### Activity Synchronization
- **Date Range Selection**: Sync activities from last 7, 30, 90 days, or all activities
- **Real-time Progress**: Live progress indicators during sync operations
- **Deduplication**: Automatic prevention of duplicate activity imports
- **Error Handling**: Comprehensive error reporting and recovery

#### Activity Visualization
- **Interactive Charts**: Heart rate, speed, elevation, and power data visualization
- **GPS Route Maps**: Full route visualization with start/end markers using OpenStreetMap
- **Performance Metrics**: Comprehensive analysis including pace, distance, duration
- **Activity Comparison**: Side-by-side analysis capabilities

### Navigation Structure
- **Landing Page** (`/`): Activity overview, statistics, and quick actions
- **Activity Detail** (`/activity/{id}`): Comprehensive individual activity analysis
- **Garmin Connect** (`/garmin`): Login interface and synchronization controls
- **Statistics** (`/stats`): Performance trends and analytics (coming soon)
- **Settings** (`/settings`): Application configuration (coming soon)

## File Formats Supported

| Format | Import | Export | Web Sync | Features |
|--------|--------|--------|----------|----------|
| **FIT** | ✅ | ✅ | ✅ | Full data, recommended |
| **GPX** | ✅ | ✅ | ✅ | GPS tracks, waypoints |
| **TCX** | ✅ | ❌ | ✅ | Training data |

## Project Structure

```
fit-dashboard/
├── app/                    # Web dashboard application
│   ├── dash_app.py        # Main Dash application with routing
│   ├── pages/             # Multi-page components
│   │   ├── calendar.py    # Landing page with activity overview
│   │   ├── activity_detail.py # Individual activity analysis
│   │   └── garmin_login.py # Garmin Connect integration UI
│   └── data/              # Database models and queries
│       ├── models.py      # SQLAlchemy models (Activity, Sample, RoutePoint)
│       └── db.py          # Database connection and utilities
├── garmin_client/         # Garmin Connect integration
│   ├── client.py          # API client with MFA support
│   └── sync.py            # Activity synchronization logic
├── desktop_ui/            # PyQt6 desktop application
│   ├── main_window.py     # Main application window
│   ├── main_window_simple.py # macOS-compatible version
│   ├── login_dialog.py    # Secure login dialog
│   ├── settings_dialog.py # Configuration dialog
│   └── download_worker.py # Background download worker
├── cli/                   # Command-line tools
│   └── gd_import.py       # Activity file import utility
├── ingest/                # File parsing utilities
│   ├── fit_parser.py      # FIT file processing
│   ├── gpx_parser.py      # GPX file processing
│   └── tcx_parser.py      # TCX file processing
├── data/                  # Database and data storage
└── activities/            # Activity files directory
```

## Troubleshooting

### Web Dashboard Issues
**Garmin Connect login fails:**
- Verify your Garmin Connect credentials are correct
- Check if your account requires MFA and enter the 6-digit code when prompted
- Clear browser cache and try again
- Check Docker logs: `docker logs garmin-dashboard-web`

**Activity pages show "Error loading activity":**
- Ensure activities are imported into the database
- Verify database connection is working
- Check that activity IDs are valid integers
- Import activities using: `python -m cli.gd_import ./activities`

**Page routing issues (404 errors):**
- Ensure Docker container is running: `docker-compose ps`
- Check container logs: `docker logs garmin-dashboard-web`
- Verify port 8050 is not being used by other services
- Restart with: `docker-compose down && docker-compose up -d --build`

**Charts or maps not loading:**
- Check browser console for JavaScript errors
- Ensure internet connection for map tiles (OpenStreetMap)
- Verify activity has GPS data for map visualization
- Check that sample data exists in database

### Docker Issues
**Volume mounting errors:**
```bash
# Ensure directories exist
mkdir -p data activities

# Check permissions
chmod 755 data activities
```

**Service won't start:**
```bash
# Check logs
docker-compose logs garmin-dashboard-web

# Restart services with rebuild
docker-compose down && docker-compose up -d --build
```

**Port conflicts:**
```bash
# Check if port 8050 is in use
lsof -i :8050

# Use different port
export DASHBOARD_PORT=8051
docker-compose up -d --build
```

### Desktop Application Issues
**Login fails:**
- Verify Garmin Connect credentials
- Check internet connection
- Review logs in `~/.garmin-dashboard/logs/`

**MFA (Two-Factor Authentication) accounts:**
- Both web and desktop applications support accounts with MFA enabled
- **Web Dashboard**: After entering credentials, you'll see an MFA prompt for your 6-digit code
- **Desktop App**: MFA prompt appears after initial login attempt
- Enter the code from your authenticator app (Google Authenticator, Authy, etc.)
- Supports email-based MFA and authenticator app codes

**Downloads fail:**
- Check rate limiting settings
- Verify sufficient disk space
- Ensure download directory is writable

**Application won't start:**
```bash
# Check PyQt6 installation
python -c "import PyQt6; print('PyQt6 OK')"

# Install system dependencies (Linux)
sudo apt-get install python3-pyqt6
```

**UI forms not readable/incorrectly formatted (macOS):**
```bash
# Use the simplified version designed for macOS compatibility
python run_desktop_app.py

# Or launch simplified version directly:
python -m desktop_ui.main_window_simple
```

The simplified version removes complex styling that can cause rendering issues on macOS and provides a cleaner, more compatible interface.

### Database Issues
**Reset database:**
```bash
# Stop services
docker-compose down

# Remove database
rm -f data/garmin_dashboard.db*

# Restart and reimport
docker-compose up -d
docker-compose --profile tools run garmin-importer
```

## API Rate Limits

Garmin Connect enforces rate limits:
- **Recommended**: 1-2 second delay between requests
- **Maximum**: ~100 requests per hour
- **Configuration**: Adjust in desktop app settings

## Security Notes

- Credentials are encrypted using Fernet encryption
- Encryption keys stored locally (`~/.garmin-dashboard/encryption.key`)
- Never commit credentials or keys to version control
- Desktop app uses system keystore when available

## Development

### Running Tests
```bash
# Local testing
python run_tests.py

# Docker testing
docker-compose --profile test run test-runner
```

### Code Formatting
```bash
# Format code
black .
isort .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure code formatting (black, isort)
5. Submit pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review project documentation
3. Create an issue with detailed reproduction steps

---

**Note**: This application is not affiliated with Garmin Ltd. Use responsibly and respect Garmin Connect's terms of service.