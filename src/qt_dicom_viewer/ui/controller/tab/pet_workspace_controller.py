"""One transactional render state for PET MPR and registered PET/CT tabs."""
from dataclasses import replace
import json
from uuid import uuid4

import numpy as np
from PySide6.QtCore import QObject, Property, Signal, Slot, QSaveFile, QIODevice, QUrl
from PySide6.QtWidgets import QFileDialog

from qt_dicom_viewer.model import (MprPlane, TabType, ToolType, ViewportConfig,
                                  TwoDViewType, WindowLevel)
from qt_dicom_viewer.model.render_models import PetBatchRenderRequest
from qt_dicom_viewer.core.mpr_rotation import (move_mpr_state_center, rotate_mpr_state_3d,
                                              rotate_crosshair_state)
from qt_dicom_viewer.core.pet_fusion import (rigid_matrix, registration_from_parameters,
    parameters_from_registration, registration_document, load_registration_document)
from qt_dicom_viewer.ui.controller.viewport.controller.pet_display_controller import PetDisplayController
from qt_dicom_viewer.ui.controller.viewport.image_2d.pet_viewport_controller import LinkedPetViewport, PetMipViewport
from .tab_controller import TabController
from .tool_controller import ToolController


class PetWorkspaceController(TabController):
    settingsChanged = Signal()

    def __init__(self, config, ct_series=None, pet_series=None, parent=None):
        self.ct_series, self.pet_series = ct_series, pet_series
        self.matrix = np.eye(4)
        self.pivot = np.zeros(3)
        self._plane = MprPlane.AXIAL
        self._ct_window = None
        self._opacity = 0.5
        self._pet_color = "grayscale"
        self._fusion_color = "hotIron"
        self._registration_active = False
        self._registration_changed = False
        self._latest = None
        self._last_result = None
        self._requested = None
        self._committed_request = None
        self._warning = ""
        self._error = ""
        self._syncing = False
        self._applying = False
        self._closed = False
        super().__init__(config, parent)

    def _create_tool_controller(self):
        self.pet_display = PetDisplayController(self)
        self.pet_display.invalidated.connect(self.request_render)
        self._tool_controller = ToolController(tab_type=TabType.MPR, modality="PT", parent=self)
        self._tool_controller.commandRequested.connect(self._handle_tool_command)
        self._tool_controller.resetRequested.connect(self._handle_tool_reset_requested)

    def _create_viewport_dict(self):
        pet_meta = next(m for m in self._tab_config.series_metas if m.modality.upper() == "PT")
        ct_meta = next((m for m in self._tab_config.series_metas if m.modality.upper() == "CT"), None)
        roles = ("ct", "pet", "fusion", "mip") if ct_meta else ("axial", "coronal", "sagittal", "mip")
        for role in roles:
            meta = ct_meta if role == "ct" else pet_meta
            plane = TwoDViewType.PET_MIP if role == "mip" else MprPlane.AXIAL if ct_meta else MprPlane(role)
            config = ViewportConfig(str(uuid4()), self._tab_config.tab_id, plane, meta.series_uid, meta, role)
            viewport = (PetMipViewport(config, self._tool_controller, self) if role == "mip" else
                        LinkedPetViewport(config, self._tool_controller, self))
            if role != "mip":
                viewport.crosshairCenterChangeRequested.connect(self.move_center)
                viewport.crosshairRotationRequested.connect(self._rotate_plane)
                viewport.mpr3DRotationRequested.connect(self._rotate_3d)
            viewport.cursorController.cursorInfoChanged.connect(viewport.overlayChanged.emit)
            self._viewport_dict[config.viewport_id] = viewport
            if not self._active_viewport_id or role == "fusion":
                self._active_viewport_id = config.viewport_id

    @Property(bool, constant=True)
    def isFusion(self):
        return self.ct_series is not None

    @Property(QObject, constant=True)
    def petController(self):
        return next(v for v in self._viewport_dict.values() if v.viewportRole not in ("ct", "mip"))

    @Property(str, notify=settingsChanged)
    def plane(self):
        return self._plane.value

    @Property(float, notify=settingsChanged)
    def ctCenter(self):
        return self._ct_window.center if self._ct_window else 40.

    @Property(float, notify=settingsChanged)
    def ctWidth(self):
        return self._ct_window.width if self._ct_window else 400.

    @Property(float, notify=settingsChanged)
    def opacity(self):
        return self._opacity

    @Property(str, notify=settingsChanged)
    def petColorMap(self):
        return self._pet_color

    @Property(str, notify=settingsChanged)
    def fusionColorMap(self):
        return self._fusion_color

    @Property(bool, notify=settingsChanged)
    def ready(self):
        return self._last_result is not None

    @Property(str, notify=settingsChanged)
    def warning(self):
        return self._error or self._warning

    @property
    def ct_description(self):
        return (f"{self.ct_series.patient_name} · "
                f"{self.ct_series.series_description or self.ct_series.series_instance_uid[-12:]}") if self.ct_series else ""

    @property
    def pet_description(self):
        return (f"{self.pet_series.patient_name} · "
                f"{self.pet_series.series_description or self.pet_series.series_instance_uid[-12:]}") if self.pet_series else ""

    @Property(bool, notify=settingsChanged)
    def registrationActive(self):
        return self._registration_active

    @Property(str, notify=settingsChanged)
    def registrationStatus(self):
        if not self.isFusion:
            return ""
        if self._registration_active:
            return "手动配准中"
        if self._registration_changed:
            return "已手动调整"
        a, b = self.ct_series.frame_of_reference_uid, self.pet_series.frame_of_reference_uid
        return "DICOM 坐标对齐" if a and a == b else "待手动配准 · 坐标预览"

    @Property("QVariantList", notify=settingsChanged)
    def registrationParameters(self):
        translation, angles = parameters_from_registration(self.matrix, self.pivot)
        return [float(x) for x in (*translation, *angles)]

    def contains_viewport(self, viewport_id):
        return viewport_id == self._tab_config.tab_id or super().contains_viewport(viewport_id)

    def accepts_render_result(self, result):
        return not self._closed and result.response_id == self._latest

    def init_render(self):
        self.request_render()

    def request_render(self):
        if self._closed or self._applying:
            return
        self._latest = str(uuid4())
        state = self.pet_display.target
        self._requested = PetBatchRenderRequest(
            request_id=self._latest, viewport_id=self._tab_config.tab_id,
            series_uid=self.pet_series.series_instance_uid,
            ct_series_uid=self.ct_series.series_instance_uid if self.ct_series else None,
            viewports=tuple((v.viewportRole, v.viewportId) for v in self._viewport_dict.values()),
            state=self._target_mpr_state, plane=self._plane,
            value_unit=state.meta.unit_id if state else None,
            pet_window=state.window if state else None, ct_window=self._ct_window,
            transform=tuple(self.matrix.ravel()), opacity=self._opacity,
            pet_color_map=self._pet_color, fusion_color_map=self._fusion_color)
        self.renderRequested.emit(self._requested)

    def handleRenderResult(self, result):
        if not self.accepts_render_result(result):
            return
        self._applying = True
        try:
            self._last_result = result
            self._committed_request = self._requested
            self._target_mpr_state = result.state
            if self._initial_mpr_state is None:
                self._initial_mpr_state = result.state
            self.pet_display.accept(result.pet_volume.pixel_value_meta, result.pet_window)
            self._ct_window = result.ct_window
            self._warning, self._error = result.warning, ""
            for frame in result.frames:
                v = self._viewport_dict[frame.viewport_id]
                if isinstance(v, LinkedPetViewport):
                    v.apply_mpr_state(result.state)
                    v._ct_pixels = result.ct_samples if v.viewportRole == "fusion" else None
                    v.measurementController.secondary_pixels = v._ct_pixels
                v.handleRenderResult(frame)
            self.settingsChanged.emit()
        finally:
            self._applying = False

    def handleRenderFailure(self, failure):
        if failure.request_id != self._latest or self._closed:
            return
        self.pet_display.fail()
        if self._committed_request is not None:
            request = self._committed_request
            self.matrix = np.asarray(request.transform).reshape(4, 4).copy()
            self._registration_changed = not np.allclose(self.matrix, np.eye(4))
            self._plane = request.plane
            self._ct_window = self._last_result.ct_window
            self._target_mpr_state = self._last_result.state
            self._opacity = request.opacity
            self._pet_color = request.pet_color_map
            self._fusion_color = request.fusion_color_map
            for frame in self._last_result.frames:
                v = self._viewport_dict[frame.viewport_id]
                if self.isFusion and isinstance(v, LinkedPetViewport):
                    v.set_plane(self._plane)
                    v.apply_mpr_state(self._target_mpr_state)
                    v._apply_specific_render_result(frame)
        self._error = str(failure.error)
        if self._last_result is None:
            for v in self._viewport_dict.values():
                v._set_load_state("error", self._error)
        else:
            for v in self._viewport_dict.values():
                v._set_load_state("ready", self._error)
        self.settingsChanged.emit()

    def move_center(self, center):
        if self._target_mpr_state is None:
            return
        self._target_mpr_state = move_mpr_state_center(self._target_mpr_state, center)
        self.request_render()

    def _rotate_plane(self, plane, angle):
        if self._target_mpr_state:
            self._target_mpr_state = rotate_crosshair_state(self._target_mpr_state, plane, angle)
            self.request_render()

    def _rotate_3d(self, axis, angle):
        if self._target_mpr_state:
            self._target_mpr_state = rotate_mpr_state_3d(self._target_mpr_state, axis, angle)
            self.request_render()

    @Slot(str)
    def setPlane(self, value):
        if not self.isFusion or value not in {p.value for p in MprPlane}:
            return
        self._plane = MprPlane(value)
        for v in self._viewport_dict.values():
            if isinstance(v, LinkedPetViewport):
                v.set_plane(self._plane)
        self.settingsChanged.emit()
        self.request_render()

    @Slot(float, float)
    def setCtWindow(self, center, width):
        if np.isfinite([center, width]).all():
            self.set_ct_window(WindowLevel(center, max(1., width)))

    def set_ct_window(self, window):
        self._ct_window = window
        self.settingsChanged.emit()
        self.request_render()

    @Slot(float)
    def setOpacity(self, value):
        if np.isfinite(value):
            self._opacity = float(np.clip(value, 0, 1))
            self.settingsChanged.emit()
            self.request_render()

    @Slot(str)
    def setPetColorMap(self, value):
        if value in ("grayscale", "hotIron"):
            self._pet_color = value
            self.settingsChanged.emit()
            self.request_render()

    @Slot(str)
    def setFusionColorMap(self, value):
        if value in ("grayscale", "hotIron"):
            self._fusion_color = value
            self.settingsChanged.emit()
            self.request_render()

    def synchronize_view(self, origin):
        if not self.isFusion or self._syncing or self._applying or origin.viewportRole == "mip":
            return
        self._syncing = True
        try:
            fields = ("zoom", "pan_x", "pan_y", "rotation_degrees", "horizontal_flip", "vertical_flip")
            for v in self._viewport_dict.values():
                if v is origin or v.viewportRole == "mip":
                    continue
                v._state = replace(v._state, **{f: getattr(origin._state, f) for f in fields})
                v.transformChanged.emit()
                v.directionLabelsChanged.emit()
                v.overlayChanged.emit()
        finally:
            self._syncing = False

    @Slot(bool)
    def setRegistrationActive(self, enabled):
        if not self.isFusion or not self.ready:
            return
        if enabled and not self._registration_active:
            self.pivot = np.asarray(self._target_mpr_state.frame.center_patient)
        self._registration_active = enabled
        for v in self._viewport_dict.values():
            v.cancelMeasurement()
            if isinstance(v, LinkedPetViewport):
                v._registration_drag = None
            v.overlayChanged.emit()
        self.settingsChanged.emit()

    def set_registration(self, matrix):
        self.matrix = rigid_matrix(matrix)
        self._registration_changed = True
        self.settingsChanged.emit()
        self.request_render()

    @Slot(int, float)
    def setRegistrationParameter(self, index, value):
        if not self.isFusion or not self.ready or not 0 <= index < 6 or not np.isfinite(value):
            return
        values = self.registrationParameters
        values[index] = value
        self.set_registration(registration_from_parameters(values[:3], values[3:], self.pivot))

    @Slot()
    def centerAlign(self):
        if not self.isFusion or not self.ready:
            return
        result = self._last_result
        matrix = self.matrix.copy()
        matrix[:3, 3] = (np.asarray(result.ct_volume.geometry.center_patient)
                        - matrix[:3, :3] @ result.pet_volume.geometry.center_patient)
        self.set_registration(matrix)

    @Slot()
    def resetRegistration(self):
        self.matrix = np.eye(4)
        self._registration_changed = False
        self.settingsChanged.emit()
        self.request_render()

    def _document(self):
        if not self.isFusion or not self.ready:
            raise ValueError("请先加载 CT/PET")
        return registration_document(self._last_result.ct_volume, self._last_result.pet_volume,
            self.ct_series.frame_of_reference_uid, self.pet_series.frame_of_reference_uid,
            self.matrix, self.pivot)

    @Slot()
    def saveRegistration(self):
        path, _ = QFileDialog.getSaveFileName(None, "保存 PET/CT 配准", "petct-registration.json", "JSON (*.json)")
        if path:
            self.save_registration_to(path)

    def save_registration_to(self, path):
        try:
            data = json.dumps(self._document(), ensure_ascii=False, indent=2).encode()
            file = QSaveFile(str(path))
            if not file.open(QIODevice.WriteOnly) or file.write(data) != len(data) or not file.commit():
                raise OSError(file.errorString())
            self._error = ""
        except (ValueError, OSError) as error:
            self._error = str(error)
        self.settingsChanged.emit()

    @Slot()
    def loadRegistration(self):
        path, _ = QFileDialog.getOpenFileName(None, "加载 PET/CT 配准", "", "JSON (*.json)")
        if path:
            self.load_registration_from(path)

    def load_registration_from(self, path):
        try:
            with open(path, encoding="utf-8") as stream:
                document = json.load(stream)
            matrix, pivot = load_registration_document(document, self._document())
            self.pivot = pivot
            self._error = ""
            self.set_registration(matrix)
        except (ValueError, OSError, TypeError, AttributeError) as error:
            self._error = str(error)
        self.settingsChanged.emit()

    def _handle_tool_command(self, command):
        if command == "viewport:reset":
            self._target_mpr_state = self._initial_mpr_state
            self.pet_display.reset()
            for v in self._viewport_dict.values():
                v.reset_all_view_state(reset_slice=False)
            self.request_render()

    def _handle_tool_reset_requested(self, value):
        if value == "window":
            self.pet_display.reset()
            if self.isFusion and self._last_result:
                self.set_ct_window(self._last_result.ct_volume.default_window)
        elif value == "mpr-rotate-3d":
            self._target_mpr_state = self._initial_mpr_state
            self.request_render()
        elif self.activeViewport:
            self.activeViewport.reset_tool_state(ToolType(value))

    def dispose(self):
        self._closed = True
        super().dispose()
