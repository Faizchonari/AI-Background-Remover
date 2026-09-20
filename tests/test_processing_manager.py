"""Unit tests for ProcessingManager, mode routing, and privacy safeguards."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from PIL import Image

from app.core.config import ConfigManager
from app.models.registry import ModelRegistry
from app.processing.processing_manager import ProcessingManager
from app.processing.backends.local_backend import LocalBackend
from app.processing.backends.cloud_backend import CloudBackend
from app.system.system_info import SystemInfo
from app.system.recommendation import ModelRecommendationEngine


class TestProcessingManager(unittest.TestCase):
    """Test suite for ProcessingManager routing, backends, and privacy enforcement."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        self.config_mgr = ConfigManager(config_dir=self.config_dir)

        # Mock ModelRegistry
        self.mock_registry = MagicMock(spec=ModelRegistry)
        self.mock_sys_info = MagicMock(spec=SystemInfo)
        self.mock_rec_engine = MagicMock(spec=ModelRecommendationEngine)

        self.consent_approved = True

        def consent_callback():
            return self.consent_approved

        self.proc_mgr = ProcessingManager(
            config_mgr=self.config_mgr,
            registry=self.mock_registry,
            sys_info=self.mock_sys_info,
            rec_engine=self.mock_rec_engine,
            privacy_consent_callback=consent_callback
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_mode(self):
        """Verify default mode is local."""
        self.assertEqual(self.proc_mgr.get_mode(), "local")
        self.assertIsInstance(self.proc_mgr.get_active_backend(), LocalBackend)

    def test_set_valid_modes(self):
        """Verify setting valid processing modes."""
        self.proc_mgr.set_mode("cloud")
        self.assertEqual(self.proc_mgr.get_mode(), "cloud")
        self.assertIsInstance(self.proc_mgr.get_active_backend(), CloudBackend)

        self.proc_mgr.set_mode("automatic")
        self.assertEqual(self.proc_mgr.get_mode(), "automatic")

        self.proc_mgr.set_mode("local")
        self.assertEqual(self.proc_mgr.get_mode(), "local")

    def test_set_invalid_mode_raises_error(self):
        """Verify setting invalid mode raises ValueError."""
        with self.assertRaises(ValueError):
            self.proc_mgr.set_mode("quantum_gpu")

    def test_automatic_mode_routing_installed_local(self):
        """In automatic mode, prefer installed local model."""
        self.proc_mgr.set_mode("automatic")
        mock_meta = MagicMock()
        mock_meta.installed_status = True
        self.mock_registry.get_metadata.return_value = mock_meta

        backend = self.proc_mgr.get_active_backend("birefnet-portrait")
        self.assertIsInstance(backend, LocalBackend)

    def test_automatic_mode_routing_uninstalled_local_falls_back_to_cloud(self):
        """In automatic mode, fallback to cloud if local model is not installed."""
        self.proc_mgr.set_mode("automatic")
        mock_meta = MagicMock()
        mock_meta.installed_status = False
        self.mock_registry.get_metadata.return_value = mock_meta

        backend = self.proc_mgr.get_active_backend("birefnet-portrait")
        self.assertIsInstance(backend, CloudBackend)

    def test_automatic_mode_routing_cloud_model(self):
        """In automatic mode, explicit cloud model routes to cloud backend."""
        self.proc_mgr.set_mode("automatic")
        backend = self.proc_mgr.get_active_backend("birefnet-portrait-cloud")
        self.assertIsInstance(backend, CloudBackend)

    def test_privacy_consent_denied_raises_permission_error(self):
        """Verify that denying privacy consent prevents cloud upload."""
        self.proc_mgr.set_mode("cloud")
        self.config_mgr.set("cloud_always_ask_upload", True)
        self.consent_approved = False  # User clicks "No"

        test_img = Image.new("RGB", (64, 64), (255, 0, 0))
        with self.assertRaises(PermissionError) as ctx:
            self.proc_mgr.process_image(test_img, "birefnet-portrait-cloud")
        self.assertIn("cancelled by user", str(ctx.exception).lower())

    def test_privacy_consent_approved_proceeds(self):
        """Verify that approving privacy consent allows cloud processing."""
        self.proc_mgr.set_mode("cloud")
        self.config_mgr.set("cloud_always_ask_upload", True)
        self.consent_approved = True  # User clicks "Yes"

        mock_provider = MagicMock()
        mock_rgba = Image.new("RGBA", (64, 64), (0, 255, 0, 255))
        mock_mask = Image.new("L", (64, 64), 255)
        mock_provider.process_image.return_value = (mock_rgba, mock_mask)
        mock_provider.display_name = "Hugging Face Spaces"

        self.proc_mgr.cloud_backend.active_provider = mock_provider

        test_img = Image.new("RGB", (64, 64), (255, 0, 0))
        rgba, mask, backend_name = self.proc_mgr.process_image(test_img, "birefnet-portrait-cloud")

        self.assertEqual(rgba.size, (64, 64))
        self.assertIn("Cloud", backend_name)
        mock_provider.process_image.assert_called_once()


if __name__ == "__main__":
    unittest.main()
