"""独立于普通测量的单切片 MTF ROI、结果缓存及后台任务。"""

from dataclasses import asdict, dataclass

from PySide6.QtCore import QObject, Property, QRunnable, QThreadPool, Qt, Signal, Slot

from qt_dicom_viewer.core.bead_mtf import compute_point_source_mtf, extract_rect_pixels
from qt_dicom_viewer.model.mtf import BeadMtfResult
from .measure.measure_controller import MeasurementController


@dataclass(frozen=True)
class MtfRequest:
    frame_key: tuple
    roi_id: str
    revision: int
    measurement_method: str
    analysis_method: str


@dataclass
class _Analysis:
    request: MtfRequest
    result: BeadMtfResult | None = None
    error: str = ""
    roi_label: str = ""


class _TaskSignals(QObject):
    completed = Signal(object, object, str)


class _MtfTask(QRunnable):
    def __init__(self, request, pixels, spacing):
        super().__init__()
        self.request, self.pixels, self.spacing = request, pixels, spacing
        self.signals = _TaskSignals()

    def run(self):
        try:
            result = compute_point_source_mtf(
                self.pixels,
                *self.spacing,
                measurement_method=self.request.measurement_method,
                analysis_method=self.request.analysis_method,
            )
        except Exception as exc:
            self.signals.completed.emit(self.request, None, str(exc) or "MTF 计算失败")
        else:
            self.signals.completed.emit(self.request, result, "")


