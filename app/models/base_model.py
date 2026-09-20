"""Abstract Base Class for Background Removal AI Models.

Defines the contract that every background removal model must satisfy.
Independent of GUI frameworks.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
from PIL import Image

from app.models.metadata import ModelMetadata


class BackgroundRemovalModel(ABC):
    """Abstract interface for background-removal models."""

    def __init__(self, metadata: ModelMetadata, device: str = "cpu"):
        self.metadata = metadata
        self.device = device
        self._is_loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        """Check if model weights are currently loaded in memory."""
        return self._is_loaded

    @abstractmethod
    def load(self, device: Optional[str] = None) -> None:
        """Load model weights into memory on the specified device ('cpu', 'cuda', etc.)."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload model from memory to free RAM/VRAM."""
        pass

    @abstractmethod
    def process_image(self, image: Image.Image) -> tuple[Image.Image, Image.Image]:
        """Process a single PIL Image.

        Requirements:
        - Must preserve the exact original image resolution.
        - Must generate an alpha matte mask (PIL Image, mode 'L').
        - Must return a tuple: (transparent_rgba_image, alpha_mask).
        """
        pass

    def get_model_info(self) -> ModelMetadata:
        """Return model metadata."""
        return self.metadata

    def process_batch(
        self,
        image_paths: list[str | Path],
        output_dir: str | Path,
        progress_callback: Optional[Callable[[int, int, str, str], None]] = None
    ) -> list[Path]:
        """Batch process a list of images non-destructively.

        Guarantees:
        - Never overwrites the original input image.
        - Saves transparent PNG images to output_dir.
        - Preserves input resolution for each image.
        - Invokes progress_callback(current_idx, total, filename, status).
        """
        if not self.is_loaded:
            self.load(self.device)

        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[Path] = []
        total = len(image_paths)

        for idx, img_path in enumerate(image_paths, start=1):
            path = Path(img_path)
            if not path.is_file():
                if progress_callback:
                    progress_callback(idx, total, path.name, "Skipped (Not Found)")
                continue

            try:
                if progress_callback:
                    progress_callback(idx, total, path.name, "Processing...")

                # Load image and ensure RGB mode
                orig_img = Image.open(str(path))
                if orig_img.mode != "RGB":
                    rgb_img = orig_img.convert("RGB")
                else:
                    rgb_img = orig_img

                # Process
                rgba_result, _ = self.process_image(rgb_img)

                # Generate safe non-destructive output path
                base_name = path.stem + "_transparent.png"
                target_path = out_dir / base_name
                counter = 1
                while target_path.exists():
                    target_path = out_dir / f"{path.stem}_transparent_{counter}.png"
                    counter += 1

                # Save as transparent PNG
                rgba_result.save(str(target_path), format="PNG")
                saved_paths.append(target_path)

                if progress_callback:
                    progress_callback(idx, total, path.name, "Done")

            except Exception as exc:
                if progress_callback:
                    progress_callback(idx, total, path.name, f"Error: {exc}")

        return saved_paths
