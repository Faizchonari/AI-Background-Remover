"""Central Model Registry for AI Background Remover.

Manages registration, discovery, metadata retrieval, installation status,
and factory instantiation of background removal AI models.
"""

import json
from pathlib import Path
import shutil
import sys
from typing import Optional, Type

from app.models.metadata import ModelMetadata
from app.models.base_model import BackgroundRemovalModel


class ModelRegistry:
    """Central registry system for all AI background removal models."""

    def __init__(self, storage_dir: Optional[str | Path] = None):
        if storage_dir is None:
            if getattr(sys, "frozen", False):
                base_dir = Path(sys.executable).resolve().parent
            else:
                base_dir = Path(__file__).resolve().parent.parent.parent
            self.storage_dir = base_dir / "model_storage"
        else:
            self.storage_dir = Path(storage_dir)

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, ModelMetadata] = {}
        self._factories: dict[str, Type[BackgroundRemovalModel]] = {}

        # Register standard known models (local and cloud)
        self._register_default_models()
        self._register_cloud_models()
        self.refresh_installed_status()

    def _register_default_models(self):
        """Register the built-in model definitions."""
        # 1. BiRefNet Portrait (First implemented model)
        self.register(
            metadata=ModelMetadata(
                model_id="birefnet-portrait",
                display_name="BiRefNet Portrait",
                description="Specialized high-resolution segmentation model optimized for human portraits, fine hair strands, and transparent fabric.",
                category="Portrait / Hair",
                version="1.0.0",
                minimum_ram=6.0,
                recommended_ram=12.0,
                gpu_requirements="Optional: 4GB+ VRAM for CUDA. Fully supports multi-threaded CPU inference.",
                supported_devices=["cpu", "cuda", "directml"],
                model_size="~950 MB",
                input_resolution=(1024, 1024),
                download_source="ZhengPeng7/BiRefNet-portrait",
                checksum="sha256:birefnet_portrait_weights_v1",
                license_information="Apache 2.0",
                installed_status=False
            )
        )

        # 2. BiRefNet General
        self.register(
            metadata=ModelMetadata(
                model_id="birefnet-general",
                display_name="BiRefNet General",
                description="Ultra-high resolution background removal for general objects, commercial products, animals, and complex backgrounds.",
                category="General Objects",
                version="1.0.0",
                minimum_ram=8.0,
                recommended_ram=16.0,
                gpu_requirements="Recommended: 6GB+ VRAM for GPU, or 16GB RAM for CPU inference.",
                supported_devices=["cpu", "cuda"],
                model_size="~950 MB",
                input_resolution=(2048, 2048),
                download_source="ZhengPeng7/BiRefNet-general",
                checksum="sha256:birefnet_general_weights_v1",
                license_information="Apache 2.0",
                installed_status=False
            )
        )

        # 3. RMBG-1.4
        self.register(
            metadata=ModelMetadata(
                model_id="rmbg-1.4",
                display_name="RMBG-1.4",
                description="State-of-the-art balanced background removal model providing rapid inference speed and excellent edge boundaries.",
                category="Balanced",
                version="1.4.0",
                minimum_ram=4.0,
                recommended_ram=8.0,
                gpu_requirements="Optional: 2GB+ VRAM. Excellent performance on multi-core CPUs.",
                supported_devices=["cpu", "cuda", "directml"],
                model_size="~176 MB",
                input_resolution=(1024, 1024),
                download_source="briaai/RMBG-1.4",
                checksum="sha256:rmbg_1_4_weights",
                license_information="Creative Commons (Non-Commercial)",
                installed_status=False
            )
        )

        # 4. BiRefNet Lite
        self.register(
            metadata=ModelMetadata(
                model_id="birefnet-lite",
                display_name="BiRefNet Lite",
                description="Compact and fast segmentation model tailored for lower-resource systems, laptops, and rapid batch processing.",
                category="Lightweight",
                version="1.0.0",
                minimum_ram=2.0,
                recommended_ram=4.0,
                gpu_requirements="Runs comfortably on CPU without dedicated GPU.",
                supported_devices=["cpu"],
                model_size="~120 MB",
                input_resolution=(512, 512),
                download_source="ZhengPeng7/BiRefNet-lite",
                checksum="sha256:birefnet_lite_weights_v1",
                license_information="Apache 2.0",
                installed_status=False
            )
        )

    def _register_cloud_models(self):
        """Load and register cloud models from config/cloud_providers.json."""
        config_path = Path(__file__).resolve().parent.parent.parent / "config" / "cloud_providers.json"
        if not config_path.is_file():
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            provider_endpoints = {
                p.get("provider_id"): p.get("default_endpoint", "")
                for p in data.get("providers", [])
            }

            for cm in data.get("cloud_models", []):
                p_id = cm.get("provider_id", "huggingface")
                def_endpoint = provider_endpoints.get(p_id, "")
                endpoint_val = cm.get("endpoint_url") or def_endpoint or cm.get("endpoint_configuration", {}).get("api_name", "/predict")

                meta = ModelMetadata(
                    model_id=cm["model_id"],
                    display_name=cm["display_name"],
                    description=cm.get("description", ""),
                    category=cm.get("category", "Portrait / Hair"),
                    version=cm.get("version", "1.0.0"),
                    minimum_ram=0.0,
                    recommended_ram=0.0,
                    gpu_requirements="Runs on remote cloud GPU.",
                    supported_devices=cm.get("supported_devices", ["Cloud GPU"]),
                    model_size=cm.get("model_size", "Remote"),
                    input_resolution=(1024, 1024),
                    download_source="",
                    checksum="",
                    license_information=cm.get("license", "Open Source"),
                    installed_status=True,
                    local_or_cloud="cloud",
                    provider=cm.get("provider", "Hugging Face"),
                    cloud_endpoint=endpoint_val,
                    requires_internet=cm.get("internet_required", True),
                    requires_authentication=cm.get("requires_authentication", False),
                    privacy_information=cm.get("privacy_information", ""),
                    free_available=cm.get("free_available", True),
                )
                self.register(meta)
        except Exception:
            pass

    def register(
        self,
        metadata: ModelMetadata,
        model_class: Optional[Type[BackgroundRemovalModel]] = None
    ) -> None:
        """Register a model with its metadata and optional implementation class."""
        self._registry[metadata.model_id] = metadata
        if model_class:
            self._factories[metadata.model_id] = model_class
        self._check_installed(metadata.model_id)

    def get_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Retrieve metadata for a registered model."""
        return self._registry.get(model_id)

    def get_model_class(self, model_id: str) -> Optional[Type[BackgroundRemovalModel]]:
        """Retrieve implementation class for a model."""
        return self._factories.get(model_id)

    def list_all(self) -> list[ModelMetadata]:
        """Return list of all registered models."""
        return list(self._registry.values())

    def list_local(self) -> list[ModelMetadata]:
        """Return list of all local models."""
        return [m for m in self._registry.values() if m.local_or_cloud == "local"]

    def list_cloud(self) -> list[ModelMetadata]:
        """Return list of all cloud models."""
        return [m for m in self._registry.values() if m.local_or_cloud == "cloud"]

    def is_cloud_model(self, model_id: str) -> bool:
        """Check if a model ID corresponds to a cloud model."""
        meta = self._registry.get(model_id)
        return meta is not None and meta.local_or_cloud == "cloud"

    def list_by_category(self, category: str) -> list[ModelMetadata]:
        """Return models belonging to a specific category."""
        return [m for m in self._registry.values() if m.category.lower() == category.lower()]

    def get_installed(self) -> list[ModelMetadata]:
        """Return models currently downloaded and ready to use (excluding cloud models)."""
        self.refresh_installed_status()
        return [m for m in self._registry.values() if m.installed_status and m.local_or_cloud == "local"]

    def _check_installed(self, model_id: str) -> bool:
        """Check if model files exist in local storage (or is cloud model)."""
        meta = self._registry.get(model_id)
        if meta and meta.local_or_cloud == "cloud":
            meta.installed_status = True
            return True

        model_dir = self.storage_dir / model_id
        is_installed = False
        if model_dir.is_dir():
            # Model is considered installed if directory exists and contains files
            files = [f for f in model_dir.iterdir() if f.is_file()]
            is_installed = len(files) > 0

        if meta:
            meta.installed_status = is_installed
        return is_installed

    def refresh_installed_status(self) -> None:
        """Refresh installed status for all registered models."""
        for model_id in self._registry:
            self._check_installed(model_id)

    def delete_model(self, model_id: str) -> bool:
        """Delete downloaded model files from local storage."""
        meta = self._registry.get(model_id)
        if meta and meta.local_or_cloud == "cloud":
            return False  # Cloud models cannot be deleted from disk

        model_dir = self.storage_dir / model_id
        if model_dir.is_dir():
            try:
                shutil.rmtree(model_dir)
                if meta:
                    meta.installed_status = False
                return True
            except Exception:
                return False
        return False
