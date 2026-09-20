"""Unit tests for BatchProcessingWorker, fault tolerance, and format conversions."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from PySide6.QtWidgets import QApplication

from app.models.metadata import ModelMetadata
from app.models.base_model import BackgroundRemovalModel
from app.processing.batch_worker import BatchProcessingWorker, QueueItem

# Ensure single QApplication instance for QPixmap / QThread
app = QApplication.instance()
if app is None:
    app = QApplication([])


class MockModel(BackgroundRemovalModel):
    """Mock model for testing batch worker without downloading weights."""

    def load(self, device=None):
        self._is_loaded = True

    def unload(self):
        self._is_loaded = False

    def process_image(self, image: Image.Image) -> tuple[Image.Image, Image.Image]:
        orig_w, orig_h = image.size
        # Generate alpha mask
        mask = Image.new("L", (orig_w, orig_h), 200)
        rgba = image.convert("RGBA")
        rgba.putalpha(mask)
        return rgba, mask


class TestBatchWorker(unittest.TestCase):
    """Test suite for batch worker execution, fault tolerance, and formats."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name) / "input"
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.meta = ModelMetadata(
            model_id="mock-model",
            display_name="Mock Model",
            description="Mock",
            category="Balanced",
            version="1.0",
            minimum_ram=2.0,
            recommended_ram=4.0,
            gpu_requirements="None",
            supported_devices=["cpu"],
            model_size="~1 MB",
            input_resolution=(512, 512),
            download_source="mock/source",
            checksum="sha256:mock",
            license_information="MIT",
            installed_status=True
        )
        self.model = MockModel(metadata=self.meta)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_queue_item_from_path(self):
        """Verify QueueItem creation and metadata parsing."""
        img_path = self.input_dir / "test_sample.png"
        img = Image.new("RGB", (640, 480), (100, 150, 200))
        img.save(str(img_path))

        item = QueueItem.from_path(img_path)
        self.assertEqual(item.filename, "test_sample.png")
        self.assertEqual(item.dimensions, (640, 480))
        self.assertIn("KB", item.file_size_str)
        self.assertEqual(item.status, "Pending")

    def test_fault_tolerant_batch_processing(self):
        """Verify that per-item errors do NOT halt the batch and subsequent items succeed."""
        # Create 2 valid images and 1 corrupt/missing entry
        img1 = self.input_dir / "valid_1.jpg"
        Image.new("RGB", (300, 200), (255, 0, 0)).save(str(img1))

        corrupt_img = self.input_dir / "missing_file.jpg"  # Does not exist

        img2 = self.input_dir / "valid_2.png"
        Image.new("RGB", (500, 400), (0, 255, 0)).save(str(img2))

        items = [
            QueueItem.from_path(img1),
            QueueItem.from_path(corrupt_img),
            QueueItem.from_path(img2),
        ]

        worker = BatchProcessingWorker(
            items=items,
            output_dir=self.output_dir,
            output_format="PNG (Transparent)",
            model=self.model
        )

        completed_events = []
        failed_events = []

        worker.item_completed.connect(lambda idx, path: completed_events.append((idx, path)))
        worker.item_failed.connect(lambda idx, err: failed_events.append((idx, err)))

        # Run synchronously for testing
        worker.run()

        # Item 0: Succeeded
        self.assertEqual(items[0].status, "Completed")
        self.assertTrue(items[0].output_path.exists())

        # Item 1: Failed without crashing the batch
        self.assertEqual(items[1].status, "Failed")
        self.assertIn(1, [f[0] for f in failed_events])

        # Item 2: Succeeded despite previous failure!
        self.assertEqual(items[2].status, "Completed")
        self.assertTrue(items[2].output_path.exists())

        # Total completed: 2, Total failed: 1
        self.assertEqual(len(completed_events), 2)
        self.assertEqual(len(failed_events), 1)

    def test_output_formats(self):
        """Verify transparent PNG, JPG (white background), and WEBP formats."""
        img_path = self.input_dir / "format_test.png"
        Image.new("RGB", (200, 200), (50, 100, 150)).save(str(img_path))

        # 1. PNG (Transparent)
        item_png = QueueItem.from_path(img_path)
        worker_png = BatchProcessingWorker([item_png], self.output_dir, "PNG (Transparent)", self.model)
        worker_png.run()
        self.assertEqual(item_png.status, "Completed")
        with Image.open(str(item_png.output_path)) as p:
            self.assertEqual(p.format, "PNG")
            self.assertEqual(p.mode, "RGBA")

        # 2. JPG (White Background)
        item_jpg = QueueItem.from_path(img_path)
        worker_jpg = BatchProcessingWorker([item_jpg], self.output_dir, "JPG (White Background)", self.model)
        worker_jpg.run()
        self.assertEqual(item_jpg.status, "Completed")
        with Image.open(str(item_jpg.output_path)) as j:
            self.assertEqual(j.format, "JPEG")
            self.assertEqual(j.mode, "RGB")

        # 3. WEBP (Transparent)
        item_webp = QueueItem.from_path(img_path)
        worker_webp = BatchProcessingWorker([item_webp], self.output_dir, "WEBP (Transparent)", self.model)
        worker_webp.run()
        self.assertEqual(item_webp.status, "Completed")
        with Image.open(str(item_webp.output_path)) as w:
            self.assertEqual(w.format, "WEBP")
            self.assertEqual(w.mode, "RGBA")

    def test_cancellation(self):
        """Verify cancellation request halts subsequent queue execution."""
        images = []
        for i in range(5):
            p = self.input_dir / f"cancel_test_{i}.png"
            Image.new("RGB", (100, 100), (i * 20, 50, 50)).save(str(p))
            images.append(QueueItem.from_path(p))

        worker = BatchProcessingWorker(images, self.output_dir, "PNG (Transparent)", self.model)

        def _cancel_after_first(idx, path):
            worker.cancel()

        worker.item_completed.connect(_cancel_after_first)
        worker.run()

        # At most 1 or 2 items should complete, remainder should be cancelled
        completed = [it for it in images if it.status == "Completed"]
        cancelled = [it for it in images if it.status == "Cancelled"]
        self.assertLess(len(completed), 5)
        self.assertGreater(len(cancelled), 0)


if __name__ == "__main__":
    unittest.main()
