"""Provides a custom exception for MibiTracker API requests.

Copyright (C) 2020 Ionpath, Inc.  All rights reserved."""

class MibiTrackerError(Exception):
    """Raise for exceptions where the response from the MibiTracker API is
        invalid or unexpected."""
