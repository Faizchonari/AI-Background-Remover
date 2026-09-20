"""Abstract Cloud Provider Interface for AI Background Remover.

Defines the contract that every cloud AI provider (Hugging Face, Custom API, etc.)
must satisfy.
"""

from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image


class CloudProvider(ABC):
    """Abstract interface for a specific cloud AI provider."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Machine identifier (e.g. 'huggingface', 'custom_api')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name (e.g. 'Hugging Face Spaces')."""
        pass

    @property
    @abstractmethod
    def plan_type(self) -> str:
        """Plan type: 'Free', 'Limited Free', 'Paid', or 'User Configured'."""
        pass

    @property
    @abstractmethod
    def requires_authentication(self) -> bool:
        """Whether this provider requires an API token."""
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        """Test reachability and authentication with the cloud provider.

        Returns:
            (is_ok: bool, message: str)
        """
        pass

    @abstractmethod
    def get_quota_status(self) -> dict:
        """Return provider quota/usage information."""
        pass

    @abstractmethod
    def process_image(
        self,
        image: Image.Image,
        model_id: str,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        """Send image to the cloud provider, receive result, and return (rgba_image, alpha_mask).

        Requirements:
        - Must preserve original image resolution.
        - Must raise specific descriptive exceptions on failure (network, 401, 429, 500, etc.).
        """
        pass

    @abstractmethod
    def cancel(self) -> None:
        """Cancel ongoing cloud request if supported."""
        pass
