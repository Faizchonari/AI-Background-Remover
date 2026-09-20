"""API Schemas for AI Background Remover Cloud Services."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImageRemovalRequest:
    """Request schema for cloud background removal."""
    image_base64: str
    format: str = "PNG"
    preserve_resolution: bool = True
    model_id: str = "birefnet-portrait"


@dataclass
class ImageRemovalResponse:
    """Response schema returned by the background removal API."""
    image_base64: str
    width: int
    height: int
    processing_time_s: float
    model_id: str
    format: str = "PNG"


@dataclass
class ErrorResponse:
    """Error response schema."""
    error: str
    code: int
    message: str
