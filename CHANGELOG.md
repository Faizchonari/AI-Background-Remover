# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
