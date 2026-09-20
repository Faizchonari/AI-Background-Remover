# Cloud Processing Guide

AI Background Remover supports **Optional Cloud Processing** alongside its primary 100% offline local processing engine. This document describes the cloud processing architecture, privacy guarantees, setup steps, and troubleshooting.

---

## 1. Architecture Overview

The application uses a provider-independent processing backend architecture:

```
                            ┌────────────────────────┐
                            │    MainWindow (GUI)    │
                            └───────────┬────────────┘
                                        │
                            ┌───────────▼────────────┐
                            │   ProcessingManager    │
                            │ (Local/Cloud/Auto Mode)│
                            └─────┬────────────┬─────┘
                                  │            │
             ┌────────────────────┘            └─────────────────────┐
             │                                                       │
┌────────────▼─────────────┐                           ┌─────────────▼────────────┐
│       LocalBackend       │                           │       CloudBackend       │
├──────────────────────────┤                           ├──────────────────────────┤
│ - Wraps ModelRegistry    │                           │ - CloudProviderManager   │
│ - Local PyTorch/BiRefNet │                           │ - Privacy Confirmation   │
│ - CPU / CUDA / DirectML  │                           │ - Network/Quota Checks   │
└──────────────────────────┘                           └─────────────┬────────────┘
                                                                     │
                                                  ┌──────────────────┴──────────────────┐
                                                  │                                     │
                                      ┌───────────▼───────────┐             ┌───────────▼───────────┐
                                      │  HuggingFaceProvider  │             │   CustomAPIProvider   │
                                      ├───────────────────────┤             ├───────────────────────┤
                                      │ - HF Spaces / ZeroGPU │             │ - Custom HTTPS URL    │
                                      │ - Gradio API / HTTP   │             │ - Custom Auth/Headers │
                                      │ - Free/Quota Handling │             │ - Advanced Settings   │
                                      └───────────────────────┘             └───────────────────────┘
```

The GUI communicates exclusively through `ProcessingBackend` and `ProcessingManager`, so switching between Local and Cloud processing requires zero changes to the rest of the application.

---

## 2. Privacy & Data Guarantees

Cloud processing transmits images to remote servers for AI processing. The application enforces strict privacy rules:

| Attribute | Local Processing | Cloud Processing |
| :--- | :--- | :--- |
| **Network Required** | **No** (100% Offline) | **Yes** (Active Internet) |
| **Data Transmission** | Images **never** leave your PC | Images sent over **HTTPS** to selected provider |
| **Consent Required** | None (Runs locally) | **Explicit user confirmation dialog** |
| **Analytics Tracking** | **Zero** analytics | **Zero** original images used for analytics |
| **Temporary Files** | Deleted after processing | Deleted immediately after inference |

### Always Ask Before Uploading
By default, the setting **"Always ask before uploading images"** is **ENABLED**. The application will ask for your explicit consent before any image leaves your computer.

---

## 3. Supported Cloud Providers

### Hugging Face Spaces (Default)
- **Status**: Available
- **Plan**: Free / Limited
- **Cost**: Free (Zero Cost)
- **Model**: BiRefNet Portrait
- **Technology**: Gradio API with ZeroGPU (NVIDIA A100 slice on demand) or CPU Basic.
- **Website**: [https://huggingface.co](https://huggingface.co)
- **Privacy Policy**: [https://huggingface.co/privacy](https://huggingface.co/privacy)

### Custom Cloud API (Advanced)
- **Status**: Configurable
- **Plan**: User Managed
- **Cost**: Self-Hosted / Provider Managed
- **Security**: Must use secure HTTPS endpoints.
- **Headers**: Supports Bearer tokens or custom API keys.

---

## 4. Setup Instructions

### Using the Default Hugging Face Space
1. Open **Settings ⚙** → **CLOUD PROCESSING**.
2. Set **Processing Mode** to **Cloud Processing** (or **Automatic**).
3. The default endpoint `https://faizchonari-birefnet-portrait.hf.space` is pre-configured.
4. Click **[ Test Connection ]** to verify connectivity.
5. Click **[ Save Settings ]**.

### Deploying Your Own Private Space
If you want dedicated ZeroGPU quota without sharing public community queues:
1. Follow the deployment guide in [`cloud/huggingface/README.md`](../cloud/huggingface/README.md).
2. Copy your Space URL: `https://<your-username>-birefnet-portrait.hf.space`.
3. Paste the URL into **Settings ⚙** → **CLOUD PROCESSING** → **Cloud Endpoint URL**.
4. (Optional) Enter your Hugging Face User Access Token (`hf_...`) and click **[ Configure Token ]**.
5. Click **[ Save Settings ]**.

---

## 5. Security & Windows DPAPI Token Storage

API keys and tokens are **never** stored in plain-text files or committed to Git:
- **Encryption**: On Windows, tokens are encrypted using **Windows DPAPI** (`CryptProtectData` via `ctypes.windll.crypt32`), bound to your Windows user account.
- **Storage Path**: `%LOCALAPPDATA%\AI-Background-Remover\credentials.enc`.
- **Masking**: Tokens are automatically masked in the UI and in all logs (e.g. `hf_****1234`).
- **Removal**: You can permanently wipe stored credentials at any time by clicking **[ Remove Credentials ]**.

---

## 6. Processing Modes

In the main application, you can switch modes using the **Mode** dropdown:

1. **Local Processing**:
   - Uses the model installed on your PC.
   - 100% offline, zero internet required.
2. **Cloud Processing**:
   - Sends images to the configured cloud provider.
   - Ideal for low-spec PCs or laptops without dedicated GPUs.
3. **Automatic**:
   - Intelligently chooses Local if the model is installed and system has adequate RAM.
   - Suggests Cloud if local resources are constrained, but **never** silently uploads without prior consent.

---

## 7. Quotas and Rate Limits

Free community tiers on Hugging Face Spaces have rate limits and queue wait times:
- If rate limits are exceeded, the application displays:
  > *"Cloud processing quota or rate limit has been reached. You can continue using Local Processing or try again later."*
- The application will **never** automatically charge you or switch to a paid service.
- When quotas are exhausted, you can instantly switch to Local Processing.

---

## 8. Offline Behavior

If you select **Cloud Processing** while your PC is offline:
1. The application detects the network failure.
2. It prompts:
   > *"Cloud processing requires an internet connection. Would you like to switch to Local Processing?"*
3. Clicking **[ Switch to Local ]** instantly shifts to local inference without closing the application.

---

## 9. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **HTTP 401 / 403** | Invalid or missing token | Check your Hugging Face token in Settings → CLOUD PROCESSING. |
| **HTTP 429** | Free rate limit reached | Wait a few minutes, or switch to Local Processing. |
| **HTTP 503 (Cold Start)** | ZeroGPU space is waking up from sleep | Wait 30 seconds for the Space to boot and retry. |
| **Network Timeout** | Slow internet or server load | Check your internet connection or use Local Processing. |
| **Image Size Exceeded** | Image exceeds 8192px | Resize image or use Local Processing. |
