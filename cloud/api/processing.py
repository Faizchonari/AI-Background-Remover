"""Cloud Server Background Removal Pipeline."""

import io
from PIL import Image
import torch
from torchvision import transforms


class CloudSegmentationPipeline:
    """Encapsulates image preprocessing, inference, and alpha matte compositing."""

    def __init__(self, model, device: str = "cpu"):
        self.model = model
        self.device = device
        self.transform = transforms.Compose([
            transforms.Resize((1024, 1024)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def process(self, image: Image.Image) -> Image.Image:
        """Run inference and return transparent RGBA image preserving original dimensions."""
        orig_w, orig_h = image.size
        rgb = image.convert("RGB")

        # Tensor conversion
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            preds = self.model(tensor)[-1].sigmoid().cpu()

        pred = preds[0].squeeze()
        pred_pil = transforms.ToPILImage()(pred)
        mask = pred_pil.resize((orig_w, orig_h), Image.Resampling.BILINEAR)

        rgba = rgb.convert("RGBA")
        rgba.putalpha(mask.convert("L"))
        return rgba
