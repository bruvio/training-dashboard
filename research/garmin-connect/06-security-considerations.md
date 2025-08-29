# Security Considerations for Garmin Connect Integration

## Overview

Integrating with Garmin Connect involves handling sensitive user credentials, personal health data, and maintaining secure communication channels. This document outlines comprehensive security considerations for both official and unofficial integration approaches.

## Credential Security

### Password and Authentication Security

#### Secure Credential Storage
```python
import os
import keyring
from cryptography.fernet import Fernet
import base64

class SecureCredentialManager:
    def __init__(self, service_name="garmin_connect"):
        self.service_name = service_name
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Generate or retrieve encryption key from secure storage"""
        key = keyring.get_password(self.service_name, "encryption_key")
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password(self.service_name, "encryption_key", key)
        return key.encode()
    
    def store_credentials(self, email, password):
        """Store credentials securely"""
        encrypted_password = self.cipher.encrypt(password.encode()).decode()
        keyring.set_password(self.service_name, email, encrypted_password)
    
    def retrieve_credentials(self, email):
        """Retrieve and decrypt credentials"""
        encrypted_password = keyring.get_password(self.service_name, email)
        if encrypted_password:
            return self.cipher.decrypt(encrypted_password.encode()).decode()
        return None
    
    def delete_credentials(self, email):
        """Securely delete stored credentials"""
        try:
            keyring.delete_password(self.service_name, email)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
```

#### Environment Variable Best Practices
```python
import os
from pathlib import Path

class EnvironmentCredentialManager:
    def __init__(self):
        self.env_file = Path.home() / '.garmin_env'
        self._ensure_secure_permissions()
    
    def _ensure_secure_permissions(self):
        """Set secure file permissions (owner read/write only)"""
        if self.env_file.exists():
            os.chmod(self.env_file, 0o600)
    
    def load_credentials(self):
        """Load credentials from environment or .env file"""
        # Priority: environment variables > .env file
        credentials = {}
        
        # Check environment variables first
        credentials['email'] = os.getenv('GARMIN_EMAIL')
        credentials['password'] = os.getenv('GARMIN_PASSWORD')
        
        # Fallback to .env file if environment variables not set
        if not credentials['email'] or not credentials['password']:
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            if key in ['GARMIN_EMAIL', 'GARMIN_PASSWORD']:
                                credentials[key.lower().replace('garmin_', '')] = value
        
        return credentials
    
    def create_env_file(self, email, password):
        """Create secure .env file with credentials"""
        env_content = f"""# Garmin Connect Credentials
# This file contains sensitive information - do not commit to version control
GARMIN_EMAIL={email}
GARMIN_PASSWORD={password}
"""
        with open(self.env_file, 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions
        os.chmod(self.env_file, 0o600)
        
        # Create .gitignore entry if in git repo
        gitignore_path = Path.cwd() / '.gitignore'
        gitignore_entry = str(self.env_file.name)
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                if gitignore_entry not in f.read():
                    with open(gitignore_path, 'a') as f:
                        f.write(f"\n# Garmin credentials\n{gitignore_entry}\n")
```

### OAuth Token Security

