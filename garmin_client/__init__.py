"""
Garmin Connect Client Package.

Provides secure authentication and activity downloading from Garmin Connect
with encrypted credential storage and comprehensive error handling.
"""

from .client import GarminConnectClient

__version__ = "1.0.0"
__all__ = ["GarminConnectClient"]
