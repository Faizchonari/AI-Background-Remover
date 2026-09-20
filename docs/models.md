# Supported AI Models

**AI Background Remover** uses state-of-the-art vision models for high-resolution dichotomous image segmentation and salient object detection.

---

## Model Registry & Architecture Overview

The application features a built-in model registry (`app/models/model_registry.py`) providing metadata, size, speed, quality ratings, and system requirements for each model.

| Model ID | Display Name | Architecture | Parameters | Download Size | Primary Use Case | Model License |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `birefnet-portrait` | **BiRefNet Portrait** | Bilateral Reference Network | ~220M | ~1.8 - 2.2 GB | People, portraits, fine hair strands | Apache 2.0 |
| `birefnet-general` | **BiRefNet General** | Bilateral Reference Network | ~220M | ~1.8 - 2.2 GB | General objects, e-commerce, animals, cars | Apache 2.0 |
| `birefnet-massive` | **BiRefNet Massive (DIS5K)** | Bilateral Reference Network | ~220M | ~2.2 GB | Complex high-resolution segmentation | Apache 2.0 |
| `rmbg-1.4` | **RMBG-1.4** | Bria RMBG Architecture | ~170M | ~680 MB | Fast lightweight background removal | CC BY-NC 4.0 |

---

## Detailed Model Breakdown

### 1. BiRefNet (Bilateral Reference Network)
- **Source**: [ZhengPeng7/BiRefNet](https://github.com/ZhengPeng7/BiRefNet)
- **Strengths**: 
  - Exceptional edge precision around fine structures (hair, fur, transparent glass, mesh fabrics).
  - High resolution inference support without aggressive downscaling.
  - Native Apache-2.0 license allowing commercial integration.
- **Requirements**:
  - Requires `kornia`, `timm`, `torch`, `torchvision`, and `transformers`.
  - CPU Mode: 8–16 GB RAM recommended.
  - GPU Mode: Minimum 6 GB VRAM.

### 2. RMBG-1.4
- **Source**: [BRIA AI / RMBG-1.4](https://huggingface.co/briaai/RMBG-1.4)
- **Strengths**:
  - Very fast inference and smaller model footprint (~680 MB).
  - Great for high-throughput batch processing on moderate hardware.
- **Licensing Notice**:
  - Released under **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0)**.
  - For commercial usage, refer to BRIA AI licensing terms.

---

## Model Recommendation Engine

The application includes an automated recommendation engine (`app/models/recommendation_engine.py`) that suggests the ideal model based on:
1. **Target Content**: Human portrait vs. product/object vs. complex scene.
2. **Available Hardware**: System RAM, GPU availability, and VRAM capacity.
3. **Execution Speed vs. Quality**: Balancing turnaround time against hair-level edge precision.

---

## Downloading & Updating Models

Models can be managed directly within the application:
1. Open **Model Manager** in the application menu or click **Download Model** when selecting an uninstalled model.
2. The download system uses atomic chunked downloading with SHA256 integrity verification.
3. If an updated model revision is released, the **Model Update Manager** lets you review version differences and safely upgrade without losing the current working model.
