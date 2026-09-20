"""Batch Processing Worker for AI Background Remover.

Runs image background removal in a background thread to keep the GUI responsive.
Guarantees:
- Never modifies or overwrites the original input image.
- Preserves exact input dimensions.
- Fault-tolerant: per-item errors do not halt the batch.
- Supports transparent PNG, JPG (white background), and WEBP.
- Thread-safe cancellation.
- Logs processing steps, timings, and exceptions to logs/app.log.
"""

from dataclasses import dataclass
import gc
from pathlib import Path
import time
import traceback
from typing import Optional
from PIL import Image

from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap

from app.models.base_model import BackgroundRemovalModel
from app.utils.logger import get_logger

logger = get_logger()


@dataclass
class QueueItem:
    """Represents a single image task in the processing queue."""
    file_path: Path
    filename: str
    dimensions: tuple[int, int]
    file_size_str: str
    status: str = "Pending"  # "Pending", "Processing...", "Completed", "Failed", "Cancelled"
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    thumbnail: Optional[QPixmap] = None
    processing_time_s: Optional[float] = None
    model_name: Optional[str] = None

    @classmethod
    def from_path(cls, path: str | Path) -> "QueueItem":
        p = Path(path)
        size_bytes = p.stat().st_size if p.exists() else 0
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        dims = (0, 0)
        try:
            with Image.open(str(p)) as img:
                dims = img.size
        except Exception:
            pass

        return cls(
            file_path=p,
            filename=p.name,
            dimensions=dims,
            file_size_str=size_str
        )


class BatchProcessingWorker(QThread):
    """Background worker executing batch background removal."""

    item_started = Signal(int, str)  # index, filename
    item_progress = Signal(int, float)  # index, percent
    item_completed = Signal(int, str)  # index, output_path
    item_failed = Signal(int, str)  # index, error_message
    batch_finished = Signal(int, int, str)  # success_count, fail_count, last_error_message

    def __init__(
        self,
        items: list[QueueItem],
        output_dir: Path | str,
        output_format: str,
        model: BackgroundRemovalModel,
        parent=None
    ):
        super().__init__(parent)
        self.items = items
        self.output_dir = Path(output_dir)
        self.output_format = output_format  # "PNG (Transparent)", "JPG (White Background)", "WEBP (Transparent)"
        self.model = model
        self._cancel_requested = False
        self.last_error: str = ""

    def cancel(self):
        """Request cancellation of the batch queue."""
        self._cancel_requested = True
        logger.info("Batch processing cancellation requested by user.")

    def run(self):
        try:
            self._run_internal()
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error(f"Fatal error in BatchProcessingWorker thread:\n{tb}")
            self.last_error = f"{exc}\n\n{tb}"
            self.batch_finished.emit(0, len(self.items), self.last_error)

    def _run_internal(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        success_count = 0
        fail_count = 0
        self.last_error = ""

        logger.info(
            f"Batch processing started: {len(self.items)} image(s) to process. "
            f"Output format: '{self.output_format}', Model: '{self.model.get_model_info().display_name}'"
        )

        # 1. Ensure model is loaded once before batch (reuse across all images)
        try:
            if not self.model.is_loaded:
                logger.info(f"Model not yet in memory. Loading once on device '{self.model.device}'...")
                self.model.load(self.model.device)
        except Exception as e:
            tb = traceback.format_exc()
            self.last_error = f"Model load failure: {e}\n\n{tb}"
            logger.error(f"Failed to load model '{self.model.get_model_info().display_name}':\n{tb}")
            for idx, item in enumerate(self.items):
                item.status = "Failed"
                item.error_message = str(e)
                self.item_failed.emit(idx, str(e))
            self.batch_finished.emit(0, len(self.items), self.last_error)
            return

        # 2. Process each image in the queue
        for idx, item in enumerate(self.items):
            if self._cancel_requested:
                item.status = "Cancelled"
                self.item_failed.emit(idx, "Batch cancelled by user.")
                logger.info(f"Skipping ({idx + 1}/{len(self.items)}): {item.filename} (Cancelled)")
                continue

            item.status = "Processing..."
            self.item_started.emit(idx, item.filename)
            logger.info(f"Processing image ({idx + 1}/{len(self.items)}): '{item.filename}'")

            try:
                t_start = time.time()

                # Open original image read-only; NEVER modify original file
                if not item.file_path.is_file():
                    raise FileNotFoundError(f"Input file not found: {item.file_path}")

                with Image.open(str(item.file_path)) as raw_img:
                    orig_w, orig_h = raw_img.size
                    orig_rgb = raw_img.convert("RGB")

                # Infer background mask (guaranteed to preserve original dimensions)
                rgba_result, _ = self.model.process_image(orig_rgb)

                # Ensure dimensions strictly preserved
                if rgba_result.size != (orig_w, orig_h):
                    rgba_result = rgba_result.resize((orig_w, orig_h), Image.Resampling.LANCZOS)

                # Determine output format & save losslessly/non-destructively
                ext = ".png"
                save_kwargs = {}

                if "JPG" in self.output_format.upper() or "JPEG" in self.output_format.upper():
                    ext = ".jpg"
                    # Composite over clean white background for JPG
                    bg = Image.new("RGB", (orig_w, orig_h), (255, 255, 255))
                    bg.paste(rgba_result, mask=rgba_result.split()[3])
                    final_image = bg
                    save_kwargs = {"format": "JPEG", "quality": 95}
                elif "WEBP" in self.output_format.upper():
                    ext = ".webp"
                    final_image = rgba_result
                    save_kwargs = {"format": "WEBP", "lossless": True}
                else:
                    # Default: Transparent PNG
                    ext = ".png"
                    final_image = rgba_result
                    save_kwargs = {"format": "PNG", "compress_level": 6}

                # Generate unique non-overwriting destination path
                base_stem = item.file_path.stem
                target_path = self.output_dir / f"{base_stem}_transparent{ext}"
                counter = 1
                while target_path.exists():
                    target_path = self.output_dir / f"{base_stem}_transparent_{counter}{ext}"
                    counter += 1

                final_image.save(str(target_path), **save_kwargs)

                elapsed = time.time() - t_start
                item.output_path = target_path
                item.processing_time_s = elapsed
                item.model_name = self.model.get_model_info().display_name
                item.status = "Completed"
                success_count += 1

                logger.info(
                    f"Completed ({idx + 1}/{len(self.items)}): '{item.filename}' in {elapsed:.2f}s "
                    f"-> '{target_path.name}' ({orig_w}x{orig_h})"
                )

                # Clean temporary image objects
                del orig_rgb, rgba_result, final_image
                gc.collect()

                self.item_completed.emit(idx, str(target_path))

            except Exception as exc:
                tb = traceback.format_exc()
                self.last_error = f"{exc}\n\n{tb}"
                logger.error(f"Failed processing image '{item.filename}':\n{tb}")

                item.status = "Failed"
                item.error_message = str(exc)
                fail_count += 1
                self.item_failed.emit(idx, str(exc))

        logger.info(f"Batch processing finished. Successful: {success_count}, Failed: {fail_count}")
        self.batch_finished.emit(success_count, fail_count, self.last_error)
