"""Processing Manager for AI Background Remover.

Coordinates Local and Cloud processing backends, manages processing modes
('local', 'cloud', 'automatic'), enforces privacy safeguards, and provides
a unified interface for the GUI and batch processing worker.
"""

from typing import Callable, Optional
from PIL import Image

from app.core.config import ConfigManager
from app.models.registry import ModelRegistry
from app.processing.backends.base import ProcessingBackend
from app.processing.backends.local_backend import LocalBackend
from app.processing.backends.cloud_backend import CloudBackend
from app.system.system_info import SystemInfo
from app.system.recommendation import ModelRecommendationEngine
from app.utils.logger import get_logger

logger = get_logger()


class ProcessingManager:
    """Unified manager orchestrating Local and Cloud backends."""

    def __init__(
        self,
        config_mgr: ConfigManager,
        registry: ModelRegistry,
        sys_info: SystemInfo,
        rec_engine: ModelRecommendationEngine,
        privacy_consent_callback: Optional[Callable[[], bool]] = None
    ):
        self.config_mgr = config_mgr
        self.registry = registry
        self.sys_info = sys_info
        self.rec_engine = rec_engine
        self.privacy_consent_callback = privacy_consent_callback

        # Initialize backends
        device = self.config_mgr.get("execution_device", "CPU").lower()
        self.local_backend = LocalBackend(registry=self.registry, device=device)
        self.cloud_backend = CloudBackend(
            config_mgr=self.config_mgr,
            privacy_consent_callback=self.privacy_consent_callback
        )

        # Mode: 'local', 'cloud', 'automatic'
        self.mode: str = self.config_mgr.get("processing_mode", "local").lower()
        if self.mode not in ("local", "cloud", "automatic"):
            self.mode = "local"

    def set_mode(self, mode: str) -> None:
        """Set processing mode: 'local', 'cloud', or 'automatic'."""
        mode_lower = mode.lower()
        if mode_lower in ("local", "cloud", "automatic"):
            self.mode = mode_lower
            self.config_mgr.set("processing_mode", self.mode)
            self.config_mgr.save()
            logger.info(f"Processing mode set to: '{self.mode.capitalize()}'")
        else:
            raise ValueError(f"Invalid processing mode: {mode}")

    def get_mode(self) -> str:
        """Get current processing mode."""
        return self.mode

    def get_active_backend(self, model_id: Optional[str] = None) -> ProcessingBackend:
        """Resolve the active backend according to current mode and conditions."""
        if self.mode == "local":
            return self.local_backend

        elif self.mode == "cloud":
            return self.cloud_backend

        elif self.mode == "automatic":
            # Intelligent decision heuristic:
            # 1. Check if model is explicitly a cloud model
            if model_id and "cloud" in model_id.lower():
                return self.cloud_backend

            # 2. Check if local model is already installed and system has adequate RAM
            target_model = model_id or "birefnet-portrait"
            meta = self.registry.get_metadata(target_model)

            if meta and meta.installed_status:
                # Local model is installed! Prefer local (free, offline, private)
                return self.local_backend

            # 3. If local model not installed or system RAM is very low (< 4GB)
            # Check if cloud is available and user previously approved or can be prompted
            return self.cloud_backend

        return self.local_backend

    def check_cloud_status(self) -> dict:
        """Check reachability and status of the configured cloud provider."""
        try:
            is_ok, msg = self.cloud_backend.check_connection()
            status_info = self.cloud_backend.get_status()
            status_info["connected"] = is_ok
            status_info["message"] = msg
            return status_info
        except Exception as e:
            return {
                "status": "Offline",
                "connected": False,
                "message": str(e),
                "plan": "Unknown",
                "backend": "Cloud"
            }

    def process_image(
        self,
        image: Image.Image,
        model_id: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image, str]:
        """Process image using the appropriate backend.

        Returns:
            (rgba_image, alpha_mask, backend_name_used)
        """
        backend = self.get_active_backend(model_id)
        rgba_result, mask = backend.process_image(image, model_id, settings)
        return rgba_result, mask, backend.backend_name

    def cancel(self) -> None:
        """Cancel ongoing processing on all backends."""
        self.local_backend.cancel()
        self.cloud_backend.cancel()