#### Token Storage and Rotation
```python
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from cryptography.fernet import Fernet

class SecureTokenManager:
    def __init__(self, token_dir="~/.garmin_tokens"):
        self.token_dir = Path(os.path.expanduser(token_dir))
        self.token_dir.mkdir(mode=0o700, exist_ok=True)
        self.db_path = self.token_dir / "tokens.db"
        self.key = self._get_encryption_key()
        self.cipher = Fernet(self.key)
        self._init_database()
    
    def _get_encryption_key(self):
        """Generate or load encryption key"""
        key_file = self.token_dir / "key.key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            os.chmod(key_file, 0o600)
        
        return key
    
    def _init_database(self):
        """Initialize encrypted token database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                user_id TEXT PRIMARY KEY,
                encrypted_tokens TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Set secure permissions on database
        os.chmod(self.db_path, 0o600)
    
    def store_tokens(self, user_id, tokens, expires_in_days=365):
        """Store encrypted tokens"""
        token_data = json.dumps(tokens).encode()
        encrypted_tokens = self.cipher.encrypt(token_data).decode()
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tokens 
            (user_id, encrypted_tokens, expires_at, last_used) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, encrypted_tokens, expires_at, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def retrieve_tokens(self, user_id):
        """Retrieve and decrypt tokens"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_tokens, expires_at FROM tokens 
            WHERE user_id = ? AND is_active = 1 AND expires_at > CURRENT_TIMESTAMP
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        if result:
            # Update last used timestamp
            cursor.execute('''
                UPDATE tokens SET last_used = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (user_id,))
            conn.commit()
        
        conn.close()
        
        if result:
            encrypted_tokens, expires_at = result
            try:
                decrypted_data = self.cipher.decrypt(encrypted_tokens.encode())
                return json.loads(decrypted_data.decode())
            except Exception as e:
                print(f"Token decryption failed: {e}")
                return None
        
        return None
    
    def revoke_tokens(self, user_id):
        """Revoke tokens for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tokens SET is_active = 0 WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM tokens WHERE expires_at < CURRENT_TIMESTAMP
        ''', )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
```

### Multi-Factor Authentication Handling

#### Secure MFA Code Handling
```python
import getpass
import qrcode
from io import BytesIO
import base64

class MFAHandler:
    def __init__(self):
        self.mfa_methods = ['totp', 'sms', 'push']
    
    def handle_mfa_challenge(self, mfa_type, challenge_data=None):
        """Securely handle MFA challenges"""
        
        if mfa_type == 'totp':
            return self._handle_totp_challenge()
        elif mfa_type == 'sms':
            return self._handle_sms_challenge(challenge_data)
        elif mfa_type == 'push':
            return self._handle_push_challenge(challenge_data)
        else:
            raise ValueError(f"Unsupported MFA type: {mfa_type}")
    
    def _handle_totp_challenge(self):
        """Handle Time-based One-Time Password"""
        print("TOTP authentication required.")
        print("Please check your authenticator app (Google Authenticator, Authy, etc.)")
        
        # Use getpass to hide input
        mfa_code = getpass.getpass("Enter 6-digit TOTP code: ")
        
        # Validate code format
        if not mfa_code.isdigit() or len(mfa_code) != 6:
            raise ValueError("TOTP code must be exactly 6 digits")
        
        return mfa_code
    
    def _handle_sms_challenge(self, phone_number=None):
        """Handle SMS-based MFA"""
        if phone_number:
            masked_phone = self._mask_phone_number(phone_number)
            print(f"SMS sent to {masked_phone}")
        else:
            print("SMS authentication code sent to your registered phone number.")
        
        sms_code = getpass.getpass("Enter SMS verification code: ")
        
        # Basic validation
        if not sms_code.isdigit() or len(sms_code) < 4:
            raise ValueError("Invalid SMS code format")
        
        return sms_code
    
    def _handle_push_challenge(self, notification_data=None):
        """Handle push notification MFA"""
        print("Push notification sent to your Garmin Connect mobile app.")
        print("Please check your phone and approve the login request.")
        print("Press Enter after approving the notification...")
        
        input()  # Wait for user confirmation
        return "approved"
    
    def _mask_phone_number(self, phone):
        """Mask phone number for security"""
        if len(phone) > 4:
            return f"***-***-{phone[-4:]}"
        return "***-***-****"
```

## Network Security

### HTTPS and Certificate Validation

