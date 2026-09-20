# Developer Guide

This document contains instructions for setting up the local development environment, understanding the application architecture, adding new models, running tests, and creating release builds.

---

## 1. Development Environment Setup

### Prerequisites
- Windows 10/11 (64-bit)
- Python 3.10 or 3.11 (64-bit)
- Git for Windows
- Inno Setup 6 (optional, for compiling the Windows installer)

### Setup Steps:
```powershell
# Clone the repository
git clone https://github.com/Faizchonari/AI-Background-Remover.git
cd AI-Background-Remover

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install core and developer dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 2. Architecture Overview

The codebase is organized in clean modular layers:

```text
AI-Background-Remover/
├── app/
│   ├── core/           # Configuration management (config.py)
│   ├── gui/            # PySide6 UI (main_window, preview, settings, model_manager_dialog, about_dialog)
│   ├── models/         # Model wrappers, registry, download manager, recommendations
│   ├── processing/     # Image processing pipeline, batch worker, thread management
│   ├── system/         # Dependency manager, hardware inspection, repair utilities
│   └── utils/          # Privacy-safe logger, path utilities
├── config/             # Default JSON configurations
├── docs/               # Technical and user documentation
├── installer/          # Inno Setup (.iss) scripts and resources
├── scripts/            # Automation batch scripts (build, test)
├── tests/              # Automated unit tests
└── release/            # Compiled installer output
```

### Key Architectural Patterns
1. **Thread Separation**: GUI interactions run strictly on the Qt main thread. Image inference and model downloads run on dedicated `QThread` / `QRunnable` background workers with signal-slot communication.
2. **Crash Resilience**: Background workers capture all exceptions locally and emit status signals. A global Qt exception hook logs errors safely and presents friendly diagnostics without crashing the GUI.
3. **Local Cache First**: The model loader inspects local directories before attempting network requests, ensuring deterministic offline behavior.
4. **Memory Hygiene**: Tensors and model weights are explicitly unallocated with `torch.cuda.empty_cache()` and `gc.collect()` when idle or switching models.

---

## 3. Adding a New AI Model

To add a new background-removal model:

1. **Register the Model**:
   Open `app/models/model_registry.py` and add a new `ModelMetadata` entry with:
   - `model_id`: Unique identifier (e.g. `birefnet-massive`)
   - `display_name`: Human-readable name
   - `repo_id`: Hugging Face repository ID
   - Hardware requirements, size, and license info

2. **Implement the Model Wrapper**:
   Create a new class in `app/models/` implementing the `BaseModel` interface:
   - `load()`: Load weights onto the target device.
   - `predict(image: PIL.Image) -> PIL.Image`: Return transparent RGBA image.
   - `unload()`: Release memory and tensors.

3. **Update Recommendation Engine**:
   In `app/models/recommendation_engine.py`, add criteria for when the new model should be suggested to the user.

---

## 4. Running Automated Tests

Run the test suite using Python's `unittest`:

```powershell
# Run all unit tests
python -m unittest discover -s tests -v

# Or use the convenience script
.\scripts\run_tests.bat
```

---

## 5. Building the Application Executable & Installer

### Step A: Build with PyInstaller
```powershell
# Build standalone directory in dist/AI-Background-Remover
.\scripts\build_executable.bat
```
This uses `ai_background_remover.spec` to bundle the Python runtime, PySide6, PyTorch, Transformers, and Kornia.

### Step B: Compile the Windows Installer
```powershell
# Compile Inno Setup installer into release/AI-Background-Remover-Setup.exe
.\scripts\build_installer.bat
```
*(Requires Inno Setup 6 installed in `C:\Users\<user>\AppData\Local\Programs\Inno Setup 6` or `C:\Program Files (x86)\Inno Setup 6`).*
