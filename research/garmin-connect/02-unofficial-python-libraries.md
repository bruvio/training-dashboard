# Unofficial Garmin Connect Python Libraries

## Overview

Several unofficial Python libraries provide access to Garmin Connect data without requiring official API approval. These libraries typically use web scraping or reverse-engineered authentication methods.

## Primary Libraries

### 1. python-garminconnect by cyberjunky

#### Overview
- **Repository**: `https://github.com/cyberjunky/python-garminconnect`
- **PyPI Package**: `garminconnect`
- **Latest Version**: Actively maintained
- **Author**: cyberjunky (Ron Klinkien)

#### Installation
```bash
pip3 install garminconnect
```

#### Key Features
- Comprehensive API wrapper for Garmin Connect
- Uses Garth authentication library
- OAuth tokens valid for approximately one year
- Access to device, activity, and health data

#### Authentication Method
- Uses same authentication as official Garmin Connect app
- Leverages Garth library for OAuth token management
- Credentials stored in `~/.garminconnect` directory
- Automatic token refresh handling

#### Available Data Methods
```python
# User and device information
get_full_name()
get_unit_system()
get_user_summary()
get_device_information()

# Activity data
get_activities(start, limit)
download_activity(activity_id, dl_fmt)  # Supports GPX, TCX, CSV
get_activity_splits(activity_id)
get_activity_details(activity_id)

# Health metrics
get_body_composition(date)
get_heart_rates(date)
get_steps_data(date)
get_sleep_data(date)
get_stress_data(date)
get_training_readiness(date)
get_max_metrics(date)

# Body metrics
get_body_battery(date)
get_floors_data(date)
get_blood_pressure(date)

# Goals and challenges
get_goals()
get_badges()
get_challenges()
get_workouts()
```

#### Example Usage
```python
from garminconnect import GarminConnect

# Initialize and login
api = GarminConnect()
api.login(email, password)

# Get user data
summary = api.get_user_summary()
activities = api.get_activities(0, 10)  # Get 10 most recent activities

# Download activity file
activity_data = api.download_activity(activity_id, GarminConnect.ActivityDownloadFormat.GPX)
```

### 2. garminconnect-ha (Home Assistant Version)

#### Overview
- **Repository**: `https://github.com/cyberjunky/python-garminconnect-ha`
- **PyPI Package**: `garminconnect-ha`
- **Purpose**: Minimal version designed for Home Assistant integration
- **Author**: cyberjunky

#### Key Differences
- Stripped down to essential methods needed for Home Assistant
- Async implementation without web scraping
- Focuses on real-time sensor data
- Optimized for Home Assistant's requirements

#### Available Sensors
- Total steps and daily step goals
- Calories burned
- Distance traveled
- Heart rate metrics
- Sleep data (duration, quality scores)
- Stress levels
- Body Battery energy monitoring

#### Rate Limiting Considerations
- Home Assistant documentation notes Garmin Connect has very low rate limits
- Maximum recommended polling frequency: once every ~5 minutes
- Library designed to work within these constraints

### 3. python-garminconnect-aio (Asynchronous Version)

#### Overview
- **Repository**: `https://github.com/cyberjunky/python-garminconnect-aio`
- **Purpose**: Asynchronous version of the main library
- **Use Case**: Applications requiring async/await patterns

#### Key Features
- Full async/await support
- Non-blocking I/O operations
- Compatible with asyncio-based applications
- Same API methods as synchronous version

### 4. Garth Authentication Library

#### Overview
- **Repository**: `https://github.com/matin/garth`
- **PyPI Package**: `garth`
- **Author**: matin
- **Purpose**: Garmin SSO authentication and Connect API client

#### Key Features
```python
# OAuth1 and OAuth2 token authentication
# Multi-factor authentication (MFA) support
# Auto-refresh of OAuth2 tokens
# Works on Google Colab
# Uses Pydantic dataclasses for validation
```

#### Installation and Usage
```bash
pip install garth

# Generate token via CLI
uvx garth login
# For China domain
uvx garth --domain garmin.cn login
```

#### API Capabilities
- Retrieve daily wellness data (sleep, stress, body battery)
- Upload fitness files
- Direct Connect API endpoint access
- JSON responses instead of HTML parsing

#### Session Management
```python
import garth

# Login and save session
garth.login(email, password)
garth.save("~/.garth")

# Resume existing session
garth.resume("~/.garth")
if garth.client.username:
    print("Session is valid")
```

## Comparison Matrix

| Library | Async Support | MFA Support | Token Persistence | Active Development |
|---------|---------------|-------------|-------------------|-------------------|
| python-garminconnect | No | Yes | Yes (1 year) | Very Active |
| garminconnect-ha | Yes | Yes | Yes | Active |
| python-garminconnect-aio | Yes | Yes | Yes | Active |
| garth | Partial | Yes | Yes | Active |

## Authentication Flow (Common Pattern)

### Initial Setup
1. Install library: `pip install garminconnect`
2. Create authentication script
3. Handle MFA if enabled on account
4. Store OAuth tokens for reuse

### Token Management
- Tokens typically valid for ~1 year
- Automatic refresh handled by libraries
- Stored in user home directory
- Can be manually configured with custom OAuth consumer keys

### Error Handling
```python
from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

try:
    api.login(email, password)
except GarminConnectAuthenticationError:
    # Handle invalid credentials
except GarminConnectTooManyRequestsError:
    # Handle rate limiting
except GarminConnectConnectionError:
    # Handle network issues
```

## Advantages of Unofficial Libraries

### Pros
- No approval process required
- Immediate access to data
- Regular updates and community support
- Access to same data as official app
- Free to use for personal projects

### Cons
- Not officially supported by Garmin
- Potential for breaking changes
- Rate limiting restrictions
- Terms of service considerations
- May violate Garmin's usage policies

## Security Considerations

### Credential Storage
- Libraries store OAuth tokens, not passwords
- Tokens stored in user home directory by default
- Consider encrypted storage for production use
- Regular token rotation recommended

### Network Security
- All communication over HTTPS
- OAuth token-based authentication
- No raw password transmission after initial login

### Compliance
- Review Garmin's Terms of Service
- Consider data usage implications
- Implement appropriate rate limiting
- Respect user privacy and data handling requirements

## Development Best Practices

### Rate Limiting
- Implement backoff strategies for HTTP 429 errors
- Cache data locally when possible
- Use efficient polling intervals
- Monitor for rate limit warnings

### Error Handling
- Robust exception handling for all API calls
- Retry logic with exponential backoff
- Graceful degradation when services unavailable
- Logging for debugging authentication issues

### Data Management
- Store activity files locally to avoid re-downloading
- Implement incremental sync strategies
- Use appropriate data structures for time series data
- Consider database storage for large datasets