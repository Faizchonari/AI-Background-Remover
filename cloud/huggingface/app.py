"""Hugging Face Space Application for AI Background Removal.

Independently deployable Gradio application supporting ZeroGPU (@spaces.GPU)
and CPU fallback. Runs BiRefNet Portrait background removal.
Exposes:
1. Gradio Interactive UI
2. Gradio API (/api/predict)
3. FastAPI REST Endpoint (/api/remove-background)
"""

import base64
import io
import os
from typing import Optional
from PIL import Image
import torch
from torchvision import transforms
from transformers import AutoModelForImageSegmentation
import gradio as gr
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from fastapi.responses import Response

# Check for Hugging Face ZeroGPU support
try:
    import spaces
    has_zerogpu = True
except ImportError:
    has_zerogpu = False
    # Mock spaces.GPU decorator for local/CPU execution
    class _MockSpaces:
        @staticmethod
        def GPU(func):
            return func
    spaces = _MockSpaces()

# 1. Model Initialization
MODEL_ID = "ZhengPeng7/BiRefNet-portrait"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading BiRefNet model '{MODEL_ID}' on device '{device}'...")

model = AutoModelForImageSegmentation.from_pretrained(
    MODEL_ID,
    trust_remote_code=True
)
model.to(device)
model.eval()

# Preprocessing transforms
transform_image = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])


@spaces.GPU
def remove_background(input_image: Image.Image) -> Image.Image:
    """Run BiRefNet background removal on input image preserving original resolution."""
    if input_image is None:
        raise ValueError("No input image provided.")

    orig_w, orig_h = input_image.size
    orig_rgb = input_image.convert("RGB")

    # Preprocess
    input_tensor = transform_image(orig_rgb).unsqueeze(0).to(device)

    # Inference
    with torch.no_grad():
        preds = model(input_tensor)[-1].sigmoid().cpu()

    # Extract mask
    pred = preds[0].squeeze()
    pred_pil = transforms.ToPILImage()(pred)
    mask = pred_pil.resize((orig_w, orig_h), Image.Resampling.BILINEAR)

    # Apply alpha mask to produce transparent RGBA image
    rgba = orig_rgb.convert("RGBA")
    rgba.putalpha(mask.convert("L"))
    return rgba


# 2. FastAPI REST Endpoint Integration
app = FastAPI(title="AI Background Remover Cloud API", version="1.0.0")

API_SECRET = os.environ.get("API_SECRET")  # Optional secret token


@app.post("/api/remove-background")
async def api_remove_background(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """REST API endpoint accepting multipart image upload and returning transparent PNG."""
    if API_SECRET:
        if not authorization or authorization.replace("Bearer ", "").strip() != API_SECRET:
            raise HTTPException(status_code=401, detail="Invalid API authorization token.")

    try:
        content = await file.read()
        input_img = Image.open(io.BytesIO(content))
        result_img = remove_background(input_img)

        out_buf = io.BytesIO()
        result_img.save(out_buf, format="PNG")
        out_buf.seek(0)
        return Response(content=out_buf.getvalue(), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
def info():
    return {
        "status": "online",
        "model": "BiRefNet Portrait",
        "device": device,
        "zerogpu_available": has_zerogpu
    }


# 3. Gradio Interface
demo = gr.Interface(
    fn=remove_background,
    inputs=gr.Image(type="pil", label="Input Image"),
    outputs=gr.Image(type="pil", label="Transparent Output (PNG)"),
    title="BiRefNet Portrait Background Remover",
    description="ZeroGPU-accelerated background removal. Upload an image to remove its background.",
    api_name="predict"
)

# Mount FastAPI to Gradio app
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
