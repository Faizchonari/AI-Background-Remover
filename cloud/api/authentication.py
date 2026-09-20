"""Cloud API Authentication Validator."""

import hmac
import os
from typing import Optional


def validate_api_token(authorization_header: Optional[str], expected_token: Optional[str] = None) -> bool:
    """Validate Bearer or token from Authorization header.

    If no expected_token is provided, checks environment variable API_SECRET.
    If no secret is configured, authentication is disabled (public access allowed).
    """
    secret = expected_token or os.environ.get("API_SECRET")
    if not secret:
        return True  # No auth required

    if not authorization_header:
        return False

    token = authorization_header
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    return hmac.compare_digest(token, secret)
