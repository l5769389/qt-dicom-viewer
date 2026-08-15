from __future__ import annotations

import logging
import sys
from importlib.resources import as_file, files

from PySide6.QtCore import QCoreApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from qt_dicom_viewer.infrastructure.exception_handler import install_exception_hooks
from qt_dicom_viewer.ui.app_controller import AppController
from qt_dicom_viewer.ui.dicom_image_provider import DicomImageProvider
from qt_dicom_viewer.infrastructure.logging_config import (
    configure_logging,
)

logger = logging.getLogger(__name__)
install_exception_hooks()

def main() -> None:
    app = QApplication(sys.argv)
    QCoreApplication.setOrganizationName("QtDicomViewer")
    QCoreApplication.setApplicationName(
        "Qt DICOM Viewer"
    )

    log_path = configure_logging(debug=True)

    logger.info("Application starting")
    logger.info("Log file: %s", log_path)
    engine = bind_controller()
    app.aboutToQuit.connect(engine.app_controller.shutdown)

    qml_path = files("qt_dicom_viewer").joinpath("qml/Main.qml")
    try:
        engine.load(qml_path)

        if not engine.rootObjects():
            logger.critical("Failed to load QML root component")
            return 1

        return app.exec()
    finally:
        engine.app_controller.shutdown()

    sys.exit(app.exec())



def bind_controller() -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    image_provider = DicomImageProvider()
    app_controller = AppController(image_provider)
    engine.addImageProvider("dicom", image_provider)
    engine.rootContext().setContextProperty("appController", app_controller)
    engine.image_provider = image_provider
    engine.app_controller = app_controller

    return engine

if __name__ == "__main__":
    main()
