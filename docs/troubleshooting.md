# Troubleshooting & Diagnostic Guide

This guide helps resolve common issues encountered while installing, configuring, or running **AI Background Remover**.

---

## 1. Crash or Application Closes During "Start Processing"

### Root Cause
BiRefNet uses dynamic module loading from Hugging Face Transformers which requires `kornia` for image transformations. If `kornia` is missing or an uncaught exception occurs in background inference threads, processing will fail.

### Solution
- Ensure you are running version **1.0.0** or newer where `kornia` is bundled and global thread exception handling is active.
- If running from source, run:
  ```powershell
  pip install kornia>=0.7.0
  ```
- Check the log file at `logs/app.log` to see the sanitized traceback.

---

## 2. Model Download Fails or Hangs

### Symptoms
- Download progress stops or times out.
- Checksum mismatch error.

### Solutions
1. **Firewall / Proxy**: Ensure `huggingface.co` is accessible on HTTPS (port 443).
2. **Disk Space**: Check that the drive containing `model_storage/` has at least 5 GB of free space.
3. **Download Interruption**: The Model Manager uses temporary download directories (`.downloading_*`). If interrupted, delete the leftover temporary directory in `model_storage/` and retry.
4. **Manual Offline Download**: If your network restricts automated Python downloads, follow [docs/offline-mode.md](offline-mode.md) to manually download the model via browser or air-gapped transfer.

---

## 3. Out of Memory (OOM) / High RAM Usage

### Symptoms
- System freezes during high-resolution batch processing.
- "Memory Safeguard" alert dialog appears in the application.

### Solutions
1. **Reduce Batch Concurrency**: In **Settings** > **Processing**, set **Maximum Parallel Jobs** to `1` or `2`.
2. **Enable Memory Safeguards**: Ensure **Memory Usage Safeguards** is enabled in Settings (stops queue when available system RAM drops below 1 GB).
3. **Close Background Applications**: High-resolution image segmentation requires significant RAM (4–8 GB per active worker). Close heavy browser tabs and memory-intensive apps before running large batches.
4. **Image Resolution**: If an image is larger than 4000x4000 px, consider resizing it slightly prior to processing.

---

## 4. CUDA / GPU Issues & Fallback to CPU

### Symptoms
- Application defaults to CPU mode even with an NVIDIA GPU installed.
- "CUDA out of memory" error.

### Solutions
1. **PyTorch CUDA Build**: PyTorch must be installed with CUDA support (`torch` with `cu118` or `cu121`). The CPU-only wheel will not use the GPU.
2. **GPU VRAM**: BiRefNet requires at least 6 GB of dedicated VRAM for stable GPU inference. If VRAM is exhausted, switch the device selector to **CPU** in **Settings** > **Processing**.
3. **AMD / Intel GPUs**: PyTorch on Windows natively targets NVIDIA CUDA. For AMD or Intel integrated graphics (e.g. AMD Ryzen APU), inference runs efficiently across multiple CPU threads.

---

## 5. Corrupted Image Files or Unsupported Formats

### Symptoms
- An image shows "Failed" in the queue while others succeed.

### Solutions
- The application processes valid **JPG, JPEG, PNG, and WEBP** images.
- If a file is truncated or corrupted, the batch processor catches the format error, marks the item as **Failed**, and continues processing the rest of the queue without interruption.
- Try re-exporting the image from an image viewer before re-adding it to the queue.

---

## 6. Log File Location & Privacy Sanitization

Logs are automatically stored locally:
```text
<Application_Directory>\logs\app.log
```
- **Privacy First**: The logger automatically scrubs user profile directory paths (e.g. `C:\Users\username\...` is sanitized to `~\...`) and never records image pixels, passwords, or personal credentials.
- When opening an issue on GitHub, please attach the relevant lines from `logs/app.log`.
