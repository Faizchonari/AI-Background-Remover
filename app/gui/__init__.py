"""GUI package for AI Background Remover."""

from app.gui.main_window import MainWindow
from app.gui.system_dialog import SystemDetailsDialog
from app.gui.model_manager_dialog import ModelManagerDialog
from app.gui.queue_widget import QueueWidget
from app.gui.preview_widget import InteractivePreviewWidget, ComparisonCanvas
from app.gui.settings_dialog import SettingsDialog
from app.gui.styles import DARK_THEME

__all__ = [
    "MainWindow",
    "SystemDetailsDialog",
    "ModelManagerDialog",
    "QueueWidget",
    "InteractivePreviewWidget",
    "ComparisonCanvas",
    "SettingsDialog",
    "DARK_THEME",
]
