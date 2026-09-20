"""Model Metadata Specification for AI Background Remover.

Defines the comprehensive metadata contract required for every AI model in the registry.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.system.system_info import SystemInfo


@dataclass
class ModelMetadata:
    """Complete metadata specification for a background removal model."""
    model_id: str
    display_name: str
    description: str
    category: str  # "Portrait / Hair", "General Objects", "Balanced", "Lightweight"
    version: str
    minimum_ram: float  # In GB
    recommended_ram: float  # In GB
    gpu_requirements: str
    supported_devices: list[str] = field(default_factory=lambda: ["cpu"])
    model_size: str = "~500 MB"
    input_resolution: tuple[int, int] = (1024, 1024)
    download_source: str = ""  # Hugging Face repo ID or direct URL
    checksum: str = ""  # Expected SHA256 or commit hash
    license_information: str = "Open Source"
    installed_status: bool = False

    def compute_compatibility(self, sys_info: "SystemInfo") -> str:
        """Determine system compatibility based on host hardware specs.

        Returns one of: 'Recommended', 'Good', 'Heavy', or 'Unsupported'.
        """
        total_ram = sys_info.ram_total_gb
        avail_ram = sys_info.ram_available_gb
        has_cuda = sys_info.cuda_available

        # Check minimum hardware floor
        if total_ram < self.minimum_ram:
            return "Unsupported (Insufficient RAM)"

        # If model requires GPU and none is present
        if "cuda" in [d.lower() for d in self.supported_devices] and "cpu" not in [d.lower() for d in self.supported_devices] and not has_cuda:
            return "Unsupported (Requires NVIDIA GPU)"

        # Check for High Quality / Heavy models on low RAM
        if self.minimum_ram >= 8.0 and total_ram < 12.0:
            return "Heavy"

        # Check recommended thresholds
        if total_ram >= self.recommended_ram and avail_ram >= (self.minimum_ram * 0.6):
            if self.category in ("Portrait / Hair", "Portrait/Hair") and total_ram >= 14.0:
                return "Recommended"
            if self.category in ("Balanced", "General Objects") and total_ram >= 8.0:
                return "Good"
            return "Good"

        if total_ram >= self.minimum_ram:
            return "Good"

        return "Heavy"

    def to_dict(self) -> dict:
        """Convert metadata to dictionary."""
        return {
            "model_id": self.model_id,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "minimum_ram": self.minimum_ram,
            "recommended_ram": self.recommended_ram,
            "gpu_requirements": self.gpu_requirements,
            "supported_devices": self.supported_devices,
            "model_size": self.model_size,
            "input_resolution": list(self.input_resolution),
            "download_source": self.download_source,
            "checksum": self.checksum,
            "license_information": self.license_information,
            "installed_status": self.installed_status,
        }
