# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification file for AI Background Remover.

Packages the application as a standalone Windows 64-bit desktop distribution (onedir)
including PySide6, PyTorch CPU runtime, OpenCV, Pillow, and Hugging Face dependencies.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = [
    ('config', 'config'),
    ('LICENSE', '.'),
    ('assets', 'assets'),
]

# Hidden imports for dynamic AI, Qt, and processing modules
hiddenimports = [
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFilter',
    'PIL.PngImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.WebPImagePlugin',
    'cv2',
    'torch',
    'torchvision',
    'torchvision.transforms',
    'transformers',
    'huggingface_hub',
    'timm',
    'einops',
    'kornia',
    'app.gui.about_dialog',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'app',
    'app.core',
    'app.core.credentials',
    'app.core.config',
    'app.gui',
    'app.gui.main_window',
    'app.gui.styles',
    'app.gui.system_dialog',
    'app.gui.model_manager_dialog',
    'app.gui.queue_widget',
    'app.gui.preview_widget',
    'app.gui.settings_dialog',
    'app.system',
    'app.system.system_info',
    'app.system.recommendation',
    'app.system.dependency_manager',
    'app.models',
    'app.models.metadata',
    'app.models.base_model',
    'app.models.registry',
    'app.models.birefnet_portrait',
    'app.processing',
    'app.processing.batch_worker',
    'app.processing.processing_manager',
    'app.processing.backends',
    'app.processing.backends.base',
    'app.processing.backends.local_backend',
    'app.processing.backends.cloud_backend',
    'app.processing.backends.providers',
    'app.processing.backends.providers.base_provider',
    'app.processing.backends.providers.huggingface_provider',
    'app.processing.backends.providers.custom_api_provider',
    'app.processing.backends.providers.future_provider',
    'app.downloads',
    'app.downloads.download_manager',
    'app.utils',
    'app.utils.logger',
]

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'IPython', 'notebook', 'pytest', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI Background Remover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AI-Background-Remover',
)
