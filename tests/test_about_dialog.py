"""Unit tests for AboutDialog and developer profile configuration."""

import os
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap

from app.core.config import ConfigManager
from app.gui.about_dialog import (
    AboutDialog, get_circular_avatar, create_initials_avatar, _get_project_root
)

# Set headless / offscreen platform for testing
os.environ["QT_QPA_PLATFORM"] = "windows"
_app = QApplication.instance() or QApplication([])


class TestAboutDialog(unittest.TestCase):
    """Test suite for AboutDialog and developer profile rendering."""

    def setUp(self):
        self.config_mgr = ConfigManager()

    def test_default_developer_metadata(self):
        """Verify that default configuration provides all required developer fields."""
        dev = self.config_mgr.get("developer", {})
        self.assertIn("name", dev)
        self.assertIn("role", dev)
        self.assertIn("description", dev)
        self.assertIn("github_username", dev)
        self.assertIn("github_profile_url", dev)
        self.assertIn("project_repo_url", dev)
        self.assertIn("avatar_path", dev)
        self.assertEqual(dev["name"], "Faiz")
        self.assertEqual(dev["github_username"], "Faizchonari")

    def test_dialog_initialization(self):
        """Verify that AboutDialog initializes without errors."""
        dialog = AboutDialog(self.config_mgr)
        self.assertEqual(dialog.windowTitle(), "About Developer & Project")
        self.assertEqual(dialog.width(), 480)
        self.assertEqual(dialog.height(), 580)

    def test_circular_avatar_generation(self):
        """Verify that circular avatar generation produces expected dimensions and valid pixmap."""
        sample_pixmap = QPixmap(100, 100)
        sample_pixmap.fill()
        circular = get_circular_avatar(sample_pixmap, size=110)
        self.assertFalse(circular.isNull())
        self.assertEqual(circular.width(), 110)
        self.assertEqual(circular.height(), 110)

    def test_initials_avatar_generation(self):
        """Verify that initials avatar produces valid pixmap with initials."""
        initials_pixmap = create_initials_avatar("FZ", size=110)
        self.assertFalse(initials_pixmap.isNull())
        self.assertEqual(initials_pixmap.width(), 110)
        self.assertEqual(initials_pixmap.height(), 110)

    def test_offline_resource_resolution(self):
        """Verify that project root and local avatar resource path resolve correctly."""
        root = _get_project_root()
        self.assertTrue(root.exists())
        avatar_path = root / "assets" / "developer_avatar.png"
        self.assertTrue(avatar_path.exists(), f"Avatar file must exist locally for offline use: {avatar_path}")


if __name__ == "__main__":
    unittest.main()
