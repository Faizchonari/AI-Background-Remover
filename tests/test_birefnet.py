"""Unit tests for BackgroundRemovalModel interface, resolution preservation, and batch processing."""

import tempfile
import unittest
from pathlib import Path
from PIL import Image

from app.models.metadata import ModelMetadata
from app.models.base_model import BackgroundRemovalModel
from app.models.birefnet_portrait import BiRefNetPortraitModel


class MockBackgroundRemover(BackgroundRemovalModel):
    """Mock implementation to test interface guarantees without downloading weights."""

    def load(self, device=None):
        self._is_loaded = True

    def unload(self):
        self._is_loaded = False

    def process_image(self, image: Image.Image) -> tuple[Image.Image, Image.Image]:
        # Preserve exact original resolution
        orig_w, orig_h = image.size
        # Generate an alpha mask (e.g., circular mask or full alpha)
        mask = Image.new("L", (orig_w, orig_h), color=180)
        rgba = image.convert("RGBA")
        rgba.putalpha(mask)
        return rgba, mask


class TestBackgroundRemovalModel(unittest.TestCase):
    """Test suite for model interface guarantees and batch processing."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name) / "input"
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.meta = ModelMetadata(
            model_id="mock-remover",
            display_name="Mock Remover",
            description="Mock for testing",
            category="Balanced",
            version="1.0",
            minimum_ram=2.0,
            recommended_ram=4.0,
            gpu_requirements="None",
            supported_devices=["cpu"],
            model_size="~1 MB",
            input_resolution=(512, 512),
            download_source="mock/repo",
            checksum="mock_sha",
            license_information="MIT",
            installed_status=True
        )
        self.model = MockBackgroundRemover(metadata=self.meta)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_birefnet_portrait_metadata(self):
        """Verify BiRefNet Portrait metadata conforms to official repository."""
        biref = BiRefNetPortraitModel()
        info = biref.get_model_info()
        self.assertEqual(info.model_id, "birefnet-portrait")
        self.assertEqual(info.download_source, "ZhengPeng7/BiRefNet-portrait")
        self.assertEqual(info.category, "Portrait / Hair")
        self.assertEqual(info.input_resolution, (1024, 1024))
        self.assertEqual(info.license_information, "Apache 2.0")

    def test_resolution_preservation(self):
        """Verify that process_image preserves arbitrary input image dimensions."""
        test_sizes = [(1920, 1080), (800, 600), (3840, 2160), (300, 300)]

        for w, h in test_sizes:
            test_img = Image.new("RGB", (w, h), color=(120, 180, 240))
            rgba_out, mask_out = self.model.process_image(test_img)

            self.assertEqual(rgba_out.size, (w, h), f"Failed preserving resolution for {w}x{h}")
            self.assertEqual(mask_out.size, (w, h), f"Failed preserving mask resolution for {w}x{h}")
            self.assertEqual(rgba_out.mode, "RGBA")
            self.assertEqual(mask_out.mode, "L")

    def test_batch_processing_non_destructive(self):
        """Verify that batch processing never overwrites input files and outputs transparent PNGs."""
        # Create 3 test input images
        input_files = []
        for i in range(3):
            p = self.input_dir / f"test_photo_{i}.jpg"
            img = Image.new("RGB", (400, 300), color=(50 * i, 70, 90))
            img.save(str(p), format="JPEG")
            input_files.append(p)

        # Record original contents and mtimes
        orig_bytes = [p.read_bytes() for p in input_files]

        progress_log = []
        def _cb(curr, total, name, status):
            progress_log.append((curr, total, name, status))

        # Run batch
        saved_paths = self.model.process_batch(input_files, self.output_dir, progress_callback=_cb)

        # 1. Output files exist and are transparent PNGs
        self.assertEqual(len(saved_paths), 3)
        for out_path in saved_paths:
            self.assertTrue(out_path.exists())
            self.assertTrue(out_path.name.endswith(".png"))
            with Image.open(str(out_path)) as out_img:
                self.assertEqual(out_img.mode, "RGBA")
                self.assertEqual(out_img.size, (400, 300))

        # 2. Original input files are UNTOUCHED
        for idx, p in enumerate(input_files):
            self.assertEqual(p.read_bytes(), orig_bytes[idx], f"Input file {p.name} was modified!")

        # 3. Running batch again creates safe non-overwriting filenames
        second_run_paths = self.model.process_batch(input_files, self.output_dir)
        self.assertEqual(len(second_run_paths), 3)
        for second_path in second_run_paths:
            self.assertIn("_transparent_1.png", second_path.name)

        # 4. Progress callback was called
        self.assertGreater(len(progress_log), 0)


if __name__ == "__main__":
    unittest.main()
