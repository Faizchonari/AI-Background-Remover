"""Model Recommendation Engine for AI Background Remover.

Evaluates system hardware capabilities (RAM, CPU cores/threads, GPU, VRAM,
acceleration backends) against configurable model requirement profiles to
recommend the most optimal background removal model and processing device.
"""

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Optional

from app.system.system_info import SystemInfo


@dataclass
class ModelProfile:
    """Specification of an AI model's resource requirements and characteristics."""
    id: str
    name: str
    category: str  # "Lightweight", "Balanced", "High Quality", "Portrait/Hair"
    min_ram_gb: float
    recommended_ram_gb: float
    min_vram_mb: float
    supports_cpu: bool
    cpu_threads_optimal: int
    resolution: str
    complexity: str
    description: str
    reason_template: str


@dataclass
class RecommendationResult:
    """Result returned by the Model Recommendation Engine."""
    recommended_model: str
    model_id: str
    category: str
    reason: str
    recommended_device: str  # "CPU" or "GPU"
    expected_performance: str
    suitable_alternatives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "recommended_model": self.recommended_model,
            "model_id": self.model_id,
            "category": self.category,
            "reason": self.reason,
            "recommended_device": self.recommended_device,
            "expected_performance": self.expected_performance,
            "suitable_alternatives": self.suitable_alternatives,
        }


# Default fallback model profiles if configuration file is not found
DEFAULT_MODEL_PROFILES = [
    ModelProfile(
        id="birefnet-portrait",
        name="BiRefNet Portrait",
        category="Portrait/Hair",
        min_ram_gb=6.0,
        recommended_ram_gb=12.0,
        min_vram_mb=4096,
        supports_cpu=True,
        cpu_threads_optimal=6,
        resolution="1024x1024",
        complexity="medium",
        description="Specialized high-resolution segmentation model optimized for human portraits and fine hair details.",
        reason_template="Suitable for portrait images and available system memory."
    ),
    ModelProfile(
        id="rmbg-1.4",
        name="RMBG-1.4",
        category="Balanced",
        min_ram_gb=4.0,
        recommended_ram_gb=8.0,
        min_vram_mb=2048,
        supports_cpu=True,
        cpu_threads_optimal=6,
        resolution="1024x1024",
        complexity="medium",
        description="General purpose state-of-the-art background remover providing balanced speed and edge precision.",
        reason_template="Optimal balance between processing speed and edge precision for multi-core CPUs."
    ),
    ModelProfile(
        id="birefnet-general",
        name="BiRefNet General",
        category="High Quality",
        min_ram_gb=8.0,
        recommended_ram_gb=16.0,
        min_vram_mb=6144,
        supports_cpu=True,
        cpu_threads_optimal=8,
        resolution="2048x2048",
        complexity="high",
        description="Ultra-high resolution background removal for complex subjects.",
        reason_template="Maximum detail and boundary accuracy for systems with ample memory."
    ),
    ModelProfile(
        id="modnet-mobile",
        name="MODNet Mobile",
        category="Lightweight",
        min_ram_gb=2.0,
        recommended_ram_gb=4.0,
        min_vram_mb=1024,
        supports_cpu=True,
        cpu_threads_optimal=4,
        resolution="512x512",
        complexity="low",
        description="Extremely fast and lightweight matting model designed for rapid processing and low-memory environments.",
        reason_template="Lightweight model selected for fast processing and minimal memory footprint."
    )
]


