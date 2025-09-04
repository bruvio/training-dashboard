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
                oauth1_file = garth_session_path / "oauth1_token.json"
                oauth2_file = garth_session_path / "oauth2_token.json"

                # Check if the session directory has the expected structure
                if garth_session_path.is_dir():
                    # Try to validate oauth1 file if it exists
                    if oauth1_file.exists():
                        try:
                            with open(oauth1_file, "r") as f:
                                oauth1_content = f.read().strip()
                                if not oauth1_content:
                                    logger.warning("OAuth1 token file is empty")
                                else:
                                    # Try to parse as JSON - garth might store different formats
                                    try:
                                        oauth1_data = json.loads(oauth1_content)
                                        # Accept both dict and string formats
                                        if isinstance(oauth1_data, (dict, str)) and oauth1_data:
                                            session_valid = True
                                            logger.debug(f"Valid OAuth1 token file found (type: {type(oauth1_data).__name__})")
                                        else:
                                            logger.warning(f"OAuth1 file contains invalid data: {oauth1_data}")
                                    except json.JSONDecodeError:
                                        # If it's not valid JSON but has content, it might be a plain token string
                                        if len(oauth1_content) > 10:  # Reasonable token length
                                            session_valid = True
                                            logger.debug("OAuth1 token file contains non-JSON token string")
                                        else:
                                            logger.warning(f"OAuth1 file contains invalid content: {oauth1_content[:50]}")
                        except Exception as e:
                            logger.warning(f"Error reading OAuth1 token file: {e}")
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

        # Clean up corrupted or invalid session files - but only if they're genuinely old or corrupted
        if not session_valid and garth_session_path.exists():
            try:
                # Check session age before cleanup to avoid removing potentially valid recent sessions
                session_age_hours = 0
                if self.session_file.exists():
                    with open(self.session_file, "r") as f:
                        session_data = json.load(f)
                        auth_time_str = session_data.get("authenticated_at")
                        if auth_time_str:
                            auth_time = datetime.fromisoformat(auth_time_str)
                            session_age_hours = (datetime.now() - auth_time).total_seconds() / 3600

                # Only clean up if session is older than 2 hours to avoid removing fresh sessions
                if session_age_hours > 2:
                    import shutil
                    shutil.rmtree(garth_session_path, ignore_errors=True)
                    logger.info(f"Cleaned up old session files (age: {session_age_hours:.1f}h)")
                else:
                    logger.info(f"Preserving recent session files (age: {session_age_hours:.1f}h) - garth may still be able to use them")
            except Exception as cleanup_error:
                logger.warning(f"Could not assess session age for cleanup: {cleanup_error}")

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

            # Try to save session - handle failures gracefully
            session_saved = False
            try:
                garth.save(str(garth_session_path))
                logger.info("Garth session saved successfully")
                session_saved = True
            except (TypeError, ValueError) as e:
                # Common serialization errors - these are non-fatal
                logger.warning(f"Garth session save failed (serialization issue): {e}")
                logger.info("Will use credential-based authentication for future sessions")
            except Exception as e:
                logger.warning(f"Failed to save garth session: {e}")
                logger.info("Will use credential-based authentication for future sessions")

            self._api = Garmin()
            self._authenticated = True

            try:
                session_data = {
                    "authenticated_at": datetime.now().isoformat(),
                    "email": email,
                    "garth_session_path": str(garth_session_path),
                    "garth_session_saved": session_saved,
                }
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f)
                logger.info("Session data saved successfully")
            except Exception as e:
                logger.warning(f"Failed to save session data: {e}")
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

    def is_authenticated(self) -> bool:
        """
        Check if client is currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated and self._api is not None

    def validate_session(self) -> bool:
        """
        Validate if a saved garth session exists and is valid.

        Returns:
            True if valid session exists, False otherwise
        """
        garth_session_path = self.config_dir / "garth_session"

        if not garth_session_path.exists():
            return False

        try:
            # Check if the session directory has the expected structure
            oauth1_file = garth_session_path / "oauth1_token.json"
            oauth2_file = garth_session_path / "oauth2_token.json"

            if not garth_session_path.is_dir():
                logger.warning("Session path exists but is not a directory")
                return False

            # Check for OAuth1 token file
            if oauth1_file.exists():
                try:
                    with open(oauth1_file, "r") as f:
                        oauth1_content = f.read().strip()
                        if not oauth1_content:
                            logger.warning("OAuth1 token file is empty")
                            return False
                        
                        # Try to parse as JSON - garth might store different formats
                        try:
                            oauth1_data = json.loads(oauth1_content)
                            # Accept both dict and string formats
                            if isinstance(oauth1_data, (dict, str)) and oauth1_data:
                                logger.debug(f"Valid OAuth1 token file found (type: {type(oauth1_data).__name__})")
                            else:
                                logger.warning(f"OAuth1 file contains invalid data: {oauth1_data}")
                                return False
                        except json.JSONDecodeError:
                            # If it's not valid JSON but has content, it might be a plain token string
                            if len(oauth1_content) > 10:  # Reasonable token length
                                logger.debug("OAuth1 token file contains non-JSON token string")
                            else:
                                logger.warning(f"OAuth1 file contains invalid content: {oauth1_content[:50]}")
                                return False
                except Exception as e:
                    logger.warning(f"Error reading OAuth1 token file: {e}")
                    return False
            else:
                logger.info("No OAuth1 token file found in session")
                return False

            # Check for OAuth2 token file  
            if oauth2_file.exists():
                try:
                    with open(oauth2_file, "r") as f:
                        oauth2_content = f.read().strip()
                        if not oauth2_content:
                            logger.warning("OAuth2 token file is empty")
                            return False
                        
                        # Try to parse as JSON - garth might store different formats
                        try:
                            oauth2_data = json.loads(oauth2_content)
                            # Accept both dict and string formats
                            if isinstance(oauth2_data, (dict, str)) and oauth2_data:
                                logger.debug(f"Valid OAuth2 token file found (type: {type(oauth2_data).__name__})")
                            else:
                                logger.warning(f"OAuth2 file contains invalid data: {oauth2_data}")
                                return False
                        except json.JSONDecodeError:
                            # If it's not valid JSON but has content, it might be a plain token string
                            if len(oauth2_content) > 10:  # Reasonable token length
                                logger.debug("OAuth2 token file contains non-JSON token string")
                            else:
                                logger.warning(f"OAuth2 file contains invalid content: {oauth2_content[:50]}")
                                return False
                except Exception as e:
                    logger.warning(f"Error reading OAuth2 token file: {e}")
                    return False
            else:
                logger.info("No OAuth2 token file found in session")
                return False

            return True

        except (json.JSONDecodeError, FileNotFoundError, TypeError, ValueError) as e:
            logger.warning(f"Session validation failed: {e}")
            return False

    def restore_session(self) -> Dict[str, str]:
        """
        Try to restore authentication from saved garth session.

        Returns:
            Dict with status and optional message:
                {"status": "SUCCESS"} -> Session restored successfully
                {"status": "NO_SESSION"} -> No valid session found
                {"status": "FAILED"} -> Session restoration failed
        """
        if not GARMIN_CONNECT_AVAILABLE:
            return {"status": "FAILED", "message": "Garmin Connect library not available"}

        garth_session_path = self.config_dir / "garth_session"

        # First check if we have any session data at all
        if not self.session_file.exists():
            return {"status": "NO_SESSION", "message": "No session file found"}

        # Check if we have valid garth session files (regardless of save flag)
        # This is more reliable than trusting the save flag since garth might 
        # create files even when save() reports an error
        garth_session_valid = self.validate_session()
        if not garth_session_valid:
            logger.info("No valid garth session files found")
            
            # Try credential-based restoration as fallback
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                email = session_data.get("email")
                
                if email and self.credentials_file.exists():
                    logger.info("Attempting credential-based authentication")
                    credentials = self.load_credentials()
                    if credentials:
                        # Re-authenticate using stored credentials
                        auth_result = self.authenticate(
                            credentials["email"],
                            credentials["password"], 
                            remember_me=True
                        )
                        if auth_result["status"] == "SUCCESS":
                            logger.info("Successfully authenticated using stored credentials")
                            return {"status": "SUCCESS", "message": "Session restored via stored credentials"}
                        elif auth_result["status"] == "MFA_REQUIRED":
                            logger.info("MFA required for credential-based authentication")
                            return {"status": "NO_SESSION", "message": "MFA required - please login"}
            except Exception as cred_error:
                logger.info(f"Credential-based restoration failed: {cred_error}")
            
            return {"status": "NO_SESSION", "message": "No valid session available"}

        try:
            # Ensure the session directory exists before attempting resume
            if not garth_session_path.exists():
                logger.warning(f"Garth session directory does not exist: {garth_session_path}")
                return {"status": "NO_SESSION", "message": "Session directory not found"}

            garth.resume(str(garth_session_path))
            logger.info("Successfully resumed garth session")

            self._api = Garmin()
            self._authenticated = True

            # Update session data
            try:
                session_data = {
                    "restored_at": datetime.now().isoformat(),
                    "garth_session_path": str(garth_session_path),
                }
                with open(self.session_file, "w") as f:
                    json.dump(session_data, f)
                logger.info("Session data updated after restoration")
            except Exception as e:
                logger.warning(f"Failed to update session data: {e}")
                # Continue anyway, session restoration was successful

            return {"status": "SUCCESS", "message": "Session restored successfully"}

        except (
            GarthException,
            FileNotFoundError,
            json.JSONDecodeError,
            NotADirectoryError,
            TypeError,
            ValueError,
        ) as e:
            logger.info(f"Session restoration failed: {e}")

            # Don't clean up session files immediately - they might be valid for garth even if we can't read them
            # Only clean up if the session is genuinely corrupted (e.g., very old or completely invalid)
            try:
                session_age_hours = 0
                if self.session_file.exists():
                    with open(self.session_file, "r") as f:
                        session_data = json.load(f)
                        auth_time_str = session_data.get("authenticated_at")
                        if auth_time_str:
                            auth_time = datetime.fromisoformat(auth_time_str)
                            session_age_hours = (datetime.now() - auth_time).total_seconds() / 3600
                
                # Only clean up if session is older than 1 hour or truly corrupted
                if session_age_hours > 1 or "corrupted" in str(e).lower():
                    import shutil
                    shutil.rmtree(garth_session_path, ignore_errors=True)
                    logger.info(f"Cleaned up old session files (age: {session_age_hours:.1f}h)")
                else:
                    logger.info(f"Preserving recent session files (age: {session_age_hours:.1f}h) - garth may still be able to use them")
                    
            except Exception as cleanup_error:
                logger.warning(f"Could not assess session age for cleanup: {cleanup_error}")

            # Try credential-based fallback before giving up completely
            if self.credentials_file.exists():
                try:
                    logger.info("Attempting credential-based fallback after garth session failure")
                    credentials = self.load_credentials()
                    if credentials:
                        auth_result = self.authenticate(
                            credentials["email"], 
                            credentials["password"],
                            remember_me=True
                        )
                        if auth_result["status"] == "SUCCESS":
                            logger.info("Successfully recovered using stored credentials")
                            return {"status": "SUCCESS", "message": "Session restored via stored credentials"}
                        elif auth_result["status"] == "MFA_REQUIRED":
                            logger.info("MFA required for credential recovery")
                            return {"status": "NO_SESSION", "message": "MFA required - please login"}
                except Exception as cred_error:
                    logger.info(f"Credential-based fallback failed: {cred_error}")

            self._authenticated = False
            return {"status": "FAILED", "message": f"Session restoration failed: {str(e)}"}

    def get_session_info(self) -> Dict[str, any]:
        """
        Get information about the current session.

        Returns:
            Dictionary with session information
        """
        session_info = {
            "authenticated": self._authenticated,
            "has_api": self._api is not None,
            "session_file_exists": self.session_file.exists(),
            "garth_session_exists": (self.config_dir / "garth_session").exists(),
        }

        # Add session file data if it exists
        if self.session_file.exists():
            try:
                with open(self.session_file, "r") as f:
                    session_data = json.load(f)
                    session_info.update(session_data)
            except Exception as e:
                session_info["session_file_error"] = str(e)

        return session_info


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
