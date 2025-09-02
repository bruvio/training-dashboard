"""
Garmin Connect Client Implementation.

Enhanced Garmin Connect client with encryption, error handling, and secure credential management.
Research-validated implementation following PRP specifications.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Union
import pickle
import base64

try:
    from garminconnect import Garmin
    import garth
    from garth.exc import GarthException

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

    def authenticate(
        self, email: str = None, password: str = None, mfa_callback=None, mfa_context=None, remember_me: bool = False
    ) -> Union[bool, str, dict]:
        """
        Authenticate with Garmin Connect using garth, with MFA support.

        Args:
            email: Garmin Connect email (optional if stored)
            password: Garmin Connect password (optional if stored)
            mfa_callback: Callable that returns MFA code when called
            mfa_context: The result2 object returned by garth.login when MFA is required (used for resuming)
            remember_me: Whether to store credentials for future logins

        Returns:
            dict with status and optional mfa_context:
                {"status": "SUCCESS"} -> Authentication successful
                {"status": "MFA_REQUIRED", "mfa_context": result2} -> MFA needed
                {"status": "MFA_FAILED"} -> MFA provided but invalid
                {"status": "FAILED"} -> Authentication failed
        """
        if not GARMIN_CONNECT_AVAILABLE:
            logger.error("garminconnect library not available")
            return {"status": "FAILED"}

        # Load stored credentials if not provided
        if email and password:
            if remember_me:
                self.store_credentials(email, password)
        else:
            credentials = self.load_credentials()
            if not credentials:
                logger.error("No credentials provided or stored")
                return {"status": "FAILED"}
            email = credentials["email"]
            password = credentials["password"]

        garth_session_path = self.config_dir / "garth_session"

        # Try to resume previous session
        try:
            garth.resume(str(garth_session_path))
            logger.info("Resumed existing garth session")
            self._api = Garmin()
            self._authenticated = True
            return {"status": "SUCCESS"}
        except (GarthException, FileNotFoundError):
            logger.info("No valid garth session found, performing fresh login")

        try:
            if mfa_context and mfa_callback:
                # Resume MFA login flow
                logger.info("Resuming login with MFA code...")
                mfa_code = mfa_callback()
                if not mfa_code:
                    logger.warning("MFA code required but not provided by callback")
                    return {"status": "MFA_REQUIRED", "mfa_context": mfa_context}

                try:
                    garth.resume_login(mfa_context, mfa_code)
                    logger.info("MFA authentication successful")
                except Exception as e:
                    logger.error(f"MFA authentication failed: {e}")
                    return {"status": "MFA_FAILED"}

            else:
                # First-time login attempt
                logger.info(f"Authenticating as {email}")
                result1, result2 = garth.login(email, password, return_on_mfa=True)

                if result1 == "needs_mfa":
                    if not mfa_callback:
                        # serialize result2 to base64 string for safe storage
                        mfa_context_serialized = base64.b64encode(pickle.dumps(result2)).decode("utf-8")
                        return {"status": "MFA_REQUIRED", "mfa_context": mfa_context_serialized}

                    # MFA callback available - collect and try to resume immediately
                    mfa_code = mfa_callback()
                    if not mfa_code:
                        logger.warning("MFA code required but not provided by callback")
                        return {"status": "MFA_REQUIRED", "mfa_context": result2}

                    try:
                        garth.resume_login(result2, mfa_code)
                        logger.info("MFA authentication successful")
                    except Exception as e:
                        logger.error(f"MFA authentication failed: {e}")
                        return {"status": "MFA_FAILED"}
                else:
                    logger.info("Direct authentication successful (no MFA required)")

            # Save session on success
            garth.save(str(garth_session_path))
            self._api = Garmin()
            self._authenticated = True

            session_data = {
                "authenticated_at": datetime.now().isoformat(),
                "email": email,
                "garth_session_path": str(garth_session_path),
            }
            with open(self.session_file, "w") as f:
                json.dump(session_data, f)

            logger.info("Authentication successful")
            return {"status": "SUCCESS"}

        except Exception as e:
            error_str = str(e).lower()
            if any(k in error_str for k in ["mfa", "verification", "2fa", "two-factor", "needs_mfa"]):
                logger.warning("MFA required but no callback provided or authentication failed")
                return {"status": "MFA_REQUIRED"}
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return {"status": "FAILED"}


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
    return client if client.authenticate(email, password) else None