#### Secure HTTP Client Configuration
```python
import requests
import ssl
from urllib3.util.ssl_ import create_urllib3_context
import certifi

class SecureHTTPClient:
    def __init__(self):
        self.session = self._create_secure_session()
    
    def _create_secure_session(self):
        """Create session with strong security settings"""
        session = requests.Session()
        
        # Force HTTPS and strong SSL/TLS
        session.verify = certifi.where()  # Use certified CA bundle
        
        # Create custom SSL context with strong settings
        ctx = create_urllib3_context()
        ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Configure session adapter with SSL context
        adapter = requests.adapters.HTTPAdapter()
        session.mount('https://', adapter)
        
        # Set secure headers
        session.headers.update({
            'User-Agent': 'GarminConnectClient/1.0',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def make_request(self, method, url, **kwargs):
        """Make secure HTTP request with validation"""
        
        # Ensure HTTPS
        if not url.startswith('https://'):
            raise ValueError("Only HTTPS URLs are allowed")
        
        # Validate domain (whitelist approach)
        allowed_domains = [
            'connect.garmin.com',
            'sso.garmin.com', 
            'apis.garmin.com',
            'connectapi.garmin.com'
        ]
        
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        if parsed_url.hostname not in allowed_domains:
            raise ValueError(f"Domain {parsed_url.hostname} not in allowed list")
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.SSLError as e:
            print(f"SSL verification failed: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            raise
```

### Request Signing and Integrity

#### OAuth Request Signing Security
```python
import hmac
import hashlib
import time
import secrets
from urllib.parse import quote

class SecureOAuthSigner:
    def __init__(self, consumer_key, consumer_secret):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
    
    def generate_nonce(self, length=32):
        """Generate cryptographically secure nonce"""
        return secrets.token_urlsafe(length)
    
    def generate_timestamp(self):
        """Generate OAuth timestamp"""
        return str(int(time.time()))
    
    def sign_request(self, method, url, params=None):
        """Sign OAuth 1.0a request with HMAC-SHA256"""
        if params is None:
            params = {}
        
        # Add OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_signature_method': 'HMAC-SHA256',  # Use SHA-256 instead of SHA-1
            'oauth_timestamp': self.generate_timestamp(),
            'oauth_nonce': self.generate_nonce(),
            'oauth_version': '1.0'
        }
        
        # Merge with request parameters
        all_params = {**params, **oauth_params}
        
        # Create signature base string
        signature_base = self._create_signature_base_string(method, url, all_params)
        
        # Create signing key
        signing_key = f"{quote(self.consumer_secret)}&"  # No token secret for 2-legged OAuth
        
        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            signature_base.encode(),
            hashlib.sha256
        ).digest()
        
        oauth_params['oauth_signature'] = quote(base64.b64encode(signature).decode())
        
        return oauth_params
    
    def _create_signature_base_string(self, method, url, params):
        """Create OAuth signature base string"""
        # Normalize parameters
        sorted_params = sorted(params.items())
        param_string = '&'.join([f"{quote(str(k))}={quote(str(v))}" for k, v in sorted_params])
        
        # Normalize URL (remove query parameters)
        base_url = url.split('?')[0]
        
        return f"{method.upper()}&{quote(base_url)}&{quote(param_string)}"
```

## Data Protection and Privacy

### Personal Health Data Security

#### Data Encryption at Rest
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
import sqlite3
import json

