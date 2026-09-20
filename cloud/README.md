# AI Background Remover - Cloud Server Architecture

This directory contains independently deployable cloud server components for **AI Background Remover**.

---

## Directory Structure

```
cloud/
├── huggingface/
│   ├── app.py                # Standalone Gradio + FastAPI application with ZeroGPU support
│   ├── requirements.txt      # Cloud server dependencies
│   └── README.md             # Hugging Face deployment instructions
├── api/
│   ├── schemas.py            # Request/response dataclasses
│   ├── authentication.py     # Token validation logic
│   └── processing.py         # Segmentation pipeline
└── README.md                 # Architecture documentation (this file)
```

---

## Supported Deployment Options

1. **Hugging Face Spaces (ZeroGPU or CPU)**:
   - Zero-cost community GPU acceleration on demand.
   - Built-in Gradio API and FastAPI REST endpoints.
   - Refer to [`huggingface/README.md`](huggingface/README.md) for setup instructions.

2. **Self-Hosted Docker / VPS**:
   - Run `uvicorn app:app --host 0.0.0.0 --port 7860` in your private infrastructure.
   - Secure behind HTTPS reverse proxy (Nginx, Caddy, Cloudflare).
   - Configure the endpoint in the desktop app under **Settings → CLOUD PROCESSING**.
