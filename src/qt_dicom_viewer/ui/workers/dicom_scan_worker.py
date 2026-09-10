import logging
import time
from dataclasses import replace
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Slot, Signal, QThread

from qt_dicom_viewer.core.dicom_scanner import DicomFolderScanner, _build_series_from_map
from qt_dicom_viewer.core.local_import import LocalImportStore, ImportCancelled, ImportErrorDetail

logger = logging.getLogger(__name__)


class DicomScanWorker(QObject):
    finished = Signal(object)
    failed = Signal(object)
    process = Signal(object)
    status = Signal(str)
    progress = Signal(int, int, int, int)
    process_report_interval = 0.75

    def __init__(self, paths, store=None, *, base_series=None):
        super().__init__()
        self.paths = [paths] if isinstance(paths, (str, Path)) else list(paths)
        self.store = store or LocalImportStore()
        self._base_series = dict(base_series or {})
        self._process_pending = Event()

    def acknowledge_process(self):
        self._process_pending.clear()

    def _merge_snapshot(self, result):
        # All sorting, duplicate merging and phase linking happen off the GUI thread.
        if not any(s.series_instance_uid in self._base_series for s in result.series):
            return result
        grouped = {}
        for series in result.series:
            old = self._base_series.get(series.series_instance_uid)
            combined = {i.sop_instance_uid: i for i in old.instances} if old else {}
            combined.update({i.sop_instance_uid: i for i in series.instances})
            for instance in combined.values():
                grouped.setdefault((instance.study_instance_uid, instance.series_instance_uid), []).append(instance)
        return replace(result, series=_build_series_from_map(grouped))

    @Slot()
    def run(self):
        latest = None
        cancelled = QThread.currentThread().isInterruptionRequested
        try:
            files = self.store.prepare(self.paths, cancelled=cancelled, progress=self.status.emit)
            self.status.emit("正在读取 DICOM 文件…")
            last_progress = 0.0

            def report(processed, dicom, skipped):
                nonlocal last_progress
                now = time.monotonic()
                if now - last_progress >= 0.15 or processed == len(files):
                    last_progress = now
                    self.progress.emit(processed, len(files), dicom, skipped)

            for result in DicomFolderScanner().scan_files(
                files, folder=Path(self.paths[0]).parent, cancelled=cancelled,
                snapshot_interval=self.process_report_interval,
                can_publish=lambda: not self._process_pending.is_set(), progress=report,
            ):
                latest = self._merge_snapshot(result)
                if not self._process_pending.is_set():
                    # At most one preview waits in the GUI event queue.
                    self._process_pending.set()
                    self.process.emit(latest)
            self.finished.emit(latest)
        except ImportCancelled:
            self.finished.emit(latest)
        except ImportErrorDetail as error:
            logger.exception("Local import rejected")
            self.failed.emit(str(error))
        except Exception:
            logger.exception("Local import failed")
            self.failed.emit("导入失败，请检查文件是否完整、可读，以及剩余磁盘空间。详细原因已记录到应用日志。")
