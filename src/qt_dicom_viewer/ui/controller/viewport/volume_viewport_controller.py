"""3D controller. Widget creation is lazy, so routing/math stay testable headlessly."""
from dataclasses import replace
import uuid
import numpy as np

from PySide6.QtCore import QObject, Property, Signal, Slot, QThreadPool, Qt

from qt_dicom_viewer.core.volume_view import (
    VolumeViewState, rotate_drag, zoom_by, nearest_face, face_rotation, drag_volume_window,
)
from qt_dicom_viewer.core.volume_edit import (
    bed_keep_mask, crop_keep_mask, polygon_area, simplify_polygon,
)
from qt_dicom_viewer.ui.workers.volume_edit_task import VolumeEditTask
from qt_dicom_viewer.model import ToolType, InteractionType
from qt_dicom_viewer.model.render_models import VolumeLoadRequest, VolumeLoadResult
from qt_dicom_viewer.model.volume_models import VOLUME_DIRECTIONS, VolumeDisplayState
from qt_dicom_viewer.volume_presets import VOLUME_PRESETS, VOLUME_PRESET_BY_ID
from .viewport_controller import ViewportController


class VolumeViewportController(ViewportController):
    nativeWindowChanged = Signal()
    stateChanged = Signal()
    loadStateChanged = Signal()
    activeInteractionChanged = Signal()
    currentFaceChanged = Signal()
    displayStateChanged = Signal()
    editStateChanged = Signal()
    maskChanged = Signal()
    selectionChanged = Signal()

    def __init__(self, viewport_config, tool_controller, parent=None):
        super().__init__(viewport_config, parent)
        self._tools = tool_controller
        self.state = VolumeViewState()
        self.display_state = VolumeDisplayState()
        self._current_face = "A"
        self.volume = None
        self._request_id = None
        self._host = None
        self._disposed = False
        self._drag = None
        self._load_state = "idle"
        self._error = ""
        self._bed_enabled = False
        self._bed_mask = None
        self.crop_mask = None
        self.visible_mask = None
        self._edit_token = 0
        self._edit_kind = ""
        self._edit_message = ""
        self._edit_task = None
        self._selection = []
        self._selection_size = None
        self._selection_state = None
        self._drawing = False
        self._tools.activeInteractionChanged.connect(self._tool_changed)

    def snapshot_image(self):
        from PySide6.QtGui import QImage
        from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
        from vtkmodules.util.numpy_support import vtk_to_numpy
        import numpy as np
        if self._host is None or self._load_state != "ready":
            raise ValueError("3D 影像尚未加载完成。")
        window = self._host.backend.window
        window.Render()
        capture = vtkWindowToImageFilter()
        capture.SetInput(window)
        capture.SetInputBufferTypeToRGB()
        capture.ReadFrontBufferOff()
        capture.Update()
        data = capture.GetOutput()
        width, height, _ = data.GetDimensions()
        scalars = data.GetPointData().GetScalars()
        if width <= 0 or height <= 0 or scalars is None:
            raise ValueError("3D 视口未生成可导出的图像。")
        pixels = vtk_to_numpy(scalars).reshape(height, width, 3)
        pixels = np.ascontiguousarray(pixels[::-1])
        return QImage(pixels.data, width, height, pixels.strides[0], QImage.Format_RGB888).copy()

    @Property(QObject, notify=nativeWindowChanged)
    def nativeWindow(self):
        return self._host.windowHandle() if self._host is not None else None

    @Property(str, notify=activeInteractionChanged)
    def activeInteraction(self):
        return self._tools.activeInteraction

    @Property(str, notify=loadStateChanged)
    def loadState(self):
        return self._load_state

    @Property(str, notify=loadStateChanged)
    def errorMessage(self):
        return self._error

    @Property(str, notify=currentFaceChanged)
    def currentFace(self):
        return self._current_face

    @Property(str, notify=currentFaceChanged)
    def currentFaceColor(self):
        return next(d.color for d in VOLUME_DIRECTIONS if d.face == self._current_face)

    @Property("QVariantList", constant=True)
    def directionOptions(self):
        return [dict(face=d.face, label=d.label, color=d.color) for d in VOLUME_DIRECTIONS]

    @Property("QVariantList", constant=True)
    def volumePresets(self):
        return [dict(presetId=p.preset_id, label=p.label, group=p.group,
                     available=self._preset_available(p)) for p in VOLUME_PRESETS]

    @Property(str, notify=displayStateChanged)
    def currentPresetId(self):
        return self.display_state.preset_id

    @Property(float, notify=displayStateChanged)
    def windowCenter(self):
        return self.display_state.window.center if self.display_state.window else 0.0

    @Property(float, notify=displayStateChanged)
    def windowWidth(self):
        return self.display_state.window.width if self.display_state.window else 0.0

    def _preset_available(self, preset):
        return not preset.ct_only or self.viewport_config.series_meta.modality.strip().upper() == "CT"

    @Property(bool, notify=editStateChanged)
    def bedRemovalEnabled(self):
        return self._bed_enabled

    @Property(bool, notify=loadStateChanged)
    def bedRemovalAvailable(self):
        return self._load_state == "ready" and self.viewport_config.series_meta.modality.strip().upper() == "CT"

    @Property(bool, notify=editStateChanged)
    def editBusy(self):
        return bool(self._edit_kind)

    @Property(str, notify=editStateChanged)
    def editMessage(self):
        return self._edit_message

    @Property(bool, notify=editStateChanged)
    def hasCrop(self):
        return self.crop_mask is not None

    @Property(bool, notify=selectionChanged)
    def hasCropSelection(self):
        return not self._drawing and polygon_area(self._selection) >= 9

    @property
    def selection_points(self):
        return self._selection

    @Slot(bool)
    def setBedRemovalEnabled(self, enabled):
        if self._disposed or not self.bedRemovalAvailable or self.editBusy or enabled == self._bed_enabled:
            return
        if enabled and self._bed_mask is None:
            self._start_edit("bed", bed_keep_mask, self.volume)
            return
        self._bed_enabled = bool(enabled)
        self._edit_message = ""
        self._update_mask()

    @Slot(str)
    def applyCrop(self, mode):
        if (self._disposed or self._load_state != "ready" or self.editBusy
                or not self.hasCropSelection or mode not in ("inside", "outside")):
            return
        self._start_edit("crop", crop_keep_mask, self.volume.geometry,
                         self._selection_state, self._selection_size,
                         tuple(self._selection), mode, self.crop_mask)

    def _start_edit(self, kind, function, *args):
        self._edit_token += 1
        self._edit_kind = kind
        self._edit_message = "正在去床板…" if kind == "bed" else "正在裁剪…"
        task = VolumeEditTask(self._edit_token, kind, function, *args)
        task.signals.finished.connect(self._edit_finished, Qt.QueuedConnection)
        self._edit_task = task
        self.editStateChanged.emit()
        QThreadPool.globalInstance().start(task)

    @Slot(int, str, object, str)
    def _edit_finished(self, token, kind, mask, error):
        if self._disposed or token != self._edit_token:
            return
        self._edit_kind = ""
        self._edit_task = None
        self._edit_message = error
        if not error:
            if kind == "bed":
                self._bed_mask, self._bed_enabled = mask, True
            else:
                self.crop_mask = mask
                self.clearCropSelection()
            self._update_mask()
        else:
            self.editStateChanged.emit()

    def _cancel_edit(self):
        # A running worker owns its immutable input; a late result cannot restore
        # edits after reset, reload or disposal.
        self._edit_token += 1
        self._edit_kind = ""
        self._edit_message = ""
        self._edit_task = None

    def _update_mask(self):
        bed = self._bed_mask if self._bed_enabled else None
        if bed is not None and self.crop_mask is not None:
            self.visible_mask = bed & self.crop_mask
        else:
            self.visible_mask = bed if bed is not None else self.crop_mask
        self.maskChanged.emit()
        self.editStateChanged.emit()

    @Slot()
    def clearCropSelection(self):
        self._drawing = False
        self._selection = []
        self._selection_state = self._selection_size = None
        self.selectionChanged.emit()

    @Slot()
    def resetCrop(self):
        if self._disposed:
            return
        if self._edit_kind == "crop":
            self._cancel_edit()
        self.crop_mask = None
        self.clearCropSelection()
        self._update_mask()

    def cancel_drag(self):
        self._drag = None
        self.clearCropSelection()

    def viewport_resized(self):
        # A pending screen selection belongs to exactly one camera/viewport.
        self.cancel_drag()

    @Slot(str)
    def setViewFace(self, face):
        if self._disposed or self._load_state != "ready" or face not in {d.face for d in VOLUME_DIRECTIONS}:
            return
        self._drag = None
        self._set_state(replace(self.state, rotation=face_rotation(face)))

    @Slot(str)
    def applyVolumePreset(self, preset_id):
        preset = VOLUME_PRESET_BY_ID.get(preset_id)
        if self._disposed or self._load_state != "ready" or preset is None or not self._preset_available(preset):
            return
        self._drag = None
        self._set_display_state(VolumeDisplayState(
            preset_id=preset_id, window=preset.default_window or self.volume.default_window,
        ))

    def _set_display_state(self, state):
        if state != self.display_state:
            self.display_state = state
            self.displayStateChanged.emit()

    @Slot()
    def ensureNativeView(self):
        if self._host is not None or self._disposed:
            return
        from qt_dicom_viewer.ui.volume_viewport_host import VolumeViewportHost
        self._host = VolumeViewportHost(self)
        self.nativeWindowChanged.emit()
        self._host.sync_status()

    @Slot(bool)
    def setNativeVisible(self, visible):
        if self._host is not None:
            self._host.set_active(visible)
        if not visible:
            self.cancel_drag()

    def request_first_loader(self):
        self.request_render()

    @Slot()
    def retry(self):
        if self._load_state != "loading":
            self.request_render()

    def request_render(self):
        if self._disposed or self._load_state == "loading":
            return
        self._request_id = str(uuid.uuid4())
        self._set_status("loading")
        self.renderRequested.emit(VolumeLoadRequest(
            request_id=self._request_id,
            viewport_id=self.viewportId,
            series_uid=self.viewport_config.series_uid,
        ))

    def accepts_result(self, result):
        return (isinstance(result, VolumeLoadResult) and not self._disposed
                and result.viewport_id == self.viewportId
                and result.response_id == self._request_id
                and result.series_uid == self.viewport_config.series_uid)

    def handleRenderResult(self, result: VolumeLoadResult):
        if not self.accepts_result(result):
            return
        self._request_id = None
        if self.volume is not result.volume:
            self._cancel_edit()
            self._bed_enabled = False
            self._bed_mask = self.crop_mask = self.visible_mask = None
            self.clearCropSelection()
            self._update_mask()
        self.volume = result.volume
        if self.display_state.window is None:
            self._set_display_state(VolumeDisplayState(window=self.volume.default_window))
        self._set_status("ready")

    def handleRenderFailure(self, failure):
        if (not self._disposed and failure.viewport_id == self.viewportId
                and failure.request_id == self._request_id):
            self._request_id = None
            self._set_status("error", str(failure.error))

    def render_failed(self, message):
        if not self._disposed:
            self._set_status("error", message)

    def _set_status(self, state, error=""):
        if state != "ready":
            self.cancel_drag()
            self._cancel_edit()
            self.editStateChanged.emit()
        self._load_state, self._error = state, error
        self.loadStateChanged.emit()

    def _tool_changed(self):
        self.cancel_drag()
        self.activeInteractionChanged.emit()

    def begin_drag(self, point, size):
        if not self._disposed and self._load_state == "ready":
            if self.activeInteraction == InteractionType.VOLUME_CROP:
                if self.editBusy:
                    return
                self.clearCropSelection()
                self._selection_size, self._selection_state = size, self.state
                self._selection = [self._clamp_selection_point(point)]
                self._drawing = True
                self.selectionChanged.emit()
                return
            self._drag = (point, size, self.state, self.display_state, self.activeInteraction)

    def _clamp_selection_point(self, point):
        return tuple(float(np.clip(v, 0, limit)) for v, limit in zip(point, self._selection_size))

    def update_drag(self, point):
        if self._drawing:
            point = self._clamp_selection_point(point)
            if np.linalg.norm(np.asarray(point)-self._selection[-1]) >= 2:
                self._selection.append(point)
                self.selectionChanged.emit()
            return
        if self._drag is None:
            return
        start, size, initial, display, tool = self._drag
        dx, dy = point[0]-start[0], point[1]-start[1]
        height = max(1, size[1])
        if tool == InteractionType.WINDOW:
            if display.window is not None:
                self._set_display_state(replace(display, window=drag_volume_window(
                    display.window, (dx, dy), size)))
            return
        if tool == InteractionType.PAN:
            state = replace(initial, pan=(initial.pan[0]+dx/height, initial.pan[1]+dy/height))
        elif tool == InteractionType.ZOOM:
            state = zoom_by(initial, -2*dy/height)
        elif tool == InteractionType.VOLUME_ROTATE:
            state = rotate_drag(initial, start, point, size)
        else:
            return
        self._set_state(state)

    def end_drag(self):
        if self._drawing:
            self._drawing = False
            self._selection = [tuple(p) for p in simplify_polygon(self._selection)]
            if not self.hasCropSelection:
                self.clearCropSelection()
            else:
                self.selectionChanged.emit()
        self._drag = None
        if self._host is not None:
            self._host.request_render(interactive=False)

    def wheel_zoom(self, angle_delta, pixel_delta):
        if self._disposed or self._load_state != "ready":
            return
        exponent = pixel_delta/200 if pixel_delta else angle_delta/600
        self._set_state(zoom_by(self.state, exponent))

    def _set_state(self, state):
        if state != self.state:
            self.clearCropSelection()
            self.state = state
            face = nearest_face(state, self._current_face)
            if face != self._current_face:
                self._current_face = face
                self.currentFaceChanged.emit()
            self.stateChanged.emit()

    def reset_tool_state(self, tool):
        if self._disposed:
            return
        self._drag = None
        if tool == ToolType.PAN:
            self._set_state(replace(self.state, pan=(0.0, 0.0)))
        elif tool == ToolType.ZOOM:
            self._set_state(replace(self.state, zoom=1.0))
        elif tool in (ToolType.VOLUME_ROTATE, ToolType.VOLUME_DIRECTION):
            self._set_state(replace(self.state, rotation=VolumeViewState().rotation))
        elif tool == ToolType.WINDOW:
            self.applyVolumePreset(self.currentPresetId)
        elif tool == ToolType.VOLUME_PRESET:
            self.applyVolumePreset("general")
        elif tool == ToolType.VOLUME_CROP:
            self.resetCrop()

    def reset_all_view_state(self):
        if self._disposed:
            return
        self._drag = None
        self._cancel_edit()
        self._bed_enabled = False
        self.crop_mask = None
        self.clearCropSelection()
        self._update_mask()
        self._set_state(VolumeViewState())
        if self.volume is not None:
            self._set_display_state(VolumeDisplayState(window=self.volume.default_window))

    def dispose(self):
        if self._disposed:
            return
        self._disposed = True
        self._request_id = None
        self._drag = None
        self._cancel_edit()
        self.clearCropSelection()
        host, self._host = self._host, None
        if host is not None:
            host.set_active(False)
            # Synchronously clear WindowContainer.window before destroying its QWidget.
            self.nativeWindowChanged.emit()
            host.dispose()
        self.volume = None
        self._bed_mask = self.crop_mask = self.visible_mask = None
