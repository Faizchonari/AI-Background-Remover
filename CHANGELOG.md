# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-20

### Added
- **Optional Cloud Processing System**:
  - **Provider-Independent Architecture**: Abstract `ProcessingBackend` interface with `LocalBackend` and `CloudBackend` (`HuggingFaceProvider`, `CustomAPIProvider`, `FutureProvider`).
  - **Zero-Install Cloud Inference**: Support for free Hugging Face Spaces (Gradio / FastAPI endpoints with ZeroGPU acceleration) and self-hosted custom REST APIs.
  - **Multi-Mode Support**: Added `Local Processing`, `Cloud Processing`, and `Automatic Mode` (prefer local, fallback to cloud or vice versa).
  - **Privacy First**: Explicit user confirmation modal dialog before any cloud upload ("Cloud Processing uploads your image to a remote server..."). Configurable "Always ask before uploading images" (default: True). Zero telemetry or analytics.
  - **Secure Credential Storage**: Hardware-backed Windows Data Protection API (DPAPI via `CryptProtectData` / `CryptUnprotectData`) storing tokens securely in `%LOCALAPPDATA%/AI-Background-Remover/credentials.enc`. Includes safe token masking (`hf_****1234`).
  - **Cloud Settings Tab**: Comprehensive settings UI for selecting backend provider, configuring endpoints, live connection testing, token management, usage statistics, and custom headers.
  - **Main Window & Queue Integration**: Clickable cloud status indicator badge, dynamic model selector reflecting active backend, and preview overlay displaying processing backend and elapsed time.
  - **Model Manager Partitioning**: Separate `LOCAL MODELS` and `CLOUD MODELS` sections with instant activation for cloud models.
  - **Standalone Cloud Server**: Complete Hugging Face Space project in `cloud/huggingface/` (FastAPI + Gradio with `@spaces.GPU` ZeroGPU support) and REST schemas in `cloud/api/`.
  - **Documentation**: Comprehensive `docs/cloud-processing.md` guide covering setup, privacy, troubleshooting, and deployment.
  - **Automated Tests**: Comprehensive test suites for credential encryption, cloud providers, mock HTTP responses, and backend routing.

---

## [1.1.0] - 2026-09-20

### Added
- **About Me / Developer Section**:
  - Added dedicated About dialog accessible from header bar and Settings dialog.
  - Included developer profile with circular avatar, role, description, and direct links to GitHub profile and project repository.
  - Bundled offline avatar resource in `assets/developer_avatar.png` ensuring 100% offline functionality after installation.
- **Automated Tests**:
  - Added unit test suite `tests/test_about_dialog.py` verifying dialog initialization, circular avatar clipping, and offline fallback rendering.

### Changed & Cleaned Up
- **Codebase Optimization**:
  - Removed obsolete prototype `app/downloads/model_downloader.py`.
  - Cleaned up unused imports across `download_manager.py`, `main_window.py`, `model_manager_dialog.py`, `preview_widget.py`, `queue_widget.py`, `settings_dialog.py`, `metadata.py`, `dependency_manager.py`, `recommendation.py`, and `system_info.py`.
  - Removed unused `psutil` hidden import from `ai_background_remover.spec`.
  - Moved `pyinstaller` exclusively to `requirements-dev.txt` keeping `requirements.txt` strictly runtime-focused.

---

## [1.0.0] - 2026-09-20

### Added
- **Modern PySide6 GUI**: Clean, dark-themed Windows desktop interface.
- **BiRefNet Integration**: Bilateral Reference Network support for ultra-high-resolution edge detection and hair segmentation.
- **Batch Processing Queue**:
  - Drag-and-drop and manual file picker support for JPG, JPEG, PNG, and WEBP.
  - Image thumbnails, dimensions, filename, status indicators, and progress tracking.
  - Per-item removal and cancel processing button with thread-safe cancellation.
  - Configurable output directory and format selection (transparent PNG, JPG, WEBP).
  - Individual error resilience allowing queue to continue if a single image fails.
- **Split-View Image Preview**:
  - Before/after slider and side-by-side comparison modes.
  - Transparency checkerboard, zoom, fit-to-window, dimensions, and processing time metadata.
- **Model Registry & Manager**:
  - Built-in metadata for BiRefNet Portrait, BiRefNet General, BiRefNet Massive, and RMBG-1.4.
  - Atomic chunked downloading with SHA256 integrity verification.
  - Automated recommendation engine based on content type and hardware.
  - Model Update Manager with atomic replacement and fallback to previous working model.
- **Settings & Diagnostics**:
  - Output folder defaults, auto-open folder, remember model, auto-start processing.
  - Hardware info viewer, system RAM safeguards, parallel worker settings.
  - AI Dependency Manager with environment verification and repair tools.
- **Windows Packaging**:
  - PyInstaller standalone executable bundling.
  - Inno Setup 6 installer (`AI-Background-Remover-Setup.exe`) with Start Menu/Desktop shortcuts and model weight persistence across updates and uninstallation.

### Fixed
- Fixed critical crash during "Start Processing" caused by missing `kornia` dependency in BiRefNet dynamic loading.
- Added global Qt exception hook to prevent silent desktop crashes and present user-friendly error dialogs.
- Fixed device placement logic to cleanly support CPU multi-threading and NVIDIA CUDA.
- Added privacy-safe local logging to scrub sensitive user profile directory paths from logs.
