"""
Garmin Connect Client Implementation.

Enhanced Garmin Connect client with encryption, error handling, and secure credential management.
Research-validated implementation following PRP specifications.
"""

import base64
from datetime import datetime
import json
import logging
from pathlib import Path
import pickle
import threading
from typing import Dict, Optional, Union

try:
    from garminconnect import Garmin
    import garth
    from garth.exc import GarthException
    import garth.sso as garth_sso

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

    def _login_with_timeout(self, email: str, password: str, timeout: int = 30):
        """
        Perform garth.login with timeout protection.

        Args:
            email: Garmin Connect email
            password: Garmin Connect password
            timeout: Timeout in seconds (default: 30)

        Returns:
            Tuple of (result1, result2) or (None, None) if timeout/error
        """
        result = {"result1": None, "result2": None, "exception": None}

        def target():
            try:
                logger.info(f"Starting garth.login for {email}")
                result1, result2 = garth.login(email, password, return_on_mfa=True)
                result["result1"] = result1
                result["result2"] = result2
                logger.info(f"garth.login completed with result: {result1}")
            except Exception as e:
                logger.error(f"garth.login failed with exception: {e}")
                result["exception"] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()

        # Wait for completion or timeout
        thread.join(timeout)

        if thread.is_alive():
            logger.error(f"garth.login timed out after {timeout} seconds")
            # Note: We can't forcefully kill the thread, but we can return timeout status
            return None, "TIMEOUT"

        if result["exception"]:
            raise result["exception"]

        return result["result1"], result["result2"]

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

        # Store credentials immediately if remember_me is enabled and credentials provided
        if remember_me and email and password:
            self.store_credentials(email, password)
            logger.info("Credentials stored (remember me enabled)")

        # Load stored credentials if not provided
        if not (email and password):
            credentials = self.load_credentials()
            if not credentials:
                logger.error("No credentials provided or stored")
                return {"status": "FAILED"}
            email = credentials["email"]
            password = credentials["password"]

        garth_session_path = self.config_dir / "garth_session"

        # Validate and try to resume previous session
        session_valid = False
        if garth_session_path.exists():
            try:
                # Pre-validate the session directory structure and files
                oauth1_file = garth_session_path / "oauth1"
                garth_session_path / "oauth2"

                # Check if the session directory has the expected structure
                if garth_session_path.is_dir():
                    # Try to validate oauth1 file if it exists
                    if oauth1_file.exists():
                        with open(oauth1_file, "r") as f:
                            oauth1_data = json.load(f)
                            # Validate that it's a proper dict, not a string
                            if isinstance(oauth1_data, dict):
                                session_valid = True
                            else:
                                logger.warning(f"OAuth1 file contains invalid data type: {type(oauth1_data)}")
                    else:
                        logger.info("No OAuth1 file found in session")
                else:
                    logger.warning("Session path exists but is not a directory")

            except (json.JSONDecodeError, FileNotFoundError, TypeError, ValueError) as validation_error:
                logger.warning(f"Session validation failed: {validation_error}")
                session_valid = False

        if session_valid:
            try:
                garth.resume(str(garth_session_path))
                logger.info("Resumed existing garth session")
                self._api = Garmin()
                self._authenticated = True
                return {"status": "SUCCESS"}
            except (
                GarthException,
                FileNotFoundError,
                json.JSONDecodeError,
                NotADirectoryError,
                TypeError,
                ValueError,
            ) as e:
                logger.info(f"Session resume failed despite validation: {e}")
                session_valid = False

        # Clean up corrupted or invalid session files
        if not session_valid and garth_session_path.exists():
            try:
                import shutil

                shutil.rmtree(garth_session_path, ignore_errors=True)
                logger.info("Cleaned up corrupted session files")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up session files: {cleanup_error}")

        logger.info("No valid session found, performing fresh login")

        try:
            if mfa_context and mfa_callback:
                # Resume MFA login flow
                logger.info("Resuming login with MFA code...")
                mfa_code = mfa_callback()
                if not mfa_code:
                    logger.warning("MFA code required but not provided by callback")
                    return {"status": "MFA_REQUIRED", "mfa_context": mfa_context}

                try:
                    garth_sso.resume_login(mfa_context, mfa_code)
                    logger.info("MFA authentication successful")
                except Exception as e:
                    logger.error(f"MFA authentication failed: {e}")
                    return {"status": "MFA_FAILED"}

            else:
                # First-time login attempt with timeout protection
                logger.info(f"Authenticating as {email}")
                result1, result2 = self._login_with_timeout(email, password, timeout=30)

                # Handle timeout case
                if result2 == "TIMEOUT":
                    logger.error("Authentication timed out - likely server/network issue")
                    return {"status": "FAILED"}

                if result1 == "needs_mfa":
                    logger.info("MFA required for authentication")
                    if not mfa_callback:
                        try:
                            # serialize result2 to base64 string for safe storage
                            logger.debug(f"Serializing MFA context: {type(result2)}")
                            mfa_context_serialized = base64.b64encode(pickle.dumps(result2)).decode("utf-8")
                            logger.info("MFA context serialized successfully")
                            return {"status": "MFA_REQUIRED", "mfa_context": mfa_context_serialized}
                        except Exception as pickle_error:
                            logger.error(f"Failed to serialize MFA context: {pickle_error}")
                            # Fallback: return MFA_REQUIRED without context (user will need to restart auth)
                            return {"status": "MFA_REQUIRED", "mfa_context": None}

                    # MFA callback available - collect and try to resume immediately
                    mfa_code = mfa_callback()
                    if not mfa_code:
                        logger.warning("MFA code required but not provided by callback")
                        mfa_context_serialized = base64.b64encode(pickle.dumps(result2)).decode("utf-8")
                        return {"status": "MFA_REQUIRED", "mfa_context": mfa_context_serialized}

                    try:
                        garth_sso.resume_login(result2, mfa_code)
                        logger.info("MFA authentication successful")
                    except Exception as e:
                        logger.error(f"MFA authentication failed: {e}")
                        return {"status": "MFA_FAILED"}
                else:
                    logger.info("Direct authentication successful (no MFA required)")

            # Save session on success
            try:
                garth.save(str(garth_session_path))
                logger.info("Garth session saved successfully")
            except Exception as e:
                logger.error(f"Failed to save garth session: {e}")
                # Continue anyway, as we can still authenticate

            self._api = Garmin()
            self._authenticated = True

            try:
                session_data = {
                    "authenticated_at": datetime.now().isoformat(),
                    "email": email,
                    "garth_session_path": str(garth_session_path),
                }
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f)
                logger.info("Session data saved successfully")
            except Exception as e:
                logger.error(f"Failed to save session data: {e}")
                # Continue anyway, authentication was successful

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
