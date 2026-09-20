"""Local AI Processing Backend for AI Background Remover.

Runs models locally on CPU, NVIDIA CUDA GPU, or DirectML without any network access.
Maintains 100% offline functionality.
"""

from typing import Optional
from PIL import Image

from app.models.registry import ModelRegistry
from app.models.base_model import BackgroundRemovalModel
from app.models.birefnet_portrait import BiRefNetPortraitModel
from app.processing.backends.base import ProcessingBackend
from app.utils.logger import get_logger

logger = get_logger()


class LocalBackend(ProcessingBackend):
    """Local processing backend using installed AI models and local hardware."""

    def __init__(self, registry: ModelRegistry, device: str = "cpu"):
        self.registry = registry
        self.device = device
        self.active_model: Optional[BackgroundRemovalModel] = None
        self._cancel_requested = False

    @property
    def backend_name(self) -> str:
        return "Local Processing"

    @property
    def is_cloud(self) -> bool:
        return False

    def is_available(self) -> bool:
        """Local backend is available if at least one model is registered."""
        return len(self.registry.list_all()) > 0

    def check_connection(self) -> tuple[bool, str]:
        """Local backend is always connected (no network needed)."""
        installed = self.registry.get_installed()
        if installed:
            return True, f"Local hardware ready. {len(installed)} model(s) installed."
        return True, "Local hardware ready (models can be downloaded via Model Manager)."

    def get_status(self) -> dict:
        installed = self.registry.get_installed()
        return {
            "status": "Ready",
            "backend": "Local",
            "device": self.device,
            "installed_models": len(installed),
            "plan": "Free (Local Offline)",
            "requires_internet": False,
        }

    def set_device(self, device: str) -> None:
        """Update inference device ('cpu', 'cuda', etc.)."""
        if self.device != device:
            self.device = device
            if self.active_model and self.active_model.is_loaded:
                logger.info(f"Switching local model device to '{device}'...")
                self.active_model.load(device)

    def load_model(self, model_id: str) -> BackgroundRemovalModel:
        """Load or retrieve the active model instance."""
        if self.active_model is not None and self.active_model.metadata.model_id == model_id:
            if not self.active_model.is_loaded:
                self.active_model.load(self.device)
            return self.active_model

        # Unload previous model
        if self.active_model is not None:
            self.active_model.unload()
            self.active_model = None

        meta = self.registry.get_metadata(model_id)
        if not meta:
            raise ValueError(f"Unknown model ID: {model_id}")

        model_cls = self.registry.get_model_class(model_id)
        if model_cls:
            self.active_model = model_cls(metadata=meta, device=self.device)
        else:
            # Fallback to BiRefNet Portrait
            self.active_model = BiRefNetPortraitModel(metadata=meta, device=self.device)

        self.active_model.load(self.device)
        return self.active_model

    def process_image(
        self,
        image: Image.Image,
        model_id: Optional[str] = None,
        settings: Optional[dict] = None
    ) -> tuple[Image.Image, Image.Image]:
        """Run local AI inference on a single image."""
        self._cancel_requested = False
        target_model_id = model_id or "birefnet-portrait"

        model = self.load_model(target_model_id)

        if self._cancel_requested:
            raise RuntimeError("Processing cancelled by user.")

        orig_w, orig_h = image.size
        orig_rgb = image.convert("RGB")

        rgba_result, mask = model.process_image(orig_rgb)

        # Strictly enforce original dimensions
        if rgba_result.size != (orig_w, orig_h):
            rgba_result = rgba_result.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
        if mask.size != (orig_w, orig_h):
            mask = mask.resize((orig_w, orig_h), Image.Resampling.BILINEAR)

        return rgba_result, mask

    def cancel(self) -> None:
        """Cancel current processing."""
        self._cancel_requested = True

    def unload(self) -> None:
        """Unload active model from memory."""
        if self.active_model:
            self.active_model.unload()
            self.active_model = None
