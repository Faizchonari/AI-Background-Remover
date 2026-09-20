"""Abstract Processing Backend Interface for AI Background Remover.

Defines the contract that every processing backend (Local or Cloud) must satisfy.
Enables transparent switching between local AI inference and cloud-based AI inference
without modifying the rest of the application.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
from PIL import Image


class ProcessingBackend(ABC):
    """Abstract interface for all processing backends (Local and Cloud)."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return human-readable backend name (e.g. 'Local Processing', 'Cloud Processing')."""
        pass

    @property
    @abstractmethod
    def is_cloud(self) -> bool:
        """Return True if this is a cloud-based backend."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is currently available for processing."""
        pass

    @abstractmethod
    def check_connection(self) -> tuple[bool, str]:
        """Verify connectivity (local hardware readiness or cloud endpoint reachability).

        Returns:
            (is_ok: bool, message: str)
        """
        pass

    @abstractmethod
    def get_status(self) -> dict:
        """Return current status dictionary containing status, provider, plan, and quota info."""
        pass

    @abstractmethod
    def process_image(
        self,
        image: Image.Image,
        model_id: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        """Process a single PIL Image.

        Requirements:
        - Must preserve the exact original image resolution.
        - Must return a tuple: (transparent_rgba_image, alpha_mask).
        - Must handle cancellation and raise appropriate errors on failure.
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Request immediate cancellation of the ongoing processing."""
        pass
