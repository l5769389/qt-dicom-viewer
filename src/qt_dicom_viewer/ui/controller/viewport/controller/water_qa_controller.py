"""Per-viewport water QA, asynchronous snapshots and bounded per-slice caching."""
from collections import OrderedDict
from dataclasses import asdict, replace
import hashlib
import math

import numpy as np
from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, Qt, Signal, Slot

from qt_dicom_viewer.core.water_qa import analyze_water_phantom, measure_water_phantom
from qt_dicom_viewer.model.water_qa import WaterQaSettings


class _Signals(QObject):
    completed = Signal(int, object, object, str)


class _QaTask(QRunnable):
    def __init__(self, token, key, pixels, spacing, settings):
        super().__init__()
        self.token, self.key = token, key
        self.pixels, self.spacing, self.settings = pixels, spacing, settings
        self.signals = _Signals()

    def run(self):
        try:
            result = analyze_water_phantom(self.pixels, self.spacing, self.settings)
        except Exception as exc:
            self.signals.completed.emit(self.token, self.key, None, str(exc) or "水模 QA 计算失败")
        else:
            self.signals.completed.emit(self.token, self.key, result, "")


class WaterQaController(QObject):
    stateChanged = Signal()
    settingsChanged = Signal()

    def __init__(self, modality, parent=None):
        super().__init__(parent)
        self._modality = modality.strip().upper()
        self._settings = WaterQaSettings()
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._tasks = {}
        self._pending = None
        self._cache = OrderedDict()
        self._token = 0
        self._closed = False
        self._enabled = False
        self._frame = self._pixels = self._key = None
        self._status, self._error, self._result = "empty", "", None
        self._drag = self._draft_centers = None
        self._hover_key = ""

    @Property(bool, constant=True)
    def available(self):
        return self._modality == "CT"

    @Property(bool, notify=stateChanged)
    def enabled(self):
        return self._enabled

    @Property(str, notify=stateChanged)
    def status(self):
        return self._status

    @Property(str, notify=stateChanged)
    def statusText(self):
        if not self.available:
            return "水模 QA 仅支持 CT 影像"
        return {"empty": "待识别", "waiting": "切片加载中…",
                "calculating": "识别中…", "error": "",
                "ready": "拖动中 · 松开更新" if self.dragging else ""}[self._status]

    @Property(bool, notify=stateChanged)
    def dragging(self):
        return self._drag is not None

    @Property(str, notify=stateChanged)
    def hoverCursorKind(self):
        return "pan" if self._hover_key else ""

    @Property(str, notify=stateChanged)
    def error(self):
        return self._error

    @Property(float, notify=settingsChanged)
    def roiDiameterMm(self):
        return self._settings.roi_diameter_mm

    @Property(float, notify=settingsChanged)
    def edgeClearanceMm(self):
        return self._settings.edge_clearance_mm

    @Property("QVariantMap", notify=stateChanged)
    def currentResult(self):
        if self._result is None or self._status != "ready":
            return {}
        result = asdict(self._result)
        result["rois"] = [asdict(roi) for roi in self._result.rois]
        return result

    @Property("QVariantList", notify=stateChanged)
    def roiItems(self):
        if self._result is None or self._frame is None or self._status != "ready":
            return []
        row_spacing, column_spacing = self._frame.instance_meta.pixel_spacing
        colors = ("#f6bf66", "#41cce5", "#41cce5", "#8de1b1", "#8de1b1")
        centers = self._draft_centers or [(r.column, r.row) for r in self._result.rois]
        return [dict(key=r.key, label=r.label, column=center[0], row=center[1],
                     radiusColumn=r.radius_mm/column_spacing, radiusRow=r.radius_mm/row_spacing,
                     meanHu=r.mean_hu, stdHu=r.std_hu, color=color,
                     editing=self._drag is not None and self._drag[0] == index,
                     hovered=r.key == self._hover_key)
                for index, (r, color, center) in enumerate(zip(self._result.rois, colors, centers))]

    def _hit_roi(self, column, row):
        if (not self._enabled or self._status != "ready" or self._result is None
                or not math.isfinite(column) or not math.isfinite(row)):
            return None
        sy, sx = self._frame.instance_meta.pixel_spacing
        for index, roi in enumerate(self._result.rois):
            if math.hypot((column-roi.column)*sx, (row-roi.row)*sy) <= roi.radius_mm:
                return index
        return None

    def update_hover(self, column, row):
        if self.dragging:
            return
        index = self._hit_roi(column, row)
        key = "" if index is None else self._result.rois[index].key
        if key != self._hover_key:
            self._hover_key = key
            self.stateChanged.emit()

    @Slot()
    def clearHover(self):
        if self._hover_key:
            self._hover_key = ""
            self.stateChanged.emit()

    def begin_drag(self, column, row):
        self.cancel_drag()
        index = self._hit_roi(column, row)
        if index is None:
            return
        self._drag = (index, column, row)
        self._draft_centers = [(r.column, r.row) for r in self._result.rois]
        self._error = ""
        self.stateChanged.emit()

    def update_drag(self, column, row):
        if not self.dragging or not math.isfinite(column) or not math.isfinite(row):
            return
        index, start_column, start_row = self._drag
        roi, phantom = self._result.rois[index], self._result.phantom
        sy, sx = self._frame.instance_meta.pixel_spacing
        dx = (roi.column+column-start_column-phantom.column)*sx
        dy = (roi.row+row-start_row-phantom.row)*sy
        distance = math.hypot(dx, dy)
        # Constrain the complete circle to the detected water region. Pointer
        # displacement remains relative to the press, so the ROI never jumps.
        scale = min(1.0, (phantom.radius_mm-roi.radius_mm)/max(distance, 1e-9))
        center = (phantom.column+dx*scale/sx, phantom.row+dy*scale/sy)
        if center != self._draft_centers[index]:
            self._draft_centers[index] = center
            self.stateChanged.emit()

    def end_drag(self, column, row):
        if not self.dragging:
            return
        self.update_drag(column, row)
        centers = self._draft_centers
        self._drag = self._draft_centers = None
        try:
            result = measure_water_phantom(self._pixels, self._frame.instance_meta.pixel_spacing,
                                          self._result.phantom, self._settings, centers=centers)
        except ValueError as exc:
            self._error = str(exc)  # Keep the last complete, valid measurement.
        else:
            self._result, self._error = result, ""
            self._cache[self._cache_key()] = (result, "")
        self.stateChanged.emit()

    def cancel_drag(self):
        if self.dragging:
            self._drag = self._draft_centers = None
            self.stateChanged.emit()

    def set_frame(self, series_uid, frame, pixels):
        if self._closed:
            return
        array = None if pixels is None else np.ascontiguousarray(pixels)
        fingerprint = None if array is None else hashlib.blake2b(array.view(np.uint8), digest_size=12).digest()
        key = (series_uid, frame.instance_meta.sop_instance_uid, frame.slice_index,
               frame.instance_meta.pixel_spacing, None if array is None else array.shape, fingerprint)
        self._frame, self._pixels = frame, array
        if key == self._key:
            return  # Window/level and inversion do not alter the original HU data.
        self._invalidate()
        self._key = key
        if self._enabled:
            self._analyze()
        else:
            self.stateChanged.emit()

    def set_current_slice(self, index):
        if self._closed:
            return
        self._invalidate()
        self._frame = self._pixels = self._key = None
        self._status = "waiting" if self._enabled else "empty"
        self.stateChanged.emit()

    def _invalidate(self):
        self._token += 1
        self._pending = None
        self._drag = self._draft_centers = None
        self._hover_key = ""
        self._status, self._error, self._result = "empty", "", None

    @Slot()
    def activate(self):
        if self._closed or not self.available:
            return
        self._enabled = True
        if self._status not in ("ready", "calculating"):
            self._analyze()

    @Slot()
    def analyze(self):
        if self._closed or not self.available:
            return
        self._enabled = True
        self._cache.pop(self._cache_key(), None)
        self._invalidate()
        self._analyze()

    def _cache_key(self):
        return self._key, self._settings

    def _analyze(self):
        if self._frame is None:
            self._status = "waiting"
            self.stateChanged.emit()
            return
        key = self._cache_key()
        cached = self._cache.get(key)
        if cached is not None:
            self._result, self._error = cached
            self._status = "error" if self._error else "ready"
            self._cache.move_to_end(key)
        elif self._pixels is None:
            self._status, self._error = "error", "当前切片没有可用的原始 CT 像素"
        else:
            self._status = "calculating"
            self._submit(self._token, key, self._pixels.copy(),
                         self._frame.instance_meta.pixel_spacing, self._settings)
        self.stateChanged.emit()

    def _submit(self, token, key, pixels, spacing, settings):
        # While scrolling, keep at most one running snapshot and the newest
        # pending slice. Never enqueue an entire series of obsolete analyses.
        if self._tasks:
            self._pending = (token, key, pixels, spacing, settings)
            return
        task = _QaTask(token, key, pixels, spacing, settings)
        self._tasks[token] = task
        task.signals.completed.connect(self._receive_result, Qt.QueuedConnection)
        self._pool.start(task)

    @Slot(int, object, object, str)
    def _receive_result(self, token, key, result, error):
        self._tasks.pop(token, None)
        pending, self._pending = self._pending, None
        if pending is not None and not self._closed and pending[0] == self._token:
            self._submit(*pending)
        if self._closed or token != self._token or key != self._cache_key() or not self._enabled:
            return
        self._result, self._error = result, error
        self._status = "error" if error else "ready"
        self._cache[key] = (result, error)
        while len(self._cache) > 16:
            self._cache.popitem(last=False)
        self.stateChanged.emit()

    @Slot(float)
    def setRoiDiameterMm(self, value):
        self._set_setting("roi_diameter_mm", value, 2, 100)

    @Slot(float)
    def setEdgeClearanceMm(self, value):
        self._set_setting("edge_clearance_mm", value, 0, 100)

    def _set_setting(self, name, value, low, high):
        if self._closed or not math.isfinite(value) or not low <= value <= high:
            return
        settings = replace(self._settings, **{name: float(value)})
        if settings == self._settings:
            return
        self._settings = settings
        self._cache.clear()
        self.settingsChanged.emit()
        self._invalidate()
        if self._enabled:
            self._analyze()
        else:
            self.stateChanged.emit()

    @Slot()
    def reset(self):
        self._enabled = False
        self._cache.clear()
        self._invalidate()
        self._settings = WaterQaSettings()
        self.settingsChanged.emit()
        self.stateChanged.emit()

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self.reset()
        self._pool.clear()
        self._pool.waitForDone()
        self._tasks.clear()
        self._frame = self._pixels = self._key = None
