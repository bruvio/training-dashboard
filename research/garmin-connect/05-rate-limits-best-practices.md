# Rate Limiting and Best Practices

## Overview

Garmin Connect implements strict rate limiting across all access methods to protect their infrastructure and ensure fair usage. Understanding and respecting these limits is crucial for building reliable integrations.

## Rate Limiting Mechanisms

### Official API Rate Limits

#### Health API Limits
- **Polling Frequency**: Maximum once every ~5 minutes recommended
- **Push Notifications**: Preferred over polling when available
- **Quota System**: Undisclosed specific limits, varies by developer tier
- **Error Response**: HTTP 429 "Too many requests: Rate limit quota violation"

#### Activity API Limits
- **Bulk Downloads**: Throttled for large historical data requests
- **Concurrent Requests**: Limited number of simultaneous connections
- **Daily Quotas**: Aggregate request limits per 24-hour period
- **Burst Protection**: Short-term high-frequency request blocking

#### Common Rate Limit Errors
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "Too many request: Limit per : Rate limit quota violation. Quota limit exceeded."
}
```

### Unofficial API Rate Limits

#### Login Rate Limiting
- **Trigger**: Frequent authentication attempts
- **Duration**: Typically 1 hour blocks
- **Causes**: 
  - Multiple failed login attempts
  - Frequent re-authentication within short periods
  - Suspicious activity patterns

#### Data Access Limits
- **General Rule**: Similar to official API limits
- **Detection Methods**: 
  - Request frequency monitoring
  - User agent analysis
  - IP-based tracking
  - Session behavior patterns

#### Garmin Connect Web Interface Limits
- **Bulk Export**: Limited to certain date ranges
- **Individual Downloads**: Throttled per activity
- **Session Timeouts**: Automatic logout after inactivity

## Best Practices for Rate Limiting

### 1. Token Persistence and Reuse

#### Avoid Frequent Re-authentication
```python
import os
import json
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, token_file="~/.garmin_tokens.json"):
        self.token_file = os.path.expanduser(token_file)
        self.tokens = self.load_tokens()
    
    def load_tokens(self):
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_tokens(self, tokens):
        self.tokens = tokens
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f)
        # Set restrictive permissions
        os.chmod(self.token_file, 0o600)
    
    def is_valid(self):
        if not self.tokens:
            return False
        
        # Check if token is expired (assuming 1 year validity)
        issued_date = datetime.fromisoformat(self.tokens.get('issued_at', ''))
        expiry_date = issued_date + timedelta(days=365)
        
        return datetime.now() < expiry_date
    
    def get_authenticated_client(self):
        if self.is_valid():
            # Resume existing session
            api = GarminConnect()
            api.restore_session(self.tokens)
            return api
        else:
            # Need fresh authentication
            return None
```

#### Session Validation Strategy
```python
def ensure_authenticated_session(api, email, password):
    """Validate session before making requests"""
    
    try:
        # Test authentication with lightweight request
        user_summary = api.get_user_summary()
        return api
    except GarminConnectAuthenticationError:
        # Session expired, re-authenticate
        print("Session expired, re-authenticating...")
        api.login(email, password)
        return api
    except Exception as e:
        print(f"Session validation failed: {e}")
        raise
```

### 2. Intelligent Request Scheduling

#### Exponential Backoff Implementation
```python
import time
import random
from functools import wraps