class HealthDataEncryption:
    def __init__(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        
        # Derive key from password using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
        self.salt = salt
    
    def encrypt_health_data(self, data):
        """Encrypt sensitive health data"""
        json_data = json.dumps(data).encode()
        encrypted_data = self.cipher.encrypt(json_data)
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_health_data(self, encrypted_data):
        """Decrypt health data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted_data.decode())

class SecureHealthDataStorage:
    def __init__(self, db_path, encryption_password):
        self.db_path = db_path
        self.encryption = HealthDataEncryption(encryption_password)
        self._init_database()
    
    def _init_database(self):
        """Initialize encrypted health data database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_data (
                user_id TEXT,
                data_type TEXT,
                date DATE,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, data_type, date)
            )
        ''')
        
        # Add index for common queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_date 
            ON health_data (user_id, date)
        ''')
        
        conn.commit()
        conn.close()
        
        # Set secure permissions
        os.chmod(self.db_path, 0o600)
    
    def store_health_data(self, user_id, data_type, date, data):
        """Store encrypted health data"""
        encrypted_data = self.encryption.encrypt_health_data(data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO health_data 
            (user_id, data_type, date, encrypted_data) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, data_type, date, encrypted_data))
        
        conn.commit()
        conn.close()
    
    def retrieve_health_data(self, user_id, data_type, start_date, end_date):
        """Retrieve and decrypt health data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, encrypted_data FROM health_data 
            WHERE user_id = ? AND data_type = ? 
            AND date BETWEEN ? AND ?
            ORDER BY date
        ''', (user_id, data_type, start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        
        decrypted_results = []
        for date, encrypted_data in results:
            try:
                data = self.encryption.decrypt_health_data(encrypted_data)
                decrypted_results.append((date, data))
            except Exception as e:
                print(f"Failed to decrypt data for {date}: {e}")
        
        return decrypted_results
```

### Data Minimization and Retention

#### Data Retention Policy
```python
from datetime import datetime, timedelta
import logging

class DataRetentionManager:
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
        
        # Define retention policies by data type
        self.retention_policies = {
            'activity_summary': timedelta(days=2555),    # 7 years
            'detailed_activity': timedelta(days=1095),   # 3 years
            'health_metrics': timedelta(days=2555),      # 7 years
            'authentication_logs': timedelta(days=90),   # 90 days
            'api_request_logs': timedelta(days=30),      # 30 days
            'error_logs': timedelta(days=365),           # 1 year
        }
    
    def cleanup_expired_data(self):
        """Remove data that exceeds retention periods"""
        cleanup_results = {}
        
        for data_type, retention_period in self.retention_policies.items():
            cutoff_date = datetime.now() - retention_period
            
            try:
                deleted_count = self._delete_expired_data(data_type, cutoff_date)
                cleanup_results[data_type] = deleted_count
                
                if deleted_count > 0:
                    self.logger.info(f"Deleted {deleted_count} expired {data_type} records")
                    
            except Exception as e:
                self.logger.error(f"Failed to cleanup {data_type}: {e}")
                cleanup_results[data_type] = f"Error: {e}"
        
        return cleanup_results
    
    def _delete_expired_data(self, data_type, cutoff_date):
        """Delete data older than cutoff date"""
        cursor = self.db.cursor()
        
        # Map data types to table operations
        table_operations = {
            'activity_summary': ("activities", "created_at"),
            'detailed_activity': ("activity_details", "created_at"),
            'health_metrics': ("health_data", "created_at"),
            'authentication_logs': ("auth_logs", "timestamp"),
            'api_request_logs': ("request_logs", "timestamp"),
            'error_logs': ("error_logs", "timestamp"),
        }
        
        if data_type not in table_operations:
            raise ValueError(f"Unknown data type: {data_type}")
        
        table_name, date_column = table_operations[data_type]
        
        cursor.execute(f'''
            DELETE FROM {table_name} 
            WHERE {date_column} < ?
        ''', (cutoff_date,))
        
        deleted_count = cursor.rowcount
        self.db.commit()
        
        return deleted_count
    
    def anonymize_old_data(self, anonymization_threshold_days=365):
        """Anonymize data older than threshold while preserving analytics value"""
        cutoff_date = datetime.now() - timedelta(days=anonymization_threshold_days)
        
        cursor = self.db.cursor()
        
        # Anonymize user identifiers in old data
        cursor.execute('''
            UPDATE activities 
            SET user_id = 'anonymous_' || ABS(RANDOM() % 100000),
                email = NULL,
                name = NULL
            WHERE created_at < ? AND user_id NOT LIKE 'anonymous_%'
        ''', (cutoff_date,))
        
        anonymized_count = cursor.rowcount
        self.db.commit()
        
        self.logger.info(f"Anonymized {anonymized_count} old activity records")
        return anonymized_count
```

### Audit Logging and Monitoring

#### Security Audit Trail
```python
import json
import hashlib
from datetime import datetime
from enum import Enum

class AuditEventType(Enum):
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    DATA_ACCESS = "DATA_ACCESS"
    DATA_EXPORT = "DATA_EXPORT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    RATE_LIMIT_HIT = "RATE_LIMIT_HIT"
    SECURITY_VIOLATION = "SECURITY_VIOLATION"

class SecurityAuditLogger:
    def __init__(self, audit_db_path):
        self.audit_db = audit_db_path
        self._init_audit_database()
    
    def _init_audit_database(self):
        """Initialize audit log database"""
        conn = sqlite3.connect(self.audit_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                user_id TEXT,
                ip_address TEXT,
                user_agent TEXT,
                event_data TEXT,
                event_hash TEXT NOT NULL,
                severity INTEGER DEFAULT 1
            )
        ''')
        
        # Create indices for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_log (timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_log (event_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_log (user_id)')
        
        conn.commit()
        conn.close()
        
        # Secure permissions
        os.chmod(self.audit_db, 0o600)
    
    def log_event(self, event_type, user_id=None, ip_address=None, 
                  user_agent=None, event_data=None, severity=1):
        """Log security-relevant event with integrity protection"""
        
        event_record = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value if isinstance(event_type, AuditEventType) else event_type,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'event_data': event_data,
            'severity': severity
        }
        
        # Create hash for integrity verification
        event_json = json.dumps(event_record, sort_keys=True)
        event_hash = hashlib.sha256(event_json.encode()).hexdigest()
        
        conn = sqlite3.connect(self.audit_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log 
            (event_type, user_id, ip_address, user_agent, event_data, event_hash, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_record['event_type'],
            event_record['user_id'],
            event_record['ip_address'],
            event_record['user_agent'],
            json.dumps(event_record['event_data']) if event_record['event_data'] else None,
            event_hash,
            event_record['severity']
        ))
        
        conn.commit()
        conn.close()
    
    def detect_suspicious_activity(self):
        """Detect patterns that may indicate security issues"""
        conn = sqlite3.connect(self.audit_db)
        cursor = conn.cursor()
        
        # Multiple failed login attempts
        cursor.execute('''
            SELECT user_id, ip_address, COUNT(*) as failure_count
            FROM audit_log 
            WHERE event_type = 'LOGIN_FAILURE' 
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY user_id, ip_address
            HAVING COUNT(*) >= 5
        ''')
        
        failed_logins = cursor.fetchall()
        
        # Unusual data access patterns
        cursor.execute('''
            SELECT user_id, COUNT(*) as access_count
            FROM audit_log 
            WHERE event_type = 'DATA_ACCESS'
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY user_id
            HAVING COUNT(*) > 100
        ''')
        
        high_access_users = cursor.fetchall()
        
        # Rate limiting violations
        cursor.execute('''
            SELECT user_id, ip_address, COUNT(*) as violation_count
            FROM audit_log 
            WHERE event_type = 'RATE_LIMIT_HIT'
            AND timestamp > datetime('now', '-1 hour')
            GROUP BY user_id, ip_address
            HAVING COUNT(*) > 10
        ''')
        
        rate_limit_violations = cursor.fetchall()
        
        conn.close()
        
        return {
            'failed_logins': failed_logins,
            'high_access_users': high_access_users,
            'rate_limit_violations': rate_limit_violations
        }
```

## Compliance and Legal Considerations

### GDPR and Data Protection

#### User Consent Management
```python
from datetime import datetime
from enum import Enum

class ConsentType(Enum):
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    MARKETING = "marketing"

class ConsentManager:
    def __init__(self, db_connection):
        self.db = db_connection
        self._init_consent_database()
    
    def _init_consent_database(self):
        """Initialize consent tracking database"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_consent (
                user_id TEXT,
                consent_type TEXT,
                consent_given BOOLEAN,
                consent_timestamp TIMESTAMP,
                consent_version TEXT,
                ip_address TEXT,
                legal_basis TEXT,
                PRIMARY KEY (user_id, consent_type, consent_version)
            )
        ''')
        
        self.db.commit()
    
    def record_consent(self, user_id, consent_type, consent_given, 
                      ip_address=None, legal_basis="consent", consent_version="1.0"):
        """Record user consent decision"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_consent 
            (user_id, consent_type, consent_given, consent_timestamp, 
             consent_version, ip_address, legal_basis)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            consent_type.value if isinstance(consent_type, ConsentType) else consent_type,
            consent_given,
            datetime.now(),
            consent_version,
            ip_address,
            legal_basis
        ))
        
        self.db.commit()
    
    def check_consent(self, user_id, consent_type, required_version="1.0"):
        """Check if user has given valid consent"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT consent_given, consent_timestamp, consent_version
            FROM user_consent 
            WHERE user_id = ? AND consent_type = ? AND consent_version = ?
            ORDER BY consent_timestamp DESC
            LIMIT 1
        ''', (
            user_id,
            consent_type.value if isinstance(consent_type, ConsentType) else consent_type,
            required_version
        ))
        
        result = cursor.fetchone()
        
        if result:
            consent_given, timestamp, version = result
            return {
                'has_consent': bool(consent_given),
                'consent_date': timestamp,
                'consent_version': version
            }
        
        return {'has_consent': False, 'consent_date': None, 'consent_version': None}
