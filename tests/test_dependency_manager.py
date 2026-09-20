"""Unit tests for Dependency Manager and Settings Configuration."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

from app.system.dependency_manager import DependencyManager, REQUIRED_COMPONENTS, DependencyInfo
from app.core.config import ConfigManager


class TestDependencyManager(unittest.TestCase):
    """Test suite for DependencyManager inspection and repair logic."""

    def test_required_components_list(self):
        """Verify all 7 required components are configured."""
        names = [c["name"] for c in REQUIRED_COMPONENTS]
        expected = [
            "PyTorch",
            "Torchvision",
            "PySide6",
            "Pillow",
            "OpenCV",
            "Transformers",
            "Hugging Face Hub",
        ]
        for name in expected:
            self.assertIn(name, names)
        self.assertEqual(len(REQUIRED_COMPONENTS), 7)

    def test_check_dependencies_structure(self):
        """Verify check_dependencies returns structured DependencyInfo for each component."""
        results = DependencyManager.check_dependencies()
        self.assertEqual(len(results), 7)

        for item in results:
            self.assertIsInstance(item, DependencyInfo)
            self.assertIsInstance(item.name, str)
            self.assertIsInstance(item.package_name, str)
            self.assertIsInstance(item.import_name, str)
            self.assertIsInstance(item.is_installed, bool)
            self.assertIsInstance(item.required_version, str)
            self.assertIsInstance(item.notes, str)

    def test_currently_installed_packages_detected(self):
        """Verify that packages installed in the environment (PySide6, Pillow) are detected."""
        results = {item.name: item for item in DependencyManager.check_dependencies()}

        # PySide6 and Pillow are known to be in the current .venv
        self.assertTrue(results["PySide6"].is_installed)
        self.assertIsNotNone(results["PySide6"].installed_version)
        self.assertEqual(results["PySide6"].notes, "OK")

        self.assertTrue(results["Pillow"].is_installed)
        self.assertIsNotNone(results["Pillow"].installed_version)
        self.assertEqual(results["Pillow"].notes, "OK")

    def test_get_missing_dependencies_filtering(self):
        """Verify get_missing_dependencies returns only uninstalled items."""
        missing = DependencyManager.get_missing_dependencies()
        self.assertIsInstance(missing, list)

        # PySide6 and Pillow should not be in missing
        missing_names = [m["name"] for m in missing]
        self.assertNotIn("PySide6", missing_names)
        self.assertNotIn("Pillow", missing_names)

    @patch("subprocess.check_call")
    def test_repair_installation_invokes_pip_selectively(self, mock_check_call):
        """Verify repair_installation invokes pip only for missing packages."""
        # Mock get_missing_dependencies to return a specific missing package
        mock_missing = [
            {
                "name": "Transformers",
                "package_name": "transformers",
                "import_name": "transformers",
                "required_version": ">= 4.40.0",
                "cpu_install_cmd": ["transformers", "timm", "einops"]
            }
        ]

        with patch.object(DependencyManager, "get_missing_dependencies", return_value=mock_missing):
            progress_messages = []
            success, msg = DependencyManager.repair_installation(
                on_progress=lambda m: progress_messages.append(m)
            )

            self.assertTrue(success)
            self.assertIn("Transformers", progress_messages[0])
            mock_check_call.assert_called_once()
            call_args = mock_check_call.call_args[0][0]
            self.assertIn("-m", call_args)
            self.assertIn("pip", call_args)
            self.assertIn("install", call_args)
            self.assertIn("transformers", call_args)

    def test_repair_installation_when_nothing_missing(self):
        """Verify repair_installation returns early when no packages are missing."""
        with patch.object(DependencyManager, "get_missing_dependencies", return_value=[]):
            success, msg = DependencyManager.repair_installation()
            self.assertTrue(success)
            self.assertIn("already installed", msg)


class TestSettingsConfiguration(unittest.TestCase):
    """Test suite for settings configuration persistence."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_mgr = ConfigManager(config_dir=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_settings_keys(self):
        """Verify all settings page configuration keys exist with proper defaults."""
        self.assertIn("output_dir", self.config_mgr._data)
        self.assertFalse(self.config_mgr.get("auto_open_output"))
        self.assertTrue(self.config_mgr.get("remember_selected_model"))
        self.assertFalse(self.config_mgr.get("auto_start_on_drop"))

        self.assertEqual(self.config_mgr.get("execution_device"), "CPU")
        self.assertEqual(self.config_mgr.get("processing_quality"), "High (Optimal)")
        self.assertEqual(self.config_mgr.get("max_parallel_jobs"), 1)
        self.assertTrue(self.config_mgr.get("memory_safeguard"))

    def test_save_and_reload_settings(self):
        """Verify modifying settings persists across reloads."""
        self.config_mgr.set("auto_open_output", True)
        self.config_mgr.set("max_parallel_jobs", 2)
        self.config_mgr.set("execution_device", "DirectML")
        self.config_mgr.save()

        # Reload in a new manager
        reloaded = ConfigManager(config_dir=self.temp_dir.name)
        self.assertTrue(reloaded.get("auto_open_output"))
        self.assertEqual(reloaded.get("max_parallel_jobs"), 2)
        self.assertEqual(reloaded.get("execution_device"), "DirectML")


class TestSettingsDialog(unittest.TestCase):
    """Test suite for SettingsDialog UI interaction and tab integrity."""

    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

    def setUp(self):
        from app.system.system_info import SystemInfo
        from app.system.recommendation import ModelRecommendationEngine
        from app.gui.settings_dialog import SettingsDialog

        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_mgr = ConfigManager(config_dir=self.temp_dir.name)
        self.sys_info = SystemInfo(
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
        self.rec_engine = ModelRecommendationEngine()
        self.dialog = SettingsDialog(self.config_mgr, self.sys_info, self.rec_engine)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_tabs_initialization(self):
        """Verify that all 6 settings tabs are initialized."""
        self.assertEqual(self.dialog.tabs.count(), 6)
        tab_titles = [self.dialog.tabs.tabText(i) for i in range(6)]
        self.assertIn("GENERAL", tab_titles)
        self.assertIn("PROCESSING", tab_titles)
        self.assertIn("CLOUD PROCESSING", tab_titles)
        self.assertIn("MODELS", tab_titles)
        self.assertIn("SYSTEM & DEPENDENCIES", tab_titles)
        self.assertIn("ABOUT DEVELOPER", tab_titles)

    def test_dependency_table_populated(self):
        """Verify the dependency table in System tab displays all 7 components."""
        self.assertEqual(self.dialog.dep_table.rowCount(), 7)
        components = [self.dialog.dep_table.item(r, 0).text() for r in range(7)]
        self.assertIn("PyTorch", components)
        self.assertIn("PySide6", components)
        self.assertIn("Pillow", components)

    def test_save_settings_from_dialog(self):
        """Verify changes in dialog widgets are saved to ConfigManager."""
        self.dialog.cb_auto_open.setChecked(True)
        self.dialog.jobs_spin.setValue(3)
        self.dialog._save_settings()

        self.assertTrue(self.config_mgr.get("auto_open_output"))
        self.assertEqual(self.config_mgr.get("max_parallel_jobs"), 3)


if __name__ == "__main__":
    unittest.main()
