import uuid
from typing import cast

from PySide6.QtCore import Property, QPointF, Signal

from qt_dicom_viewer.core.geometry_2d import point_distance
from qt_dicom_viewer.model import (
    CrosshairCenterChange,
    CrosshairMoveContext,
    ImagePoint,
    InteractionResult,
    MprImageGeometry,
    MprPlane,
    MprRenderRequest,
    MprRenderResult,
    OperationStartContext,
    PointerPosition,
    RenderRequest,
    RenderResult,
    Vector3,
    ViewportConfig, MprFrame,
)
from qt_dicom_viewer.model.ui_models import CrosshairColor, CrosshairStyle
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from .image_2d_viewport_controller import (
    Image2DViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.operation.crosshair_move_operation import (
    CrosshairMoveOperation,
)
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation


_CROSSHAIR_STYLES = {
    MprPlane.AXIAL: CrosshairColor("green", "blue"),
    MprPlane.CORONAL: CrosshairColor("red", "blue"),
    MprPlane.SAGITTAL: CrosshairColor("red", "green"),
}


class MprViewportController(Image2DViewportController):
    crosshairCenterChangeRequested = Signal(object)
    renderInvalidated = Signal(str)

    def __init__(
        self,
        viewport_config: ViewportConfig,
        tool_controller: ToolController,
        parent=None,
    ) -> None:
        if not isinstance(viewport_config.viewport_type, MprPlane):
            raise ValueError(
                "MprViewportController requires an MPR plane config"
            )
        super().__init__(viewport_config, tool_controller, parent)
        self._plane_geometry: MprImageGeometry | None = None
        self._crosshair_image_position: ImagePoint | None = None
        self._crosshair_operation = CrosshairMoveOperation()
        self._crosshair_style = CrosshairStyle(
            _CROSSHAIR_STYLES[viewport_config.viewport_type]
        )

    def build_mpr_render_request(
            self,
            *,
            mpr_frame: MprFrame | None,
            initial: bool = False,
    ) -> MprRenderRequest:
        state = self.viewport_state

        return MprRenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            window=None if initial else state.window,
            inverted=False if initial else state.inverted,
            plane=self.viewport_config.viewport_type,
            mpr_frame=mpr_frame,
        )

    def _build_render_request(self, *, initial: bool) -> RenderRequest:
        return self.build_mpr_render_request(
            mpr_frame=None,
            initial=initial,
        )

    def request_render(self) -> None:
        """Report stale local state; TabController decides when to render."""
        self.renderInvalidated.emit(
            self.viewport_config.viewport_id
        )

    def _validate_render_result(self, result: RenderResult) -> None:
        if not isinstance(result, MprRenderResult):
            raise TypeError("MprViewportController requires MprRenderResult")
        if result.view_type != self.viewport_config.viewport_type:
            raise ValueError("MPR render result targets a different plane")

    def _apply_specific_render_result(self, result: RenderResult) -> None:
        mpr_result = cast(MprRenderResult, result)
        geometry = mpr_result.plane_geometry
        self._plane_geometry = geometry
        self._crosshair_image_position = None

        if geometry is not None:
            column, row = geometry.mpr_point_to_image_point(
                (0.0, 0.0, 0.0)
            )
            self._crosshair_image_position = ImagePoint(
                column=column,
                row=row,
            )

        self.crosshairImagePositionChanged.emit()

    def _begin_specific_interaction(
        self,
        position: PointerPosition,
        endpoint_tolerance: float,
    ) -> tuple[DragOperation, OperationStartContext] | None:
        if not self._crosshair_hit_test(position, endpoint_tolerance):
            return None
        return self._crosshair_operation, CrosshairMoveContext(
            current_pan_x=self.viewport_state.pan_x,
            current_pan_y=self.viewport_state.pan_y,
        )

    def _apply_specific_interaction_result(
        self,
        result: InteractionResult,
    ) -> bool:
        if not isinstance(result, CrosshairCenterChange):
            return False
        self._apply_crosshair_move(result.position)
        return True

    def _crosshair_hit_test(
        self,
        position: PointerPosition,
        endpoint_tolerance: float,
    ) -> bool:
        crosshair_position = self._crosshair_image_position
        if crosshair_position is None:
            return False
        if position.image is None:
            return False
        return (
            point_distance(
                position.image,
                crosshair_position,
            )
            < endpoint_tolerance
        )

    def _apply_crosshair_move(self, position: ImagePoint) -> None:
        geometry = self._plane_geometry
        if geometry is None:
            return
        center_patient: Vector3 = geometry.image_point_to_patient(
            column=position.column,
            row=position.row,
        )
        self.crosshairCenterChangeRequested.emit(center_patient)

    @Property("QVariantMap", constant=True)
    def crosshairStyle(self) -> dict:
        style = self._crosshair_style
        return {
            "centerGap": style.centerGap,
            "lineWidth": style.lineWidth,
            "horizontalColor": style.color.horizontal,
            "verticalColor": style.color.vertical,
        }

    @Property(
        QPointF,
        notify=Image2DViewportController.crosshairImagePositionChanged,
    )
    def crosshairImagePosition(self) -> QPointF:
        position = self._crosshair_image_position
        if position is None:
            return QPointF(-1.0, -1.0)
        return QPointF(position.column, position.row)
