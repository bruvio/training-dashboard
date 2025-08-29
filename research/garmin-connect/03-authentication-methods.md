# Garmin Connect Authentication Methods

## Overview

Garmin Connect supports multiple authentication approaches depending on whether you use official APIs or unofficial libraries. Each method has different complexity, security, and maintenance requirements.

## Official API Authentication

### OAuth 1.0a (Official Method)

#### Overview
- **Protocol**: OAuth 1.0a (NOT OAuth 2.0)
- **Garmin's Position**: No plans to implement OAuth 2.0
- **Use Case**: Official Garmin Connect Developer Program APIs
- **Security**: High - industry standard OAuth implementation

#### Three-Step Process

##### 1. Acquire Unauthorized Request Token
```http
POST https://connectapi.garmin.com/oauth-service/oauth/request_token
Authorization: OAuth realm="",
    oauth_consumer_key="YOUR_CONSUMER_KEY",
    oauth_signature_method="HMAC-SHA1",
    oauth_timestamp="1234567890",
    oauth_nonce="RANDOM_STRING",
    oauth_version="1.0",
    oauth_signature="CALCULATED_SIGNATURE"
```

##### 2. User Authorization
- Redirect user to Garmin Connect authorization URL
- User grants permission for your application
- Garmin provides authorized request token

##### 3. Exchange for Access Token
```http
POST https://connectapi.garmin.com/oauth-service/oauth/access_token
Authorization: OAuth realm="",
    oauth_consumer_key="YOUR_CONSUMER_KEY",
    oauth_token="REQUEST_TOKEN",
    oauth_verifier="AUTHORIZATION_CODE",
    oauth_signature_method="HMAC-SHA1",
    oauth_timestamp="1234567890",
    oauth_nonce="RANDOM_STRING",
    oauth_version="1.0",
    oauth_signature="CALCULATED_SIGNATURE"
```

#### Implementation Considerations
- **Signature Calculation**: HMAC-SHA1 signature generation required
- **Nonce Generation**: Unique random string for each request
- **Timestamp**: Unix timestamp for request timing
- **Consumer Key/Secret**: Provided by Garmin after developer approval

#### Python Implementation Example
```python
import requests
from requests_oauthlib import OAuth1

# OAuth 1.0a setup
auth = OAuth1(
    client_key='YOUR_CONSUMER_KEY',
    client_secret='YOUR_CONSUMER_SECRET',
    resource_owner_key='USER_ACCESS_TOKEN',
    resource_owner_secret='USER_ACCESS_TOKEN_SECRET',
    signature_type='AUTH_HEADER'
)

# Make authenticated request
response = requests.get(
    'https://apis.garmin.com/wellness-api/rest/activities',
    auth=auth
)
```

## Unofficial Authentication Methods

### Garth-Based Authentication

#### Overview
- **Library**: Garth by matin
- **Method**: Reverse-engineered Garmin Connect app authentication
- **Token Types**: OAuth1 and OAuth2 tokens
- **Validity**: Approximately 1 year
- **MFA Support**: Yes

#### Authentication Flow

##### Initial Login
```python
import garth
from getpass import getpass

# Interactive login
email = input("Enter email address: ")
password = getpass("Enter password: ")
garth.login(email, password)

# Save session for future use
garth.save("~/.garth")
```

##### MFA Handling
```python
# If MFA is enabled, garth will prompt for MFA code
# The library handles TOTP, SMS, and app-based MFA
try:
    garth.login(email, password)
except garth.exc.MFARequiredError:
    # Library will automatically prompt for MFA code
    pass
```

##### Session Restoration
```python
# Resume existing session
garth.resume("~/.garth")

# Check if session is valid
if garth.client.username:
    print(f"Logged in as: {garth.client.username}")
else:
    print("Session expired, need to re-login")
```

#### Token Management
```python
# Manual OAuth consumer configuration (optional)
import garth.sso
garth.sso.OAUTH_CONSUMER = {
    'key': 'your_custom_consumer_key',
    'secret': 'your_custom_consumer_secret'
}

# Then login normally
garth.login(email, password)
```

### python-garminconnect Authentication

#### Overview
- **Built on**: Garth library
- **Abstraction Level**: High-level wrapper
- **Token Storage**: `~/.garminconnect` directory
- **Auto-refresh**: Yes

#### Basic Usage
```python
from garminconnect import GarminConnect

# Initialize client
api = GarminConnect()

# Login (handles MFA automatically if needed)
api.login("your_email@example.com", "your_password")

# The library automatically manages tokens after login
```