class ModelRecommendationEngine:
    """Engine that evaluates system hardware against configurable model profiles."""

    def __init__(self, config_path: Optional[str | Path] = None):
        self.profiles: list[ModelProfile] = []
        self.preferences: dict = {
            "prefer_portrait_for_general": True,
            "min_free_ram_headroom_gb": 1.5,
            "cpu_inference_thread_cap": 12,
        }
        self.load_config(config_path)

    def load_config(self, config_path: Optional[str | Path] = None) -> None:
        """Load model profiles from JSON configuration file, or fallback to defaults."""
        if config_path is None:
            # Check default path relative to project root
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = base_dir / "config" / "models.json"

        path = Path(config_path)
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                loaded_profiles = []
                for item in data.get("models", []):
                    loaded_profiles.append(ModelProfile(
                        id=item["id"],
                        name=item["name"],
                        category=item["category"],
                        min_ram_gb=float(item.get("min_ram_gb", 4.0)),
                        recommended_ram_gb=float(item.get("recommended_ram_gb", 8.0)),
                        min_vram_mb=float(item.get("min_vram_mb", 2048)),
                        supports_cpu=bool(item.get("supports_cpu", True)),
                        cpu_threads_optimal=int(item.get("cpu_threads_optimal", 6)),
                        resolution=str(item.get("resolution", "1024x1024")),
                        complexity=str(item.get("complexity", "medium")),
                        description=str(item.get("description", "")),
                        reason_template=str(item.get("reason_template", "Suitable for your hardware configuration."))
                    ))
                
                if loaded_profiles:
                    self.profiles = loaded_profiles
                if "preferences" in data:
                    self.preferences.update(data["preferences"])
                return
            except Exception:
                pass

        # Fallback if file read fails
        self.profiles = list(DEFAULT_MODEL_PROFILES)

    def recommend(self, sys_info: SystemInfo, preferred_category: Optional[str] = None) -> RecommendationResult:
        """Analyze system hardware and recommend the most suitable model and processing device.

        Considers:
        - Available RAM and total RAM
        - GPU vendor, VRAM, and CUDA availability
        - Supported acceleration backend
        - Model memory requirements and resolution
        - Expected CPU multi-threaded throughput
        """
        # Determine recommended processing device
        # NVIDIA GPU with CUDA and >= 4GB VRAM gets GPU recommendation
        # AMD integrated graphics shares system RAM; CPU multi-threading is more reliable and stable
        if sys_info.cuda_available and sys_info.gpu_memory_mb and sys_info.gpu_memory_mb >= 3500:
            rec_device = "GPU"
        else:
            rec_device = "CPU"

        available_ram = sys_info.ram_available_gb
        total_ram = sys_info.ram_total_gb
        vram_mb = sys_info.gpu_memory_mb or 0.0

        # Filter candidates that can run on the target device within memory limits
        compatible_profiles = []
        for p in self.profiles:
            if rec_device == "CPU":
                if not p.supports_cpu:
                    continue
                # System must have at least min_ram_gb total
                if total_ram >= p.min_ram_gb:
                    compatible_profiles.append(p)
            else:  # GPU
                if vram_mb >= p.min_vram_mb:
                    compatible_profiles.append(p)

        if not compatible_profiles:
            # Fallback to lightest available model
            fallback = min(self.profiles, key=lambda x: x.min_ram_gb)
            compatible_profiles = [fallback]

        # If user has a preferred category, prioritize that
        if preferred_category:
            category_matches = [p for p in compatible_profiles if p.category.lower() == preferred_category.lower()]
            if category_matches:
                compatible_profiles = category_matches

        # Selection heuristic based on hardware tier
        selected_profile: ModelProfile
        reason: str
        expected_perf: str

        if rec_device == "GPU":
            if vram_mb >= 6000 and total_ram >= 12.0:
                # High-end GPU
                selected_profile = next((p for p in compatible_profiles if p.category == "High Quality"), compatible_profiles[0])
                reason = f"High-performance GPU with {vram_mb / 1024:.1f} GB VRAM detected for maximum segmentation quality."
                expected_perf = "Very Fast (< 1 second per image on GPU)"
            else:
                # Moderate GPU
                selected_profile = next((p for p in compatible_profiles if p.category in ("Portrait/Hair", "Balanced")), compatible_profiles[0])
                reason = f"GPU acceleration enabled with {vram_mb / 1024:.1f} GB VRAM for responsive processing."
                expected_perf = "Fast (~1-2 seconds per image on GPU)"
        else:
            # CPU Inference Mode (e.g. AMD Ryzen 5 5500U, 16 GB RAM)
            if total_ram >= 12.0 and available_ram >= 4.0:
                # 16 GB system with plenty of RAM
                selected_profile = next((p for p in compatible_profiles if p.category == "Portrait/Hair"), None)
                if not selected_profile:
                    selected_profile = next((p for p in compatible_profiles if p.category == "Balanced"), compatible_profiles[0])
                
                reason = "Suitable for portrait images and available system memory."
                expected_perf = f"Balanced (~2-4 seconds per image on {sys_info.cpu_cores}-core CPU)"
            elif total_ram >= 8.0:
                # 8 GB system
                selected_profile = next((p for p in compatible_profiles if p.category == "Balanced"), compatible_profiles[0])
                reason = "Optimal balance between processing speed and edge precision for multi-core CPUs."
                expected_perf = f"Standard (~3-5 seconds per image on {sys_info.cpu_cores}-core CPU)"
            else:
                # Low RAM system (< 8 GB)
                selected_profile = next((p for p in compatible_profiles if p.category == "Lightweight"), compatible_profiles[0])
                reason = "Lightweight model selected for fast processing and minimal memory footprint."
                expected_perf = "Fast (~1-2 seconds per image on CPU)"

            # Format reason using profile template for CPU if provided
            try:
                formatted_reason = selected_profile.reason_template.format(
                    ram_available=available_ram,
                    ram_total=total_ram,
                    cpu_cores=sys_info.cpu_cores,
                    cpu_threads=sys_info.cpu_threads
                )
                if formatted_reason:
                    reason = formatted_reason
            except Exception:
                pass


        alternatives = [p.name for p in compatible_profiles if p.id != selected_profile.id]

        return RecommendationResult(
            recommended_model=selected_profile.name,
            model_id=selected_profile.id,
            category=selected_profile.category,
            reason=reason,
            recommended_device=rec_device,
            expected_performance=expected_perf,
            suitable_alternatives=alternatives
        )
