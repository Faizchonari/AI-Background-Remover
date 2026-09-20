"""Unit tests for Model Recommendation Engine."""

import unittest
from app.system.system_info import SystemInfo
from app.system.recommendation import (
    ModelRecommendationEngine,
    RecommendationResult,
    ModelProfile
)


class TestModelRecommendationEngine(unittest.TestCase):
    """Test suite for hardware-aware model recommendation engine."""

    def setUp(self):
        self.engine = ModelRecommendationEngine()

    def test_ryzen_5500u_target_hardware_profile(self):
        """Test user's target hardware: AMD Ryzen 5 5500U, 16GB RAM, integrated graphics, no CUDA."""
        sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 11 (Build 22631)",
            architecture="64-bit",
            cpu_name="AMD Ryzen 5 5500U with Radeon Graphics",
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_mhz=2100.0,
            ram_total_gb=16.0,
            ram_available_gb=8.5,
            gpu_name="AMD Radeon Graphics",
            gpu_vendor="AMD",
            gpu_memory_mb=512.0,
            cuda_available=False,
            amd_acceleration_available=True,
            acceleration_backend="DirectML / OpenCL (AMD Radeon)",
            current_device="CPU"
        )

        result: RecommendationResult = self.engine.recommend(sys_info)

        self.assertEqual(result.recommended_device, "CPU")
        self.assertEqual(result.recommended_model, "BiRefNet Portrait")
        self.assertEqual(result.category, "Portrait/Hair")
        self.assertIn("portrait", result.reason.lower())
        self.assertIn("memory", result.reason.lower())
        self.assertIn("CPU", result.expected_performance)

    def test_low_ram_system_profile(self):
        """Test resource-constrained system: 4GB RAM, dual-core CPU, no GPU."""
        sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 10",
            architecture="64-bit",
            cpu_name="Intel Core i3-7100U",
            cpu_cores=2,
            cpu_threads=4,
            cpu_frequency_mhz=2400.0,
            ram_total_gb=4.0,
            ram_available_gb=1.8,
            gpu_name="Intel HD Graphics 620",
            gpu_vendor="Intel",
            gpu_memory_mb=128.0,
            cuda_available=False,
            amd_acceleration_available=False,
            acceleration_backend="CPU (PyTorch multi-threading)",
            current_device="CPU"
        )

        result: RecommendationResult = self.engine.recommend(sys_info)

        self.assertEqual(result.recommended_device, "CPU")
        self.assertEqual(result.recommended_model, "MODNet Mobile")
        self.assertEqual(result.category, "Lightweight")
        self.assertIn("lightweight", result.reason.lower())

    def test_nvidia_cuda_high_end_profile(self):
        """Test high-end GPU system: RTX 4070, 12GB VRAM, CUDA available."""
        sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 11",
            architecture="64-bit",
            cpu_name="AMD Ryzen 7 7800X3D",
            cpu_cores=8,
            cpu_threads=16,
            cpu_frequency_mhz=4200.0,
            ram_total_gb=32.0,
            ram_available_gb=24.0,
            gpu_name="NVIDIA GeForce RTX 4070",
            gpu_vendor="NVIDIA",
            gpu_memory_mb=12288.0,
            cuda_available=True,
            amd_acceleration_available=False,
            acceleration_backend="CUDA (NVIDIA Acceleration)",
            current_device="GPU"
        )

        result: RecommendationResult = self.engine.recommend(sys_info)

        self.assertEqual(result.recommended_device, "GPU")
        self.assertEqual(result.category, "High Quality")
        self.assertEqual(result.recommended_model, "BiRefNet General")
        self.assertIn("GPU", result.reason)

    def test_nvidia_cuda_entry_level_profile(self):
        """Test entry-level NVIDIA GPU: GTX 1650, 4GB VRAM, CUDA available."""
        sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 11",
            architecture="64-bit",
            cpu_name="Intel Core i5-10400F",
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_mhz=2900.0,
            ram_total_gb=16.0,
            ram_available_gb=10.0,
            gpu_name="NVIDIA GeForce GTX 1650",
            gpu_vendor="NVIDIA",
            gpu_memory_mb=4096.0,
            cuda_available=True,
            amd_acceleration_available=False,
            acceleration_backend="CUDA (NVIDIA Acceleration)",
            current_device="GPU"
        )

        result: RecommendationResult = self.engine.recommend(sys_info)

        self.assertEqual(result.recommended_device, "GPU")
        self.assertIn(result.category, ("Portrait/Hair", "Balanced"))

    def test_configurable_profiles_can_be_added(self):
        """Verify that recommendation rules are configurable and support adding new models."""
        custom_profile = ModelProfile(
            id="custom-model-2026",
            name="Custom Future Model",
            category="High Quality",
            min_ram_gb=2.0,
            recommended_ram_gb=4.0,
            min_vram_mb=1024,
            supports_cpu=True,
            cpu_threads_optimal=4,
            resolution="4096x4096",
            complexity="ultra",
            description="Next generation model.",
            reason_template="Custom recommendation reason for {ram_total:.0f} GB."
        )

        engine = ModelRecommendationEngine()
        engine.profiles.insert(0, custom_profile)

        sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 11",
            architecture="64-bit",
            cpu_name="AMD Ryzen 5 5500U",
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_mhz=2100.0,
            ram_total_gb=16.0,
            ram_available_gb=10.0,
            gpu_name="AMD Radeon Graphics",
            gpu_vendor="AMD",
            gpu_memory_mb=512.0,
            cuda_available=False,
            amd_acceleration_available=True,
            acceleration_backend="CPU",
            current_device="CPU"
        )

        # Force requesting High Quality category
        result = engine.recommend(sys_info, preferred_category="High Quality")
        self.assertEqual(result.recommended_model, "Custom Future Model")


if __name__ == "__main__":
    unittest.main()
