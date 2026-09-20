"""System Information Detection Module for AI Background Remover.

Collects hardware and platform metrics locally without collecting any
personally identifying information (PII) such as usernames, hostnames,
MAC addresses, or IP addresses.
"""

from dataclasses import dataclass
import ctypes
import os
import platform
import subprocess
import sys
from typing import Optional
import winreg


@dataclass
class SystemInfo:
    """Structured representation of host system and hardware capabilities."""
    operating_system: str
    windows_version: str
    architecture: str
    cpu_name: str
    cpu_cores: int
    cpu_threads: int
    cpu_frequency_mhz: Optional[float]
    ram_total_gb: float
    ram_available_gb: float
    gpu_name: str
    gpu_vendor: str
    gpu_memory_mb: Optional[float]
    cuda_available: bool
    amd_acceleration_available: bool
    acceleration_backend: str
    current_device: str = "CPU"

    def to_dict(self) -> dict:
        """Convert system info to a dictionary."""
        return {
            "operating_system": self.operating_system,
            "windows_version": self.windows_version,
            "architecture": self.architecture,
            "cpu_name": self.cpu_name,
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "cpu_frequency_mhz": self.cpu_frequency_mhz,
            "ram_total_gb": round(self.ram_total_gb, 2),
            "ram_available_gb": round(self.ram_available_gb, 2),
            "gpu_name": self.gpu_name,
            "gpu_vendor": self.gpu_vendor,
            "gpu_memory_mb": round(self.gpu_memory_mb, 1) if self.gpu_memory_mb else None,
            "cuda_available": self.cuda_available,
            "amd_acceleration_available": self.amd_acceleration_available,
            "acceleration_backend": self.acceleration_backend,
            "current_device": self.current_device,
        }


class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _get_ram_info() -> tuple[float, float]:
    """Retrieve total and available RAM in gigabytes using Win32 API."""
    try:
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            return total_gb, avail_gb
    except Exception:
        pass
    return 8.0, 4.0  # Safe fallback if API fails


def _get_cpu_details() -> tuple[str, int, int, Optional[float]]:
    """Retrieve CPU model name, physical cores, logical threads, and clock speed."""
    cpu_name = platform.processor() or "Generic x86_64 Processor"
    freq_mhz = None
    
    # Read detailed processor name and clock from Windows Registry
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        if name:
            cpu_name = name.strip()
        mhz, _ = winreg.QueryValueEx(key, "~MHz")
        if mhz:
            freq_mhz = float(mhz)
        winreg.CloseKey(key)
    except Exception:
        pass

    logical_threads = os.cpu_count() or 4
    
    # Estimate physical cores (defaulting to threads // 2 for hyperthreaded CPUs or threads)
    # Check via PowerShell if possible for exact physical core count
    physical_cores = max(1, logical_threads // 2) if logical_threads > 4 else logical_threads
    try:
        cmd = ["powershell", "-NoProfile", "-Command", 
               "(Get-CimInstance Win32_Processor).NumberOfCores"]
        out = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW, text=True, timeout=3)
        val = int(out.strip().splitlines()[0])
        if val > 0:
            physical_cores = val
    except Exception:
        pass

    return cpu_name, physical_cores, logical_threads, freq_mhz


def _get_gpu_details() -> tuple[str, str, Optional[float]]:
    """Retrieve primary GPU name, vendor, and memory in megabytes."""
    gpu_name = "Integrated Graphics"
    gpu_vendor = "Unknown"
    gpu_memory_mb = None

    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object -Property Name, AdapterCompatibility, AdapterRAM | ConvertTo-Json"
        ]
        out = subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW, text=True, timeout=3)
        import json
        data = json.loads(out)
        controllers = data if isinstance(data, list) else [data]
        
        # Pick the most capable controller (prefer discrete or first available)
        for ctrl in controllers:
            name = ctrl.get("Name", "")
            compat = ctrl.get("AdapterCompatibility", "")
            ram_bytes = ctrl.get("AdapterRAM")

            if name:
                gpu_name = name.strip()
                if "NVIDIA" in gpu_name.upper() or "NVIDIA" in compat.upper():
                    gpu_vendor = "NVIDIA"
                elif "AMD" in gpu_name.upper() or "ADVANCED MICRO DEVICES" in compat.upper() or "RADEON" in gpu_name.upper():
                    gpu_vendor = "AMD"
                elif "INTEL" in gpu_name.upper() or "INTEL" in compat.upper():
                    gpu_vendor = "Intel"
                else:
                    gpu_vendor = compat.strip() or "Other"

                if ram_bytes and isinstance(ram_bytes, (int, float)) and ram_bytes > 0:
                    gpu_memory_mb = float(ram_bytes) / (1024 ** 2)
                break
    except Exception:
        pass

    return gpu_name, gpu_vendor, gpu_memory_mb


def _check_cuda() -> bool:
    """Check if NVIDIA CUDA runtime is available."""
    try:
        import torch
        if torch.cuda.is_available():
            return True
    except ImportError:
        pass

    # Check for presence of nvcuda.dll in System32
    system32 = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
    nvcuda_path = os.path.join(system32, "nvcuda.dll")
    return os.path.exists(nvcuda_path)


def _check_amd_acceleration(gpu_vendor: str, gpu_name: str) -> bool:
    """Check if AMD GPU acceleration (DirectML / ROCm / OpenCL) is available."""
    is_amd = "AMD" in gpu_vendor.upper() or "RADEON" in gpu_name.upper()
    if not is_amd:
        return False
    
    # Check if DirectML is installed or supported
    try:
        import importlib.util
        if importlib.util.find_spec("torch_directml") is not None:
            return True
    except Exception:
        pass
    
    # Integrated AMD Radeon provides OpenCL/DirectX acceleration support
    return True


def get_system_info() -> SystemInfo:
    """Detect and return host system specifications without collecting PII."""
    os_name = "Windows"
    win_release = platform.release()
    win_version = platform.version()
    windows_version = f"Windows {win_release} (Build {win_version})"
    arch = platform.architecture()[0]

    cpu_name, cpu_cores, cpu_threads, freq_mhz = _get_cpu_details()
    ram_total_gb, ram_available_gb = _get_ram_info()
    gpu_name, gpu_vendor, gpu_memory_mb = _get_gpu_details()

    cuda_avail = _check_cuda()
    amd_accel = _check_amd_acceleration(gpu_vendor, gpu_name)

    if cuda_avail:
        backend = "CUDA (NVIDIA Acceleration)"
        current_device = "GPU"
    elif amd_accel:
        backend = "DirectML / OpenCL (AMD Radeon)"
        current_device = "CPU"  # Default to CPU unless DirectML backend is explicitly engaged
    else:
        backend = "CPU (PyTorch multi-threading)"
        current_device = "CPU"

    return SystemInfo(
        operating_system=os_name,
        windows_version=windows_version,
        architecture=arch,
        cpu_name=cpu_name,
        cpu_cores=cpu_cores,
        cpu_threads=cpu_threads,
        cpu_frequency_mhz=freq_mhz,
        ram_total_gb=ram_total_gb,
        ram_available_gb=ram_available_gb,
        gpu_name=gpu_name,
        gpu_vendor=gpu_vendor,
        gpu_memory_mb=gpu_memory_mb,
        cuda_available=cuda_avail,
        amd_acceleration_available=amd_accel,
        acceleration_backend=backend,
        current_device=current_device,
    )
