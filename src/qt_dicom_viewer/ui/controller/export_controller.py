"""Own the export dialog and one cancellable background export at a time."""

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from qt_dicom_viewer.core.series_export import ExportCancelled, ExportError, ExportRequest, export_series


class _ExportJob(QRunnable):
    def __init__(self, request, cancel, progress, completed):
        super().__init__()
        self.request, self.cancel = request, cancel
        self.progress, self.completed = progress, completed

    def run(self):
        try:
            result = export_series(self.request, cancel=self.cancel, progress=self.progress.emit)
            self.completed.emit(result, "")
        except ExportCancelled:
            self.completed.emit(None, "已取消导出，未保留未完成文件。")
        except ExportError as exc:
            self.completed.emit(None, str(exc))
        except Exception:
            self.completed.emit(None, "导出失败，请检查源文件、目录权限和剩余空间。")


class ExportController(QObject):
    changed = Signal()
    dialogChanged = Signal()
    _progress = Signal(int, int)
    _completed = Signal(object, str)

    def __init__(self, catalog, settings, parent=None):
        super().__init__(parent)
        self._catalog, self._settings = catalog, settings
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._cancel = Event()
        self._closing = False
        self._busy = False
        self._open = False
        self._locked = False
        self._series_uid = ""
        self._count = 0
        self._done = self._total = 0
        self._message = self._output = ""
        self._progress.connect(self._on_progress)
        self._completed.connect(self._on_completed)

    @Property(bool, notify=dialogChanged)
    def dialogOpen(self):
        return self._open

    @Property(bool, notify=dialogChanged)
    def anonymousLocked(self):
        return self._locked

    @Property(int, notify=dialogChanged)
    def instanceCount(self):
        return self._count

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(str, notify=changed)
    def outputDirectory(self):
        return self._output

    @Property(int, notify=changed)
    def completedCount(self):
        return self._done

    @Property(int, notify=changed)
    def totalCount(self):
        return self._total

    @Slot(str, bool)
    def openSeries(self, uid, anonymous_locked=False):
        if self._busy or self._closing:
            return
        series = self._catalog.get_series(uid)
        self._series_uid = uid
        self._count = len(series.instances) if series else 0
        self._locked = anonymous_locked
        self._message = "" if self._count else "所选序列没有可导出的文件"
        self._output = ""
        self._done = self._total = 0
        self._open = True
        self.dialogChanged.emit()
        self.changed.emit()

    @Slot()
    def closeDialog(self):
        if not self._busy:
            self._open = False
            self.dialogChanged.emit()

    @Slot(str, bool)
    def startExport(self, file_format, anonymous):
        if self._busy or self._closing or not self._open:
            return
        series = self._catalog.get_series(self._series_uid)
        if file_format not in ("png", "dicom") or not series or not series.instances:
            self._message = "请选择有效序列及 PNG / DICOM 格式"
            self.changed.emit()
            return
        # Capture an immutable snapshot; subsequent imports/selections cannot
        # change the running export or accidentally export a different series.
        request = ExportRequest(tuple(instance.path for instance in series.instances),
                                Path(self._settings.exportDirectory), file_format,
                                self._locked or anonymous)
        self._cancel = Event()
        self._busy = True
        self._output = ""
        self._message = "正在检查源文件…"
        self._done = self._total = 0
        self.changed.emit()
        self._pool.start(_ExportJob(request, self._cancel, self._progress, self._completed))

    @Slot()
    def cancelExport(self):
        if self._busy:
            self._cancel.set()
            self._message = "正在取消…"
            self.changed.emit()

    @Slot(int, int)
    def _on_progress(self, done, total):
        if self._closing:
            return
        self._done, self._total = done, total
        if not self._cancel.is_set():
            self._message = f"正在导出 {done} / {total}"
        self.changed.emit()

    @Slot(object, str)
    def _on_completed(self, result, error):
        self._busy = False
        if self._closing:
            return
        self._output = str(result.directory) if result else ""
        self._message = f"导出完成，共 {result.file_count} 个文件。" if result else error
        self.changed.emit()

    @Slot()
    def openOutputDirectory(self):
        if self._output and not QDesktopServices.openUrl(QUrl.fromLocalFile(self._output)):
            self._message = "无法打开目录，请根据下方路径手动打开。"
            self.changed.emit()

    def shutdown(self):
        self._closing = True
        self._cancel.set()
        self._pool.waitForDone()
