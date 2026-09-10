from typing import Dict
from dataclasses import replace

from qt_dicom_viewer.core.local_import import LocalImportStore
from qt_dicom_viewer.core.dicom_scanner import _build_series_from_map

from PySide6.QtCore import QObject, Signal, QThread, QTimer, Slot, Property, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog
from qt_dicom_viewer.ui.dialogs.local_import_dialog import select_import_paths

from qt_dicom_viewer.model import DicomFolderScanSnapshot, DicomSeriesRecord
from qt_dicom_viewer.application.series_catalog import SeriesCatalog
from qt_dicom_viewer.ui.workers.dicom_scan_worker import (
    DicomScanWorker,
)

from qt_dicom_viewer.core.series_sidebar import build_sidebar_rows
from qt_dicom_viewer.ui.controller.series_sidebar_model import SeriesSidebarModel
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
        self._status_message = ""
        self._import_error = False
        self._last_import_directory = ""
        self._import_store = LocalImportStore()
        self._import_base = {}
        self._last_import_snapshot = None
        self._scan_series_record: Dict[str, DicomSeriesRecord] = {}
        self._removed_series_uids: set[str] = set()
        self._series_catalog:SeriesCatalog = series_catalog
        self._active_series_uid = ""
        self._selected_series_uids = []
        self._fusion_anchor_uid = ""
        self._fusion_partner_uid = ""
        self._fusion_dialog_open = False
        self._fusion_error = ""
        self._fusion_show_all = False
        self._patient_search = ""
        self._collapsed_groups: set[str] = set()
        self._thumbnails: dict[str, str] = {}
        self._thumbnail_version = 0
        self._image_provider = image_provider
        self._closing = False
        self._sidebar_model = SeriesSidebarModel(self)
        self._compact_sidebar_model = SeriesSidebarModel(self)
        self.sidebarItemsChanged.connect(self._refresh_sidebar_model)
        self._thumbnail_service = ThumbnailService(self) if image_provider is not None else None
        self._thumbnail_timer = QTimer(self)
        self._thumbnail_timer.setSingleShot(True)
        self._thumbnail_timer.setInterval(150)
        self._thumbnail_timer.timeout.connect(self._request_thumbnails)
        if self._thumbnail_service is not None:
            self._thumbnail_service.finished.connect(self._accept_thumbnail)


    def _start_folder_scan(self, folder: str) -> None:
        self._start_import([folder])

    def _start_import(self, paths):
        if self._closing or self._scanning or not paths:
            return
        self._last_import_snapshot = None
        self._import_base = dict(self._scan_series_record)
        self._set_status("正在准备导入…")
        # An explicit new import can restore items removed from the previous scan.
        self._removed_series_uids.clear()
        self._set_scanning(True)
        thread = QThread(self)
        worker = DicomScanWorker(paths, self._import_store)

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
        worker.status.connect(self._set_status)

    @Slot(object)
    def _handle_scan_process(self, result:DicomFolderScanSnapshot) -> None:
        if self._closing or result is None: return
        self._last_import_snapshot = result
        merged = self._merge_import(result)
        self._update_series_record(merged)
        self.update_series_session(merged)
        self._set_status(f"正在读取影像 · {result.dicom_file_count} 个 DICOM / {result.total_file_count} 个文件")

    def _merge_import(self, result):
        grouped = {}
        for series in result.series:
            uid = series.series_instance_uid
            if uid not in self._import_base:
                # Sidebar removal deliberately retains records used by open views.
                self._import_base[uid] = self._series_catalog.get_series(uid)
            old = self._import_base.get(uid)
            combined = {i.sop_instance_uid: i for i in old.instances} if old else {}
            combined.update({i.sop_instance_uid: i for i in series.instances})
            for instance in combined.values():
                grouped.setdefault((instance.study_instance_uid, instance.series_instance_uid), []).append(instance)
        return replace(result, series=_build_series_from_map(grouped))

    def update_series_session(self, dicom_scan_snapshot:DicomFolderScanSnapshot):
        self._series_catalog.update(dicom_scan_snapshot)


    @Slot(object)
    def _handle_scan_finished(self, result: DicomFolderScanSnapshot | None) -> None:
        if self._closing: return
        if result is not None:
            self._handle_scan_process(result)
        final = self._last_import_snapshot
        if self._scan_thread and self._scan_thread.isInterruptionRequested():
            self._set_status("已取消导入；已载入的序列仍可使用。")
        elif final is None or not final.dicom_file_count:
            self._set_status("未找到可用的 DICOM 影像，请检查所选文件。", True)
        else:
            self._set_status(f"已导入 {len(final.series)} 个序列、{final.dicom_file_count} 个 DICOM 文件"
                             + (f" · 跳过 {final.skipped_file_count} 个重复或非 DICOM 文件" if final.skipped_file_count else ""))

    @Slot(object)
    def _handle_scan_failed(self, error) -> None:
        if not self._closing:
            self._set_status(str(error), True)

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self): return self._status_message

    @Property(bool, notify=statusMessageChanged)
    def importError(self): return self._import_error

    @Slot(str)
    def _set_status(self, message, error=False):
        if self._closing: return
        self._status_message, self._import_error = message, error
        self.statusMessageChanged.emit()

    @Slot()
    def dismissImportStatus(self):
        if not self._scanning: self._set_status("")

    @Slot()
    def cancelImport(self):
        if self._scan_thread:
            self._set_status("正在取消导入…")
            self._scan_thread.requestInterruption()

    @Slot("QVariantList", result=bool)
    def canImportUrls(self, urls):
        return bool(urls) and not self._closing and not self._scanning and all(
            QUrl(url).isLocalFile() and QUrl(url).toLocalFile() for url in urls)

    @Slot("QVariantList", result=bool)
    def importUrls(self, urls):
        if not self.canImportUrls(urls): return False
        self._start_import([QUrl(url).toLocalFile() for url in urls])
        return True

    @Slot()
    def openImportDialog(self):
        if self._closing:
            return
        if self._scanning:
            self.cancelImport()
            return
        paths = select_import_paths(self._last_import_directory)
        if paths:
            from pathlib import Path
            self._last_import_directory = str(Path(paths[0]).parent)
            self._start_import(paths)

    @Slot()
    def openFilesDialog(self):
        if self._scanning: return
        files, _ = QFileDialog.getOpenFileNames(None, "打开 DICOM 文件或压缩包", "",
            "DICOM 与压缩包 (*.dcm *.dicom *.ima *.zip *.rar *.7z *.tar *.gz *.tgz *.bz2 *.tbz2 *.xz *.txz);;所有文件 (*)")
        if files: self._start_import(files)

    def cleanup_imports(self):
        self._import_store.cleanup()

    @Slot()
    def _clean_scan_thread(self) -> None:
        thread = self._scan_thread
        # finished is emitted before the worker's deferred deletion completes.
        # Keep its Python wrapper alive until the native thread has fully exited.
        if thread is not None:
            thread.wait()
        self._scan_thread = None
        self._scan_worker = None
        self._import_base = {}
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

    def _refresh_sidebar_model(self):
        rows = self.sidebarItems
        self._sidebar_model.update_rows(rows, self._patient_search)
        # The compact rail keeps the search scope but exposes series inside folded groups.
        if self._collapsed_groups and not self._patient_search.strip():
            rows = build_sidebar_rows(self._scan_series_record.values(), self._patient_search,
                                      set(), self._thumbnails)
        self._compact_sidebar_model.update_rows(
            [row for row in rows if row["kind"] == "series"], self._patient_search)

    @Property(QObject, constant=True)
    def compactSidebarModel(self):
        return self._compact_sidebar_model

    @Property(QObject, constant=True)
    def sidebarModel(self):
        return self._sidebar_model

    @Property(bool, notify=seriesItemsChanged)
    def hasSeries(self):
        return bool(self._scan_series_record)

    @Property("QVariantList", notify=sidebarItemsChanged)
    def sidebarItems(self):
        return build_sidebar_rows(self._scan_series_record.values(), self._patient_search,
                                  self._collapsed_groups, self._thumbnails)

    @Property(str, notify=selectionChanged)
    def activeSeriesUid(self):
        return self._active_series_uid

    @Property(bool, notify=selectionChanged)
    def activeSeriesSupportsFourD(self) -> bool:
        return self.seriesSupportsFourD(self._active_series_uid)

    @Slot(str, result=bool)
    def seriesSupportsFourD(self, series_uid: str) -> bool:
        series = self._scan_series_record.get(series_uid)
        return bool(series is not None and series.supports_four_d)
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
        elif not self._selected_series_uids:
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

    @staticmethod
    def _same_patient(a, b):
        return bool(a.patient_id and b.patient_id and
                    (a.patient_id, a.patient_id_issuer) == (b.patient_id, b.patient_id_issuer))

    @Property("QVariantMap", notify=fusionDialogChanged)
    def fusionAnchor(self):
        record = self._scan_series_record.get(self._fusion_anchor_uid)
        return self._fusion_record_item(record) if record else {}

    @Property(str, notify=fusionDialogChanged)
    def fusionTargetModality(self):
        return "CT" if self.seriesModality(self._fusion_anchor_uid) == "PT" else "PET"

    @Property(bool, notify=fusionDialogChanged)
    def fusionShowAllPatients(self):
        return self._fusion_show_all

    @Slot(bool)
    def setFusionShowAllPatients(self, enabled):
        self._fusion_show_all = bool(enabled)
        if self._fusion_partner_uid not in {r["seriesUid"] for r in self.fusionCandidates}:
            self._fusion_partner_uid = ""
        self._fusion_error = ""
        self.fusionDialogChanged.emit()

    def _fusion_record_item(self, record):
        from qt_dicom_viewer.core.pet_fusion import fusion_series_error
        return dict(seriesUid=record.series_instance_uid, patientName=record.patient_name,
                    patientId=record.patient_id, studyDate=record.study_date,
                    description=record.series_description or record.modality,
                    modality="PET" if record.modality.upper() == "PT" else record.modality,
                    count=record.dicom_file_count,
                    thumbnailUrl=self._thumbnails.get(record.series_instance_uid, ""),
                    error=fusion_series_error(record))

    @Property(bool, notify=fusionDialogChanged)
    def fusionCanConfirm(self):
        from qt_dicom_viewer.core.pet_fusion import fusion_series_error
        a = self._scan_series_record.get(self._fusion_anchor_uid)
        b = self._scan_series_record.get(self._fusion_partner_uid)
        return bool(a and b and {a.modality.upper(), b.modality.upper()} == {"CT", "PT"}
                    and not fusion_series_error(a) and not fusion_series_error(b))

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

    @Property("QVariantMap", notify=sidebarItemsChanged)
    def fusionThumbnails(self):
        # Update images independently of the candidates model: a late thumbnail
        # must not recreate delegates or move the user's scroll position.
        return dict(self._thumbnails)

    @Property("QVariantList", notify=fusionDialogChanged)
    def fusionCandidates(self):
        anchor = self._scan_series_record.get(self._fusion_anchor_uid)
        if anchor is None:
            return []
        target = "CT" if anchor.modality.upper() == "PT" else "PT"
        records = [r for r in self._scan_series_record.values() if r.modality.upper() == target
                   and (self._fusion_show_all or self._same_patient(anchor, r))]
        def rank(r):
            same = self._same_patient(anchor, r)
            return (0 if same and r.study_instance_uid == anchor.study_instance_uid else 1 if same else 2,
                    0 if anchor.frame_of_reference_uid and anchor.frame_of_reference_uid == r.frame_of_reference_uid else 1,
                    r.study_date, r.series_description, r.series_instance_uid)
        items = []
        for record in sorted(records, key=rank):
            item = self._fusion_record_item(record)
            same = self._same_patient(anchor, record)
            item["relationship"] = ("同患者 · 同检查" if same and anchor.study_instance_uid
                                    and anchor.study_instance_uid == record.study_instance_uid else
                                    "同患者 · 其他检查" if same else "需核对患者身份")
            item["spatialStatus"] = ("共享空间坐标" if anchor.frame_of_reference_uid
                                     and anchor.frame_of_reference_uid == record.frame_of_reference_uid
                                     else "需核对配准")
            items.append(item)
        return items

    @Slot()
    def requestFusionView(self):
        self._fusion_error = ""
        self._fusion_partner_uid = ""
        self._fusion_show_all = False
        selected = self._selected_series_uids or ([self._active_series_uid] if self._active_series_uid else [])
        self._fusion_anchor_uid = selected[0] if selected else ""
        self._fusion_dialog_open = True
        if len(selected) not in (1, 2):
            self._fusion_error = "请选择一个序列，或恰好一个 CT 和一个 PET 序列"
            self._fusion_anchor_uid = ""
        elif len(selected) == 2:
            self._fusion_partner_uid = selected[1]
            a = self._scan_series_record.get(selected[0])
            b = self._scan_series_record.get(selected[1])
            self._fusion_show_all = bool(a and b and not self._same_patient(a, b))
            self.confirmFusion(False)
        elif self.seriesModality(selected[0]) not in ("CT", "PT"):
            self._fusion_error = "融合仅支持 CT 和 PET 序列"
            self._fusion_anchor_uid = ""
        else:
            from qt_dicom_viewer.core.pet_fusion import fusion_series_error
            self._fusion_error = fusion_series_error(self._scan_series_record[selected[0]])
            self._fusion_partner_uid = next((item["seriesUid"] for item in self.fusionCandidates
                                             if not item["error"]), "")
        self.fusionDialogChanged.emit()

    @Slot(str)
    def selectFusionPartner(self, uid):
        if uid not in {item["seriesUid"] for item in self.fusionCandidates if not item["error"]}:
            self._fusion_error = "请选择列表中可用的一个 CT 和一个 PET 序列"
            self._fusion_partner_uid = ""
            self.fusionDialogChanged.emit()
            return
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

    @Slot(object)
    def acceptPacsImport(self, snapshot: DicomFolderScanSnapshot):
        if self._closing:
            return
        for series in snapshot.series:
            self._removed_series_uids.discard(series.series_instance_uid)
        self.update_series_session(snapshot)
        self._update_series_record(snapshot)
        self.setPatientSearch("")
        self._collapsed_groups.clear()
        self.sidebarItemsChanged.emit()
        if snapshot.series:
            first_uid = snapshot.series[0].series_instance_uid
            self.selectSeries(first_uid)
            self.openSeriesView(first_uid, "2d")

    @Slot()
    def openFolderDialog(self) -> None:
        if self._scanning:
            return
        folder = QFileDialog.getExistingDirectory(None, "打开 DICOM 文件夹")
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
            "supports4D": summary.supports_four_d,
        } for series_id,summary  in self._scan_series_record.items()]

    @Property(bool, notify=scanningChanged)
    def scanning(self) -> bool:
        return self._scanning


    @Slot(str, str)
    def openSeriesView(self, active_series_uid: str, tab_type: str):
        if active_series_uid not in self._scan_series_record:
            return
        series = self._series_catalog.get_series(active_series_uid)
        if series is None:
            return
        if tab_type == "4d" and not series.supports_four_d:
            return
        if series.modality.upper() == "PT" and tab_type not in ("2d", "tag", "mpr", "3d"):
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
        self._remove_series([series_uid])

    @Slot()
    def removeSelectedSeries(self) -> None:
        if not self._scanning:
            self._remove_series(self._selected_series_uids)

    @Slot()
    def clearSeries(self) -> None:
        if self._scanning:
            return
        search_changed = bool(self._patient_search)
        self._patient_search = ""
        self._collapsed_groups.clear()
        if search_changed:
            self.patientSearchChanged.emit()
        self._remove_series(list(self._scan_series_record))
        if not self._scan_series_record:
            self._refresh_sidebar_model()

    def _remove_series(self, series_uids) -> None:
        removed = set(series_uids).intersection(self._scan_series_record)
        if not removed:
            return
        self._removed_series_uids.update(removed)
        self._thumbnail_timer.stop()
        for uid in removed:
            del self._scan_series_record[uid]
            if self._thumbnail_service is not None:
                self._thumbnail_service.cancel(uid)
            self._thumbnails.pop(uid, None)
            if self._image_provider is not None:
                self._image_provider.remove_image("thumbnail-" + uid)

        self._selected_series_uids = [uid for uid in self._selected_series_uids if uid not in removed]
        if self._active_series_uid in removed:
            self._active_series_uid = self._selected_series_uids[-1] if self._selected_series_uids else ""
        if self._fusion_anchor_uid in removed or self._fusion_partner_uid in removed:
            self._fusion_dialog_open = False
            self._fusion_anchor_uid = self._fusion_partner_uid = ""
            self._fusion_error = ""
        self.selectionChanged.emit()
        self.fusionDialogChanged.emit()
        self.seriesItemsChanged.emit()
        self.sidebarItemsChanged.emit()
        if self._thumbnail_service is not None and not self._scanning and self._scan_series_record:
            self._thumbnail_timer.start()