def exponential_backoff(max_retries=5, base_delay=1, max_delay=60):
    """Decorator for exponential backoff retry logic"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except GarminConnectTooManyRequestsError:
                    if attempt == max_retries - 1:
                        raise
                    
                    # Calculate delay with jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    
                    print(f"Rate limited, waiting {total_delay:.1f} seconds...")
                    time.sleep(total_delay)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(base_delay)
            
        return wrapper
    return decorator

# Usage
@exponential_backoff(max_retries=3, base_delay=2)
def download_activity_safe(api, activity_id, format_type):
    return api.download_activity(activity_id, format_type)
```

#### Request Queue Management
```python
from collections import deque
import time
import threading

class RateLimitedQueue:
    def __init__(self, max_requests_per_minute=10):
        self.queue = deque()
        self.request_times = deque()
        self.max_requests = max_requests_per_minute
        self.lock = threading.Lock()
    
    def add_request(self, func, *args, **kwargs):
        """Add request to queue with rate limiting"""
        with self.lock:
            self.queue.append((func, args, kwargs))
    
    def process_queue(self):
        """Process queued requests respecting rate limits"""
        while self.queue:
            # Clean old request timestamps
            current_time = time.time()
            while self.request_times and self.request_times[0] < current_time - 60:
                self.request_times.popleft()
            
            # Check if we can make a request
            if len(self.request_times) < self.max_requests:
                with self.lock:
                    if self.queue:
                        func, args, kwargs = self.queue.popleft()
                        self.request_times.append(current_time)
                        
                        try:
                            result = func(*args, **kwargs)
                            yield result
                        except Exception as e:
                            print(f"Request failed: {e}")
            else:
                # Wait before next request
                time.sleep(1)
```

### 3. Caching and Local Storage

#### Activity Metadata Caching
```python
import sqlite3
import json
from datetime import datetime, timedelta

class ActivityCache:
    def __init__(self, db_path="garmin_cache.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_cache (
                activity_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_cached_activity(self, activity_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data FROM activity_cache 
            WHERE activity_id = ? AND expires_at > CURRENT_TIMESTAMP
        ''', (activity_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def cache_activity(self, activity_id, data, ttl_hours=24):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        cursor.execute('''
            INSERT OR REPLACE INTO activity_cache 
            (activity_id, data, expires_at) VALUES (?, ?, ?)
        ''', (activity_id, json.dumps(data), expires_at))
        
        conn.commit()
        conn.close()
```

#### File-Based Caching
```python
import os
import pickle
from pathlib import Path

class FileCache:
    def __init__(self, cache_dir="~/.garmin_cache"):
        self.cache_dir = Path(os.path.expanduser(cache_dir))
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_path(self, key):
        return self.cache_dir / f"{key}.pkl"
    
    def get(self, key, max_age_hours=24):
        cache_file = self.get_cache_path(key)
        
        if not cache_file.exists():
            return None
        
        # Check file age
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > max_age_hours * 3600:
            cache_file.unlink()  # Remove expired cache
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def set(self, key, value):
        cache_file = self.get_cache_path(key)
        
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)
```

### 4. Batch Operations and Bulk Processing

#### Efficient Activity Sync
```python
def incremental_activity_sync(api, last_sync_date=None, batch_size=50):
    """Sync activities in batches to minimize API calls"""
    
    # Get activity list (lightweight request)
    if last_sync_date:
        start_date = last_sync_date.isoformat()
    else:
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
    
    activities = api.get_activities_by_date(
        start_date,
        datetime.now().isoformat(),
        limit=1000  # Get comprehensive list
    )
    
    # Process in batches
    for i in range(0, len(activities), batch_size):
        batch = activities[i:i + batch_size]
        
        print(f"Processing batch {i//batch_size + 1}/{(len(activities) + batch_size - 1)//batch_size}")
        
        for activity in batch:
            activity_id = activity['activityId']
            
            # Check if we already have this activity
            if not activity_exists_locally(activity_id):
                try:
                    # Download with rate limiting
                    download_activity_safe(api, activity_id)
                    time.sleep(1)  # Basic rate limiting between requests
                except Exception as e:
                    print(f"Failed to download activity {activity_id}: {e}")
        
        # Pause between batches
        print("Batch complete, pausing...")
        time.sleep(5)
```

#### Priority-Based Processing
```python
from enum import Enum
import heapq

class Priority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class PriorityQueue:
    def __init__(self):
        self.queue = []
        self.index = 0
    
    def add_task(self, priority, func, *args, **kwargs):
        heapq.heappush(self.queue, (priority.value, self.index, func, args, kwargs))
        self.index += 1
    
    def process_tasks(self, api):
        while self.queue:
            priority, _, func, args, kwargs = heapq.heappop(self.queue)
            
            try:
                result = func(api, *args, **kwargs)
                yield result
                
                # Different delays based on priority
                if priority == Priority.HIGH.value:
                    time.sleep(0.5)
                elif priority == Priority.MEDIUM.value:
                    time.sleep(1.0)
                else:
                    time.sleep(2.0)
                    
            except GarminConnectTooManyRequestsError:
                # Re-queue with lower priority
                new_priority = Priority(min(priority + 1, 3))
                heapq.heappush(self.queue, (new_priority.value, self.index, func, args, kwargs))
                self.index += 1
                time.sleep(10)  # Longer wait for rate limit recovery
```

### 5. Monitoring and Health Checks

#### API Health Monitoring
```python
import logging
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIHealthStatus:
    is_healthy: bool
    last_successful_request: Optional[datetime]
    consecutive_failures: int
    current_rate_limit_status: str
    estimated_recovery_time: Optional[datetime]

class APIHealthMonitor:
    def __init__(self):
        self.health_status = APIHealthStatus(
            is_healthy=True,
            last_successful_request=None,
            consecutive_failures=0,
            current_rate_limit_status="OK",
            estimated_recovery_time=None
        )
        self.logger = logging.getLogger(__name__)
    
    def record_success(self):
        self.health_status.is_healthy = True
        self.health_status.last_successful_request = datetime.now()
        self.health_status.consecutive_failures = 0
        self.health_status.current_rate_limit_status = "OK"
        self.health_status.estimated_recovery_time = None
    
    def record_rate_limit(self, retry_after=None):
        self.health_status.consecutive_failures += 1
        self.health_status.current_rate_limit_status = "RATE_LIMITED"
        
        if retry_after:
            self.health_status.estimated_recovery_time = datetime.now() + timedelta(seconds=retry_after)
        else:
            # Estimate recovery time based on consecutive failures
            recovery_seconds = min(2 ** self.health_status.consecutive_failures, 3600)
            self.health_status.estimated_recovery_time = datetime.now() + timedelta(seconds=recovery_seconds)
        
        self.logger.warning(f"Rate limit hit. Estimated recovery: {self.health_status.estimated_recovery_time}")
    
    def should_make_request(self):
        if not self.health_status.is_healthy:
            if self.health_status.estimated_recovery_time:
                return datetime.now() > self.health_status.estimated_recovery_time
            return False
        return True
    
    def get_recommended_delay(self):
        """Get recommended delay before next request"""
        if self.health_status.consecutive_failures == 0:
            return 1  # Normal operation
        elif self.health_status.consecutive_failures < 3:
            return 5  # Minor issues
        else:
            return 15  # Major issues
```

#### Request Logging and Analytics
```python
import json
from collections import defaultdict, Counter

class RequestAnalytics:
    def __init__(self):
        self.request_log = []
        self.error_counts = Counter()
        self.endpoint_stats = defaultdict(list)
    
    def log_request(self, endpoint, method="GET", status_code=200, response_time=0, error=None):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'response_time': response_time,
            'error': str(error) if error else None
        }
        
        self.request_log.append(log_entry)
        self.endpoint_stats[endpoint].append(response_time)
        
        if error:
            self.error_counts[type(error).__name__] += 1
    
    def get_stats_summary(self):
        total_requests = len(self.request_log)
        if total_requests == 0:
            return {"message": "No requests recorded"}
        
        error_rate = sum(self.error_counts.values()) / total_requests
        
        avg_response_times = {
            endpoint: sum(times) / len(times)
            for endpoint, times in self.endpoint_stats.items()
        }
        
        return {
            'total_requests': total_requests,
            'error_rate': error_rate,
            'most_common_errors': self.error_counts.most_common(5),
            'average_response_times': avg_response_times
        }
    
    def export_logs(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.request_log, f, indent=2)
```

## Production Deployment Considerations

### Load Balancing and Distribution

#### Multiple Account Strategy
```python
class AccountPool:
    def __init__(self, accounts):
        self.accounts = accounts  # List of (email, password) tuples
        self.account_clients = {}
        self.account_health = {}
        self.current_account = 0
    
    def get_healthy_client(self):
        """Get a client from a healthy account"""
        attempts = 0
        while attempts < len(self.accounts):
            account_id = self.current_account % len(self.accounts)
            
            if self.is_account_healthy(account_id):
                return self.get_account_client(account_id)
            
            self.current_account = (self.current_account + 1) % len(self.accounts)
            attempts += 1
        
        raise Exception("No healthy accounts available")
    
    def mark_account_rate_limited(self, account_id):
        self.account_health[account_id] = {
            'status': 'rate_limited',
            'recovery_time': datetime.now() + timedelta(hours=1)
        }
```

### Error Recovery Strategies

#### Circuit Breaker Pattern
```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except self.expected_exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Monitoring and Alerting

#### Health Check Endpoint
```python
from flask import Flask, jsonify

app = Flask(__name__)
health_monitor = APIHealthMonitor()

@app.route('/health')
def health_check():
    status = health_monitor.health_status
    
    response = {
        'status': 'healthy' if status.is_healthy else 'unhealthy',
        'last_successful_request': status.last_successful_request.isoformat() if status.last_successful_request else None,
        'consecutive_failures': status.consecutive_failures,
        'rate_limit_status': status.current_rate_limit_status,
        'estimated_recovery': status.estimated_recovery_time.isoformat() if status.estimated_recovery_time else None
    }
    
    return jsonify(response), 200 if status.is_healthy else 503
```

This comprehensive approach to rate limiting and best practices ensures reliable, sustainable access to Garmin Connect data while respecting API limits and maintaining good performance.