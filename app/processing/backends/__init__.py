"""Backends package for AI Background Remover."""

from app.processing.backends.base import ProcessingBackend
from app.processing.backends.local_backend import LocalBackend
from app.processing.backends.cloud_backend import CloudBackend

__all__ = [
    "ProcessingBackend",
    "LocalBackend",
    "CloudBackend",
]
