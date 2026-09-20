"""Script to capture pixel-perfect screenshots of the AI Background Remover application."""

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication
from app.gui.main_window import MainWindow
from app.processing.batch_worker import QueueItem


def capture():
    # Set offscreen or windows platform
    os.environ["QT_QPA_PLATFORM"] = "windows"
    app = QApplication.instance() or QApplication(sys.argv)

    window = MainWindow()
    window.resize(1240, 800)

    # Populate sample items
    img1 = PROJECT_ROOT / "input" / "portrait_1.jpg"
    out1 = PROJECT_ROOT / "output" / "portrait_1_transparent.png"
    img2 = PROJECT_ROOT / "input" / "portrait_2.jpg"
    out2 = PROJECT_ROOT / "output" / "portrait_2_transparent.png"
    img3 = PROJECT_ROOT / "input" / "test_portrait.jpg"

    item1 = QueueItem.from_path(img1)
    item1.status = "Completed"
    item1.output_path = out1
    item1.processing_time_s = 32.87
    item1.model_name = "BiRefNet Portrait"

    item2 = QueueItem.from_path(img2)
    item2.status = "Completed"
    item2.output_path = out2
    item2.processing_time_s = 31.92
    item2.model_name = "BiRefNet Portrait"

    item3 = QueueItem.from_path(img3)
    item3.status = "Pending"
    item3.model_name = "BiRefNet Portrait"

    window.queue_widget.items = [item1, item2, item3]
    window.queue_widget._refresh_table()
    window.queue_widget.table.selectRow(0)

    # Display item1 in preview widget
    window.preview_widget.display_item(item1)
    window.preview_widget.canvas.split_pos = 0.50
    window.preview_widget.canvas.fit_to_window()

    # Progress bar and status
    window.progress_bar.setValue(67)
    window.status_bar.showMessage("Processed 2 of 3 images | BiRefNet Portrait loaded on CPU (6 threads)")

    window.show()
    app.processEvents()

    # Create screenshots directory if needed
    screenshot_dir = PROJECT_ROOT / "screenshots"
    screenshot_dir.mkdir(exist_ok=True)

    # 1. Main Window Screenshot (Split View)
    main_shot = window.grab()
    main_path = screenshot_dir / "app_main_window.png"
    main_shot.save(str(main_path), "PNG")
    print(f"Captured: {main_path}")

    # 2. Side-by-side mode screenshot
    window.preview_widget._set_mode("side_by_side")
    window.preview_widget.canvas.fit_to_window()
    app.processEvents()
    side_shot = window.grab()
    side_path = screenshot_dir / "preview_side_by_side.png"
    side_shot.save(str(side_path), "PNG")
    print(f"Captured: {side_path}")

    window.close()
    print("Done capturing screenshots!")


if __name__ == "__main__":
    capture()