class MtfController(QObject):
    stateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._roi = MeasurementController(
            self,
            max_per_frame=1,
            geometry_only=True,
            adaptive_roi_hit_tolerance=True,
            physical_square_roi=True,
        )
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._analyses: dict[str, _Analysis] = {}
        self._tasks: dict[MtfRequest, _MtfTask] = {}
        self._revision = 0
        self._measurement_method = "bead"
        self._analysis_method = "direct_fft"
        self._closed = False
        self._frame = None
        self._pixels = None
        self._roi.measurementCommitted.connect(self._on_committed)
        self._roi.measurementsChanged.connect(self._on_geometry_changed)
        self._roi.activeTransactionChanged.connect(self.stateChanged.emit)

    @Property(QObject, constant=True)
    def roiController(self):
        return self._roi

    @Property("QVariantList", constant=True)
    def measurementMethods(self):
        return [
            {"value": "bead", "label": "微珠"},
            {"value": "wire", "label": "细丝"},
        ]

    @Property("QVariantList", constant=True)
    def analysisMethods(self):
        return [
            {"value": "direct_fft", "label": "直接 FFT"},
            {"value": "gaussian", "label": "高斯拟合"},
        ]

    @Property(str, notify=stateChanged)
    def measurementMethod(self):
        return self._measurement_method

    @Property(str, notify=stateChanged)
    def analysisMethod(self):
        return self._analysis_method

    @Slot(str)
    def setMeasurementMethod(self, method):
        if method == self._measurement_method:
            return
        if method not in {item["value"] for item in self.measurementMethods}:
            return
        # 不同测试体对 ROI 的语义不同，不能静默复用旧框。
        self._measurement_method = method
        self._analyses.clear()
        self._roi.clear_all()
        self.stateChanged.emit()

    @Slot(str)
    def setAnalysisMethod(self, method):
        if method == self._analysis_method:
            return
        if method not in {item["value"] for item in self.analysisMethods}:
            return
        self._analysis_method = method
        # 同一测试体只改变分析方式时保留几何，并使用当前原始像素快照重算。
        self._analyses.clear()
        visible = self._roi.visible_measurements
        if visible and self._frame is not None:
            self._schedule(visible[-1])
        self.stateChanged.emit()

    def set_frame(self, series_uid, frame, pixels):
        if self._closed:
            return
        self._frame, self._pixels = frame, pixels
        self._roi.set_frame(series_uid, frame)
        visible = self._roi.visible_measurements
        if visible and self._current_analysis() is None:
            # 分析方式切换后，其他切片的 ROI 在再次显示时按当前方式惰性重算。
            self._schedule(visible[-1])
        self.stateChanged.emit()

    def set_current_slice(self, index):
        self._frame, self._pixels = None, None
        self._roi.set_current_slice(index)
        self.stateChanged.emit()

    def _current_analysis(self):
        visible = self._roi.visible_measurements
        if self._frame is None or not visible:
            return None
        analysis = self._analyses.get(visible[-1].measurement_id)
        if (analysis and analysis.request.frame_key == self._roi.frame_key
                and analysis.request.measurement_method == self._measurement_method
                and analysis.request.analysis_method == self._analysis_method):
            return analysis
        return None

    @Property(str, notify=stateChanged)
    def status(self):
        if self._roi.has_active_transaction:
            return "editing"
        analysis = self._current_analysis()
        if analysis is None:
            return "empty"
        if analysis.error:
            return "error"
        return "ready" if analysis.result else "calculating"

    @Property(str, notify=stateChanged)
    def statusText(self):
        source = "单颗微珠" if self._measurement_method == "bead" else "垂直扫描平面的细丝截面"
        return {"editing": "松开后计算", "empty": f"框选{source}及外围背景",
                "error": "当前 ROI 无法计算", "ready": "",
                "calculating": "正在计算 MTF…"}[self.status]

    @Property(str, notify=stateChanged)
    def roiMetricLabel(self):
        analysis = self._current_analysis()
        if self.status != "ready" or analysis is None or analysis.result is None:
            return ""

        def metric(value):
            return "未达到" if value is None else f"{value:.3f}"

        result = analysis.result
        return (
            f"{analysis.roi_label}\n"
            f"MTF50  X {metric(result.x.mtf50)} · Y {metric(result.y.mtf50)} lp/mm\n"
            f"MTF10  X {metric(result.x.mtf10)} · Y {metric(result.y.mtf10)} lp/mm"
        )

    @Property("QVariantMap", notify=stateChanged)
    def currentResult(self):
        analysis = self._current_analysis()
        if self.status != "ready":
            return {}
        # QML 图表只消费两个方向；状态、警告和方法已有独立属性，不重复复制。
        payload = {direction: asdict(getattr(analysis.result, direction))
                   for direction in ("x", "y")}
        # 显式列表才能稳定地转换为 QML 可遍历的 QVariantList，而不是 Python 元组对象。
        for direction in ("x", "y"):
            for field in ("lsf", "frequency", "mtf"):
                payload[direction][field] = list(payload[direction][field])
        return payload

    @Property(str, notify=stateChanged)
    def error(self):
        analysis = self._current_analysis()
        return analysis.error if self.status == "error" else ""

    @Property("QStringList", notify=stateChanged)
    def warnings(self):
        analysis = self._current_analysis()
        return list(analysis.result.warnings) if self.status == "ready" else []

    @Slot()
    def _on_geometry_changed(self):
        retained = {m.measurement_id for m in self._roi.committed_measurements}
        self._analyses = {key: value for key, value in self._analyses.items() if key in retained}
        self.stateChanged.emit()

    @Slot(object)
    def _on_committed(self, measurement):
        if self._closed or self._frame is None:
            return
        self._schedule(measurement)
        self.stateChanged.emit()

    def _schedule(self, measurement):
        """为已提交 ROI 创建带方法版本的后台请求。"""
        self._revision += 1
        request = MtfRequest(
            self._roi.frame_key,
            measurement.measurement_id,
            self._revision,
            self._measurement_method,
            self._analysis_method,
        )
        analysis = _Analysis(request)
        self._analyses[measurement.measurement_id] = analysis
        try:
            snapshot = extract_rect_pixels(self._pixels, measurement.points)
            # 元数据中的原始 PixelSpacing 不存在时，不能借用显示几何的 1 mm 回退值。
            spacing = self._frame.instance_meta.pixel_spacing
            if spacing is None:
                raise ValueError("缺少原始 DICOM PixelSpacing，不能计算 lp/mm 或 mm")
            roi_rows, roi_columns = snapshot.shape
            row_spacing, column_spacing = spacing
            first, second = measurement.points
            width_mm = abs(first.column - second.column) * column_spacing
            height_mm = abs(first.row - second.row) * row_spacing
            analysis.roi_label = (
                f"ROI  {width_mm:.2f} × {height_mm:.2f} mm · "
                f"{roi_columns} × {roi_rows} px"
            )
            self._submit(request, snapshot, spacing)
        except (ValueError, TypeError) as exc:
            analysis.error = str(exc)

    def _submit(self, request, snapshot, spacing):
        """只在提交后调用，任务持有像素副本而不访问视口或 QML 对象。"""
        task = _MtfTask(request, snapshot, spacing)
        self._tasks[request] = task
        task.signals.completed.connect(self._receive_result, Qt.ConnectionType.QueuedConnection)
        self._pool.start(task)

    @Slot(object, object, str)
    def _receive_result(self, request, result, error):
        self._tasks.pop(request, None)
        analysis = self._analyses.get(request.roi_id)
        if self._closed or analysis is None or analysis.request != request:
            return
        # 非当前切片允许保存仍然有效的结果，但属性始终只返回当前切片的缓存。
        analysis.result, analysis.error = result, error
        self.stateChanged.emit()

    @Slot()
    def reset(self):
        self._analyses.clear()
        self._roi.clear_all()
        self.stateChanged.emit()

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self.reset()
        self._pool.clear()
        # 当前纯数值任务结束后再销毁信号对象，避免关闭标签页时跨线程访问已销毁对象。
        self._pool.waitForDone()
        self._tasks.clear()
        self._pixels = None
