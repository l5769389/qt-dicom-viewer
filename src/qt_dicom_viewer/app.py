from __future__ import annotations

import logging
import sys
from importlib.resources import as_file, files

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon, QPixmap
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

def configure_process_identity() -> None:
    """Match installed shortcuts before Windows creates any application windows."""
    if sys.platform == "win32":
        import ctypes

        set_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_id.argtypes = [ctypes.c_wchar_p]
        set_id.restype = ctypes.c_long
        result = set_id("com.junliu.dicomvision")
        if result != 0:
            logger.warning("Could not set Windows application identity: %s", result)


def configure_application_identity(app: QApplication) -> None:
    app.setApplicationDisplayName("Voxenra")
    pixmap = QPixmap()
    brand = files("qt_dicom_viewer").joinpath("qml/assets/brand/voxenra-mark.png")
    if pixmap.loadFromData(brand.read_bytes()):
        app.setWindowIcon(QIcon(pixmap))
    else:
        logger.warning("Could not load application icon")


def main() -> None:
    configure_process_identity()
    app = QApplication(sys.argv)
    configure_application_identity(app)
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


def bind_controller() -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    image_provider = DicomImageProvider()
    app_controller = AppController(image_provider)
    from qt_dicom_viewer.ui.svg_icon_provider import SvgIconProvider
    engine.addImageProvider("navigation", SvgIconProvider())
    engine.addImageProvider("dicom", image_provider)
    engine.rootContext().setContextProperty("appController", app_controller)
    engine.image_provider = image_provider
    engine.app_controller = app_controller

    return engine

if __name__ == "__main__":
    main()
