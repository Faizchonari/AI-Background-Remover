"""Interactive Image Queue Widget for AI Background Remover.

Supports drag-and-drop ingestion, multi-file queue management,
thumbnail rendering, status badges, and item removal.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QAbstractItemView
)

from app.processing.batch_worker import QueueItem

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class QueueWidget(QWidget):
    """Batch image queue management widget."""

    item_selected = Signal(object)  # QueueItem
    queue_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items: list[QueueItem] = []
        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header Row
        header_layout = QHBoxLayout()
        header_lbl = QLabel("Image Queue")
        header_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #E2E8F0;")
        header_layout.addWidget(header_lbl)

        self.count_lbl = QLabel("(0 images)")
        self.count_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        header_layout.addWidget(self.count_lbl)

        header_layout.addStretch()

        add_btn = QPushButton("+ Select Images")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                padding: 5px 12px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        add_btn.clicked.connect(self._browse_images)
        header_layout.addWidget(add_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #CBD5E1;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        clear_btn.clicked.connect(self.clear_queue)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Thumb", "File & Resolution", "Status", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 56)
        self.table.setColumnWidth(3, 40)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        layout.addWidget(self.table)

        # Drag and Drop hint
        self.hint_lbl = QLabel("Drag & drop JPG, PNG, or WEBP images here")
        self.hint_lbl.setAlignment(Qt.AlignCenter)
        self.hint_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic; margin-top: 2px;")
        layout.addWidget(self.hint_lbl)

    def add_paths(self, paths: list[Path | str]):
        """Add image paths to the queue."""
        added = False
        for p in paths:
            path_obj = Path(p)
            if path_obj.is_file() and path_obj.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Check for duplicates
                if any(it.file_path == path_obj for it in self.items):
                    continue

                item = QueueItem.from_path(path_obj)
                # Load small thumbnail
                pixmap = QPixmap(str(path_obj))
                if not pixmap.isNull():
                    item.thumbnail = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                self.items.append(item)
                added = True

        if added:
            self._refresh_table()
            self.queue_count_changed.emit(len(self.items))
            if self.items and self.table.currentRow() < 0:
                self.table.selectRow(0)

    def _refresh_table(self):
        self.table.setRowCount(len(self.items))
        self.count_lbl.setText(f"({len(self.items)} image{'s' if len(self.items) != 1 else ''})")

        for row, item in enumerate(self.items):
            self.table.setRowHeight(row, 54)

            # Column 0: Thumbnail
            thumb_lbl = QLabel()
            thumb_lbl.setAlignment(Qt.AlignCenter)
            if item.thumbnail:
                thumb_lbl.setPixmap(item.thumbnail)
            else:
                thumb_lbl.setText("IMG")
            self.table.setCellWidget(row, 0, thumb_lbl)

            # Column 1: Info (Filename, Size, Resolution)
            res_str = f"{item.dimensions[0]}x{item.dimensions[1]}" if item.dimensions != (0, 0) else "Unknown"
            info_text = f"<b>{item.filename}</b><br><span style='color: #94A3B8; font-size: 11px;'>{res_str} • {item.file_size_str}</span>"
            info_lbl = QLabel(info_text)
            info_lbl.setContentsMargins(6, 2, 6, 2)
            self.table.setCellWidget(row, 1, info_lbl)

            # Column 2: Status Badge
            status_lbl = QLabel(item.status)
            status_lbl.setAlignment(Qt.AlignCenter)
            status_color = "#F59E0B" if item.status == "Pending" else (
                "#38BDF8" if "Processing" in item.status else (
                    "#4ADE80" if item.status == "Completed" else "#EF4444"
                )
            )
            status_lbl.setStyleSheet(f"""
                color: {status_color};
                font-weight: 700;
                font-size: 11px;
                padding: 3px 8px;
            """)
            self.table.setCellWidget(row, 2, status_lbl)

            # Column 3: Remove Button [X]
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(28, 28)
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94A3B8;
                    border: none;
                    font-weight: bold;
                    font-size: 13px;
                }
                QPushButton:hover {
                    color: #EF4444;
                    background-color: rgba(239, 68, 68, 0.15);
                    border-radius: 14px;
                }
            """)
            remove_btn.clicked.connect(lambda checked=False, r=row: self._remove_item(r))
            self.table.setCellWidget(row, 3, remove_btn)

    def update_item_status(self, index: int, status: str, output_path: Optional[Path] = None, error: Optional[str] = None):
        """Update status for a specific queue item."""
        if 0 <= index < len(self.items):
            item = self.items[index]
            item.status = status
            if output_path:
                item.output_path = output_path
            if error:
                item.error_message = error

            widget = self.table.cellWidget(index, 2)
            if isinstance(widget, QLabel):
                widget.setText(status)
                status_color = "#F59E0B" if status == "Pending" else (
                    "#38BDF8" if "Processing" in status else (
                        "#4ADE80" if status == "Completed" else "#EF4444"
                    )
                )
                widget.setStyleSheet(f"color: {status_color}; font-weight: 700; font-size: 11px; padding: 3px 8px;")

            # If this is the currently selected item, emit selected signal to update preview
            if self.table.currentRow() == index:
                self.item_selected.emit(item)

    def _remove_item(self, row: int):
        if 0 <= row < len(self.items):
            del self.items[row]
            self._refresh_table()
            self.queue_count_changed.emit(len(self.items))
            if self.items:
                new_row = min(row, len(self.items) - 1)
                self.table.selectRow(new_row)
            else:
                self.item_selected.emit(None)

    def clear_queue(self):
        self.items.clear()
        self._refresh_table()
        self.queue_count_changed.emit(0)
        self.item_selected.emit(None)

    def _on_row_selected(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.items):
            self.item_selected.emit(self.items[row])

    def _browse_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if files:
            self.add_paths(files)

    # Drag and Drop Event Handlers
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        if paths:
            self.add_paths(paths)
            event.acceptProposedAction()
