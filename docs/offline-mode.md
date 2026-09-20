# Offline Mode & Air-Gapped Deployment

**AI Background Remover** is designed with a strict **local-first, privacy-first** architecture. Once model weights are downloaded, the application operates completely offline with **zero** internet dependency.

---

## How Offline Mode Works

- **100% Local Inference**: All machine learning computation happens on your local CPU or GPU.
- **No Cloud Telemetry**: Images, processing results, and logs are never uploaded to remote servers or third-party APIs.
- **Local Cache First**: The application checks `model_storage/` first. If valid model files exist, it executes without attempting network connections.

---

## Local Model Storage Locations

AI models are stored in:
- **Default Relative Path**: `<Application_Directory>\model_storage\<model-id>\`
- **Configurable Location**: You can customize your model directory in **Settings** > **Models** > **Model Storage Location**.

### Standard Directory Structure:
```text
model_storage/
├── birefnet-portrait/
│   ├── config.json
│   ├── model.safetensors (or pytorch_model.bin)
│   ├── preprocessor_config.json
│   └── ...
├── birefnet-general/
│   └── ...
└── models_metadata.json
```

---

## Pre-Downloading Models for Air-Gapped / Offline Systems

For secure environments, air-gapped computers, or machines without high-speed internet, you can pre-download model weights and transfer them manually.

### Step-by-Step Pre-Download Procedure:

#### 1. Download on an Internet-Connected Machine
You can use Python with `huggingface_hub` to download the exact model repository:

```powershell
# In PowerShell:
pip install huggingface_hub

# Download BiRefNet Portrait:
python -c "from huggingface_hub import snapshot_download; snapshot_download('ZhengPeng7/BiRefNet-portrait', local_dir='birefnet-portrait', local_dir_use_symlinks=False)"

# Download BiRefNet General:
python -c "from huggingface_hub import snapshot_download; snapshot_download('ZhengPeng7/BiRefNet-general', local_dir='birefnet-general', local_dir_use_symlinks=False)"
```

> **Windows Note:**
> Always specify `local_dir_use_symlinks=False` on Windows to ensure actual files are downloaded rather than filesystem symlinks that fail across file transfers.

#### 2. Verify File Integrity
Ensure the model folder contains:
- `config.json`
- `model.safetensors` (or `pytorch_model.bin`)
- Model configuration and preprocessor scripts

#### 3. Transfer to Air-Gapped Machine
1. Copy the downloaded model folder(s) to a USB drive or local network share.
2. On the target machine, copy the folder into the application's `model_storage/` directory:
   ```text
   C:\Program Files\AI Background Remover\model_storage\birefnet-portrait\
   ```
   (or whichever folder is set in your application's `config/default_config.json`).
3. Ensure a `models_metadata.json` file is present or register the folder in **Model Manager**.

#### 4. Launch Application
Launch **AI Background Remover**. The Model Manager will detect the pre-installed model weights with a green checkmark (`Installed: version 1.0.0`), allowing immediate offline processing.
