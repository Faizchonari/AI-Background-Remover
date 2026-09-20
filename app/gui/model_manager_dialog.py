"""Professional Model Manager Page for AI Background Remover.

Enables discovering, downloading, cancelling, updating, and removing local AI models.
Displays model metadata, hardware requirements, real-time download metrics,
and system compatibility assessments.
"""

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget,
    QProgressBar, QMessageBox
)

from app.models.metadata import ModelMetadata
from app.models.registry import ModelRegistry
from app.downloads.download_manager import DownloadManager, DownloadProgress
from app.system.system_info import SystemInfo


class _ProgressBridge(QObject):
    """Bridge for cross-thread download updates into Qt's event loop."""
    progress_updated = Signal(str, object)  # model_id, DownloadProgress
    download_finished = Signal(str, bool, str)  # model_id, success, message


class ModelCard(QFrame):
    """Interactive card representing a single AI model in the Model Manager."""

    use_model_clicked = Signal(str)
    model_status_changed = Signal(str)

    def __init__(
        self,
        metadata: ModelMetadata,
        sys_info: SystemInfo,
        download_mgr: DownloadManager,
        registry: ModelRegistry,
        bridge: _ProgressBridge,
        parent=None
    ):
        super().__init__(parent)
        self.metadata = metadata
        self.sys_info = sys_info
        self.download_mgr = download_mgr
        self.registry = registry
        self.bridge = bridge

        self.setObjectName("systemCard")
        self.setFrameShape(QFrame.StyledPanel)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header Row: Title & Category & Version & Size
        header = QHBoxLayout()
        title = QLabel(self.metadata.display_name)
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38BDF8;")
        header.addWidget(title)

        cat_badge = QLabel(self.metadata.category)
        cat_badge.setStyleSheet("""
            background-color: #1E3A8A;
            color: #93C5FD;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        """)
        header.addWidget(cat_badge)

        header.addStretch()

        ver_size = QLabel(f"Version: {self.metadata.version}  •  Size: {self.metadata.model_size}")
        ver_size.setStyleSheet("color: #94A3B8; font-size: 12px;")
        header.addWidget(ver_size)

        layout.addLayout(header)

        # Description
        desc = QLabel(self.metadata.description)
        desc.setStyleSheet("color: #CBD5E1; font-size: 13px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Hardware requirements
        if self.metadata.local_or_cloud == "cloud":
            hw_text = (
                f"Execution: Cloud Server (GPU Accelerated)  •  "
                f"Requires Internet: Yes  •  Provider: {self.metadata.provider}  •  "
                f"License: {self.metadata.license_information}"
            )
        else:
            hw_text = (
                f"Hardware Requirements: Min {self.metadata.minimum_ram:.0f} GB RAM "
                f"(Recommended: {self.metadata.recommended_ram:.0f} GB)  •  "
                f"Resolution: {self.metadata.input_resolution[0]}x{self.metadata.input_resolution[1]}  •  "
                f"License: {self.metadata.license_information}"
            )
        hw_lbl = QLabel(hw_text)
        hw_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        hw_lbl.setWordWrap(True)
        layout.addWidget(hw_lbl)

        # Status & Compatibility Row
        status_row = QHBoxLayout()
        status_row.setSpacing(10)

        # Status label
        self.status_lbl = QLabel()
        self._update_status_badge()
        status_row.addWidget(self.status_lbl)

        # Compatibility
        comp = self.metadata.compute_compatibility(self.sys_info)
        comp_color = "#4ADE80" if "Recommended" in comp or "Good" in comp or "Cloud" in comp else "#F59E0B"
        comp_lbl = QLabel(f"System compatibility: <b>{comp}</b>")
        comp_lbl.setStyleSheet(f"color: {comp_color}; font-size: 12px;")
        status_row.addWidget(comp_lbl)

        status_row.addStretch()
        layout.addLayout(status_row)

        # Download Progress Area (hidden by default)
        self.progress_container = QWidget()
        prog_layout = QVBoxLayout(self.progress_container)
        prog_layout.setContentsMargins(0, 4, 0, 4)
        prog_layout.setSpacing(4)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 4px;
                height: 14px;
                text-align: center;
                color: #FFFFFF;
                font-size: 10px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 3px;
            }
        """)
        prog_layout.addWidget(self.progress_bar)

        self.speed_lbl = QLabel("Starting download...")
        self.speed_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        prog_layout.addWidget(self.speed_lbl)

        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)

        # Action Buttons Row
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(8)
        self._build_action_buttons()
        layout.addLayout(self.btn_layout)

    def _update_status_badge(self):
        if self.metadata.local_or_cloud == "cloud":
            self.status_lbl.setText("Status: Available (Cloud)")
            self.status_lbl.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 12px;")
        elif self.download_mgr.is_downloading(self.metadata.model_id):
            self.status_lbl.setText("Status: Downloading")
            self.status_lbl.setStyleSheet("color: #F59E0B; font-weight: 700; font-size: 12px;")
        elif self.metadata.installed_status:
            self.status_lbl.setText("Status: Installed")
            self.status_lbl.setStyleSheet("color: #4ADE80; font-weight: 700; font-size: 12px;")
        else:
            self.status_lbl.setText("Status: Available")
            self.status_lbl.setStyleSheet("color: #38BDF8; font-weight: 700; font-size: 12px;")

    def _clear_btn_layout(self):
        while self.btn_layout.count():
            item = self.btn_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _build_action_buttons(self):
        self._clear_btn_layout()

        # Cloud Model Action: Instant Use (no disk download needed)
        if self.metadata.local_or_cloud == "cloud":
            use_btn = QPushButton("Use Cloud Model")
            use_btn.setObjectName("actionBtn")
            use_btn.setStyleSheet("background-color: #059669; color: white; padding: 6px 16px; font-weight: 700;")
            use_btn.clicked.connect(lambda: self.use_model_clicked.emit(self.metadata.model_id))
            self.btn_layout.addWidget(use_btn)
            self.btn_layout.addStretch()
            return

        if self.download_mgr.is_downloading(self.metadata.model_id):
            cancel_btn = QPushButton("Cancel Download")
            cancel_btn.setStyleSheet("background-color: #DC2626; color: white; padding: 6px 14px;")
            cancel_btn.clicked.connect(self._on_cancel_download)
            self.btn_layout.addWidget(cancel_btn)
            self.btn_layout.addStretch()

        elif self.metadata.installed_status:
            use_btn = QPushButton("Use Model")
            use_btn.setObjectName("actionBtn")
            use_btn.setStyleSheet("background-color: #059669; color: white; padding: 6px 14px; font-weight: 700;")
            use_btn.clicked.connect(lambda: self.use_model_clicked.emit(self.metadata.model_id))
            self.btn_layout.addWidget(use_btn)

            update_btn = QPushButton("Update")
            update_btn.setObjectName("outlineBtn")
            update_btn.clicked.connect(self._on_download_clicked)
            self.btn_layout.addWidget(update_btn)

            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("background-color: #334155; color: #F87171; border: 1px solid #475569; padding: 6px 12px;")
            remove_btn.clicked.connect(self._on_remove_clicked)
            self.btn_layout.addWidget(remove_btn)

            self.btn_layout.addStretch()

        else:
            dl_btn = QPushButton("Download")
            dl_btn.setStyleSheet("background-color: #2563EB; color: white; padding: 6px 16px; font-weight: 700;")
            dl_btn.clicked.connect(self._on_download_clicked)
            self.btn_layout.addWidget(dl_btn)
            self.btn_layout.addStretch()

    def _on_download_clicked(self):
        # User confirmation before downloading as required
        reply = QMessageBox.question(
            self,
            "Download Model",
            f"Download '{self.metadata.display_name}' ({self.metadata.model_size}) from Hugging Face Hub?\n\n"
            f"Source: {self.metadata.download_source}\n"
            f"Target Directory: model_storage/{self.metadata.model_id}",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.speed_lbl.setText("Connecting to server...")
        self._update_status_badge()
        self._build_action_buttons()

        def _progress_cb(progress: DownloadProgress):
            self.bridge.progress_updated.emit(self.metadata.model_id, progress)

        def _finished_cb(success: bool, msg: str):
            self.bridge.download_finished.emit(self.metadata.model_id, success, msg)

        self.download_mgr.start_download(
            metadata=self.metadata,
            on_progress=_progress_cb,
            on_finished=_finished_cb
        )

    def _on_cancel_download(self):
        self.download_mgr.cancel_download(self.metadata.model_id)
        self.speed_lbl.setText("Cancelling download...")

    def _on_remove_clicked(self):
        reply = QMessageBox.question(
            self,
            "Remove Model",
            f"Are you sure you want to delete the local weights for '{self.metadata.display_name}'?\n\n"
            f"This will free {self.metadata.model_size} of storage space.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.registry.delete_model(self.metadata.model_id):
                self._update_status_badge()
                self._build_action_buttons()
                self.model_status_changed.emit(self.metadata.model_id)
                QMessageBox.information(self, "Removed", f"'{self.metadata.display_name}' has been deleted from local storage.")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete model files for '{self.metadata.display_name}'.")

    def handle_progress_update(self, progress: DownloadProgress):
        self.progress_bar.setValue(int(progress.percentage))
        dl_mb = progress.downloaded_bytes / (1024 * 1024)
        tot_mb = progress.total_bytes / (1024 * 1024)
        self.speed_lbl.setText(
            f"{progress.speed_mbps:.1f} MB/s  •  {dl_mb:.1f} MB / {tot_mb:.1f} MB  •  "
            f"{progress.eta_seconds:.0f}s remaining"
        )

    def handle_download_finished(self, success: bool, msg: str):
        self.progress_container.setVisible(False)
        self._update_status_badge()
        self._build_action_buttons()
        self.model_status_changed.emit(self.metadata.model_id)

        if success:
            QMessageBox.information(self, "Download Complete", f"'{self.metadata.display_name}' is ready to use!")
        else:
            QMessageBox.warning(self, "Download Notice", msg)


class ModelManagerDialog(QDialog):
    """Full-featured Model Manager window."""

    model_selected = Signal(str)

    def __init__(
        self,
        registry: ModelRegistry,
        download_mgr: DownloadManager,
        sys_info: SystemInfo,
        parent=None
    ):
        super().__init__(parent)
        self.registry = registry
        self.download_mgr = download_mgr
        self.sys_info = sys_info

        self.setWindowTitle("AI Model Manager")
        self.resize(780, 640)
        self.setMinimumSize(680, 480)

        self.bridge = _ProgressBridge()
        self.bridge.progress_updated.connect(self._on_progress_updated)
        self.bridge.download_finished.connect(self._on_download_finished)

        self.cards: dict[str, ModelCard] = {}
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        # Header Title
        title = QLabel("MODEL MANAGER")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px;")
        root_layout.addWidget(title)

        subtitle = QLabel("Browse available AI models, inspect resource requirements, and manage local weights.")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 4px;")
        root_layout.addWidget(subtitle)

        # Scroll Area for Model Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.card_layout = QVBoxLayout(container)
        self.card_layout.setContentsMargins(0, 0, 10, 0)
        # 1. LOCAL MODELS SECTION
        local_header = QLabel("LOCAL MODELS (Runs 100% Offline on Your PC)")
        local_header.setStyleSheet("font-size: 13px; font-weight: 800; color: #4ADE80; margin-top: 4px; margin-bottom: 2px;")
        self.card_layout.addWidget(local_header)

        for meta in self.registry.list_local():
            card = ModelCard(
                metadata=meta,
                sys_info=self.sys_info,
                download_mgr=self.download_mgr,
                registry=self.registry,
                bridge=self.bridge,
                parent=self
            )
            card.use_model_clicked.connect(self._on_use_model)
            self.cards[meta.model_id] = card
            self.card_layout.addWidget(card)

        # 2. CLOUD MODELS SECTION
        cloud_models = self.registry.list_cloud()
        if cloud_models:
            cloud_header = QLabel("CLOUD MODELS (Remote Inference • Requires Internet)")
            cloud_header.setStyleSheet("font-size: 13px; font-weight: 800; color: #38BDF8; margin-top: 14px; margin-bottom: 2px;")
            self.card_layout.addWidget(cloud_header)

            for meta in cloud_models:
                card = ModelCard(
                    metadata=meta,
                    sys_info=self.sys_info,
                    download_mgr=self.download_mgr,
                    registry=self.registry,
                    bridge=self.bridge,
                    parent=self
                )
                card.use_model_clicked.connect(self._on_use_model)
                self.cards[meta.model_id] = card
                self.card_layout.addWidget(card)

        self.card_layout.addStretch()
        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        # Bottom Bar
        bottom = QHBoxLayout()
        bottom.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #2563EB; color: white; padding: 7px 20px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)

        root_layout.addLayout(bottom)

    def _on_progress_updated(self, model_id: str, progress: DownloadProgress):
        if model_id in self.cards:
            self.cards[model_id].handle_progress_update(progress)

    def _on_download_finished(self, model_id: str, success: bool, msg: str):
        if model_id in self.cards:
            self.cards[model_id].handle_download_finished(success, msg)

    def _on_use_model(self, model_id: str):
        self.model_selected.emit(model_id)
        self.accept()
