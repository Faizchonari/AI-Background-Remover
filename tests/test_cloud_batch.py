"""Unit tests for BatchProcessingWorker with CloudBackend, error resilience, and backend tracking."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from PySide6.QtWidgets import QApplication

from app.processing.backends.base import ProcessingBackend
from app.processing.batch_worker import BatchProcessingWorker, QueueItem

app = QApplication.instance()
if app is None:
    app = QApplication([])


class MockCloudBackend(ProcessingBackend):
    """Mock cloud backend for testing batch worker interactions."""

    def __init__(self, should_fail_on_index: int = -1):
        self.should_fail_on_index = should_fail_on_index
        self.call_count = 0
        self._cancelled = False

    @property
    def backend_name(self) -> str:
        return "Cloud (Hugging Face Spaces)"

    @property
    def is_cloud(self) -> bool:
        return True

    def is_available(self) -> bool:
        return True

    def process_image(self, image: Image.Image, model_id=None, settings=None):
        self.call_count += 1
        if self.should_fail_on_index == self.call_count:
            raise RuntimeError("Cloud processing quota reached (HTTP 429)")

        orig_w, orig_h = image.size
        rgba = Image.new("RGBA", (orig_w, orig_h), (0, 200, 100, 220))
        mask = Image.new("L", (orig_w, orig_h), 220)
        return rgba, mask

    def cancel(self):
        self._cancelled = True

    def check_connection(self) -> tuple[bool, str]:
        return True, "Connected successfully"

    def get_status(self) -> dict:
        return {"status": "Available", "backend": "Cloud"}


class TestCloudBatch(unittest.TestCase):
    """Test suite for batch processing using cloud backend."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name) / "input"
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create 3 test images
        self.test_files = []
        for i in range(3):
            file_path = self.input_dir / f"test_img_{i}.png"
            img = Image.new("RGB", (64, 64), (i * 50, 100, 150))
            img.save(file_path)
            self.test_files.append(file_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_batch_processing_with_cloud_backend(self):
        """Verify batch worker executes via cloud backend and records backend_used."""
        items = [QueueItem.from_path(path) for path in self.test_files]
        mock_backend = MockCloudBackend()

        worker = BatchProcessingWorker(
            items=items,
            model=None,
            output_dir=self.output_dir,
            output_format="PNG (Transparent)",
            backend=mock_backend,
            model_id="birefnet-portrait-cloud"
        )

        completed_items = []
        worker.item_completed.connect(lambda idx, path: completed_items.append((idx, path)))

        # Run synchronously for test
        worker.run()

        self.assertEqual(len(completed_items), 3)
        for itm in items:
            self.assertEqual(itm.status, "Completed")
            self.assertIsNone(itm.error_message)
            self.assertEqual(itm.backend_used, "Cloud (Hugging Face Spaces)")
            self.assertIsNotNone(itm.output_path)
            self.assertTrue(Path(itm.output_path).exists())

    def test_cloud_batch_fault_tolerance(self):
        """Verify one failed cloud image does not crash remaining batch."""
        items = [QueueItem.from_path(path) for path in self.test_files]
        # Fail on item 2 (1-indexed call_count == 2, which corresponds to index 1)
        mock_backend = MockCloudBackend(should_fail_on_index=2)

        worker = BatchProcessingWorker(
            items=items,
            model=None,
            output_dir=self.output_dir,
            output_format="PNG (Transparent)",
            backend=mock_backend,
            model_id="birefnet-portrait-cloud"
        )

        worker.run()

        # Item 0 succeeded
        self.assertEqual(items[0].status, "Completed")
        self.assertIsNone(items[0].error_message)

        # Item 1 failed with 429 error
        self.assertEqual(items[1].status, "Failed")
        self.assertIsNotNone(items[1].error_message)
        self.assertIn("quota", items[1].error_message.lower())

        # Item 2 succeeded (batch did not crash!)
        self.assertEqual(items[2].status, "Completed")
        self.assertIsNone(items[2].error_message)

    def test_cloud_batch_cancellation(self):
        """Verify cancelling batch worker stops processing."""
        items = [QueueItem.from_path(path) for path in self.test_files]
        mock_backend = MockCloudBackend()

        worker = BatchProcessingWorker(
            items=items,
            model=None,
            output_dir=self.output_dir,
            output_format="PNG (Transparent)",
            backend=mock_backend,
            model_id="birefnet-portrait-cloud"
        )

        # Cancel immediately
        worker.cancel()
        worker.run()

        self.assertTrue(worker._cancel_requested)
        self.assertTrue(mock_backend._cancelled)


if __name__ == "__main__":
    unittest.main()
