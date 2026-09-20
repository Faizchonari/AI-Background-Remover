"""Official BiRefNet Portrait Model Implementation.

Repository: ZhengPeng7/BiRefNet-portrait
Architecture: Bilateral Reference Network for High-Resolution Dichotomous Image Segmentation
Specialized for: Human portraits, fine hair matting, and transparent materials.
"""

import gc
from pathlib import Path
import sys
from typing import Optional
from PIL import Image

from app.models.metadata import ModelMetadata
from app.models.base_model import BackgroundRemovalModel
from app.utils.logger import get_logger

logger = get_logger()


class BiRefNetPortraitModel(BackgroundRemovalModel):
    """Implementation of ZhengPeng7/BiRefNet-portrait."""

    def __init__(self, metadata: Optional[ModelMetadata] = None, storage_dir: Optional[Path | str] = None, device: str = "cpu"):
        if metadata is None:
            metadata = ModelMetadata(
                model_id="birefnet-portrait",
                display_name="BiRefNet Portrait",
                description="Specialized high-resolution segmentation model optimized for human portraits and fine hair details.",
                category="Portrait / Hair",
                version="1.1.0",
                minimum_ram=6.0,
                recommended_ram=12.0,
                gpu_requirements="Optional: 4GB+ VRAM for CUDA. Fully supports multi-threaded CPU inference.",
                supported_devices=["cpu", "cuda", "directml"],
                model_size="~950 MB",
                input_resolution=(1024, 1024),
                download_source="ZhengPeng7/BiRefNet-portrait",
                checksum="sha256:birefnet_portrait_weights_v1",
                license_information="Apache 2.0",
                installed_status=False
            )
        super().__init__(metadata=metadata, device=device)
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent.parent
            self.storage_dir = base_dir / "model_storage"

        self._model = None
        self._transform = None

    def load(self, device: Optional[str] = None) -> None:
        """Load BiRefNet weights into memory from local storage or Hugging Face cache."""
        target_device = (device or self.device).lower()
        self.device = target_device

        logger.info(f"Loading BiRefNet Portrait model on device: '{self.device}'...")

        # 1. Verify required runtime dependencies
        try:
            import kornia
        except ImportError:
            msg = "The BiRefNet model requires the 'kornia' package. Please install it via the Dependency Manager or run `pip install kornia`."
            logger.error(msg)
            raise RuntimeError(msg)

        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation

        # Optimize CPU intra-op thread count for AMD Ryzen 5 5500U (6 cores)
        if self.device == "cpu":
            torch.set_num_threads(6)
            logger.info("Configured PyTorch CPU thread count to 6 for optimal AMD Ryzen 5 5500U execution.")

        model_dir = self.storage_dir / self.metadata.model_id

        # Use local directory if complete config exists, otherwise Hugging Face repository
        if (model_dir / "config.json").is_file():
            source = str(model_dir)
            logger.info(f"Loading model weights from local directory: {model_dir}")
        else:
            source = self.metadata.download_source
            logger.info(f"Loading model weights from repository: {source} (cache: {self.storage_dir})")

        self._model = AutoModelForImageSegmentation.from_pretrained(
            source,
            trust_remote_code=True,
            cache_dir=str(self.storage_dir)
        )

        self._model.to(self.device)
        self._model.eval()

        # Standard BiRefNet input normalization pipeline
        self._transform = transforms.Compose([
            transforms.Resize(self.metadata.input_resolution),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        self._is_loaded = True
        logger.info("BiRefNet Portrait model loaded successfully and ready for inference.")

    def unload(self) -> None:
        """Unload model from RAM/VRAM to free resources."""
        if self._model is not None:
            logger.info("Unloading BiRefNet Portrait model and freeing memory...")
            del self._model
            self._model = None
        self._transform = None
        self._is_loaded = False

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def process_image(self, image: Image.Image) -> tuple[Image.Image, Image.Image]:
        """Process image, preserve original resolution, and generate alpha mask."""
        if not self.is_loaded or self._model is None:
            self.load(self.device)

        import torch
        from torchvision import transforms

        # 1. Record original dimensions to guarantee exact resolution preservation
        orig_w, orig_h = image.size

        # 2. Preprocess: resize to input resolution (1024, 1024) and normalize
        rgb_image = image.convert("RGB")
        input_tensor = self._transform(rgb_image).unsqueeze(0).to(self.device)

        # 3. Model Inference
        with torch.no_grad():
            preds = self._model(input_tensor)[-1].sigmoid().cpu()
            pred_mask = preds[0].squeeze()
            mask_pil = transforms.ToPILImage()(pred_mask)

            # Explicit tensor cleanup
            del preds, pred_mask, input_tensor

        # 4. Resize predicted mask back to the EXACT original dimensions
        mask_original_res = mask_pil.resize((orig_w, orig_h), Image.Resampling.BILINEAR)
        del mask_pil

        # 5. Composite original image with transparent alpha channel
        rgba_image = rgb_image.convert("RGBA")
        rgba_image.putalpha(mask_original_res)

        return rgba_image, mask_original_res
