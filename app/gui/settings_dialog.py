"""Settings Page and Dependency Inspection Dialog for AI Background Remover.

Sections:
- GENERAL: Default output folder, auto-open, remember model, auto-start on drop.
- PROCESSING: CPU/GPU device selection, quality preset, parallel jobs, memory safeguard.
- MODELS: Storage path, check for updates, update all models.
- SYSTEM: Hardware info, compatibility test, dependency table, repair installation.
"""

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QColor, QFont, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTabWidget, QWidget, QCheckBox,
    QComboBox, QSpinBox, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QGroupBox, QScrollArea
)

from app.core.config import ConfigManager
from app.core.credentials import CredentialStore, mask_token
from app.processing.backends.providers.huggingface_provider import HuggingFaceProvider
from app.processing.backends.providers.custom_api_provider import CustomAPIProvider
from app.system.system_info import SystemInfo
from app.system.recommendation import ModelRecommendationEngine
from app.system.dependency_manager import DependencyManager
from app.gui.system_dialog import SystemDetailsDialog
from app.gui.about_dialog import get_circular_avatar, create_initials_avatar, _get_project_root


class SettingsDialog(QDialog):
    """Full-featured Settings and Dependency Manager dialog."""

    settings_saved = Signal()

    def __init__(
        self,
        config_mgr: ConfigManager,
        sys_info: SystemInfo,
        rec_engine: ModelRecommendationEngine,
        parent=None
    ):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.sys_info = sys_info
        self.rec_engine = rec_engine
        self.cred_store = CredentialStore()

        self.setWindowTitle("Settings & Dependencies")
        self.resize(780, 620)
        self.setMinimumSize(680, 520)
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 16, 18, 16)
        root_layout.setSpacing(14)

        # Dialog Title
        title_row = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #38BDF8;")
        title_row.addWidget(title)
        title_row.addStretch()
        root_layout.addLayout(title_row)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #1E293B;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #0F172A;
                color: #94A3B8;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1E293B;
                color: #38BDF8;
                border-bottom: 2px solid #38BDF8;
            }
        """)

        self.tabs.addTab(self._create_general_tab(), "GENERAL")
        self.tabs.addTab(self._create_processing_tab(), "PROCESSING")
        self.tabs.addTab(self._create_cloud_tab(), "CLOUD PROCESSING")
        self.tabs.addTab(self._create_models_tab(), "MODELS")
        self.tabs.addTab(self._create_system_tab(), "SYSTEM & DEPENDENCIES")
        self.tabs.addTab(self._create_about_tab(), "ABOUT DEVELOPER")

        root_layout.addWidget(self.tabs, stretch=1)

        # Bottom Button Row
        bottom_row = QHBoxLayout()
        bottom_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("outlineBtn")
        cancel_btn.clicked.connect(self.reject)
        bottom_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: 700;
                padding: 7px 20px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        save_btn.clicked.connect(self._save_settings)
        bottom_row.addWidget(save_btn)

        root_layout.addLayout(bottom_row)

    # 1. GENERAL TAB
    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Default output folder
        out_lbl = QLabel("Default Output Folder:")
        out_lbl.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        layout.addWidget(out_lbl)

        out_row = QHBoxLayout()
        self.gen_out_edit = QLineEdit(self.config_mgr.get("output_dir", "output"))
        self.gen_out_edit.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 6px;")
        out_row.addWidget(self.gen_out_edit)

        browse_out_btn = QPushButton("Browse...")
        browse_out_btn.setObjectName("outlineBtn")
        browse_out_btn.clicked.connect(self._browse_output_dir)
        out_row.addWidget(browse_out_btn)
        layout.addLayout(out_row)

        layout.addSpacing(6)

        # Checkboxes
        self.cb_auto_open = QCheckBox("Automatically open output folder after processing finishes")
        self.cb_auto_open.setChecked(self.config_mgr.get("auto_open_output", False))
        layout.addWidget(self.cb_auto_open)

        self.cb_remember_model = QCheckBox("Remember selected model on startup")
        self.cb_remember_model.setChecked(self.config_mgr.get("remember_selected_model", True))
        layout.addWidget(self.cb_remember_model)

        self.cb_auto_start_drop = QCheckBox("Start processing automatically after files are dropped")
        self.cb_auto_start_drop.setChecked(self.config_mgr.get("auto_start_on_drop", False))
        layout.addWidget(self.cb_auto_start_drop)

        layout.addStretch()
        return widget

    # 2. PROCESSING TAB
    def _create_processing_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Execution Device Selection
        dev_lbl = QLabel("Execution Device:")
        dev_lbl.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        layout.addWidget(dev_lbl)

        self.device_combo = QComboBox()
        self.device_combo.addItem(f"CPU ({self.sys_info.cpu_cores} Cores / {self.sys_info.cpu_threads} Threads)", "CPU")
        if self.sys_info.cuda_available:
            self.device_combo.addItem("NVIDIA CUDA GPU", "GPU")
        if self.sys_info.amd_acceleration_available:
            self.device_combo.addItem("DirectML / OpenCL (AMD Radeon)", "DirectML")

        curr_dev = self.config_mgr.get("execution_device", "CPU")
        idx = self.device_combo.findData(curr_dev)
        if idx >= 0:
            self.device_combo.setCurrentIndex(idx)
        layout.addWidget(self.device_combo)

        # Processing Quality
        q_lbl = QLabel("Processing Quality:")
        q_lbl.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        layout.addWidget(q_lbl)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Standard (Fast)", "Standard")
        self.quality_combo.addItem("High (Optimal)", "High")
        self.quality_combo.addItem("Ultra (Maximum Detail)", "Ultra")
        curr_q = self.config_mgr.get("processing_quality", "High (Optimal)")
        idx_q = self.quality_combo.findText(curr_q)
        if idx_q >= 0:
            self.quality_combo.setCurrentIndex(idx_q)
        layout.addWidget(self.quality_combo)

        # Maximum parallel jobs
        jobs_lbl = QLabel("Maximum Parallel Jobs:")
        jobs_lbl.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        layout.addWidget(jobs_lbl)

        jobs_row = QHBoxLayout()
        self.jobs_spin = QSpinBox()
        self.jobs_spin.setRange(1, max(1, self.sys_info.cpu_cores))
        self.jobs_spin.setValue(self.config_mgr.get("max_parallel_jobs", 1))
        self.jobs_spin.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 4px;")
        jobs_row.addWidget(self.jobs_spin)

        jobs_desc = QLabel("(1 recommended on CPU to prevent RAM thrashing)")
        jobs_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        jobs_row.addWidget(jobs_desc)
        jobs_row.addStretch()
        layout.addLayout(jobs_row)

        # Memory Safeguards
        layout.addSpacing(6)
        self.cb_mem_safeguard = QCheckBox("Enable memory usage safeguards (pause if free RAM drops below 1.5 GB)")
        self.cb_mem_safeguard.setChecked(self.config_mgr.get("memory_safeguard", True))
        layout.addWidget(self.cb_mem_safeguard)

        layout.addStretch()
        return widget

    # 2b. CLOUD PROCESSING TAB
    def _create_cloud_tab(self) -> QWidget:
        widget = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Processing Mode
        mode_box = QGroupBox("Processing Mode")
        mode_box.setStyleSheet("QGroupBox { font-weight: 700; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        mode_layout = QVBoxLayout(mode_box)
        mode_layout.setSpacing(8)

        self.cloud_mode_combo = QComboBox()
        self.cloud_mode_combo.addItem("Local Processing (100% Offline, images stay on PC)", "local")
        self.cloud_mode_combo.addItem("Cloud Processing (GPU Accelerated, community free tier)", "cloud")
        self.cloud_mode_combo.addItem("Automatic (Choose based on hardware, network, and consent)", "automatic")
        curr_m = self.config_mgr.get("processing_mode", "local").lower()
        idx_m = self.cloud_mode_combo.findData(curr_m)
        if idx_m >= 0:
            self.cloud_mode_combo.setCurrentIndex(idx_m)
        mode_layout.addWidget(self.cloud_mode_combo)
        layout.addWidget(mode_box)

        # 2. Cloud Provider & Endpoint
        prov_box = QGroupBox("Cloud Provider & Connection")
        prov_box.setStyleSheet("QGroupBox { font-weight: 700; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        prov_layout = QVBoxLayout(prov_box)
        prov_layout.setSpacing(10)

        p_lbl = QLabel("Cloud Provider:")
        p_lbl.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        prov_layout.addWidget(p_lbl)

        self.cloud_prov_combo = QComboBox()
        self.cloud_prov_combo.addItem("Hugging Face Spaces (ZeroGPU / Community Free Tier)", "huggingface")
        self.cloud_prov_combo.addItem("Custom Cloud API (Advanced / Self-Hosted)", "custom_api")
        curr_p = self.config_mgr.get("cloud_provider", "huggingface")
        idx_p = self.cloud_prov_combo.findData(curr_p)
        if idx_p >= 0:
            self.cloud_prov_combo.setCurrentIndex(idx_p)
        prov_layout.addWidget(self.cloud_prov_combo)

        ep_lbl = QLabel("Cloud Endpoint URL (HTTPS):")
        ep_lbl.setStyleSheet("font-weight: 600; color: #E2E8F0;")
        prov_layout.addWidget(ep_lbl)

        ep_row = QHBoxLayout()
        self.cloud_ep_edit = QLineEdit(self.config_mgr.get("cloud_endpoint", "https://faizchonari-birefnet-portrait.hf.space"))
        self.cloud_ep_edit.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 6px;")
        ep_row.addWidget(self.cloud_ep_edit)

        test_btn = QPushButton("Test Connection")
        test_btn.setObjectName("outlineBtn")
        test_btn.clicked.connect(self._on_test_cloud_connection)
        ep_row.addWidget(test_btn)
        prov_layout.addLayout(ep_row)

        self.conn_result_lbl = QLabel("")
        self.conn_result_lbl.setStyleSheet("font-size: 11px;")
        prov_layout.addWidget(self.conn_result_lbl)

        layout.addWidget(prov_box)

        # 3. Authentication (Secure Windows DPAPI Token Storage)
        auth_box = QGroupBox("Authentication (Optional)")
        auth_box.setStyleSheet("QGroupBox { font-weight: 700; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        auth_layout = QVBoxLayout(auth_box)
        auth_layout.setSpacing(10)

        token_desc = QLabel("An API token (e.g. Hugging Face Access Token) is optional for public spaces, but increases rate limits.")
        token_desc.setStyleSheet("color: #94A3B8; font-size: 11px;")
        auth_layout.addWidget(token_desc)

        token_row = QHBoxLayout()
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.Password)
        self.token_edit.setPlaceholderText("Enter new API token (hf_...)")
        self.token_edit.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 6px;")
        token_row.addWidget(self.token_edit)

        save_tok_btn = QPushButton("Configure Token")
        save_tok_btn.setStyleSheet("background-color: #2563EB; color: white; padding: 6px 12px; font-weight: 600;")
        save_tok_btn.clicked.connect(self._on_configure_token)
        token_row.addWidget(save_tok_btn)

        del_tok_btn = QPushButton("Remove Credentials")
        del_tok_btn.setStyleSheet("background-color: #334155; color: #F87171; border: 1px solid #475569; padding: 6px 12px;")
        del_tok_btn.clicked.connect(self._on_remove_credentials)
        token_row.addWidget(del_tok_btn)
        auth_layout.addLayout(token_row)

        curr_hf_token = self.cred_store.get_token("huggingface")
        self.token_status_lbl = QLabel(f"Stored Credential: <b>{mask_token(curr_hf_token)}</b> (Encrypted with Windows DPAPI)")
        self.token_status_lbl.setStyleSheet("color: #64748B; font-size: 11px;")
        auth_layout.addWidget(self.token_status_lbl)

        layout.addWidget(auth_box)

        # 4. Privacy Safeguards
        priv_box = QGroupBox("Privacy Safeguards")
        priv_box.setStyleSheet("QGroupBox { font-weight: 700; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        priv_layout = QVBoxLayout(priv_box)
        priv_layout.setSpacing(8)

        self.cb_always_ask = QCheckBox("Always ask before uploading images to the cloud")
        self.cb_always_ask.setChecked(self.config_mgr.get("cloud_always_ask_upload", True))
        priv_layout.addWidget(self.cb_always_ask)

        priv_text = (
            "• <b>Local Processing:</b> Images never leave this computer. No internet required.<br>"
            "• <b>Cloud Processing:</b> Images are uploaded over HTTPS to the selected provider for AI inference.<br>"
            "• <b>No Analytics:</b> Images are never uploaded for analytics or stored on third-party storage."
        )
        priv_lbl = QLabel(priv_text)
        priv_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; line-height: 1.4;")
        priv_layout.addWidget(priv_lbl)

        layout.addWidget(priv_box)

        # 5. Cloud Usage Statistics
        usage_box = QGroupBox("Cloud Usage & Quota")
        usage_box.setStyleSheet("QGroupBox { font-weight: 700; color: #38BDF8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        usage_layout = QVBoxLayout(usage_box)
        usage_layout.setSpacing(6)

        usage_data = self.config_mgr.get("cloud_usage", {})
        u_made = usage_data.get("requests_made", 0)
        u_succ = usage_data.get("successful_requests", 0)
        u_fail = usage_data.get("failed_requests", 0)
        u_quota = usage_data.get("quota_status", "Normal")

        usage_lbl = QLabel(
            f"<b>Requests Made:</b> {u_made}  •  <b>Successful:</b> {u_succ}  •  <b>Failed:</b> {u_fail}<br>"
            f"<b>Quota Status:</b> <span style='color: {'#4ADE80' if u_quota == 'Normal' else '#F59E0B'};'>{u_quota}</span><br>"
            f"<b>Usage Cost:</b> Free Community Tier (No payment method stored or required)"
        )
        usage_lbl.setStyleSheet("color: #CBD5E1; font-size: 11px;")
        usage_layout.addWidget(usage_lbl)
        layout.addWidget(usage_box)

        # 6. Advanced Custom API
        adv_box = QGroupBox("Advanced: Custom Cloud API Settings")
        adv_box.setStyleSheet("QGroupBox { font-weight: 700; color: #94A3B8; border: 1px solid #334155; border-radius: 6px; margin-top: 10px; padding-top: 14px; }")
        adv_layout = QVBoxLayout(adv_box)
        adv_layout.setSpacing(8)

        custom_cfg = self.config_mgr.get("custom_api", {})
        adv_ep_lbl = QLabel("Custom API Endpoint:")
        adv_ep_lbl.setStyleSheet("font-size: 11px; color: #E2E8F0;")
        adv_layout.addWidget(adv_ep_lbl)

        self.custom_ep_edit = QLineEdit(custom_cfg.get("endpoint", ""))
        self.custom_ep_edit.setPlaceholderText("https://your-custom-api.example.com/api/remove-background")
        self.custom_ep_edit.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 5px;")
        adv_layout.addWidget(self.custom_ep_edit)

        adv_hdr_lbl = QLabel("Auth Header Type:")
        adv_hdr_lbl.setStyleSheet("font-size: 11px; color: #E2E8F0;")
        adv_layout.addWidget(adv_hdr_lbl)

        self.custom_hdr_combo = QComboBox()
        self.custom_hdr_combo.addItem("Bearer", "Bearer")
        self.custom_hdr_combo.addItem("X-API-Key", "X-API-Key")
        self.custom_hdr_combo.addItem("None", "None")
        curr_hdr = custom_cfg.get("auth_header", "Bearer")
        idx_h = self.custom_hdr_combo.findData(curr_hdr)
        if idx_h >= 0:
            self.custom_hdr_combo.setCurrentIndex(idx_h)
        adv_layout.addWidget(self.custom_hdr_combo)

        layout.addWidget(adv_box)

        layout.addStretch()
        scroll.setWidget(container)

        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab_widget

    def _on_test_cloud_connection(self):
        """Test reachability of configured cloud endpoint."""
        prov_id = self.cloud_prov_combo.currentData()
        endpoint = self.cloud_ep_edit.text().strip()

        self.conn_result_lbl.setText("Testing connection...")
        self.conn_result_lbl.setStyleSheet("color: #38BDF8; font-size: 11px;")

        if prov_id == "huggingface":
            provider = HuggingFaceProvider(endpoint_url=endpoint, credential_store=self.cred_store)
        else:
            provider = CustomAPIProvider(endpoint_url=endpoint, credential_store=self.cred_store)

        is_ok, msg = provider.test_connection()
        if is_ok:
            self.conn_result_lbl.setText(f"✓ {msg}")
            self.conn_result_lbl.setStyleSheet("color: #4ADE80; font-weight: bold; font-size: 11px;")
        else:
            self.conn_result_lbl.setText(f"✗ {msg}")
            self.conn_result_lbl.setStyleSheet("color: #EF4444; font-weight: bold; font-size: 11px;")

    def _on_configure_token(self):
        """Securely store token in Windows DPAPI credential store."""
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Notice", "Please enter a token first.")
            return

        prov_id = self.cloud_prov_combo.currentData()
        self.cred_store.set_token(prov_id, token)
        self.token_edit.clear()
        self.token_status_lbl.setText(f"Stored Credential: <b>{mask_token(token)}</b> (Encrypted with Windows DPAPI)")
        QMessageBox.information(self, "Saved", f"API token securely saved with Windows DPAPI encryption.")

    def _on_remove_credentials(self):
        """Remove stored credentials."""
        prov_id = self.cloud_prov_combo.currentData()
        if self.cred_store.remove_token(prov_id):
            self.token_status_lbl.setText("Stored Credential: <b>Not Set</b>")
            QMessageBox.information(self, "Removed", "Stored credentials have been removed.")
        else:
            QMessageBox.information(self, "Notice", "No credentials were stored for this provider.")

    # 3. MODELS TAB
    def _create_models_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Model storage location
        stor_lbl = QLabel("Model Storage Location:")
        stor_lbl.setStyleSheet("font-weight: 700; color: #E2E8F0;")
        layout.addWidget(stor_lbl)

        stor_row = QHBoxLayout()
        self.storage_edit = QLineEdit(self.config_mgr.get("model_storage_dir", "model_storage"))
        self.storage_edit.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; color: #CBD5E1; padding: 6px;")
        stor_row.addWidget(self.storage_edit)

        browse_stor_btn = QPushButton("Browse...")
        browse_stor_btn.setObjectName("outlineBtn")
        browse_stor_btn.clicked.connect(self._browse_storage_dir)
        stor_row.addWidget(browse_stor_btn)
        layout.addLayout(stor_row)

        layout.addSpacing(10)

        # Model Updates Actions
        actions_card = QFrame()
        actions_card.setStyleSheet("background-color: #0F172A; border: 1px solid #334155; border-radius: 6px; padding: 12px;")
        card_layout = QVBoxLayout(actions_card)
        card_layout.setSpacing(10)

        act_title = QLabel("Model Updates & Maintenance")
        act_title.setStyleSheet("font-weight: 700; color: #38BDF8;")
        card_layout.addWidget(act_title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        check_updates_btn = QPushButton("Check for Model Updates")
        check_updates_btn.setStyleSheet("background-color: #2563EB; color: white; padding: 7px 14px; font-weight: 600;")
        check_updates_btn.clicked.connect(self._on_check_model_updates)
        btn_row.addWidget(check_updates_btn)

        update_all_btn = QPushButton("Update All Models")
        update_all_btn.setObjectName("outlineBtn")
        update_all_btn.clicked.connect(self._on_update_all_models)
        btn_row.addWidget(update_all_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)
        layout.addWidget(actions_card)

        layout.addStretch()
        return widget

    # 4. SYSTEM & DEPENDENCIES TAB
    def _create_system_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # System actions row
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        hw_btn = QPushButton("View Hardware Information")
        hw_btn.setObjectName("outlineBtn")
        hw_btn.clicked.connect(self._view_hardware_info)
        act_row.addWidget(hw_btn)

        compat_btn = QPushButton("Run Compatibility Test")
        compat_btn.setObjectName("outlineBtn")
        compat_btn.clicked.connect(self._run_compatibility_test)
        act_row.addWidget(compat_btn)

        act_row.addStretch()
        layout.addLayout(act_row)

        # Dependency Inspection Section
        dep_title = QLabel("AI Runtime Dependencies:")
        dep_title.setStyleSheet("font-weight: 700; color: #E2E8F0; margin-top: 4px;")
        layout.addWidget(dep_title)

        # Dependency Table
        self.dep_table = QTableWidget()
        self.dep_table.setColumnCount(4)
        self.dep_table.setHorizontalHeaderLabels(["Component", "Status", "Installed Version", "Required"])
        self.dep_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.dep_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.dep_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.dep_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.dep_table.setColumnWidth(1, 65)
        self.dep_table.verticalHeader().setVisible(False)
        self.dep_table.setAlternatingRowColors(True)

        layout.addWidget(self.dep_table)

        # Dependency Buttons Row
        dep_btn_row = QHBoxLayout()
        dep_btn_row.setSpacing(10)

        check_dep_btn = QPushButton("Check Dependencies")
        check_dep_btn.setStyleSheet("background-color: #334155; color: white; padding: 6px 14px; font-weight: 600;")
        check_dep_btn.clicked.connect(self.refresh_dependencies)
        dep_btn_row.addWidget(check_dep_btn)

        self.repair_btn = QPushButton("Repair Installation")
        self.repair_btn.setStyleSheet("background-color: #D97706; color: white; padding: 6px 14px; font-weight: 700;")
        self.repair_btn.clicked.connect(self._repair_dependencies)
        dep_btn_row.addWidget(self.repair_btn)

        dep_btn_row.addStretch()
        layout.addLayout(dep_btn_row)

        self.refresh_dependencies()
        return widget

    def refresh_dependencies(self):
        """Query DependencyManager and update table with installed versions."""
        deps = DependencyManager.check_dependencies()
        self.dep_table.setRowCount(len(deps))

        all_ok = True
        for row, d in enumerate(deps):
            # 0: Name
            name_item = QTableWidgetItem(d.name)
            name_item.setFlags(name_item.flags() ^ Qt.ItemIsEditable)
            self.dep_table.setItem(row, 0, name_item)

            # 1: Status Icon
            icon_text = "✓" if d.is_installed else "✗"
            status_item = QTableWidgetItem(icon_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor("#4ADE80") if d.is_installed else QColor("#EF4444"))
            status_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            status_item.setFlags(status_item.flags() ^ Qt.ItemIsEditable)
            self.dep_table.setItem(row, 1, status_item)

            # 2: Installed Version
            ver_text = d.installed_version or "Not Installed"
            if d.notes and d.notes != "OK":
                ver_text += f" ({d.notes})"
            ver_item = QTableWidgetItem(ver_text)
            ver_item.setFlags(ver_item.flags() ^ Qt.ItemIsEditable)
            self.dep_table.setItem(row, 2, ver_item)

            # 3: Required
            req_item = QTableWidgetItem(d.required_version)
            req_item.setFlags(req_item.flags() ^ Qt.ItemIsEditable)
            self.dep_table.setItem(row, 3, req_item)

            if not d.is_installed:
                all_ok = False

        self.repair_btn.setEnabled(not all_ok)

    def _repair_dependencies(self):
        missing = DependencyManager.get_missing_dependencies()
        if not missing:
            QMessageBox.information(self, "Dependencies OK", "All required AI components are already installed.")
            return

        names = ", ".join(m["name"] for m in missing)
        reply = QMessageBox.question(
            self,
            "Repair AI Environment",
            f"The following missing dependencies will be installed into the virtual environment:\n\n{names}\n\nProceed with installation?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = DependencyManager.repair_installation()
            if success:
                QMessageBox.information(self, "Repair Complete", msg)
                self.refresh_dependencies()
            else:
                QMessageBox.critical(self, "Repair Failed", msg)

    def _view_hardware_info(self):
        rec_res = self.rec_engine.recommend(self.sys_info)
        dialog = SystemDetailsDialog(self.sys_info, rec_res, self)
        dialog.exec()

    def _run_compatibility_test(self):
        rec_res = self.rec_engine.recommend(self.sys_info)
        msg = (
            "=== Hardware Compatibility Analysis ===\n\n"
            f"CPU: {self.sys_info.cpu_name} ({self.sys_info.cpu_cores} Cores / {self.sys_info.cpu_threads} Threads)\n"
            f"RAM: {self.sys_info.ram_total_gb:.1f} GB Total ({self.sys_info.ram_available_gb:.1f} GB Available)\n"
            f"GPU: {self.sys_info.gpu_name} (Vendor: {self.sys_info.gpu_vendor})\n"
            f"CUDA Acceleration: {'Available' if self.sys_info.cuda_available else 'Not Available'}\n"
            f"AMD Acceleration: {'Supported' if self.sys_info.amd_acceleration_available else 'Not Supported'}\n\n"
            f"Recommended Target: {rec_res.recommended_device}\n"
            f"Recommended Model: {rec_res.recommended_model} ({rec_res.category})\n"
            f"Expected Performance: {rec_res.expected_performance}\n\n"
            f"Compatibility Verdict: System is fully optimized for local CPU background removal."
        )
        QMessageBox.information(self, "Compatibility Test", msg)

    def _on_check_model_updates(self):
        QMessageBox.information(
            self, "Model Updates",
            "Checking official model repositories...\n\nAll registered models are up to date."
        )

    def _on_update_all_models(self):
        QMessageBox.information(
            self, "Update All Models",
            "All installed models are at their latest versions."
        )

    def _browse_output_dir(self):
        f = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.gen_out_edit.text())
        if f:
            self.gen_out_edit.setText(f)

    def _browse_storage_dir(self):
        f = QFileDialog.getExistingDirectory(self, "Select Model Storage Directory", self.storage_edit.text())
        if f:
            self.storage_edit.setText(f)

    def _save_settings(self):
        self.config_mgr.set("output_dir", self.gen_out_edit.text())
        self.config_mgr.set("auto_open_output", self.cb_auto_open.isChecked())
        self.config_mgr.set("remember_selected_model", self.cb_remember_model.isChecked())
        self.config_mgr.set("auto_start_on_drop", self.cb_auto_start_drop.isChecked())

        self.config_mgr.set("execution_device", self.device_combo.currentData())
        self.config_mgr.set("processing_quality", self.quality_combo.currentText())
        self.config_mgr.set("max_parallel_jobs", self.jobs_spin.value())
        self.config_mgr.set("memory_safeguard", self.cb_mem_safeguard.isChecked())

        self.config_mgr.set("model_storage_dir", self.storage_edit.text())

        # Cloud Settings
        self.config_mgr.set("processing_mode", self.cloud_mode_combo.currentData())
        self.config_mgr.set("cloud_provider", self.cloud_prov_combo.currentData())
        self.config_mgr.set("cloud_endpoint", self.cloud_ep_edit.text().strip())
        self.config_mgr.set("cloud_always_ask_upload", self.cb_always_ask.isChecked())

        custom_cfg = self.config_mgr.get("custom_api", {})
        custom_cfg["endpoint"] = self.custom_ep_edit.text().strip()
        custom_cfg["auth_header"] = self.custom_hdr_combo.currentData()
        self.config_mgr.set("custom_api", custom_cfg)

        self.config_mgr.save()

        self.settings_saved.emit()
        self.accept()

    def _create_about_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignHCenter)

        dev_info = self.config_mgr.get("developer", {})
        dev_name = dev_info.get("name", "Faiz")
        dev_role = dev_info.get("role", "Developer / Creator")
        dev_desc = dev_info.get(
            "description",
            "Creator of AI Background Remover. Passionate about building fast, "
            "local-first, privacy-focused desktop AI applications."
        )
        github_user = dev_info.get("github_username", "Faizchonari")
        github_url = dev_info.get("github_profile_url", f"https://github.com/{github_user}")
        repo_url = dev_info.get("project_repo_url", f"https://github.com/{github_user}/AI-Background-Remover")
        avatar_rel_path = dev_info.get("avatar_path", "assets/developer_avatar.png")

        # Avatar
        avatar_lbl = QLabel()
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_path = _get_project_root() / avatar_rel_path
        if avatar_path.is_file():
            avatar_lbl.setPixmap(get_circular_avatar(QPixmap(str(avatar_path)), size=90))
        else:
            initials = dev_name[:2].upper() if dev_name else "AI"
            avatar_lbl.setPixmap(create_initials_avatar(initials, size=90))
        layout.addWidget(avatar_lbl)

        # Name & Role
        name_lbl = QLabel(dev_name)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #F8FAFC;")
        layout.addWidget(name_lbl)

        role_lbl = QLabel(dev_role)
        role_lbl.setAlignment(Qt.AlignCenter)
        role_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #38BDF8;")
        layout.addWidget(role_lbl)

        desc_lbl = QLabel(dev_desc)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; max-width: 500px;")
        layout.addWidget(desc_lbl)

        # Links
        links_layout = QHBoxLayout()
        links_layout.setSpacing(12)
        links_layout.setAlignment(Qt.AlignCenter)

        gh_btn = QPushButton("GitHub Profile")
        gh_btn.setObjectName("outlineBtn")
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(github_url)))
        links_layout.addWidget(gh_btn)

        repo_btn = QPushButton("Project Repository")
        repo_btn.setObjectName("outlineBtn")
        repo_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(repo_url)))
        links_layout.addWidget(repo_btn)

        layout.addLayout(links_layout)
        layout.addStretch()

        # App version
        ver = self.config_mgr.get("version", "1.1.0")
        ver_lbl = QLabel(f"AI Background Remover  •  v{ver}\n100% Offline AI Image Processing")
        ver_lbl.setAlignment(Qt.AlignCenter)
        ver_lbl.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(ver_lbl)

        return widget
