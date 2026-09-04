import time

from PySide6.QtCore import QObject, Slot, Signal, QThread

from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner


class DicomScanWorker(QObject):
    finished = Signal(object)
    failed = Signal(object)
    process = Signal(object)
    folder: str
    process_report_interval = 0.1

    def __init__(self, folder:str) -> None:
        super().__init__()
        self.folder = folder



    @Slot()
    def run(self) -> None:
        try:
            latest_emit_time = 0
            lastest_result = None

            for result in DicomFolderScanner().scan(self.folder):
                if QThread.currentThread().isInterruptionRequested():
                    self.finished.emit(lastest_result)
                    return
                now = time.monotonic()
                lastest_result = result
                if  now - latest_emit_time >= self.process_report_interval:
                    latest_emit_time = now
                    self.process.emit(result)
                    lastest_result = None
            self.finished.emit(lastest_result)
        except Exception as e:
            self.failed.emit('error')

