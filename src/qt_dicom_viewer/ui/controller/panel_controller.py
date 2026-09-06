from typing import Dict

from PySide6.QtCore import QObject, Signal, QThread, QTimer, Slot, Property, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from qt_dicom_viewer.model import DicomFolderScanSnapshot, DicomSeriesRecord
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.ui.workers.dicom_scan_worker import (
    DicomScanWorker,
)

from qt_dicom_viewer.core.series_sidebar import build_sidebar_rows
from qt_dicom_viewer.service.thumbnail_service import ThumbnailRequest, ThumbnailService


class PanelController(QObject):
    statusMessageChanged = Signal()
    scanningChanged = Signal()
    seriesItemsChanged = Signal()
    sidebarItemsChanged = Signal()
    selectionChanged = Signal()
    patientSearchChanged = Signal()
    # series_uid , tab_type
    tabCreateRequested = Signal(str, str)
    fusionCreateRequested = Signal(str, str)
    fusionDialogChanged = Signal()

    # parent=self 是 Qt 的对象所有权关系，不是业务上的“父子 Controller 调用关系”。
    def __init__(self, parent=None, series_catalog=None, *, image_provider=None) -> None:
        super().__init__(parent)
        self._scan_thread: QThread | None = None
        self._scan_worker: DicomScanWorker | None = None
        self._scanning = False
        self._scan_series_record: Dict[str, DicomSeriesRecord] = {}
        self._removed_series_uids: set[str] = set()
        self._series_catalog:SeriesCatalog = series_catalog
        self._active_series_uid = ""
        self._selected_series_uids = []
        self._fusion_anchor_uid = ""
        self._fusion_partner_uid = ""
        self._fusion_dialog_open = False
        self._fusion_error = ""
        self._patient_search = ""
        self._collapsed_groups: set[str] = set()
        self._thumbnails: dict[str, str] = {}
        self._thumbnail_version = 0
        self._image_provider = image_provider
        self._closing = False
        self._thumbnail_service = ThumbnailService(self) if image_provider is not None else None
        self._thumbnail_timer = QTimer(self)
        self._thumbnail_timer.setSingleShot(True)
        self._thumbnail_timer.setInterval(150)
        self._thumbnail_timer.timeout.connect(self._request_thumbnails)
        if self._thumbnail_service is not None:
            self._thumbnail_service.finished.connect(self._accept_thumbnail)


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
        if not scanning and not self._closing:
            self._thumbnail_timer.start()

    def _update_series_record(self, process:DicomFolderScanSnapshot | None) -> None:
        if process is None or self._closing:
            return
        for each_series in process.series:
            if each_series.series_instance_uid in self._removed_series_uids:
                continue
            self._scan_series_record[each_series.series_instance_uid] = each_series
        self.seriesItemsChanged.emit()
        self.sidebarItemsChanged.emit()
        self.fusionDialogChanged.emit()
        if self._thumbnail_service is not None:
            self._thumbnail_timer.start()

    @Property("QVariantList", notify=sidebarItemsChanged)
    def sidebarItems(self):
        return build_sidebar_rows(self._scan_series_record.values(), self._patient_search,
                                  self._collapsed_groups, self._thumbnails)

    @Property(str, notify=selectionChanged)
    def activeSeriesUid(self):
        return self._active_series_uid

    @Property(str, notify=selectionChanged)
    def activeSeriesModality(self) -> str:
        series = self._scan_series_record.get(self._active_series_uid)
        return series.modality.strip().upper() if series is not None else ""

    @Slot(str, result=str)
    def seriesModality(self, series_uid: str) -> str:
        series = self._scan_series_record.get(series_uid)
        return series.modality.strip().upper() if series is not None else ""

    @Slot(str)
    def selectSeries(self, series_uid):
        if series_uid in self._scan_series_record:
            self._active_series_uid = series_uid
            self._selected_series_uids = [series_uid]
            self.selectionChanged.emit()

    @Property("QVariantList", notify=selectionChanged)
    def selectedSeriesUids(self):
        return list(self._selected_series_uids)

    @Slot(str, bool)
    def selectSeriesWithModifiers(self, uid, additive):
        if not additive:
            self.selectSeries(uid)
        elif uid in self._scan_series_record:
            if uid in self._selected_series_uids:
                self._selected_series_uids.remove(uid)
            else:
                self._selected_series_uids.append(uid)
            self._active_series_uid = self._selected_series_uids[-1] if self._selected_series_uids else ""
            self.selectionChanged.emit()

    @Slot(str)
    def selectContextSeries(self, uid):
        if uid in self._selected_series_uids:
            self._active_series_uid = uid
            self.selectionChanged.emit()
        else:
            self.selectSeries(uid)

    @Property(bool, notify=fusionDialogChanged)
    def fusionDialogOpen(self):
        return self._fusion_dialog_open

    @Property(str, notify=fusionDialogChanged)
    def fusionError(self):
        return self._fusion_error

    @Property(str, notify=fusionDialogChanged)
    def fusionPartnerUid(self):
        return self._fusion_partner_uid

    @Property(str, notify=fusionDialogChanged)
    def fusionIdentityWarning(self):
        a = self._scan_series_record.get(self._fusion_anchor_uid)
        b = self._scan_series_record.get(self._fusion_partner_uid)
        if a is None or b is None:
            return ""
        if a.patient_id and b.patient_id and (a.patient_id, a.patient_id_issuer) == (b.patient_id, b.patient_id_issuer):
            if a.study_instance_uid and a.study_instance_uid == b.study_instance_uid:
                return ""
            return f"同患者的不同检查或检查信息缺失：{a.study_date or '日期未知'} / {b.study_date or '日期未知'}。请核对是否适合融合。"
        return (f"请核对所选数据：{a.patient_name} / {a.patient_id or 'ID 缺失'} 与 "
                f"{b.patient_name} / {b.patient_id or 'ID 缺失'}。患者身份不同或无法确认。")

    @Property("QVariantList", notify=fusionDialogChanged)
    def fusionCandidates(self):
        from qt_dicom_viewer.core.pet_fusion import fusion_series_error
        anchor = self._scan_series_record.get(self._fusion_anchor_uid)
        if anchor is None:
            return []
        target = "CT" if anchor.modality.upper() == "PT" else "PT"
        records = [r for r in self._scan_series_record.values() if r.modality.upper() == target]
        def rank(r):
            same = bool(anchor.patient_id and r.patient_id and
                        (anchor.patient_id, anchor.patient_id_issuer) == (r.patient_id, r.patient_id_issuer))
            return (0 if same and r.study_instance_uid == anchor.study_instance_uid else 1 if same else 2,
                    r.study_date, r.series_description, r.series_instance_uid)
        return [dict(seriesUid=r.series_instance_uid, patientName=r.patient_name,
                     patientId=r.patient_id, studyDate=r.study_date,
                     description=r.series_description, count=r.dicom_file_count,
                     error=fusion_series_error(r)) for r in sorted(records, key=rank)]

    @Slot()
    def requestFusionView(self):
        self._fusion_error = ""
        self._fusion_partner_uid = ""
        selected = self._selected_series_uids or ([self._active_series_uid] if self._active_series_uid else [])
        self._fusion_anchor_uid = selected[0] if selected else ""
        self._fusion_dialog_open = True
        if len(selected) not in (1, 2):
            self._fusion_error = "请选择一个序列，或恰好一个 CT 和一个 PET 序列"
            self._fusion_anchor_uid = ""
        elif len(selected) == 2:
            self._fusion_partner_uid = selected[1]
            self.confirmFusion(False)
        elif self.seriesModality(selected[0]) not in ("CT", "PT"):
            self._fusion_error = "融合仅支持 CT 和 PET 序列"
            self._fusion_anchor_uid = ""
        self.fusionDialogChanged.emit()

    @Slot(str)
    def selectFusionPartner(self, uid):
        self._fusion_partner_uid = uid
        self._fusion_error = ""
        self.fusionDialogChanged.emit()

    @Slot(bool)
    def confirmFusion(self, identity_confirmed):
        from qt_dicom_viewer.core.pet_fusion import fusion_series_error
        records = [self._scan_series_record.get(uid) for uid in (self._fusion_anchor_uid, self._fusion_partner_uid)]
        if any(r is None for r in records):
            self._fusion_error = "请选择配对序列；原序列可能已被移除"
        elif {r.modality.upper() for r in records} != {"CT", "PT"}:
            self._fusion_error = "融合需要恰好一个 CT 和一个 PET 序列"
        else:
            self._fusion_error = next((error for r in records if (error := fusion_series_error(r))), "")
            if not self._fusion_error and (not self.fusionIdentityWarning or identity_confirmed):
                ct = next(r for r in records if r.modality.upper() == "CT")
                pet = next(r for r in records if r.modality.upper() == "PT")
                if self._series_catalog.get_series(ct.series_instance_uid) and self._series_catalog.get_series(pet.series_instance_uid):
                    self._fusion_dialog_open = False
                    self.fusionCreateRequested.emit(ct.series_instance_uid, pet.series_instance_uid)
                else:
                    self._fusion_error = "序列已不在当前目录中"
        self.fusionDialogChanged.emit()

    @Slot()
    def cancelFusion(self):
        self._fusion_dialog_open = False
        self._fusion_partner_uid = ""
        self.fusionDialogChanged.emit()

    @Property(str, notify=patientSearchChanged)
    def patientSearch(self):
        return self._patient_search

    @Slot(str)
    def setPatientSearch(self, value):
        if value != self._patient_search:
            self._patient_search = value
            self.patientSearchChanged.emit()
            self.sidebarItemsChanged.emit()

    @Slot(str)
    def toggleGroup(self, key):
        if key in self._collapsed_groups:
            self._collapsed_groups.remove(key)
        else:
            self._collapsed_groups.add(key)
        self.sidebarItemsChanged.emit()

    @Slot()
    def _request_thumbnails(self):
        if self._closing or self._scanning or self._thumbnail_service is None:
            return
        for series in self._scan_series_record.values():
            if series.instances:
                instance = series.instances[len(series.instances) // 2]
                self._thumbnail_service.submit(ThumbnailRequest(series.series_instance_uid, instance.path))

    @Slot(object, object)
    def _accept_thumbnail(self, request, image):
        if self._closing or image.isNull():
            return
        series = self._scan_series_record.get(request.series_uid)
        if not series or not series.instances or series.instances[len(series.instances) // 2].path != request.path:
            return
        image_id = "thumbnail-" + request.series_uid
        self._image_provider.set_image(image_id, image)
        self._thumbnail_version += 1
        self._thumbnails[request.series_uid] = f"image://dicom/{image_id}/{self._thumbnail_version}"
        self.sidebarItemsChanged.emit()

    @Slot()
    def shutdown(self):
        self._closing = True
        self._thumbnail_timer.stop()
        if self._thumbnail_service is not None:
            self._thumbnail_service.shutdown()
        if self._scan_thread is not None:
            self._scan_thread.requestInterruption()
            self._scan_thread.quit()
            self._scan_thread.wait()

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

    @Property(bool, notify=scanningChanged)
    def scanning(self) -> bool:
        return self._scanning


    @Slot(str, str)
    def openSeriesView(self, active_series_uid: str, tab_type: str):
        if active_series_uid not in self._scan_series_record:
            return
        series = self._series_catalog.get_series(active_series_uid)
        if series is not None:
            if (
                series.modality.upper() == "PT"
                and tab_type not in ("2d", "tag", "mpr")
            ):
                return
            self.tabCreateRequested.emit(active_series_uid, tab_type)

    @Slot(str, result=bool)
    def openSeriesDirectory(self, series_uid: str) -> bool:
        series = self._scan_series_record.get(series_uid)
        source = series.first_file if series is not None else None
        if source is None:
            return False
        directory = source.parent
        if not directory.is_dir():
            return False
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    @Slot(str)
    def removeSeries(self, series_uid: str) -> None:
        series = self._scan_series_record.pop(series_uid, None)
        if series is None:
            return

        self._removed_series_uids.add(series_uid)
        self._thumbnail_timer.stop()
        if self._thumbnail_service is not None:
            self._thumbnail_service.cancel(series_uid)
        self._thumbnails.pop(series_uid, None)
        if self._image_provider is not None:
            self._image_provider.remove_image("thumbnail-" + series_uid)

        if self._active_series_uid == series_uid:
            self._active_series_uid = ""
            self.selectionChanged.emit()
        if series_uid in self._selected_series_uids:
            self._selected_series_uids.remove(series_uid)
            self.selectionChanged.emit()
        self.fusionDialogChanged.emit()
        self.seriesItemsChanged.emit()
        self.sidebarItemsChanged.emit()
        if self._thumbnail_service is not None and not self._scanning:
            self._thumbnail_timer.start()
