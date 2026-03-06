"""
Jet Delivery Python Wrapper

A Python client library for interacting with the Jet Delivery API.
"""

from .client import JetDeliveryClient
from .exceptions import (
    JetDeliveryError,
    JetDeliveryAPIError,
    JetDeliveryAuthenticationError,
    JetDeliveryNotFoundError,
    JetDeliveryValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "JetDeliveryClient",
    "JetDeliveryError",
    "JetDeliveryAPIError",
    "JetDeliveryAuthenticationError",
    "JetDeliveryNotFoundError",
    "JetDeliveryValidationError",
]