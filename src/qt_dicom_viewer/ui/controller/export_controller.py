"""Export displayed pixels or exact source DICOM files without altering source data."""
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
from threading import Event
from uuid import uuid4

from PySide6.QtCore import QObject, Property, Signal, Slot, QRunnable, QThreadPool, QSaveFile, QIODevice, QSize
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QFileDialog


def copy_dicom_series(series, destination, cancelled=None, progress=lambda value: None):
    """Stage a new export directory; never overwrite or partially publish an export."""
    destination = Path(destination)
    output = destination / ("dicom-export-" + datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8])
    files, seen, counts, groups = [], set(), {}, {}
    for record in series:
        instances = list(record.instances)
        instances.extend(instance for phase in getattr(record, "phases", ()) for instance in phase.instances)
        for instance in instances:
            source = Path(instance.path).resolve()
            if source not in seen:
                seen.add(source)
                uid = getattr(instance, "series_instance_uid", record.series_instance_uid)
                group = groups.setdefault(uid, len(groups) + 1)
                counts[group] = counts.get(group, 0) + 1
                files.append((source, group, counts[group]))
    staging = Path(tempfile.mkdtemp(prefix=".dicom-export-", dir=destination))
    try:
        if not files:
            raise ValueError("当前序列没有可导出的 DICOM 文件。")
        for index, (source, series_number, number) in enumerate(files):
            if cancelled and cancelled.is_set():
                raise InterruptedError("导出已取消。")
            folder = staging / f"series-{series_number:02d}"
            folder.mkdir(exist_ok=True)
            shutil.copyfile(source, folder / f"{number:06d}.dcm")
            progress((index + 1) / len(files))
        if cancelled and cancelled.is_set():
            raise InterruptedError("导出已取消。")
        if output.exists():
            raise FileExistsError("导出目录已存在，请重试。")
        staging.rename(output)
        return output, len(files)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


class _ExportSignals(QObject):
    finished = Signal(str, bool)
    progress = Signal(float)


class _CopyJob(QRunnable):
    def __init__(self, series, destination, cancel):
        super().__init__()
        self.series, self.destination, self.cancel = series, destination, cancel
        self.signals = _ExportSignals()

    def run(self):
        try:
            path, count = copy_dicom_series(self.series, self.destination, self.cancel, self.signals.progress.emit)
            message, error = f"已导出 {count} 个 DICOM 文件：{path}", False
        except InterruptedError:
            message, error = "导出已取消。", False
        except (OSError, ValueError) as exc:
            message, error = f"DICOM 导出失败：{exc}", True
        except Exception:
            message, error = "DICOM 导出失败，请检查源文件和保存目录。", True
        self.signals.finished.emit(message, error)


class ExportController(QObject):
    changed = Signal()

    def __init__(self, workspace, catalog, parent=None):
        super().__init__(parent)
        self.workspace, self.catalog = workspace, catalog
        self._busy, self._error, self._message, self._progress = False, False, "", 0.0
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._cancel = Event()
        self._job = self._grab = None
        self._png_path = ""

    @Property(bool, notify=changed)
    def busy(self): return self._busy

    @Property(bool, notify=changed)
    def isError(self): return self._error

    @Property(str, notify=changed)
    def message(self): return self._message

    @Property(float, notify=changed)
    def progress(self): return self._progress

    def _start(self, message):
        self._busy, self._error, self._message, self._progress = True, False, message, 0.0
        self.changed.emit()

    @Slot(str, bool)
    def _finish(self, message, error=False):
        self._busy, self._message, self._error = False, message, error
        self._grab = self._job = None
        self.changed.emit()

    @Slot(float)
    def _set_progress(self, progress):
        self._progress = progress
        self.changed.emit()

    def current_series(self):
        tab = self.workspace.activeTab
        if not tab or self.workspace.activeTabType in ("tag", "settings", "pacs"):
            return []
        # A fusion workspace exports both source series in separate directories.
        return [record for meta in tab.tab_config.series_metas
                if (record := self.catalog.get_series(meta.series_uid)) is not None]

    @Slot()
    def exportDicom(self):
        if self._busy:
            return
        series = self.current_series()
        if not series:
            self._finish("请先打开影像序列。", True)
            return
        folder = QFileDialog.getExistingDirectory(None, "导出 DICOM · 选择保存目录")
        if not folder:
            self._finish("已取消导出。")
            return
        self.export_dicom_to(series, folder)

    def export_dicom_to(self, series, folder):
        if self._busy:
            return
        self._cancel = Event()
        self._start("正在导出 DICOM…")
        self._job = _CopyJob(tuple(series), folder, self._cancel)
        self._job.signals.finished.connect(self._finish)
        self._job.signals.progress.connect(self._set_progress)
        self._pool.start(self._job)

    @Slot(QObject, float)
    def exportPng(self, item, pixel_ratio=1.0):
        if self._busy:
            return
        viewport = self.workspace.activeViewport
        if not viewport or getattr(viewport, "loadState", "ready") != "ready":
            self._finish("影像尚未加载完成。", True)
            return
        path, _ = QFileDialog.getSaveFileName(None, "导出 PNG", "viewport.png", "PNG 图像 (*.png)")
        if not path:
            self._finish("已取消导出。")
            return
        if not Path(path).suffix:
            path += ".png"
        self._start("正在导出 PNG…")
        try:
            if viewport.viewportType == "volume":
                self._save_png(viewport.snapshot_image(), path)
            elif isinstance(item, QQuickItem) and item.isVisible() and item.width() > 0 and item.height() > 0:
                # Read DPR in QML: PySide can incorrectly parent the window wrapper
                # to this item when QQuickItem.window() is called.
                ratio = max(1.0, float(pixel_ratio))
                self._grab = item.grabToImage(QSize(round(item.width() * ratio), round(item.height() * ratio)))
                if self._grab is None:
                    raise ValueError("当前视口无法截图。")
                self._png_path = path
                self._grab.ready.connect(self._png_ready)
            else:
                raise ValueError("当前视口不可见。")
        except (OSError, ValueError, RuntimeError) as exc:
            self._finish(f"PNG 导出失败：{exc}", True)

    @Slot()
    def _png_ready(self):
        if self._grab is not None:
            self._save_png(self._grab.image(), self._png_path)

    def _save_png(self, image, path):
        output = QSaveFile(str(path))
        if image.isNull() or not output.open(QIODevice.WriteOnly):
            self._finish("PNG 导出失败，无法写入保存位置。", True)
            return
        if not image.save(output, "PNG") or not output.commit():
            output.cancelWriting()
            self._finish("PNG 导出失败，请检查磁盘空间及目录权限。", True)
            return
        self._finish(f"PNG 已保存：{path}")

    @Slot()
    def cancel(self):
        if self._job:
            self._cancel.set()
        elif self._grab:
            self._finish("导出已取消。")

    def shutdown(self):
        self._cancel.set()
        self._pool.waitForDone()
