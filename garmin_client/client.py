"""
Garmin Connect Client Implementation.

Enhanced Garmin Connect client with encryption, error handling, and secure credential management.
Research-validated implementation following PRP specifications.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime, date, timedelta

try:
    from garminconnect import Garmin

    GARMIN_CONNECT_AVAILABLE = True
except ImportError:
    GARMIN_CONNECT_AVAILABLE = False

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class GarminConnectClient:
    """Enhanced Garmin Connect client with encryption and error handling."""

    def __init__(self, config_dir: Path = None):
        """
        Initialize Garmin Connect client.

        Args:
            config_dir: Directory for storing configuration and credentials.
                       Defaults to ~/.garmin-dashboard
        """
        self.config_dir = config_dir or Path.home() / ".garmin-dashboard"
        self.config_dir.mkdir(exist_ok=True)

        # Configuration files
        self.credentials_file = self.config_dir / "credentials.enc"
        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "session.json"
        self.log_file = self.config_dir / "client.log"

        # Initialize encryption
        self._encryption_key = self._get_or_create_key()

        # API instance
        self._api: Optional[Garmin] = None
        self._authenticated = False

        # Setup logging
        self._setup_logging()

        # Check if Garmin Connect library is available
        if not GARMIN_CONNECT_AVAILABLE:
            logger.warning("garminconnect library not available. Please install with: pip install garminconnect")

        logger.info("GarminConnectClient initialized")

    def _setup_logging(self):
        """Set up logging to file."""
        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for credentials."""
        key_file = self.config_dir / "key.bin"

        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Secure permissions
            logger.info("Created new encryption key")
            return key

    def store_credentials(self, email: str, password: str):
        """
        Securely store Garmin Connect credentials.

        Args:
            email: Garmin Connect email
            password: Garmin Connect password
        """
        fernet = Fernet(self._encryption_key)

        credentials = {"email": email, "password": password, "stored_at": datetime.now().isoformat()}

        encrypted_data = fernet.encrypt(json.dumps(credentials).encode())
        self.credentials_file.write_bytes(encrypted_data)
        self.credentials_file.chmod(0o600)

        logger.info("Credentials stored securely")

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load and decrypt stored credentials.

        Returns:
            Dictionary with email and password, or None if not found
        """
        if not self.credentials_file.exists():
            return None

        try:
            fernet = Fernet(self._encryption_key)
            encrypted_data = self.credentials_file.read_bytes()
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None

    def clear_credentials(self):
        """Clear stored credentials."""
        if self.credentials_file.exists():
            self.credentials_file.unlink()
            logger.info("Credentials cleared")

    def authenticate(self, email: str = None, password: str = None, mfa_callback=None) -> bool:
        """
        Authenticate with Garmin Connect with MFA support.

        Args:
            email: Garmin Connect email (optional if stored)
            password: Garmin Connect password (optional if stored)
            mfa_callback: Callback function to get MFA code when needed

        Returns:
            True if authentication successful, False otherwise
        """
        if not GARMIN_CONNECT_AVAILABLE:
            logger.error("garminconnect library not available")
            return False

        # Use provided credentials or load from storage
        if email and password:
            self.store_credentials(email, password)
        else:
            credentials = self.load_credentials()
            if not credentials:
                logger.error("No credentials provided or stored")
                return False
            email = credentials["email"]
            password = credentials["password"]

        try:
            logger.info(f"Attempting to authenticate as {email}")

            # Create MFA prompt function
            def mfa_prompt():
                if mfa_callback:
                    return mfa_callback()
                else:
                    # Fallback to console prompt
                    return input("Enter MFA code: ")

            # Initialize Garmin client with MFA support
            self._api = Garmin(email, password, prompt_mfa=mfa_prompt)
            self._api.login()

            # Store successful session info
            session_data = {"authenticated_at": datetime.now().isoformat(), "email": email}
            with open(self.session_file, "w") as f:
                json.dump(session_data, f)

            self._authenticated = True
            logger.info(f"Successfully authenticated as {email}")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def is_authenticated(self) -> bool:
        """Check if client is currently authenticated."""
        return self._authenticated and self._api is not None

    def logout(self):
        """Logout and clear session."""
        self._api = None
        self._authenticated = False

        if self.session_file.exists():
            self.session_file.unlink()

        logger.info("Logged out successfully")

    def get_activities(
        self, start_date: Union[date, str], end_date: Union[date, str] = None, limit: int = 100
    ) -> List[Dict]:
        """
        Get activities for date range.

        Args:
            start_date: Start date (date object or ISO string)
            end_date: End date (date object or ISO string). Defaults to today.
            limit: Maximum number of activities to retrieve

        Returns:
            List of activity dictionaries
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return []

        # Convert dates to strings if needed
        if isinstance(start_date, date):
            start_date = start_date.isoformat()

        if end_date is None:
            end_date = date.today().isoformat()
        elif isinstance(end_date, date):
            end_date = end_date.isoformat()

        try:
            logger.info(f"Retrieving activities from {start_date} to {end_date}")
            activities = self._api.get_activities_by_date(start_date, end_date, limit=limit)

            logger.info(f"Retrieved {len(activities)} activities")
            return activities if activities else []

        except Exception as e:
            logger.error(f"Failed to retrieve activities: {e}")
            return []

    def download_activity(self, activity_id: int, format_type: str = "fit", output_dir: Path = None) -> Optional[Path]:
        """
        Download single activity file.

        Args:
            activity_id: Garmin activity ID
            format_type: File format ('fit' or 'gpx')
            output_dir: Output directory (defaults to config_dir/downloads)

        Returns:
            Path to downloaded file, or None if failed
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Call authenticate() first.")
            return None

        output_dir = output_dir or (self.config_dir / "downloads")
        output_dir.mkdir(exist_ok=True)

        try:
            # Get activity details for naming
            activity_detail = self._api.get_activity(activity_id)
            activity_name = activity_detail.get("activityName", f"activity_{activity_id}")

            # Clean filename for filesystem safety
            safe_name = "".join(c for c in activity_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
            safe_name = safe_name[:50]  # Limit length
            filename = f"{activity_id}_{safe_name}.{format_type.lower()}"
            output_path = output_dir / filename

            logger.info(f"Downloading activity {activity_id} as {format_type}")

            # Download file based on format
            if format_type.lower() == "fit":
                file_data = self._api.download_activity(activity_id, dl_fmt=self._api.ActivityDownloadFormat.ORIGINAL)
            elif format_type.lower() == "gpx":
                file_data = self._api.download_activity(activity_id, dl_fmt=self._api.ActivityDownloadFormat.GPX)
            else:
                logger.error(f"Unsupported format: {format_type}")
                return None

            # Save file
            output_path.write_bytes(file_data)
            logger.info(f"Downloaded activity {activity_id} to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to download activity {activity_id}: {e}")
            return None

    def download_multiple_activities(
        self,
        activity_ids: List[int],
        format_type: str = "fit",
        output_dir: Path = None,
        max_concurrent: int = 3,
        delay_between: float = 1.0,
    ) -> Dict[int, Optional[Path]]:
        """
        Download multiple activities with rate limiting.

        Args:
            activity_ids: List of activity IDs to download
            format_type: File format ('fit' or 'gpx')
            output_dir: Output directory
            max_concurrent: Maximum concurrent downloads
            delay_between: Delay between downloads in seconds

        Returns:
            Dictionary mapping activity_id to download path (or None if failed)
        """
        results = {}

        logger.info(f"Starting download of {len(activity_ids)} activities")

        for i, activity_id in enumerate(activity_ids):
            try:
                # Rate limiting delay
                if i > 0:
                    import time

                    time.sleep(delay_between)

                result = self.download_activity(activity_id, format_type, output_dir)
                results[activity_id] = result

                logger.info(f"Downloaded {i+1}/{len(activity_ids)} activities")

            except Exception as e:
                logger.error(f"Failed to download activity {activity_id}: {e}")
                results[activity_id] = None

        successful_downloads = len([p for p in results.values() if p is not None])
        logger.info(f"Download complete: {successful_downloads}/{len(activity_ids)} successful")

        return results

    def get_config(self) -> Dict:
        """
        Load application configuration.

        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Default configuration
        default_config = {
            "default_download_format": "fit",
            "download_directory": str(self.config_dir / "downloads"),
            "max_concurrent_downloads": 3,
            "rate_limit_delay": 1.0,
            "auto_import_to_dashboard": True,
            "activities_directory": "./activities",
        }

        # Save default config
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict):
        """
        Save application configuration.

        Args:
            config: Configuration dictionary to save
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get_session_info(self) -> Optional[Dict]:
        """
        Get current session information.

        Returns:
            Session information dictionary or None
        """
        if not self.session_file.exists():
            return None

        try:
            with open(self.session_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session info: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test if the client can connect to Garmin Connect.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.is_authenticated():
            return False

        try:
            # Try to get a small amount of data
            activities = self.get_activities(start_date=date.today() - timedelta(days=1), limit=1)
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_user_profile(self) -> Optional[Dict]:
        """
        Get user profile information.

        Returns:
            User profile dictionary or None if failed
        """
        if not self.is_authenticated():
            logger.error("Not authenticated")
            return None

        try:
            profile = self._api.get_user_profile()
            logger.info("Retrieved user profile")
            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None


# Convenience functions for common operations
def create_client(config_dir: Path = None) -> GarminConnectClient:
    """Create a new Garmin Connect client instance."""
    return GarminConnectClient(config_dir)


def quick_authenticate(email: str, password: str, config_dir: Path = None) -> Optional[GarminConnectClient]:
    """
    Quickly authenticate and return client instance.

    Args:
        email: Garmin Connect email
        password: Garmin Connect password
        config_dir: Configuration directory

    Returns:
        Authenticated client instance or None if failed
    """
    client = GarminConnectClient(config_dir)
    if client.authenticate(email, password):
        return client
    return None
