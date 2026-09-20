"""Placeholder for Future Cloud AI Providers.

Follows the CloudProvider interface but remains cleanly disabled with 'Coming soon'
status without executing any fake API calls.
"""

from typing import Optional
from PIL import Image

from app.processing.backends.providers.base_provider import CloudProvider


class FutureProvider(CloudProvider):
    """Stub for upcoming cloud providers (e.g. Replicate, Fal.ai)."""

    def __init__(self, provider_id: str = "future_provider", display_name: str = "Upcoming Cloud Provider"):
        self._provider_id = provider_id
        self._display_name = display_name

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def plan_type(self) -> str:
        return "Coming soon"

    @property
    def requires_authentication(self) -> bool:
        return True

    def test_connection(self) -> tuple[bool, str]:
        return False, f"{self.display_name} integration is currently in development (Coming soon)."

    def get_quota_status(self) -> dict:
        return {
            "provider": self.display_name,
            "plan": "Coming soon",
            "status": "In Development",
            "cost": "N/A",
            "limits": "N/A",
            "requires_internet": True,
        }

    def process_image(
        self,
        image: Image.Image,
        model_id: str,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        raise NotImplementedError(f"{self.display_name} is coming soon and cannot currently process images.")

    def cancel(self) -> None:
        pass
