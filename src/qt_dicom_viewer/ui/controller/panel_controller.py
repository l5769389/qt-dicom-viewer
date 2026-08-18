from typing import Dict

from PySide6.QtCore import QObject, Signal, QThread, Slot, Property
from PySide6.QtWidgets import QFileDialog

from qt_dicom_viewer.model import DicomFolderScanSnapshot, DicomSeriesSummary
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.ui.workers.dicom_scan_worker import (
    DicomScanWorker,
)


class PanelController(QObject):
    statusMessageChanged = Signal()
    scanningChanged = Signal()
    seriesItemsChanged = Signal()
    activeSeriesChanged = Signal(object)

    # parent=self 是 Qt 的对象所有权关系，不是业务上的“父子 Controller 调用关系”。
    def __init__(self,parent = None, series_catalog = None) -> None:
        super().__init__(parent)
        self._scan_thread: QThread | None = None
        self._scan_worker: DicomScanWorker | None = None
        self._scanning = False
        self._scan_series_record:Dict[str, DicomSeriesSummary] = {}
        self._series_catalog:SeriesCatalog = series_catalog


    def _start_folder_scan(self, folder: str) -> None:
        self._set_scanning(True)
        thread = QThread(self)
        worker = DicomScanWorker(folder)

        self._scan_thread = thread
        self._scan_worker = worker

        worker.moveToThread(thread)
        self._wire_scan_thread(self._scan_thread, self._scan_worker)
        thread.start()

    def _wire_scan_thread(self,thread: QThread | None, worker: QObject | None) -> None:
        if thread is None or worker is None:
            return

        thread.started.connect(worker.run)
        worker.finished.connect(self._handle_scan_finished)
        worker.failed.connect(self._handle_scan_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._clean_scan_thread)

        worker.process.connect(self._handle_scan_process)

    def _handle_scan_process(self, result:DicomFolderScanSnapshot) -> None:
        self._update_series_record(result)
        self.update_series_session(result)

    def update_series_session(self, dicom_scan_snapshot:DicomFolderScanSnapshot):
        self._series_catalog.update(dicom_scan_snapshot)


    def _handle_scan_finished(self, result: DicomFolderScanSnapshot | None) -> None:
        if result is not None:
            self._update_series_record(result)
            self.update_series_session(result)

    def _handle_scan_failed(self, error) -> None:
        pass

    def _clean_scan_thread(self) -> None:
        thread = self._scan_thread
        self._scan_thread = None
        self._scan_worker = None
        self._set_scanning(False)

        if thread is not None:
            thread.deleteLater()

    def _set_scanning(self, scanning: bool) -> None:
        if self._scanning == scanning:
            return

        self._scanning = scanning
        self.scanningChanged.emit()

    def _update_series_record(self, process:DicomFolderScanSnapshot | None) -> None:
        if process is None:
            return
        for each_series in process.series:
            self._scan_series_record[each_series.series_instance_uid] = each_series
        self.seriesItemsChanged.emit()

    @Slot()
    def openFolderDialog(self) -> None:
        if self._scanning:
            return
        folder = QFileDialog.getExistingDirectory(None, "Open DICOM Folder")
        if not folder:
            return

        self._start_folder_scan(folder)

    @Property("QVariantList", notify=seriesItemsChanged)
    def seriesItems(self):
       return [{
            "patientName": summary.patient_name,
            "seriesInstanceUid": summary.series_instance_uid,
            "dicomFileCount": summary.dicom_file_count,
            "modality": summary.modality,
        } for series_id,summary  in self._scan_series_record.items()]


    @Slot(str)
    def loadSeries(self,active_series_uid):
        series = self._series_catalog.get_series(active_series_uid)
        if series is not None:
            self.activeSeriesChanged.emit(active_series_uid)


