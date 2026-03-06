"""
Common schemas
==============
"""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Generic message response."""

    detail: str
    """Response message."""
