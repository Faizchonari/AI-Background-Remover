"""Interactive Image Preview System for AI Background Remover.

Provides:
- Before/After interactive slider (split view)
- Side-by-side comparison view
- Smooth zoom & pan (mouse wheel, 100%, fit-to-window)
- Transparency checkerboard background
- Metadata overlay: dimensions, processing time, model name
- Non-destructive rendering
"""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QRect, QRectF, QPoint, QPointF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPixmap, QImage,
    QMouseEvent, QWheelEvent, QPaintEvent, QFont
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QButtonGroup
)

from app.processing.batch_worker import QueueItem


class ComparisonCanvas(QWidget):
    """Custom canvas drawing before/after slider or side-by-side with checkerboard and zoom."""

    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.orig_pixmap: Optional[QPixmap] = None
        self.result_pixmap: Optional[QPixmap] = None

        self.view_mode = "slider"  # "slider" or "side_by_side"
        self.split_pos = 0.5  # 0.0 to 1.0

        # Zoom and Pan
        self.zoom = 1.0
        self.pan_offset = QPointF(0, 0)
        self._dragging_pan = False
        self._dragging_slider = False
        self._last_mouse_pos = QPoint()

        # Checkerboard colors
        self.check_c1 = QColor("#1E293B")
        self.check_c2 = QColor("#0F172A")
        self.check_size = 16

    def set_images(self, orig_path: Optional[Path | str], result_path: Optional[Path | str]):
        """Load pixmaps for comparison."""
        self.orig_pixmap = QPixmap(str(orig_path)) if orig_path and Path(orig_path).is_file() else None
        self.result_pixmap = QPixmap(str(result_path)) if result_path and Path(result_path).is_file() else None
        self.fit_to_window()
        self.update()

    def set_view_mode(self, mode: str):
        self.view_mode = mode
        self.update()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom * 0.8)

    def zoom_100(self):
        self.set_zoom(1.0)
        self.pan_offset = QPointF(0, 0)
        self.update()

    def fit_to_window(self):
        """Fit image to current canvas size."""
        ref = self.orig_pixmap or self.result_pixmap
        if not ref or ref.isNull() or self.width() <= 0 or self.height() <= 0:
            self.zoom = 1.0
            self.pan_offset = QPointF(0, 0)
            self.zoom_changed.emit(self.zoom)
            self.update()
            return

        w_ratio = (self.width() - 20) / ref.width()
        h_ratio = (self.height() - 20) / ref.height()
        fit_zoom = min(w_ratio, h_ratio)
        self.set_zoom(min(fit_zoom, 2.0))
        self.pan_offset = QPointF(0, 0)
        self.update()

    def set_zoom(self, new_zoom: float):
        self.zoom = max(0.1, min(new_zoom, 10.0))
        self.zoom_changed.emit(self.zoom)
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # Fill background
        painter.fillRect(self.rect(), QColor("#0B1120"))

        ref = self.orig_pixmap or self.result_pixmap
        if not ref or ref.isNull():
            # Placeholder text
            painter.setPen(QColor("#64748B"))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignCenter, "Select an image from the queue to inspect")
            return

        img_w = ref.width() * self.zoom
        img_h = ref.height() * self.zoom

        # Center in canvas
        base_x = (self.width() - img_w) / 2 + self.pan_offset.x()
        base_y = (self.height() - img_h) / 2 + self.pan_offset.y()
        target_rect = QRectF(base_x, base_y, img_w, img_h)

        if self.view_mode == "side_by_side":
            self._paint_side_by_side(painter, target_rect)
        else:
            self._paint_slider(painter, target_rect)

    def _draw_checkerboard(self, painter: QPainter, rect: QRectF):
        """Draw a transparent checkerboard pattern within rect."""
        painter.save()
        painter.setClipRect(rect)
        x_start = int(rect.left())
        y_start = int(rect.top())
        x_end = int(rect.right()) + self.check_size
        y_end = int(rect.bottom()) + self.check_size

        for y in range(y_start, y_end, self.check_size):
            for x in range(x_start, x_end, self.check_size):
                color = self.check_c1 if ((x // self.check_size) + (y // self.check_size)) % 2 == 0 else self.check_c2
                painter.fillRect(QRect(x, y, self.check_size, self.check_size), color)
        painter.restore()

    def _paint_side_by_side(self, painter: QPainter, target_rect: QRectF):
        # Calculate scaled half width
        half_w = (self.width() - 30) / 2
        ref = self.orig_pixmap or self.result_pixmap
        aspect = ref.width() / ref.height() if ref.height() > 0 else 1.0

        pane_h = min(self.height() - 20, half_w / aspect)
        pane_w = pane_h * aspect

        y_top = (self.height() - pane_h) / 2

        # Left: Original
        rect_orig = QRectF(10, y_top, pane_w, pane_h)
        painter.fillRect(rect_orig, QColor("#0F172A"))
        if self.orig_pixmap:
            painter.drawPixmap(rect_orig.toRect(), self.orig_pixmap)

        # Label Left
        painter.setPen(QColor("#38BDF8"))
        painter.drawText(QRectF(14, y_top + 8, 120, 24), Qt.AlignLeft, "ORIGINAL")

        # Right: Result with Checkerboard
        x_res = self.width() - pane_w - 10
        rect_res = QRectF(x_res, y_top, pane_w, pane_h)
        self._draw_checkerboard(painter, rect_res)

        if self.result_pixmap:
            painter.drawPixmap(rect_res.toRect(), self.result_pixmap)
        else:
            painter.setPen(QColor("#64748B"))
            painter.drawText(rect_res, Qt.AlignCenter, "Processing needed")

        # Label Right
        painter.setPen(QColor("#4ADE80"))
        painter.drawText(QRectF(x_res + 8, y_top + 8, 140, 24), Qt.AlignLeft, "BACKGROUND REMOVED")

    def _paint_slider(self, painter: QPainter, target_rect: QRectF):
        # 1. Draw Checkerboard background across full target rect
        self._draw_checkerboard(painter, target_rect)

        # 2. Draw Result (Background Removed) on entire target rect
        if self.result_pixmap:
            painter.drawPixmap(target_rect.toRect(), self.result_pixmap)
        elif self.orig_pixmap:
            painter.drawPixmap(target_rect.toRect(), self.orig_pixmap)

        # 3. Clip and Draw Original on Left Side
        split_x = target_rect.left() + (target_rect.width() * self.split_pos)
        clip_orig = QRectF(target_rect.left(), target_rect.top(), split_x - target_rect.left(), target_rect.height())

        if self.orig_pixmap:
            painter.save()
            painter.setClipRect(clip_orig)
            painter.drawPixmap(target_rect.toRect(), self.orig_pixmap)
            painter.restore()

        # 4. Draw Split Line & Draggable Handle
        if target_rect.left() <= split_x <= target_rect.right():
            # Line
            pen = QPen(QColor("#38BDF8"), 2)
            painter.setPen(pen)
            painter.drawLine(QPointF(split_x, target_rect.top()), QPointF(split_x, target_rect.bottom()))

            # Circular Handle in center
            handle_y = target_rect.top() + target_rect.height() / 2
            painter.setBrush(QBrush(QColor("#0284C7")))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawEllipse(QPointF(split_x, handle_y), 16, 16)

            # Arrows icon inside handle
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(split_x - 14, handle_y - 12, 28, 24), Qt.AlignCenter, "◄ ►")

        # Labels
        painter.setPen(QColor("#E2E8F0"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(QRectF(target_rect.left() + 10, target_rect.top() + 10, 100, 20), Qt.AlignLeft, "ORIGINAL")
        painter.drawText(QRectF(target_rect.right() - 110, target_rect.top() + 10, 100, 20), Qt.AlignRight, "RESULT")

    # Mouse Events for Slider Dragging & Panning
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            ref = self.orig_pixmap or self.result_pixmap
            if ref and self.view_mode == "slider":
                img_w = ref.width() * self.zoom
                base_x = (self.width() - img_w) / 2 + self.pan_offset.x()
                split_x = base_x + (img_w * self.split_pos)
                if abs(event.position().x() - split_x) < 25:
                    self._dragging_slider = True
                    return

            self._dragging_pan = True
            self._last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        ref = self.orig_pixmap or self.result_pixmap
        if self._dragging_slider and ref:
            img_w = ref.width() * self.zoom
            base_x = (self.width() - img_w) / 2 + self.pan_offset.x()
            if img_w > 0:
                pos = (event.position().x() - base_x) / img_w
                self.split_pos = max(0.0, min(1.0, pos))
                self.update()
        elif self._dragging_pan:
            delta = event.pos() - self._last_mouse_pos
            self.pan_offset += QPointF(delta.x(), delta.y())
            self._last_mouse_pos = event.pos()
            self.update()
        elif ref and self.view_mode == "slider":
            img_w = ref.width() * self.zoom
            base_x = (self.width() - img_w) / 2 + self.pan_offset.x()
            split_x = base_x + (img_w * self.split_pos)
            if abs(event.position().x() - split_x) < 25:
                self.setCursor(Qt.SplitHCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging_slider = False
        self._dragging_pan = False

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 0.85
        self.set_zoom(self.zoom * factor)


class InteractivePreviewWidget(QFrame):
    """Complete image preview widget with toolbar controls and canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("previewCard")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Top Control Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # View Mode Toggle
        self.slider_mode_btn = QPushButton("Split Slider")
        self.slider_mode_btn.setCheckable(True)
        self.slider_mode_btn.setChecked(True)
        self.slider_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #CBD5E1;
                border: 1px solid #334155;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:checked {
                background-color: #2563EB;
                color: #FFFFFF;
                border-color: #3B82F6;
            }
        """)
        self.slider_mode_btn.clicked.connect(lambda: self._set_mode("slider"))
        toolbar.addWidget(self.slider_mode_btn)

        self.side_mode_btn = QPushButton("Side-by-Side")
        self.side_mode_btn.setCheckable(True)
        self.side_mode_btn.setStyleSheet(self.slider_mode_btn.styleSheet())
        self.side_mode_btn.clicked.connect(lambda: self._set_mode("side_by_side"))
        toolbar.addWidget(self.side_mode_btn)

        toolbar.addSpacing(10)

        # Zoom Controls
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(26, 26)
        zoom_in_btn.clicked.connect(lambda: self.canvas.zoom_in())
        toolbar.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(26, 26)
        zoom_out_btn.clicked.connect(lambda: self.canvas.zoom_out())
        toolbar.addWidget(zoom_out_btn)

        fit_btn = QPushButton("Fit")
        fit_btn.setObjectName("outlineBtn")
        fit_btn.setFixedSize(36, 26)
        fit_btn.clicked.connect(lambda: self.canvas.fit_to_window())
        toolbar.addWidget(fit_btn)

        btn_100 = QPushButton("1:1")
        btn_100.setObjectName("outlineBtn")
        btn_100.setFixedSize(36, 26)
        btn_100.clicked.connect(lambda: self.canvas.zoom_100())
        toolbar.addWidget(btn_100)

        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; margin-left: 4px;")
        toolbar.addWidget(self.zoom_lbl)

        toolbar.addStretch()

        # Metadata Overlay Labels
        self.dims_lbl = QLabel("")
        self.dims_lbl.setStyleSheet("color: #38BDF8; font-size: 11px; font-weight: 600;")
        toolbar.addWidget(self.dims_lbl)

        self.model_lbl = QLabel("")
        self.model_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        toolbar.addWidget(self.model_lbl)

        self.time_lbl = QLabel("")
        self.time_lbl.setStyleSheet("color: #4ADE80; font-size: 11px; font-weight: 700;")
        toolbar.addWidget(self.time_lbl)

        layout.addLayout(toolbar)

        # Main Canvas
        self.canvas = ComparisonCanvas(self)
        self.canvas.zoom_changed.connect(self._on_zoom_changed)
        layout.addWidget(self.canvas, stretch=1)

    def _set_mode(self, mode: str):
        if mode == "slider":
            self.slider_mode_btn.setChecked(True)
            self.side_mode_btn.setChecked(False)
        else:
            self.slider_mode_btn.setChecked(False)
            self.side_mode_btn.setChecked(True)
        self.canvas.set_view_mode(mode)

    def _on_zoom_changed(self, zoom: float):
        self.zoom_lbl.setText(f"{int(zoom * 100)}%")

    def display_item(self, item: Optional[QueueItem]):
        """Update canvas and metadata labels from QueueItem."""
        if not item:
            self.canvas.set_images(None, None)
            self.dims_lbl.setText("")
            self.model_lbl.setText("")
            self.time_lbl.setText("")
            return

        self.canvas.set_images(item.file_path, item.output_path)

        if item.dimensions != (0, 0):
            self.dims_lbl.setText(f"{item.dimensions[0]} × {item.dimensions[1]} px")
        else:
            self.dims_lbl.setText("")

        if item.model_name:
            self.model_lbl.setText(f"Model: {item.model_name}")
        else:
            self.model_lbl.setText("")

        if item.processing_time_s is not None:
            self.time_lbl.setText(f"Time: {item.processing_time_s:.2f}s")
        else:
            self.time_lbl.setText("")
