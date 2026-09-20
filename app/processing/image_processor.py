"""Image Processing Module for AI Background Remover.

Handles image loading, color space conversions, mask application,
and output saving with PNG transparency.
"""

from pathlib import Path
from typing import Optional
from PIL import Image
import numpy as np


class ImageProcessor:
    """Utility class for image input/output and alpha mask operations."""

    @staticmethod
    def load_image(file_path: str | Path) -> Image.Image:
        """Load an image and ensure RGB mode for AI inference."""
        img = Image.open(str(file_path))
        if img.mode != "RGB":
            img = img.convert("RGB")
        return img

    @staticmethod
    def apply_alpha_mask(image: Image.Image, mask: Image.Image | np.ndarray) -> Image.Image:
        """Apply an alpha matte mask to an RGB image to produce a transparent RGBA image."""
        if isinstance(mask, np.ndarray):
            mask = Image.fromarray((mask * 255).astype(np.uint8))

        if mask.size != image.size:
            mask = mask.resize(image.size, Image.Resampling.BILINEAR)

        rgba_image = image.convert("RGBA")
        rgba_image.putalpha(mask.convert("L"))
        return rgba_image

    @staticmethod
    def save_image(image: Image.Image, output_path: str | Path) -> None:
        """Save processed image with alpha transparency (PNG)."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path), format="PNG")
