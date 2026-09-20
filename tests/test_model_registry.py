"""Unit tests for Model Registry and Metadata System."""

import tempfile
import unittest
from pathlib import Path

from app.models.metadata import ModelMetadata
from app.models.registry import ModelRegistry
from app.system.system_info import SystemInfo


class TestModelRegistry(unittest.TestCase):
    """Test suite for Model Registry and Metadata contract."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = ModelRegistry(storage_dir=self.temp_dir.name)
        self.mock_sys_info = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 11",
            architecture="64-bit",
            cpu_name="AMD Ryzen 5 5500U with Radeon Graphics",
            cpu_cores=6,
            cpu_threads=12,
            cpu_frequency_mhz=2100.0,
            ram_total_gb=16.0,
            ram_available_gb=8.0,
            gpu_name="AMD Radeon Graphics",
            gpu_vendor="AMD",
            gpu_memory_mb=512.0,
            cuda_available=False,
            amd_acceleration_available=True,
            acceleration_backend="CPU",
            current_device="CPU"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_models_registered(self):
        """Verify default models exist in registry."""
        models = self.registry.list_all()
        model_ids = [m.model_id for m in models]
        self.assertIn("birefnet-portrait", model_ids)
        self.assertIn("birefnet-general", model_ids)
        self.assertIn("rmbg-1.4", model_ids)
        self.assertIn("birefnet-lite", model_ids)

    def test_all_15_metadata_fields_present(self):
        """Verify all 15 required metadata fields are properly populated."""
        meta = self.registry.get_metadata("birefnet-portrait")
        self.assertIsNotNone(meta)

        self.assertIsInstance(meta.model_id, str)
        self.assertIsInstance(meta.display_name, str)
        self.assertIsInstance(meta.description, str)
        self.assertIsInstance(meta.category, str)
        self.assertIsInstance(meta.version, str)
        self.assertIsInstance(meta.minimum_ram, float)
        self.assertIsInstance(meta.recommended_ram, float)
        self.assertIsInstance(meta.gpu_requirements, str)
        self.assertIsInstance(meta.supported_devices, list)
        self.assertIsInstance(meta.model_size, str)
        self.assertIsInstance(meta.input_resolution, tuple)
        self.assertEqual(len(meta.input_resolution), 2)
        self.assertIsInstance(meta.download_source, str)
        self.assertIsInstance(meta.checksum, str)
        self.assertIsInstance(meta.license_information, str)
        self.assertIsInstance(meta.installed_status, bool)

    def test_system_compatibility_calculation(self):
        """Verify system compatibility evaluates accurately based on hardware."""
        portrait_meta = self.registry.get_metadata("birefnet-portrait")
        comp = portrait_meta.compute_compatibility(self.mock_sys_info)
        self.assertIn(comp, ("Recommended", "Good"))

        # Test on low-memory system (4GB RAM)
        low_ram_sys = SystemInfo(
            operating_system="Windows",
            windows_version="Windows 10",
            architecture="64-bit",
            cpu_name="Intel Core i3",
            cpu_cores=2,
            cpu_threads=4,
            cpu_frequency_mhz=2000.0,
            ram_total_gb=4.0,
            ram_available_gb=1.5,
            gpu_name="Intel HD",
            gpu_vendor="Intel",
            gpu_memory_mb=128.0,
            cuda_available=False,
            amd_acceleration_available=False,
            acceleration_backend="CPU",
            current_device="CPU"
        )
        self.assertIn("Unsupported", portrait_meta.compute_compatibility(low_ram_sys))

        lite_meta = self.registry.get_metadata("birefnet-lite")
        self.assertIn(lite_meta.compute_compatibility(low_ram_sys), ("Good", "Recommended"))

    def test_category_filtering(self):
        """Verify filtering models by category."""
        portraits = self.registry.list_by_category("Portrait / Hair")
        self.assertTrue(any(m.model_id == "birefnet-portrait" for m in portraits))

        balanced = self.registry.list_by_category("Balanced")
        self.assertTrue(any(m.model_id == "rmbg-1.4" for m in balanced))

    def test_dynamic_registration_and_deletion(self):
        """Verify adding and deleting custom models."""
        custom_meta = ModelMetadata(
            model_id="custom-test-model",
            display_name="Custom Test Model",
            description="A test model.",
            category="Custom",
            version="0.1.0",
            minimum_ram=2.0,
            recommended_ram=4.0,
            gpu_requirements="None",
            supported_devices=["cpu"],
            model_size="~50 MB",
            input_resolution=(256, 256),
            download_source="test/model",
            checksum="sha256:test",
            license_information="MIT",
            installed_status=False
        )
        self.registry.register(custom_meta)
        self.assertIsNotNone(self.registry.get_metadata("custom-test-model"))

        # Simulate installed files
        model_dir = Path(self.temp_dir.name) / "custom-test-model"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "weights.bin").write_text("dummy")

        self.registry.refresh_installed_status()
        self.assertTrue(self.registry.get_metadata("custom-test-model").installed_status)

        # Delete model
        deleted = self.registry.delete_model("custom-test-model")
        self.assertTrue(deleted)
        self.assertFalse(self.registry.get_metadata("custom-test-model").installed_status)
        self.assertFalse(model_dir.exists())


if __name__ == "__main__":
    unittest.main()
