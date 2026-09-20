"""Main Window for AI Background Remover.

Implements the complete user interface:
- Drag & drop image ingestion (JPG, JPEG, PNG, WEBP)
- Image queue management with thumbnails, status, and removal
- Model selection with dynamic [Download Model] button for uninstalled models
- Configurable output directory and format (default: transparent PNG)
- Non-destructive batch processing with fault-tolerant worker thread
- Side-by-side Original → Result preview
- Output folder direct launch
"""

from pathlib import Path
import sys
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QFrame,
    QFileDialog, QProgressBar, QMessageBox, QSplitter,
    QStatusBar, QLineEdit
)

from app.system.system_info import SystemInfo, get_system_info
from app.system.recommendation import ModelRecommendationEngine, RecommendationResult
from app.gui.system_dialog import SystemDetailsDialog
from app.gui.model_manager_dialog import ModelManagerDialog
from app.gui.queue_widget import QueueWidget
from app.gui.preview_widget import InteractivePreviewWidget
from app.gui.settings_dialog import SettingsDialog
from app.gui.about_dialog import AboutDialog
from app.core.config import ConfigManager
from app.models.registry import ModelRegistry
from app.models.birefnet_portrait import BiRefNetPortraitModel
from app.models.base_model import BackgroundRemovalModel
from app.downloads.download_manager import DownloadManager
from app.processing.batch_worker import BatchProcessingWorker, QueueItem



