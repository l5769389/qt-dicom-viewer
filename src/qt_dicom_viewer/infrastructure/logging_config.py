from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def configure_logging(debug: bool = False) -> Path:
    log_root = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.AppLocalDataLocation
        )
    )
    log_directory = log_root / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    log_path = log_directory / "dicomvision.log"

    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | %(levelname)-8s | "
            "%(threadName)s | %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            console_handler,
            file_handler,
        ],
        force=True,
    )

    return log_path