#### Advanced Configuration
```python
# Custom token directory
api = GarminConnect()
api.login(email, password, tokenstore_base64="custom_token_data")

# Manual OAuth consumer setting (via Garth)
import garth.sso
garth.sso.OAUTH_CONSUMER = {
    'key': 'custom_consumer_key',
    'secret': 'custom_consumer_secret'
}
api.login(email, password)
```

#### Error Handling
```python
from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

try:
    api.login(email, password)
except GarminConnectAuthenticationError as e:
    print(f"Authentication failed: {e}")
except GarminConnectTooManyRequestsError as e:
    print(f"Rate limited: {e}")
except GarminConnectConnectionError as e:
    print(f"Connection error: {e}")
```

## Session-Based Authentication (Legacy)

### CloudScraper Method (Deprecated)
- **Status**: No longer recommended
- **Issues**: Fragile, blocked by Cloudflare
- **Replacement**: Garth-based authentication

### Direct Web Scraping (Not Recommended)
- **Risk**: High - violates terms of service
- **Maintenance**: Breaks frequently with UI changes
- **Detection**: Easily detected and blocked

## Multi-Factor Authentication (MFA)

### Supported MFA Types
1. **TOTP (Time-based One-Time Password)**
   - Apps like Google Authenticator, Authy
   - 6-digit codes that refresh every 30 seconds

2. **SMS-based**
   - Text message with verification code
   - Carrier-dependent reliability

3. **Push Notifications**
   - Garmin Connect app-based approval
   - Requires mobile device with app installed

### MFA Implementation
```python
# Garth handles MFA automatically
try:
    garth.login(email, password)
except garth.exc.MFARequiredError:
    # Library will prompt for appropriate MFA method
    mfa_code = input("Enter MFA code: ")
    garth.login(email, password, mfa_code=mfa_code)
```

## Token Storage and Security

### Storage Locations
```bash
# Garth tokens
~/.garth/

# python-garminconnect tokens  
~/.garminconnect/

# Custom token storage
export GARTH_HOME="/custom/path"
```

### Token File Structure
```json
{
  "oauth1_token": "...",
  "oauth2_token": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1234567890
  },
  "domain": "garmin.com",
  "username": "user@example.com"
}
```

### Security Best Practices

#### Token Protection
- Set appropriate file permissions (600)
- Consider encrypted storage for production
- Rotate tokens regularly
- Monitor for unauthorized access

#### Environment Variables
```bash
# Avoid hardcoding credentials
export GARMIN_EMAIL="your_email@example.com"
export GARMIN_PASSWORD="your_password"
```

```python
import os
from garminconnect import GarminConnect

email = os.getenv('GARMIN_EMAIL')
password = os.getenv('GARMIN_PASSWORD')

if email and password:
    api = GarminConnect()
    api.login(email, password)
```

## Rate Limiting and Authentication

### Login Rate Limits
- **Issue**: Frequent login attempts can trigger temporary blocks
- **Duration**: Typically 1 hour
- **Mitigation**: Use persistent tokens, avoid frequent re-authentication

### Best Practices
```python
# Check token validity before re-authenticating
def ensure_authenticated(api):
    try:
        # Try a simple API call to test authentication
        api.get_user_summary()
        return True
    except GarminConnectAuthenticationError:
        # Re-authenticate only if needed
        api.login(email, password)
        return True
    except Exception as e:
        print(f"Authentication check failed: {e}")
        return False
```

## Error Handling Strategies

### Common Authentication Errors
```python
def robust_login(email, password, max_retries=3):
    for attempt in range(max_retries):
        try:
            api = GarminConnect()
            api.login(email, password)
            return api
        except GarminConnectTooManyRequestsError:
            # Rate limited - wait and retry
            sleep_time = 2 ** attempt  # Exponential backoff
            time.sleep(sleep_time)
        except GarminConnectAuthenticationError as e:
            if "MFA" in str(e):
                # Handle MFA requirement
                mfa_code = input("Enter MFA code: ")
                api.login(email, password, mfa_code=mfa_code)
                return api
            else:
                raise  # Invalid credentials
    raise Exception("Max retries exceeded")
```

### Monitoring Authentication Health
```python
def monitor_auth_status(api):
    try:
        user_info = api.get_user_summary()
        last_activity = api.get_activities(0, 1)
        return {
            "authenticated": True,
            "user": user_info.get("displayName"),
            "last_sync": last_activity[0].get("startTimeLocal") if last_activity else None
        }
    except Exception as e:
        return {
            "authenticated": False,
            "error": str(e)
        }
```

## Regional Considerations

### Garmin China
```python
# For garmin.cn users
import garth
garth.configure(domain="garmin.cn")
garth.login(email, password)
```

### Different Domains
- **Global**: garmin.com
- **China**: garmin.cn
- **Configuration**: Some libraries support domain switching