class MainWindow(QMainWindow):
    """Main application window for AI Background Remover."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Background Remover")
        self.resize(1200, 780)
        self.setMinimumSize(960, 640)
        self.setAcceptDrops(True)

        # 0. Application Configuration
        self.config_mgr = ConfigManager()

        # 1. Hardware Detection & Recommendation Engine
        self.sys_info: SystemInfo = get_system_info()
        self.rec_engine = ModelRecommendationEngine()
        self.rec_result: RecommendationResult = self.rec_engine.recommend(self.sys_info)

        # 2. Model Registry & Download Manager
        self.registry = ModelRegistry()
        self.download_mgr = DownloadManager(self.registry.storage_dir)

        # Register BiRefNet Portrait implementation
        self.registry.register(
            metadata=self.registry.get_metadata("birefnet-portrait"),
            model_class=BiRefNetPortraitModel
        )

        # 3. Default Paths & Settings
        if getattr(sys, "frozen", False):
            self.project_root = Path(sys.executable).resolve().parent
        else:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        configured_out = self.config_mgr.get("output_dir")
        if configured_out:
            self.output_dir = Path(configured_out)
        else:
            self.output_dir = self.project_root / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.worker: Optional[BatchProcessingWorker] = None
        self.active_model_instance: Optional[BackgroundRemovalModel] = None

        # 4. Initialize UI
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(16, 14, 16, 12)
        root_layout.setSpacing(10)

        # Top Header Bar
        header = self._create_header()
        root_layout.addLayout(header)

        # Top Control Bar: Model, Output Folder, Format
        control_bar = self._create_control_bar()
        root_layout.addWidget(control_bar)

        # Main Workspace: Left Queue + Right Split Preview
        workspace_splitter = QSplitter(Qt.Horizontal)
        workspace_splitter.setChildrenCollapsible(False)

        # Left: Image Queue Widget
        self.queue_widget = QueueWidget(self)
        self.queue_widget.item_selected.connect(self._on_queue_item_selected)
        self.queue_widget.queue_count_changed.connect(self._on_queue_count_changed)
        workspace_splitter.addWidget(self.queue_widget)
        workspace_splitter.setStretchFactor(0, 4)

        # Right: Dual Interactive Preview (Slider, Side-by-Side, Zoom, Checkerboard)
        self.preview_widget = InteractivePreviewWidget(self)
        workspace_splitter.addWidget(self.preview_widget)
        workspace_splitter.setStretchFactor(1, 6)

        root_layout.addWidget(workspace_splitter, stretch=1)


        # Bottom Action & Progress Bar
        bottom_bar = self._create_bottom_bar()
        root_layout.addLayout(bottom_bar)

        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def _create_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 2)

        title_col = QVBoxLayout()
        title_col.setSpacing(1)

        title_lbl = QLabel("AI Background Remover")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel("100% Offline AI image background removal • Preserves original resolution")
        sub_lbl.setStyleSheet("font-size: 12px; color: #94A3B8;")
        title_col.addWidget(sub_lbl)

        header.addLayout(title_col)
        header.addStretch()

        # Hardware Badge & System Details Button
        badge_text = f"⚙ {self.rec_result.recommended_device} Mode ({self.sys_info.cpu_cores}C/{self.sys_info.cpu_threads}T)"
        if self.sys_info.cuda_available:
            badge_text = "⚡ NVIDIA CUDA Active"

        device_badge = QLabel(badge_text)
        device_badge.setStyleSheet("""
            background-color: #0369A1;
            color: #E0F2FE;
            padding: 5px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 11px;
        """)
        header.addWidget(device_badge)

        sys_details_btn = QPushButton("System Specs")
        sys_details_btn.setObjectName("outlineBtn")
        sys_details_btn.clicked.connect(self._open_system_details)
        header.addWidget(sys_details_btn)

        settings_btn = QPushButton("Settings ⚙")
        settings_btn.setObjectName("outlineBtn")
        settings_btn.clicked.connect(self._open_settings)
        header.addWidget(settings_btn)

        about_btn = QPushButton("About ℹ")
        about_btn.setObjectName("outlineBtn")
        about_btn.clicked.connect(self._open_about)
        header.addWidget(about_btn)

        return header

    def _create_control_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("systemCard")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # 1. Model Selection
        model_lbl = QLabel("Model:")
        model_lbl.setStyleSheet("font-weight: 700; color: #CBD5E1;")
        layout.addWidget(model_lbl)

        self.model_combo = QComboBox()
        for meta in self.registry.list_all():
            self.model_combo.addItem(f"{meta.display_name}  [{meta.category}]", meta.model_id)

        # Select recommended or remembered model
        target_model = self.rec_result.model_id
        if self.config_mgr.get("remember_selected_model", True):
            saved_model = self.config_mgr.get("default_model")
            if saved_model and self.model_combo.findData(saved_model) >= 0:
                target_model = saved_model

        idx = self.model_combo.findData(target_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)

        # Dynamic [Download Model] button (visible only if selected model is not installed)
        self.download_model_btn = QPushButton("Download Model")
        self.download_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #D97706;
                color: white;
                font-weight: 700;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #B45309; }
        """)
        self.download_model_btn.clicked.connect(self._on_quick_download_model)
        layout.addWidget(self.download_model_btn)

        manage_btn = QPushButton("Manage Models")
        manage_btn.setObjectName("outlineBtn")
        manage_btn.clicked.connect(self._open_model_manager)
        layout.addWidget(manage_btn)

        layout.addSpacing(10)

        # 2. Output Folder Selection
        out_lbl = QLabel("Output Folder:")
        out_lbl.setStyleSheet("font-weight: 700; color: #CBD5E1;")
        layout.addWidget(out_lbl)

        self.out_path_edit = QLineEdit(str(self.output_dir))
        self.out_path_edit.setReadOnly(True)
        self.out_path_edit.setStyleSheet("""
            QLineEdit {
                background-color: #0F172A;
                border: 1px solid #334155;
                color: #CBD5E1;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.out_path_edit)

        select_folder_btn = QPushButton("Select Folder")
        select_folder_btn.setObjectName("outlineBtn")
        select_folder_btn.clicked.connect(self._select_output_folder)
        layout.addWidget(select_folder_btn)

        layout.addSpacing(10)

        # 3. Output Format Selector
        fmt_lbl = QLabel("Format:")
        fmt_lbl.setStyleSheet("font-weight: 700; color: #CBD5E1;")
        layout.addWidget(fmt_lbl)

        self.format_combo = QComboBox()
        self.format_combo.addItem("PNG (Transparent)", "PNG")
        self.format_combo.addItem("WEBP (Transparent)", "WEBP")
        self.format_combo.addItem("JPG (White Background)", "JPG")
        layout.addWidget(self.format_combo)

        self._check_model_installation_state()
        return bar


    def _create_bottom_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setObjectName("actionBtn")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: white;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 24px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #047857; }
            QPushButton:disabled { background-color: #334155; color: #64748B; }
        """)
        self.start_btn.clicked.connect(self._start_processing)
        bar.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("Cancel Processing")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC2626;
                color: white;
                font-weight: 700;
                padding: 10px 18px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #B91C1C; }
            QPushButton:disabled { background-color: #334155; color: #64748B; }
        """)
        self.cancel_btn.clicked.connect(self._cancel_processing)
        bar.addWidget(self.cancel_btn)

        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.setObjectName("outlineBtn")
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        bar.addWidget(self.open_folder_btn)

        bar.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(240)
        bar.addWidget(self.progress_bar)

        self.progress_text = QLabel("")
        self.progress_text.setStyleSheet("color: #94A3B8; font-size: 12px;")
        bar.addWidget(self.progress_text)

        return bar

    def _update_status_bar(self):
        active_model = self.model_combo.currentText()
        count = len(self.queue_widget.items)
        self.status_bar.showMessage(
            f"Ready | Model: {active_model} | Queue: {count} image{'s' if count != 1 else ''} | "
            f"Output: {self.output_dir.name}/"
        )

    def _check_model_installation_state(self):
        """Show or hide the [Download Model] button based on installed status."""
        model_id = self.model_combo.currentData()
        meta = self.registry.get_metadata(model_id)
        if meta and not meta.installed_status:
            self.download_model_btn.setVisible(True)
            self.download_model_btn.setText(f"Download {meta.display_name}")
        else:
            self.download_model_btn.setVisible(False)

    def _on_model_changed(self):
        new_model_id = self.model_combo.currentData()
        if self.active_model_instance and self.active_model_instance.metadata.model_id != new_model_id:
            self.active_model_instance.unload()
            self.active_model_instance = None

        if self.config_mgr.get("remember_selected_model", True):
            selected_model = self.model_combo.currentData()
            if selected_model:
                self.config_mgr.set("default_model", selected_model)
                self.config_mgr.save()
        self._check_model_installation_state()
        self._update_status_bar()

    def _on_quick_download_model(self):
        """Triggered when [Download Model] is clicked next to model combo."""
        self._open_model_manager()

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", str(self.output_dir)
        )
        if folder:
            self.output_dir = Path(folder)
            self.out_path_edit.setText(str(self.output_dir))
            self.config_mgr.set("output_dir", str(self.output_dir))
            self.config_mgr.save()
            self._update_status_bar()

    def _open_output_folder(self):
        """Open output directory directly in Windows Explorer."""
        if self.output_dir.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.output_dir)))
        else:
            QMessageBox.warning(self, "Notice", f"Output folder does not exist yet: {self.output_dir}")

    def _on_queue_item_selected(self, item: Optional[QueueItem]):
        """Render original and result preview for selected queue item."""
        self.preview_widget.display_item(item)


    def _on_queue_count_changed(self, count: int):
        self._update_status_bar()
        self.start_btn.setEnabled(count > 0 and (self.worker is None or not self.worker.isRunning()))

    def _start_processing(self):
        """Start batch processing images in background worker."""
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Processing in Progress", "A batch job is currently running. Please wait or cancel.")
            return

        if not self.queue_widget.items:
            QMessageBox.information(self, "Queue Empty", "Please select or drag-and-drop images first.")
            return

        model_id = self.model_combo.currentData()
        meta = self.registry.get_metadata(model_id)

        # Check model installation
        if meta and not meta.installed_status:
            reply = QMessageBox.question(
                self,
                "Model Not Downloaded",
                f"'{meta.display_name}' ({meta.model_size}) must be downloaded before processing.\n\n"
                "Would you like to open the Model Manager to download it now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._open_model_manager()
            return

        # Instantiate or reuse loaded model
        if self.active_model_instance is None or self.active_model_instance.metadata.model_id != model_id:
            if self.active_model_instance is not None:
                self.active_model_instance.unload()
            model_cls = self.registry.get_model_class(model_id)
            if model_cls:
                self.active_model_instance = model_cls(metadata=meta)
            else:
                # Fallback to BiRefNet Portrait
                self.active_model_instance = BiRefNetPortraitModel(metadata=meta)

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.queue_widget.items))
        self.progress_bar.setValue(0)
        self.progress_text.setText(f"0 / {len(self.queue_widget.items)}")

        # Initialize and launch background worker
        self.worker = BatchProcessingWorker(
            items=self.queue_widget.items,
            output_dir=self.output_dir,
            output_format=self.format_combo.currentText(),
            model=self.active_model_instance,
            parent=self
        )
        self.worker.item_started.connect(self._on_worker_item_started)
        self.worker.item_completed.connect(self._on_worker_item_completed)
        self.worker.item_failed.connect(self._on_worker_item_failed)
        self.worker.batch_finished.connect(self._on_worker_batch_finished)
        self.worker.start()

    def _cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.cancel_btn.setEnabled(False)
            self.status_bar.showMessage("Cancelling batch processing after current image...")

    def _on_worker_item_started(self, index: int, filename: str):
        self.queue_widget.update_item_status(index, "Processing...")
        self.status_bar.showMessage(f"Processing ({index + 1}/{len(self.queue_widget.items)}): {filename}")

    def _on_worker_item_completed(self, index: int, output_path: str):
        self.queue_widget.update_item_status(index, "Completed", output_path=Path(output_path))
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.progress_text.setText(f"{self.progress_bar.value()} / {self.progress_bar.maximum()}")
        if self.queue_widget.table.currentRow() == index:
            self.preview_widget.display_item(self.queue_widget.items[index])

    def _on_worker_item_failed(self, index: int, error: str):
        self.queue_widget.update_item_status(index, "Failed", error=error)
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        self.progress_text.setText(f"{self.progress_bar.value()} / {self.progress_bar.maximum()}")

    def _on_worker_batch_finished(self, success_count: int, fail_count: int, last_error: str = ""):
        self.start_btn.setEnabled(len(self.queue_widget.items) > 0)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_text.setText("")
        self._update_status_bar()

        if success_count == 0 and fail_count > 0:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Processing Failed")
            msg_box.setText("Background removal failed. See details in the log.")
            msg_box.setInformativeText("The application will remain open. You can check the log (logs/app.log) or view error details below.")
            if last_error:
                msg_box.setDetailedText(last_error)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        elif fail_count > 0:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Batch Completed with Errors")
            msg_box.setText(f"Batch processing completed with {fail_count} failure(s).\n\nSuccessful: {success_count}\nFailed: {fail_count}\n\nOutput folder: {self.output_dir}")
            if last_error:
                msg_box.setDetailedText(last_error)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec()
        else:
            msg = f"Batch processing complete!\n\nSuccessful: {success_count}\nFailed: 0\n\nOutput folder: {self.output_dir}"
            QMessageBox.information(self, "Processing Finished", msg)

        if self.config_mgr.get("auto_open_output", False) and success_count > 0:
            self._open_output_folder()

    def closeEvent(self, event):
        """Safely handle application closing during background processing."""
        if self.worker is not None and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Processing in Progress",
                "Batch processing is currently running.\nDo you want to cancel processing and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait(2000)
                if self.active_model_instance:
                    self.active_model_instance.unload()
                event.accept()
            else:
                event.ignore()
        else:
            if self.active_model_instance:
                self.active_model_instance.unload()
            event.accept()

    def _open_system_details(self):
        dialog = SystemDetailsDialog(self.sys_info, self.rec_result, self)
        dialog.exec()

    def _open_settings(self):
        dialog = SettingsDialog(
            config_mgr=self.config_mgr,
            sys_info=self.sys_info,
            rec_engine=self.rec_engine,
            parent=self
        )
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _open_about(self):
        dialog = AboutDialog(self.config_mgr, self)
        dialog.exec()

    def _on_settings_saved(self):
        new_out = self.config_mgr.get("output_dir")
        if new_out:
            self.output_dir = Path(new_out)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.out_path_edit.setText(str(self.output_dir))
        self._update_status_bar()

    def _open_model_manager(self):
        dialog = ModelManagerDialog(
            registry=self.registry,
            download_mgr=self.download_mgr,
            sys_info=self.sys_info,
            parent=self
        )
        dialog.model_selected.connect(self._on_model_selected_from_manager)
        dialog.exec()
        self._check_model_installation_state()

    def _on_model_selected_from_manager(self, model_id: str):
        idx = self.model_combo.findData(model_id)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self._check_model_installation_state()
        self.status_bar.showMessage(f"Active model set to: {model_id}")

    # Drag & Drop support for the entire window
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        if paths:
            self.queue_widget.add_paths(paths)
            event.acceptProposedAction()
            if self.config_mgr.get("auto_start_on_drop", False):
                self._start_processing()
