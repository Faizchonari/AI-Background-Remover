"""Modern Dark Theme QSS Styling for AI Background Remover."""

DARK_THEME = """
/* Base Window & Widget Styling */
QMainWindow, QDialog {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QWidget {
    color: #F8FAFC;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #1E293B;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #475569;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #64748B;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* System Analysis Card */
QFrame#systemCard {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px;
}

QLabel#cardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #38BDF8;
    margin-bottom: 4px;
}

QLabel#fieldLabel {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-top: 6px;
}

QLabel#fieldValue {
    color: #F1F5F9;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 2px;
}

QLabel#reasonBox {
    background-color: #0F172A;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    color: #CBD5E1;
    font-size: 12px;
    line-height: 1.4;
}

/* Badges */
QLabel#badge {
    background-color: #0284C7;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
}

QLabel#badgeWarning {
    background-color: #D97706;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 4px;
}

/* Buttons */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 9px 16px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1D4ED8;
}

QPushButton:pressed {
    background-color: #1E40AF;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748B;
}

QPushButton#outlineBtn {
    background-color: transparent;
    color: #38BDF8;
    border: 1px solid #0284C7;
}

QPushButton#outlineBtn:hover {
    background-color: rgba(2, 132, 199, 0.15);
}

QPushButton#actionBtn {
    background-color: #059669;
    font-size: 14px;
    padding: 10px 20px;
}

QPushButton#actionBtn:hover {
    background-color: #047857;
}

/* Combo Box */
QComboBox {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 24px;
    font-weight: 500;
}

QComboBox:hover {
    border-color: #0284C7;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #334155;
}

QComboBox QAbstractItemView {
    background-color: #1E293B;
    color: #F8FAFC;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    border: 1px solid #334155;
    outline: none;
}

/* Preview Canvas Frames */
QFrame#previewCard {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px;
}

QLabel#previewPlaceholder {
    border: 2px dashed #334155;
    border-radius: 8px;
    color: #64748B;
    font-size: 13px;
    background-color: #0B1120;
}

/* Table Widget */
QTableWidget {
    background-color: #1E293B;
    color: #F8FAFC;
    gridline-color: #334155;
    border: 1px solid #334155;
    border-radius: 6px;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0F172A;
    color: #94A3B8;
    padding: 6px 10px;
    font-weight: 700;
    border: 1px solid #334155;
}

/* Status Bar & Progress Bar */
QStatusBar {
    background-color: #0F172A;
    border-top: 1px solid #1E293B;
    color: #94A3B8;
    font-size: 12px;
}

QProgressBar {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: #FFFFFF;
    font-size: 10px;
}

QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 3px;
}
"""
