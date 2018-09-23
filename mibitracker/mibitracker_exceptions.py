"""Provides a custom exception for MibiTracker API requests."""

class MibiTrackerError(Exception):
    """Raise for exceptions where the response from the MibiTracker API is
        invalid or unexpected."""
