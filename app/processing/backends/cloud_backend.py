"""Cloud Processing Backend for AI Background Remover.

Manages cloud AI providers (Hugging Face, Custom API), privacy safeguards,
image pre-validation, quota tracking, and error mapping.
"""

from pathlib import Path
from typing import Callable, Optional
from PIL import Image

from app.core.config import ConfigManager
from app.core.credentials import CredentialStore
from app.processing.backends.base import ProcessingBackend
from app.processing.backends.providers.base_provider import CloudProvider
from app.processing.backends.providers.huggingface_provider import HuggingFaceProvider
from app.processing.backends.providers.custom_api_provider import CustomAPIProvider
from app.processing.backends.providers.future_provider import FutureProvider
from app.utils.logger import get_logger

logger = get_logger()


class CloudBackend(ProcessingBackend):
    """Cloud processing backend coordinating multiple cloud AI providers."""

    def __init__(
        self,
        config_mgr: ConfigManager,
        cred_store: Optional[CredentialStore] = None,
        privacy_consent_callback: Optional[Callable[[], bool]] = None
    ):
        self.config_mgr = config_mgr
        self.cred_store = cred_store or CredentialStore()
        self.privacy_consent_callback = privacy_consent_callback

        # Initialize providers
        self.providers: dict[str, CloudProvider] = {
            "huggingface": HuggingFaceProvider(
                endpoint_url=self.config_mgr.get("cloud_endpoint"),
                timeout=self.config_mgr.get("cloud_timeout_seconds", 35),
                credential_store=self.cred_store
            ),
            "custom_api": CustomAPIProvider(
                endpoint_url=self.config_mgr.get("custom_api", {}).get("endpoint", ""),
                auth_header_type=self.config_mgr.get("custom_api", {}).get("auth_header", "Bearer"),
                timeout=self.config_mgr.get("cloud_timeout_seconds", 35),
                credential_store=self.cred_store
            ),
            "replicate": FutureProvider("replicate", "Replicate"),
        }

        active_id = self.config_mgr.get("cloud_provider", "huggingface")
        self.active_provider: CloudProvider = self.providers.get(active_id, self.providers["huggingface"])

    @property
    def backend_name(self) -> str:
        return f"Cloud ({self.active_provider.display_name})"

    @property
    def is_cloud(self) -> bool:
        return True

    def set_provider(self, provider_id: str) -> None:
        """Switch active cloud provider."""
        if provider_id in self.providers:
            self.active_provider = self.providers[provider_id]
            self.config_mgr.set("cloud_provider", provider_id)
            self.config_mgr.save()
            logger.info(f"Switched cloud provider to: '{self.active_provider.display_name}'")
        else:
            raise ValueError(f"Unknown cloud provider: {provider_id}")

    def is_available(self) -> bool:
        """Check if cloud processing can be attempted."""
        return self.active_provider is not None

    def check_connection(self) -> tuple[bool, str]:
        """Verify reachability of the active cloud provider."""
        return self.active_provider.test_connection()

    def get_status(self) -> dict:
        """Return provider status and quota info."""
        status = self.active_provider.get_quota_status()
        status["backend"] = "Cloud"
        status["active_provider_id"] = self.active_provider.provider_id
        return status

    def _validate_image(self, image: Image.Image) -> None:
        """Validate input image dimensions and mode before uploading."""
        if not image or image.size[0] <= 0 or image.size[1] <= 0:
            raise ValueError("Invalid image dimensions (empty or 0-pixel image).")

        # Check maximum dimension guard (e.g. 8192px)
        max_dim = 8192
        if image.size[0] > max_dim or image.size[1] > max_dim:
            raise ValueError(
                f"Image dimensions ({image.size[0]}x{image.size[1]}) exceed cloud maximum limit of {max_dim}px. "
                "Please resize or use Local Processing."
            )

    def process_image(
        self,
        image: Image.Image,
        model_id: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        """Process an image using the active cloud provider with privacy and dimension safeguards."""
        # 1. Privacy Safeguard: Check if consent is needed
        always_ask = self.config_mgr.get("cloud_always_ask_upload", True)
        acknowledged = self.config_mgr.get("cloud_privacy_acknowledged", False)

        if always_ask or not acknowledged:
            if self.privacy_consent_callback:
                user_approved = self.privacy_consent_callback()
                if not user_approved:
                    raise PermissionError(
                        "Cloud processing cancelled by user. Image was NOT uploaded to any third-party server."
                    )
                self.config_mgr.set("cloud_privacy_acknowledged", True)
                self.config_mgr.save()

        # 2. Pre-validate image
        self._validate_image(image)

        target_model = model_id or "birefnet-portrait-cloud"

        # 3. Send to cloud provider
        try:
            rgba_result, mask = self.active_provider.process_image(image, target_model, settings)
            self.config_mgr.record_cloud_request(success=True, quota_status="Normal")
            return rgba_result, mask

        except Exception as e:
            quota_status = "Quota Exhausted" if "429" in str(e) or "quota" in str(e).lower() else "Error"
            self.config_mgr.record_cloud_request(success=False, quota_status=quota_status)
            raise

    def cancel(self) -> None:
        """Cancel ongoing cloud request."""
        self.active_provider.cancel()
