"""Main Entry Point for AI Background Remover Desktop Application.

Initializes the PySide6 application, applies modern dark styling,
detects system hardware, configures local logging, and launches the main window.
Includes a global exception hook to ensure errors never silently close the app.
"""

from pathlib import Path
import sys
import traceback
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

# Ensure project root is on sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.gui.main_window import MainWindow
from app.gui.styles import DARK_THEME
from app.utils.logger import setup_logger

logger = setup_logger("AI-Background-Remover-Main")


def global_exception_hook(exctype, value, tb):
    """Global exception hook to prevent silent application crashes.

    Logs detailed technical traceback to logs/app.log and presents
    a friendly user-facing modal dialog with a 'View Error Details' option.
    """
    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    logger.error(f"Unhandled application exception:\n{tb_text}")

    # Display friendly dialog to user without closing the application
    app = QApplication.instance()
    if app:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Application Error")
        msg_box.setText("Background removal failed or encountered an error.\nSee details in the log (logs/app.log).")
        msg_box.setInformativeText("The application will remain open. You may try again or select a different model.")
        msg_box.setDetailedText(tb_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    else:
        sys.__excepthook__(exctype, value, tb)


def main():
    """Application entry point."""
    # Register global exception hook
    sys.excepthook = global_exception_hook

    logger.info("=========================================")
    logger.info("AI Background Remover: Application Startup")
    logger.info("=========================================")

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AI Background Remover")
    app.setApplicationVersion("1.2.0")
    app.setOrganizationName("LocalAI")

    # Apply global modern dark theme
    app.setStyleSheet(DARK_THEME)

    # Initialize main window (auto-detects hardware and runs recommendation engine)
    window = MainWindow()

    # Log detected hardware and model recommendation
    sys_info = window.sys_info
    rec_res = window.rec_result
    logger.info(
        f"Detected Hardware: CPU='{sys_info.cpu_name}' ({sys_info.cpu_cores}C/{sys_info.cpu_threads}T), "
        f"RAM={sys_info.ram_total_gb:.1f}GB total ({sys_info.ram_available_gb:.1f}GB available), "
        f"GPU='{sys_info.gpu_name}' (Vendor={sys_info.gpu_vendor}), "
        f"CUDA={sys_info.cuda_available}, AMD_Accel={sys_info.amd_acceleration_available}"
    )
    logger.info(f"Recommended Target: Device={rec_res.recommended_device}, Model={rec_res.recommended_model} ({rec_res.category})")

    window.show()
    logger.info("Main window initialized and displayed.")

    # Support smoke test flag for automated headless/CI testing
    if "--smoke-test" in sys.argv:
        logger.info("Smoke test flag detected: scheduling automatic shutdown in 2 seconds...")
        QTimer.singleShot(2000, app.quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
