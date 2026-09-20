"""System Details Dialog for AI Background Remover.

Displays a complete, formatted hardware inspection report in a modern modal window.
Allows copying hardware metrics to clipboard without any personally identifying information.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QApplication, QMessageBox
)

from app.system.system_info import SystemInfo
from app.system.recommendation import RecommendationResult


class SystemDetailsDialog(QDialog):
    """Modal dialog displaying comprehensive system hardware information."""

    def __init__(self, sys_info: SystemInfo, rec_result: RecommendationResult, parent=None):
        super().__init__(parent)
        self.sys_info = sys_info
        self.rec_result = rec_result
        self.setWindowTitle("System & Hardware Details")
        self.resize(620, 520)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        title = QLabel("Hardware & Environment Specifications")
        title.setObjectName("dialogTitle")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #E2E8F0;")
        layout.addWidget(title)

        subtitle = QLabel("Local hardware metrics collected for AI model tuning. No personal data collected.")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(subtitle)

        # Table of System Information
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        items = [
            ("Operating System", self.sys_info.operating_system),
            ("Windows Version", self.sys_info.windows_version),
            ("Architecture", self.sys_info.architecture),
            ("CPU Model", self.sys_info.cpu_name),
            ("Physical Cores", str(self.sys_info.cpu_cores)),
            ("Logical Threads", str(self.sys_info.cpu_threads)),
            ("CPU Base Clock", f"{self.sys_info.cpu_frequency_mhz:.0f} MHz" if self.sys_info.cpu_frequency_mhz else "N/A"),
            ("Total System RAM", f"{self.sys_info.ram_total_gb:.2f} GB"),
            ("Available RAM", f"{self.sys_info.ram_available_gb:.2f} GB"),
            ("Primary GPU", self.sys_info.gpu_name),
            ("GPU Vendor", self.sys_info.gpu_vendor),
            ("GPU VRAM", f"{self.sys_info.gpu_memory_mb:.0f} MB" if self.sys_info.gpu_memory_mb else "Shared System Memory"),
            ("NVIDIA CUDA Available", "Yes" if self.sys_info.cuda_available else "No"),
            ("AMD GPU Acceleration", "Supported" if self.sys_info.amd_acceleration_available else "No"),
            ("Active Backend", self.sys_info.acceleration_backend),
            ("Current Execution Device", self.sys_info.current_device),
            ("Recommended Model", self.rec_result.recommended_model),
            ("Model Category", self.rec_result.category),
            ("Expected Performance", self.rec_result.expected_performance),
        ]

        self.table.setRowCount(len(items))
        for row, (prop, val) in enumerate(items):
            p_item = QTableWidgetItem(prop)
            p_item.setFlags(p_item.flags() ^ Qt.ItemIsEditable)
            v_item = QTableWidgetItem(val)
            v_item.setFlags(v_item.flags() ^ Qt.ItemIsEditable)
            self.table.setItem(row, 0, p_item)
            self.table.setItem(row, 1, v_item)

        layout.addWidget(self.table)

        # Button Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        copy_btn = QPushButton("Copy Specs to Clipboard")
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                border: 1px solid #475569;
                padding: 7px 14px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        copy_btn.clicked.connect(self._copy_to_clipboard)
        btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                padding: 7px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _copy_to_clipboard(self):
        text_lines = ["=== AI Background Remover - System Hardware Report ==="]
        for row in range(self.table.rowCount()):
            prop = self.table.item(row, 0).text()
            val = self.table.item(row, 1).text()
            text_lines.append(f"{prop}: {val}")
        text_lines.append(f"Recommendation Reason: {self.rec_result.reason}")
        
        QApplication.clipboard().setText("\n".join(text_lines))
        QMessageBox.information(self, "Copied", "Hardware specifications copied to clipboard!")
