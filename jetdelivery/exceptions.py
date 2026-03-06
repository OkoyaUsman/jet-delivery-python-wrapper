"""
Custom exceptions for the Jet Delivery API wrapper.
"""


class JetDeliveryError(Exception):
    """Base exception for all Jet Delivery API errors."""

    pass


class JetDeliveryAPIError(JetDeliveryError):
    """Exception raised for API errors."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class JetDeliveryAuthenticationError(JetDeliveryAPIError):
    """Exception raised for authentication errors."""

    pass


class JetDeliveryNotFoundError(JetDeliveryAPIError):
    """Exception raised when a resource is not found."""

    pass


class JetDeliveryValidationError(JetDeliveryAPIError):
    """Exception raised for validation errors."""

    pass