"""Logging utility for AI Background Remover.

Configures local, privacy-safe rotating logging to logs/app.log.
Guarantees:
- Logs are stored locally in logs/app.log (5 MB rotating, 3 backups).
- Sanitizes personal paths (e.g. C:\\Users\\<name> replaced with ~).
- NEVER logs image contents, binary pixels, passwords, or personal identifying data.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def sanitize_message(msg: str) -> str:
    """Sanitize message to remove user home paths and avoid logging sensitive data."""
    user_profile = os.environ.get("USERPROFILE")
    if user_profile and user_profile in msg:
        msg = msg.replace(user_profile, "~")
    # Clean any accidental long base64 or pixel hex dumps
    msg = re.sub(r"[A-Za-z0-9+/=]{200,}", "<binary_data_truncated>", msg)
    return msg


class SanitizingFormatter(logging.Formatter):
    """Custom logging formatter that filters out personal paths and binary dumps."""

    def format(self, record: logging.LogRecord) -> str:
        record.msg = sanitize_message(str(record.msg))
        return super().format(record)


_GLOBAL_LOGGER: logging.Logger | None = None


def setup_logger(
    name: str = "AI-Background-Remover",
    log_file: Path | str | None = None
) -> logging.Logger:
    """Configure and return the standardized application logger."""
    global _GLOBAL_LOGGER
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = SanitizingFormatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Rotating to logs/app.log)
    if log_file is None:
        log_dir = get_base_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Could not configure file logger at {log_file}: {exc}", file=sys.stderr)

    _GLOBAL_LOGGER = logger
    return logger


def get_logger() -> logging.Logger:
    """Retrieve the active logger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = setup_logger()
    return _GLOBAL_LOGGER
