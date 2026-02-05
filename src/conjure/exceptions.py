"""Conjure SDK Exceptions."""


class ConjureError(Exception):
    """Base exception for all Conjure errors."""

    pass


class ConjureAPIError(ConjureError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(ConjureAPIError):
    """Authentication failed - invalid or missing API key."""

    pass


class RateLimitError(ConjureAPIError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ValidationError(ConjureAPIError):
    """Request validation failed."""

    pass


class NotFoundError(ConjureAPIError):
    """Requested resource not found."""

    pass
