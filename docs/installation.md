# Installation Guide

This guide covers installing **AI Background Remover** either via the pre-built Windows installer or from source.

---

## Method 1: Windows Installer (Recommended for End Users)

The Windows installer (`AI-Background-Remover-Setup.exe`) is completely standalone. It does **not** require Python, Git, VS Code, or any command-line tools.

### Steps:
1. Download `AI-Background-Remover-Setup.exe` from the official [GitHub Releases](https://github.com/Faizchonari/AI-Background-Remover/releases) page.
2. Double-click the installer to launch the setup wizard.
3. Select your desired installation path (default: `C:\Program Files\AI Background Remover` or `%LocalAppData%\Programs\AI Background Remover`).
4. (Optional) Check the box to create a Desktop shortcut.
5. Click **Install**.
6. Launch **AI Background Remover** from the Start Menu or Desktop.

> **Model Weights & Offline Usage Notice:**
> The installer does **not** bundle multiple gigabytes of AI models by default to keep the initial download light. On first launch, navigate to **Model Manager** or select a model in the processing queue to download your desired model (e.g. BiRefNet Portrait or General). Downloaded models are safely stored in your local directory and preserved across application updates and uninstalls.
>
> **Once the required models and dependencies are installed, image processing can run completely offline.**

---

## Method 2: Running from Source (For Developers & Contributors)

### Prerequisites:
- Windows 10/11 (64-bit)
- Python 3.10 or 3.11 (Ensure "Add Python to PATH" is checked during installation)
- Git for Windows

### 1. Clone the Repository
```powershell
git clone https://github.com/Faizchonari/AI-Background-Remover.git
cd AI-Background-Remover
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Run the Application
```powershell
python -m app.main
```

---

## Uninstallation

To uninstall the application:
1. Open Windows **Settings** > **Apps** > **Installed apps**.
2. Locate **AI Background Remover** and click **Uninstall**.
3. Or run `unins000.exe` located in the application installation directory.

> **Data Safety:**
> Your downloaded AI models in `model_storage` and generated images in `output` are retained by default so you do not lose downloaded weights.
