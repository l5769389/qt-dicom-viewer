from dataclasses import replace
from math import atan2

import numpy as np
from PySide6.QtCore import Property, Signal, Slot, QPointF, QObject

from qt_dicom_viewer.model import MprPlane, WindowLevel
from qt_dicom_viewer.model.render_models import PetMipRenderResult
from qt_dicom_viewer.core.mpr_rotation import axis_angle_rotation_matrix
from .image_2d_viewport_controller import Image2DViewportController
from .mpr_viewport_controller import MprViewportController, _CROSSHAIR_STYLES
from qt_dicom_viewer.model.ui_models import CrosshairStyle


class LinkedPetViewport(MprViewportController):
    # PySide needs a local notifier here: a grandparent Signal descriptor
    # produces an invalid meta-object signal index when QML wraps this class.
    linkedOverlayChanged = Signal()
    def __init__(self, config, tools, owner):
        self.owner = owner
        self._registration_drag = None
        self._ct_pixels = None
        super().__init__(config, tools, owner)
        self._pet_display = owner.pet_display
        self._pet_display.changed.connect(self.petDisplayChanged.emit)
        self._pet_display.changed.connect(self.overlayChanged.emit)
        self.transformChanged.connect(lambda: owner.synchronize_view(self))
        self.overlayChanged.connect(self.linkedOverlayChanged.emit)

    def request_render(self):
        self.owner.request_render()

    def set_plane(self, plane):
        self.viewport_config = replace(self.viewport_config, viewport_type=plane)
        self._crosshair_style = CrosshairStyle(_CROSSHAIR_STYLES[plane])
        self._plane_geometry = None
        self.viewportTypeChanged.emit()
        self.directionLabelsChanged.emit()
        self.crosshairImagePositionChanged.emit()

    def apply_window_level(self, result):
        if self.viewportRole == "ct":
            self.owner.set_ct_window(result.window)
        else:
            super().apply_window_level(result)

    @Slot(float, float)
    def applyWindowPreset(self, center, width):
        if self.viewportRole == "ct":
            self.owner.set_ct_window(WindowLevel(center, max(1., width)))
        else:
            self.setPetDisplayUpper(center + width / 2)

    @Property("QVariantMap", notify=linkedOverlayChanged)
    def overlayInfo(self):
        info = Image2DViewportController.overlayInfo.fget(self)
        info.update(viewRole=self.viewportRole, registration=self.owner.registrationStatus,
                    fusionWarning=self.owner.warning,
                    ctSeries=self.owner.ct_description, petSeries=self.owner.pet_description)
        if self.owner._ct_window:
            info.update(ctWindowCenter=f"{self.owner._ct_window.center:g}",
                        ctWindowWidth=f"{self.owner._ct_window.width:g}")
        return info

    @Property(str, notify=linkedOverlayChanged)
    def secondaryCursorText(self):
        p = self.cursorController._pointer_meta
        if self.viewportRole != "fusion" or self._ct_pixels is None or p is None:
            return ""
        row, col = int(p.pointer_y), int(p.pointer_x)
        if 0 <= row < self._ct_pixels.shape[0] and 0 <= col < self._ct_pixels.shape[1]:
            value = self._ct_pixels[row, col]
            return f"CT: {value:.1f} HU" if np.isfinite(value) else "CT: -- HU"
        return "CT: -- HU"

    @Slot(float, float, int, bool, float, float, float, float)
    def beginInteraction(self, x, y, buttons, image_valid, column, row, endpoint_tolerance, line_tolerance):
        if self.owner.registrationActive and self.viewportRole in ("pet", "fusion") and self._plane_geometry:
            self.cancelMeasurement()
            self._registration_drag = (np.array([column, row]), self.owner.matrix.copy(), buttons)
            return
        super().beginInteraction(x, y, buttons, image_valid, column, row, endpoint_tolerance, line_tolerance)

    @Slot(float, float, result=bool)
    def updateRegistrationDrag(self, column, row):
        if self._registration_drag is None:
            return False
        start, initial, buttons = self._registration_drag
        g = self._plane_geometry
        if g is None or not np.isfinite([column, row]).all():
            return True
        step = np.eye(4)
        if buttons & 2:
            pivot = self.owner.pivot
            index = g.patient_to_image_index @ np.array([*pivot, 1])
            center = np.array([index[2], index[1]])
            a = (start-center) * [g.column_spacing, g.row_spacing]
            b = (np.array([column, row])-center) * [g.column_spacing, g.row_spacing]
            if np.linalg.norm(a) < 1e-6 or np.linalg.norm(b) < 1e-6:
                return True
            angle = atan2(b[1], b[0]) - atan2(a[1], a[0])
            rotation = axis_angle_rotation_matrix(tuple(np.cross(g.column_direction_patient,
                                                                 g.row_direction_patient)), angle)
            step[:3, :3] = rotation
            step[:3, 3] = pivot - rotation @ pivot
        else:
            delta = np.array([column, row]) - start
            step[:3, 3] = (delta[0] * g.column_spacing * np.asarray(g.column_direction_patient)
                           + delta[1] * g.row_spacing * np.asarray(g.row_direction_patient))
        self.owner.set_registration(step @ initial)
        return True

    @Slot(float, float, bool, float, float)
    def endInteraction(self, *args):
        if self._registration_drag is not None:
            self._registration_drag = None
            return
        super().endInteraction(*args)


class PetMipViewport(Image2DViewportController):
    def __init__(self, config, tools, owner):
        self.owner = owner
        self._mip_result = None
        super().__init__(config, tools, owner)
        self._pet_display = owner.pet_display
        self._pet_display.changed.connect(self.petDisplayChanged.emit)
        self._pet_display.changed.connect(self.overlayChanged.emit)

    @Property(int, notify=Image2DViewportController.sliceChanged)
    def sliceCount(self):
        return 0

    def request_render(self):
        self.owner.request_render()

    def _validate_render_result(self, result):
        if not isinstance(result, PetMipRenderResult):
            raise TypeError("Expected PET MIP result")

    def _apply_specific_render_result(self, result):
        self._mip_result = result
        self.crosshairImagePositionChanged.emit()

    def apply_slice_index(self, index):
        pass

    def _measurement_context(self, *args):
        return None

    @Slot(bool, float, float, float, float, float, float)
    def selectMeasurementAt(self, valid, column, row, *args):
        result = self._mip_result
        if not valid or result is None:
            return
        r, c = int(round(row)), int(round(column))
        if 0 <= r < result.peak_positions.shape[0] and 0 <= c < result.peak_positions.shape[1]:
            point = result.peak_positions[r, c]
            if np.isfinite(point).all():
                self.owner.move_center(tuple(float(x) for x in point))

    @Property("QVariantMap", notify=Image2DViewportController.overlayChanged)
    def overlayInfo(self):
        info = Image2DViewportController.overlayInfo.fget(self)
        info.update(viewRole="mip", viewType="PET MIP · 最大值投影")
        return info

    @Property(bool, constant=True)
    def hasCrosshair(self):
        return True

    @Property("QVariantMap", constant=True)
    def crosshairStyle(self):
        return {"centerGap": 6, "lineWidth": 1, "horizontalColor": "green", "verticalColor": "blue"}

    @Property(QPointF, notify=Image2DViewportController.crosshairImagePositionChanged)
    def crosshairImagePosition(self):
        if self._mip_result is None or self.owner._target_mpr_state is None:
            return QPointF(-1, -1)
        p = self._mip_result.plane_geometry.patient_to_image_index @ np.array(
            [*self.owner._target_mpr_state.frame.center_patient, 1])
        return QPointF(float(p[2]), float(p[1]))
