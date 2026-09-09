import time
from pathlib import Path

from PySide6.QtCore import QObject, Slot, Signal, QThread

from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner
from qt_dicom_viewer.core.local_import import (
    LocalImportStore,
    ImportCancelled,
    ImportErrorDetail,
)


class DicomScanWorker(QObject):
    finished = Signal(object)
    failed = Signal(object)
    process = Signal(object)
    status = Signal(str)
    process_report_interval = 0.1

    def __init__(self, paths, store=None):
        super().__init__()
        self.paths = [paths] if isinstance(paths, (str, Path)) else list(paths)
        self.store = store or LocalImportStore()

    @Slot()
    def run(self):
        latest = None
        cancelled = QThread.currentThread().isInterruptionRequested
        try:
            files = self.store.prepare(
                self.paths, cancelled=cancelled, progress=self.status.emit
            )
            self.status.emit("正在读取 DICOM 文件…")
            last_emit = 0
            for result in DicomFolderScanner().scan_files(
                files, folder=Path(self.paths[0]).parent, cancelled=cancelled
            ):
                latest = result
                now = time.monotonic()
                if now - last_emit >= self.process_report_interval:
                    last_emit = now
                    self.process.emit(result)
            self.finished.emit(latest)
        except ImportCancelled:
            self.finished.emit(latest)
        except ImportErrorDetail as error:
            self.failed.emit(str(error))
        except Exception:
            self.failed.emit("导入失败，请检查文件是否完整、可读，以及剩余磁盘空间。")
