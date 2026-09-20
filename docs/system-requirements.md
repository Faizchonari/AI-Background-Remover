# System Requirements

This document outlines the hardware and software specifications required to run or develop **AI Background Remover**.

---

## Supported Operating Systems

| OS | Architecture | Status |
| :--- | :--- | :--- |
| **Windows 11** | 64-bit (x64) | **Officially Supported & Tested** |
| **Windows 10** (Build 19041+) | 64-bit (x64) | **Supported** |
| Linux / macOS | x64 / ARM64 | Community / Developer Mode Only (Python source) |

---

## Hardware Requirements

AI Background Remover runs high-resolution deep learning vision models (such as BiRefNet) entirely on your local machine.

### Minimum Specifications (CPU Mode)
- **Processor**: Intel Core i5 (8th Gen+) / AMD Ryzen 5 3000 series or equivalent (6 cores recommended)
- **RAM**: 8 GB System RAM (16 GB recommended for batch processing high-resolution images)
- **Disk Space**: 
  - 1.5 GB for application runtime and dependencies
  - 2.5 GB to 5.0 GB per downloaded AI model (e.g. BiRefNet weights)
  - 10 GB+ recommended free space on target drive for temporary files and batch image output
- **Display**: 1280 x 720 minimum screen resolution

### Recommended Specifications (High Performance)
- **Processor**: Modern 8-core CPU (Intel Core i7/i9 11th Gen+, AMD Ryzen 7 5000+)
- **RAM**: 16 GB - 32 GB DDR4/DDR5
- **Dedicated GPU** (Optional):
  - **NVIDIA GPU**: RTX 2060 / 3060 or higher with minimum 6 GB - 8 GB VRAM (CUDA 11.8 or 12.x compatible)
  - **AMD / Intel GPU**: DirectML / CPU fallback
- **Storage**: Fast NVMe SSD for fast model loading and disk caching

---

## Software Dependencies (Installed Automatically in Packaged Build)

When using the official installer (`AI-Background-Remover-Setup.exe`), all necessary runtime binaries and Python virtual environments are pre-bundled. No external runtime installation is required.

For building from source or development:
- **Python**: 3.10 or 3.11 (64-bit)
- **Microsoft Visual C++ Redistributable 2015–2022** (x64)
- **Inno Setup 6.x** (only needed if building the Windows installer)
