"""About Me & Project Information Dialog for AI Background Remover.

Displays developer profile, avatar, project information, and GitHub links.
Operates completely offline with bundled local resources.
"""

from pathlib import Path
import sys

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor,
    QPen, QBrush, QDesktopServices, QFont
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QWidget
)

from app.core.config import ConfigManager


def _get_project_root() -> Path:
    """Resolve base directory whether running in source or PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def get_circular_avatar(pixmap: QPixmap, size: int = 110) -> QPixmap:
    """Create an antialiased circular avatar with a subtle accent border."""
    scaled = pixmap.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    out = QPixmap(size, size)
    out.fill(Qt.transparent)

    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    path = QPainterPath()
    path.addEllipse(2, 2, size - 4, size - 4)
    painter.setClipPath(path)

    # Center-crop image into circular clip
    crop_x = (scaled.width() - size) // 2
    crop_y = (scaled.height() - size) // 2
    painter.drawPixmap(-crop_x, -crop_y, scaled)

    # Draw border ring
    painter.setClipping(False)
    pen = QPen(QColor("#38BDF8"), 2.5)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    painter.end()
    return out


def create_initials_avatar(initials: str, size: int = 110) -> QPixmap:
    """Fallback avatar with developer initials when no image file exists."""
    out = QPixmap(size, size)
    out.fill(Qt.transparent)

    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # Background circle
    brush = QBrush(QColor("#1E293B"))
    pen = QPen(QColor("#38BDF8"), 2.5)
    painter.setBrush(brush)
    painter.setPen(pen)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # Initials text
    font = QFont("Segoe UI", 32, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#38BDF8"))
    painter.drawText(0, 0, size, size, Qt.AlignCenter, initials)

    painter.end()
    return out


class AboutDialog(QDialog):
    """Simple, professional About Me dialog for AI Background Remover."""

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.setWindowTitle("About Developer & Project")
        self.setFixedSize(480, 580)
        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 20)
        root_layout.setSpacing(14)

        # Developer configuration data (read from config or defaults)
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

        # Container Card
        card = QFrame()
        card.setObjectName("aboutCard")
        card.setStyleSheet("""
            QFrame#aboutCard {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setAlignment(Qt.AlignHCenter)

        # 1. Profile Photo
        avatar_lbl = QLabel()
        avatar_lbl.setAlignment(Qt.AlignCenter)
        avatar_path = _get_project_root() / avatar_rel_path

        if avatar_path.is_file():
            raw_pixmap = QPixmap(str(avatar_path))
            avatar_lbl.setPixmap(get_circular_avatar(raw_pixmap, size=110))
        else:
            initials = dev_name[:2].upper() if dev_name else "AI"
            avatar_lbl.setPixmap(create_initials_avatar(initials, size=110))
        card_layout.addWidget(avatar_lbl)

        # 2. Developer Name
        name_lbl = QLabel(dev_name)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #F8FAFC;")
        card_layout.addWidget(name_lbl)

        # 3. Role / Subtitle
        role_lbl = QLabel(dev_role)
        role_lbl.setAlignment(Qt.AlignCenter)
        role_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #38BDF8;")
        card_layout.addWidget(role_lbl)

        # 4. Developer Description
        desc_lbl = QLabel(dev_desc)
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; line-height: 1.4; padding: 0 10px;")
        card_layout.addWidget(desc_lbl)

        # 5. Divider
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #334155; margin: 4px 0;")
        card_layout.addWidget(sep)

        # 6. Links Row
        links_layout = QHBoxLayout()
        links_layout.setSpacing(12)
        links_layout.setAlignment(Qt.AlignCenter)

        gh_btn = QPushButton("GitHub Profile")
        gh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0F172A;
                color: #CBD5E1;
                border: 1px solid #475569;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2563EB;
                color: #FFFFFF;
                border-color: #3B82F6;
            }
        """)
        gh_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(github_url)))
        links_layout.addWidget(gh_btn)

        repo_btn = QPushButton("Project Repository")
        repo_btn.setStyleSheet(gh_btn.styleSheet())
        repo_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(repo_url)))
        links_layout.addWidget(repo_btn)

        card_layout.addLayout(links_layout)

        # 7. Application & Version Info
        version_str = self.config_mgr.get("version", "1.1.0")
        app_info_lbl = QLabel(f"AI Background Remover  •  v{version_str}\nApache-2.0 License  •  100% Local Inference")
        app_info_lbl.setAlignment(Qt.AlignCenter)
        app_info_lbl.setStyleSheet("font-size: 11px; color: #64748B; margin-top: 6px;")
        card_layout.addWidget(app_info_lbl)

        root_layout.addWidget(card)

        # Bottom Close Button
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()

        root_layout.addLayout(btn_row)
