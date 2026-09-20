"""Unit tests for InteractivePreviewWidget and ComparisonCanvas."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from PySide6.QtWidgets import QApplication

from app.gui.preview_widget import InteractivePreviewWidget, ComparisonCanvas
from app.processing.batch_worker import QueueItem

# Ensure single QApplication instance
app = QApplication.instance()
if app is None:
    app = QApplication([])


class TestPreviewWidget(unittest.TestCase):
    """Test suite for image preview system, zoom, slider, and metadata."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.orig_file = Path(self.temp_dir.name) / "test_orig.png"
        self.result_file = Path(self.temp_dir.name) / "test_result.png"

        # Create dummy original RGB image
        Image.new("RGB", (800, 600), (100, 150, 200)).save(str(self.orig_file))
        # Create dummy result RGBA image with transparency
        res_img = Image.new("RGBA", (800, 600), (100, 150, 200, 128))
        res_img.save(str(self.result_file))

        self.widget = InteractivePreviewWidget()
        self.canvas = self.widget.canvas

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_state(self):
        """Verify default view mode and zoom levels."""
        self.assertEqual(self.canvas.view_mode, "slider")
        self.assertEqual(self.canvas.split_pos, 0.5)
        self.assertEqual(self.canvas.zoom, 1.0)

    def test_view_mode_switching(self):
        """Verify switching between Slider and Side-by-Side modes."""
        self.widget._set_mode("side_by_side")
        self.assertEqual(self.canvas.view_mode, "side_by_side")
        self.assertTrue(self.widget.side_mode_btn.isChecked())
        self.assertFalse(self.widget.slider_mode_btn.isChecked())

        self.widget._set_mode("slider")
        self.assertEqual(self.canvas.view_mode, "slider")
        self.assertTrue(self.widget.slider_mode_btn.isChecked())
        self.assertFalse(self.widget.side_mode_btn.isChecked())

    def test_zoom_clamping(self):
        """Verify zoom factor is clamped within safe bounds (0.1x to 10.0x)."""
        self.canvas.set_zoom(0.01)
        self.assertEqual(self.canvas.zoom, 0.1)

        self.canvas.set_zoom(15.0)
        self.assertEqual(self.canvas.zoom, 10.0)

        self.canvas.zoom_100()
        self.assertEqual(self.canvas.zoom, 1.0)

    def test_metadata_display(self):
        """Verify dimensions, processing time, and model name are formatted properly."""
        item = QueueItem(
            file_path=self.orig_file,
            filename=self.orig_file.name,
            dimensions=(800, 600),
            file_size_str="120 KB",
            status="Completed",
            output_path=self.result_file,
            processing_time_s=1.85,
            model_name="BiRefNet Portrait"
        )

        self.widget.display_item(item)

        self.assertIn("800 × 600 px", self.widget.dims_lbl.text())
        self.assertIn("1.85s", self.widget.time_lbl.text())
        self.assertIn("BiRefNet Portrait", self.widget.model_lbl.text())

    def test_non_destructive_guarantee(self):
        """Verify that loading images into preview never modifies the original or result files."""
        orig_bytes_before = self.orig_file.read_bytes()
        result_bytes_before = self.result_file.read_bytes()

        item = QueueItem(
            file_path=self.orig_file,
            filename=self.orig_file.name,
            dimensions=(800, 600),
            file_size_str="120 KB",
            status="Completed",
            output_path=self.result_file
        )

        self.widget.display_item(item)
        self.canvas.zoom_in()
        self.canvas.zoom_out()
        self.widget._set_mode("side_by_side")

        self.assertEqual(self.orig_file.read_bytes(), orig_bytes_before)
        self.assertEqual(self.result_file.read_bytes(), result_bytes_before)


if __name__ == "__main__":
    unittest.main()
