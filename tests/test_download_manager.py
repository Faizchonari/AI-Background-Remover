"""Unit tests for Model Download Manager."""

import tempfile
import unittest
from pathlib import Path

from app.models.metadata import ModelMetadata
from app.downloads.download_manager import (
    DownloadManager,
    DownloadProgress,
    ModelDownloadTask
)


class TestDownloadManager(unittest.TestCase):
    """Test suite for download manager, progress tracking, and cancellation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.download_mgr = DownloadManager(storage_dir=self.temp_dir.name)
        self.meta = ModelMetadata(
            model_id="test-model",
            display_name="Test Model",
            description="Test description",
            category="Lightweight",
            version="1.0.0",
            minimum_ram=2.0,
            recommended_ram=4.0,
            gpu_requirements="None",
            supported_devices=["cpu"],
            model_size="~1 MB",
            input_resolution=(256, 256),
            download_source="https://httpbin.org/bytes/1024",
            checksum="sha256:test",
            license_information="MIT",
            installed_status=False
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_download_progress_dataclass(self):
        """Verify DownloadProgress attributes and calculations."""
        prog = DownloadProgress(
            downloaded_bytes=500_000,
            total_bytes=1_000_000,
            percentage=50.0,
            speed_mbps=2.5,
            eta_seconds=12.0,
            status_text="Downloading... (50.0%)"
        )
        self.assertEqual(prog.percentage, 50.0)
        self.assertEqual(prog.speed_mbps, 2.5)
        self.assertEqual(prog.eta_seconds, 12.0)

    def test_cancellation_flag(self):
        """Verify that cancel requests halt download task gracefully."""
        task = ModelDownloadTask(
            metadata=self.meta,
            storage_dir=self.temp_dir.name
        )
        self.assertFalse(task._cancel_requested)
        task.cancel()
        self.assertTrue(task._cancel_requested)

    def test_is_downloading_tracking(self):
        """Verify is_downloading properly reflects active tasks."""
        self.assertFalse(self.download_mgr.is_downloading("test-model"))


if __name__ == "__main__":
    unittest.main()
