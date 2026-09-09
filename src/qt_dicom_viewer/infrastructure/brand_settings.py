"""Voxenra storage identity and non-destructive legacy preference migration."""
import logging
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QStandardPaths, QSaveFile, QIODevice

logger = logging.getLogger(__name__)
APP_NAME = "Voxenra"
# Compatibility only: released versions stored user preferences under this name.
LEGACY_ORGANIZATION = "QtDicomViewer"
LEGACY_APPLICATION = "Qt DICOM Viewer"


def migrate_preferences(source: Path, destination: Path) -> None:
    if source == destination:
        return
    for name in ("display-settings.json", "pacs.json"):
        old, new = source / name, destination / name
        if not old.is_file() or new.exists():
            continue
        try:
            contents = old.read_bytes()
            destination.mkdir(parents=True, exist_ok=True)
            output = QSaveFile(str(new))
            if not output.open(QIODevice.WriteOnly):
                raise OSError(output.errorString())
            if output.write(contents) != len(contents):
                output.cancelWriting()
                raise OSError(output.errorString())
            if not output.commit():
                raise OSError(output.errorString())
        except OSError:
            logger.exception("Could not migrate legacy preference file %s", name)


def configure_storage_identity() -> None:
    QCoreApplication.setOrganizationName(LEGACY_ORGANIZATION)
    QCoreApplication.setApplicationName(LEGACY_APPLICATION)
    source = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
    QCoreApplication.setOrganizationName(APP_NAME)
    QCoreApplication.setApplicationName(APP_NAME)
    destination = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation))
    migrate_preferences(source, destination)
