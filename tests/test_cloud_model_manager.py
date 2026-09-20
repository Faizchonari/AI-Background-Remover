"""Unit tests for Cloud Models, Registry Partitioning, and Cloud Metadata."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.models.metadata import ModelMetadata
from app.models.registry import ModelRegistry


class TestCloudModelManager(unittest.TestCase):
    """Test suite for local vs cloud model separation in ModelRegistry."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.registry = ModelRegistry(storage_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cloud_models_registered(self):
        """Verify cloud models are loaded into the registry."""
        cloud_models = self.registry.list_cloud()
        self.assertGreaterEqual(len(cloud_models), 1)

        cloud_ids = [m.model_id for m in cloud_models]
        self.assertIn("birefnet-portrait-cloud", cloud_ids)

    def test_local_vs_cloud_separation(self):
        """Verify list_local and list_cloud return mutually exclusive partitions."""
        local_models = self.registry.list_local()
        cloud_models = self.registry.list_cloud()

        local_ids = {m.model_id for m in local_models}
        cloud_ids = {m.model_id for m in cloud_models}

        # No intersection between local and cloud
        self.assertEqual(len(local_ids.intersection(cloud_ids)), 0)

        # Verify specific models in partitions
        self.assertIn("birefnet-portrait", local_ids)
        self.assertIn("rmbg-1.4", local_ids)
        self.assertIn("birefnet-portrait-cloud", cloud_ids)

    def test_is_cloud_model_helper(self):
        """Verify is_cloud_model correctly identifies model types."""
        self.assertTrue(self.registry.is_cloud_model("birefnet-portrait-cloud"))
        self.assertFalse(self.registry.is_cloud_model("birefnet-portrait"))
        self.assertFalse(self.registry.is_cloud_model("rmbg-1.4"))
        self.assertFalse(self.registry.is_cloud_model("nonexistent-model"))

    def test_cloud_metadata_attributes(self):
        """Verify cloud-specific metadata attributes."""
        cloud_meta = self.registry.get_metadata("birefnet-portrait-cloud")
        self.assertIsNotNone(cloud_meta)

        self.assertEqual(cloud_meta.local_or_cloud, "cloud")
        self.assertEqual(cloud_meta.provider, "Hugging Face")
        self.assertTrue(cloud_meta.requires_internet)
        self.assertIsNotNone(cloud_meta.cloud_endpoint)
        self.assertTrue(cloud_meta.cloud_endpoint.startswith("https://"))

        # Verify compatibility check returns Available (Cloud GPU)
        mock_sys_info = MagicMock()
        compat = cloud_meta.compute_compatibility(mock_sys_info)
        self.assertEqual(compat, "Available (Cloud GPU)")

    def test_local_metadata_attributes(self):
        """Verify local-specific metadata attributes."""
        local_meta = self.registry.get_metadata("birefnet-portrait")
        self.assertIsNotNone(local_meta)

        self.assertEqual(local_meta.local_or_cloud, "local")
        self.assertFalse(local_meta.requires_internet)


if __name__ == "__main__":
    unittest.main()