```

#### Data Subject Rights Implementation
```python
class DataSubjectRights:
    def __init__(self, db_connection, storage_manager):
        self.db = db_connection
        self.storage = storage_manager
    
    def export_user_data(self, user_id):
        """Export all user data in portable format (GDPR Article 20)"""
        cursor = self.db.cursor()
        
        # Collect all user data from various tables
        user_data = {}
        
        # Profile data
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        user_data['profile'] = cursor.fetchall()
        
        # Activity data
        cursor.execute('SELECT * FROM activities WHERE user_id = ?', (user_id,))
        user_data['activities'] = cursor.fetchall()
        
        # Health data
        cursor.execute('SELECT * FROM health_data WHERE user_id = ?', (user_id,))
        user_data['health_metrics'] = cursor.fetchall()
        
        # Consent records
        cursor.execute('SELECT * FROM user_consent WHERE user_id = ?', (user_id,))
        user_data['consent_history'] = cursor.fetchall()
        
        # Package for export
        export_package = {
            'export_date': datetime.now().isoformat(),
            'user_id': user_id,
            'data': user_data,
            'format_version': '1.0'
        }
        
        return json.dumps(export_package, indent=2, default=str)
    
    def delete_user_data(self, user_id, verification_token):
        """Permanently delete all user data (GDPR Article 17)"""
        
        # Verify deletion request (implement your verification logic)
        if not self._verify_deletion_request(user_id, verification_token):
            raise ValueError("Invalid deletion verification")
        
        cursor = self.db.cursor()
        
        # Begin transaction for atomic deletion
        cursor.execute('BEGIN TRANSACTION')
        
        try:
            # Delete from all relevant tables
            tables_to_clean = [
                'user_profiles',
                'activities', 
                'health_data',
                'user_consent',
                'auth_tokens',
                'audit_log'
            ]
            
            deletion_log = {}
            for table in tables_to_clean:
                cursor.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
                deletion_log[table] = cursor.rowcount
            
            # Delete associated files
            file_deletion_count = self.storage.delete_user_files(user_id)
            deletion_log['files_deleted'] = file_deletion_count
            
            cursor.execute('COMMIT')
            
            # Log the deletion (anonymized)
            self._log_data_deletion(user_id, deletion_log)
            
            return deletion_log
            
        except Exception as e:
            cursor.execute('ROLLBACK')
            raise Exception(f"Data deletion failed: {e}")
    
    def _verify_deletion_request(self, user_id, verification_token):
        """Verify that deletion request is legitimate"""
        # Implement verification logic (email confirmation, etc.)
        return True  # Simplified for example
    
    def _log_data_deletion(self, user_id, deletion_log):
        """Log data deletion event for compliance"""
        # Create anonymous log entry
        audit_logger = SecurityAuditLogger('audit.db')
        audit_logger.log_event(
            event_type="DATA_DELETION",
            user_id=f"deleted_user_{hashlib.sha256(user_id.encode()).hexdigest()[:8]}",
            event_data=deletion_log,
            severity=2
        )
```

This comprehensive security framework addresses the major security concerns when integrating with Garmin Connect, from credential management to compliance with data protection regulations.