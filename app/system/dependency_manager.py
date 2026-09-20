"""AI Dependency Manager for AI Background Remover.

Checks whether required AI components and runtime libraries are available,
inspects installed versions, and selectively installs only genuinely missing packages.
Does not blindly reinstall packages.
"""

from dataclasses import dataclass
import importlib.metadata
import importlib.util
import os
import subprocess
import sys
from typing import Callable, Optional


@dataclass
class DependencyInfo:
    """Status and version information for a required component."""
    name: str
    package_name: str
    import_name: str
    is_installed: bool
    installed_version: Optional[str]
    required_version: str
    notes: str


REQUIRED_COMPONENTS = [
    {
        "name": "PyTorch",
        "package_name": "torch",
        "import_name": "torch",
        "required_version": ">= 2.2.0",
        "cpu_install_cmd": ["torch", "--index-url", "https://download.pytorch.org/whl/cpu"]
    },
    {
        "name": "Torchvision",
        "package_name": "torchvision",
        "import_name": "torchvision",
        "required_version": ">= 0.17.0",
        "cpu_install_cmd": ["torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"]
    },
    {
        "name": "PySide6",
        "package_name": "PySide6",
        "import_name": "PySide6",
        "required_version": ">= 6.6.0",
        "cpu_install_cmd": ["PySide6"]
    },
    {
        "name": "Pillow",
        "package_name": "Pillow",
        "import_name": "PIL",
        "required_version": ">= 10.2.0",
        "cpu_install_cmd": ["Pillow"]
    },
    {
        "name": "OpenCV",
        "package_name": "opencv-python-headless",
        "import_name": "cv2",
        "required_version": ">= 4.9.0",
        "cpu_install_cmd": ["opencv-python-headless"]
    },
    {
        "name": "Transformers",
        "package_name": "transformers",
        "import_name": "transformers",
        "required_version": ">= 4.40.0",
        "cpu_install_cmd": ["transformers", "timm", "einops", "kornia"]
    },
    {
        "name": "Hugging Face Hub",
        "package_name": "huggingface_hub",
        "import_name": "huggingface_hub",
        "required_version": ">= 0.21.0",
        "cpu_install_cmd": ["huggingface_hub"]
    },
]


class DependencyManager:
    """Inspects and manages runtime AI dependencies."""

    @staticmethod
    def check_dependencies() -> list[DependencyInfo]:
        """Inspect installed versions of all required components without reinstalling."""
        results = []

        for comp in REQUIRED_COMPONENTS:
            import_name = comp["import_name"]
            pkg_name = comp["package_name"]

            # 1. Check if package can be imported/found
            is_found = importlib.util.find_spec(import_name) is not None

            # 2. Query installed version
            version_str = None
            if is_found:
                try:
                    version_str = importlib.metadata.version(pkg_name)
                except Exception:
                    # Fallback to module __version__
                    try:
                        mod = __import__(import_name)
                        version_str = getattr(mod, "__version__", None)
                    except Exception:
                        version_str = "Installed"

            # 3. Formulate notes
            notes = ""
            if is_found and version_str:
                if import_name == "torch":
                    try:
                        import torch
                        if torch.cuda.is_available():
                            notes = f"CUDA {torch.version.cuda}"
                        else:
                            notes = "CPU Build"
                    except Exception:
                        notes = "CPU Build"
                else:
                    notes = "OK"
            else:
                notes = "Not Installed"

            results.append(DependencyInfo(
                name=comp["name"],
                package_name=pkg_name,
                import_name=import_name,
                is_installed=(is_found and version_str is not None),
                installed_version=version_str,
                required_version=comp["required_version"],
                notes=notes
            ))

        return results

    @staticmethod
    def get_missing_dependencies() -> list[dict]:
        """Return list of required component definitions that are not currently installed."""
        deps = DependencyManager.check_dependencies()
        missing = []
        for d in deps:
            if not d.is_installed:
                cfg = next((c for c in REQUIRED_COMPONENTS if c["name"] == d.name), None)
                if cfg:
                    missing.append(cfg)
        return missing

    @staticmethod
    def repair_installation(
        missing_only: bool = True,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> tuple[bool, str]:
        """Selectively install only missing packages into the active environment."""
        missing = DependencyManager.get_missing_dependencies()
        if not missing:
            return True, "All required dependencies are already installed."

        python_exe = sys.executable
        installed_any = False

        for comp in missing:
            if on_progress:
                on_progress(f"Installing missing package: {comp['name']}...")

            cmd = [python_exe, "-m", "pip", "install"] + comp["cpu_install_cmd"]

            try:
                subprocess.check_call(
                    cmd,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                installed_any = True
            except subprocess.CalledProcessError as exc:
                return False, f"Failed installing {comp['name']}: {exc}"

        return True, "Missing dependencies repaired successfully."
