# Hugging Face Spaces Deployment Guide

This directory contains everything needed to deploy the **BiRefNet Portrait Background Remover** as a free, ZeroGPU-accelerated or CPU-hosted service on Hugging Face Spaces.

---

## 1. Prerequisites

- A free account on [Hugging Face](https://huggingface.co).
- Basic familiarity with Hugging Face Spaces.

---

## 2. Deployment Steps

1. **Create a New Space**:
   - Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
   - **Space name**: `birefnet-portrait` (or any custom name).
   - **License**: `Apache 2.0`.
   - **Space SDK**: Select **Gradio**.
   - **Space hardware**:
     - For free GPU acceleration: Select **ZeroGPU** (NVIDIA A100 slice on demand).
     - Or select **CPU Basic** (2 vCPU, 16 GB RAM - Free).
   - **Visibility**: **Public** (recommended for easy desktop app connection) or **Private** (requires token).

2. **Upload Files**:
   Upload the following files from this directory to your Space repository:
   - `app.py`
   - `requirements.txt`

3. **Space Building**:
   - Hugging Face will automatically install dependencies and start the application.
   - Wait 1–2 minutes until the status badge turns green (`Running`).

---

## 3. Connecting to the Desktop Application

1. In your Hugging Face Space, click the **three dots menu (⋮)** in the top right and select **Embed this Space** or copy the Direct URL:
   ```
   https://<your-username>-birefnet-portrait.hf.space
   ```
2. Open the **AI Background Remover** desktop application:
   - Go to **Settings ⚙** → **CLOUD PROCESSING**.
   - Paste your Space URL into **Cloud Endpoint URL**.
   - (Optional) If your Space is private or you want higher rate limits, add your **Hugging Face Access Token**.
   - Click **[ Test Connection ]** to verify connectivity.
   - Click **[ Save Settings ]**.
3. In the main application:
   - Set **Processing Mode** to **Cloud Processing**.
   - Start processing images!

---

## 4. Features & Endpoints

- **Interactive Web UI**: Available at the root URL.
- **Gradio API Endpoint**: `/api/predict` (used by the desktop client).
- **FastAPI REST Endpoint**: `/api/remove-background` (accepts multipart file upload, returns transparent PNG).
- **Health Check**: `/info` returns model and ZeroGPU status.
