import logging
from dataclasses import replace
from math import isfinite

import numpy as np
from PySide6.QtCore import QObject, Signal, Slot, Property, QPointF

from qt_dicom_viewer.model import ViewportState, ViewportConfig, RenderRequest, RenderResult, \
    WindowLevel, FrameDisplayMeta, InteractionType, Point, Offset, DragUpdateEvent, \
    DisplayStyle, ViewportTransformAction, PointerPosition, ImagePoint, MeasurementKind, OperationStartContext
from qt_dicom_viewer.model.interaction import InteractionResult, SliceIndexChange, WindowLevelChange, PanChange, \
    ZoomChange, WindowLevelContext, ScrollContext, PanContext, ZoomContext, MeasureContext
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.controller.cursor_controller import CursorController
from qt_dicom_viewer.ui.controller.viewport.controller.measure.measure_controller import MeasurementController
from qt_dicom_viewer.ui.controller.viewport.controller.overlay_presenter import OverlayPresenter
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation
from qt_dicom_viewer.ui.controller.viewport.operation.pan_operation import PanOperation
from qt_dicom_viewer.ui.controller.viewport.operation.scroll_operation import ScrollOperation
from qt_dicom_viewer.ui.controller.viewport.operation.window_level_operation import WindowLevelOperation
from qt_dicom_viewer.ui.controller.viewport.operation.zoom_operation import ZoomOperation
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController

logger = logging.getLogger(__name__)

DISPLAY_STYLES = {
    "grayscale": DisplayStyle(
        color_map="grayscale",
        no_data_color="#000000",
    ),
    "hotIron": DisplayStyle(
        color_map="hotIron",
        no_data_color="#090000",
    ),
    "rainbow": DisplayStyle(
        color_map="rainbow",
        no_data_color="#000020",
    ),
}

def _make_pointer_position(
        viewport_x: float,
        viewport_y: float,
        image_valid: bool,
        column: float,
        row: float,
) -> PointerPosition:
    image_point = None

    if (
            image_valid
            and isfinite(column)
            and isfinite(row)
    ):
        image_point = ImagePoint(
            column=column,
            row=row,
        )

    return PointerPosition(
        viewport=Point(
            x=viewport_x,
            y=viewport_y,
        ),
        image=image_point,
    )


class Image2DViewportController(ViewportController):
    imageSourceChanged = Signal()
    overlayChanged = Signal()
    imageDimensionChanged = Signal()
    transformChanged = Signal()
    displayStyleChanged = Signal()
    crosshairImagePositionChanged = Signal()
    hit_tolerance = 6

    def __init__(self, viewport_config: ViewportConfig, tool_controller: ToolController, parent=None):
        super().__init__(viewport_config=viewport_config, parent=parent)
        self._modality_pixel: np.ndarray | None = None
        self._state = ViewportState(
            slice_index=self._initial_slice_index(),
            slice_count=None,
        )
        self._image_revision = 0
        self._has_image = False
        self._frame_meta: FrameDisplayMeta | None = None
        self._measure_controller = MeasurementController(self)
        self._tool_controller = tool_controller
        self._scroll_operation = ScrollOperation()
        self._pan_operation = PanOperation()
        self._zoom_operation = ZoomOperation()
        self._cursor_controller = CursorController(viewport_config=self.viewport_config, parent=self)
        self._overlay_presenter = OverlayPresenter()
        self._active_drag_operation: DragOperation | None = None
        self._window_level_operation = WindowLevelOperation()
        self._active_drag_start_position: PointerPosition | None = None

    def _initial_slice_index(self) -> int | None:
        return None

    def _build_render_request(self, *, initial: bool) -> RenderRequest:
        raise NotImplementedError

    def _validate_render_result(self, result: RenderResult) -> None:
        raise NotImplementedError

    def _apply_specific_render_result(self, result: RenderResult) -> None:
        raise NotImplementedError

    def _begin_specific_interaction(
        self,
        position: PointerPosition,
        endpoint_tolerance: float,
    ) -> tuple[DragOperation, OperationStartContext] | None:
        return None

    def _apply_specific_interaction_result(
        self,
        result: InteractionResult,
    ) -> bool:
        return False

    @Property(QObject, constant=True)
    def cursorController(self):
        return self._cursor_controller


    def request_first_loader(self) -> None:
        request = self._build_render_request(initial=True)
        logger.debug(
            "Render started: request_id=%s viewport_id=%s",
            request.request_id,
            request.viewport_id,
        )
        self.renderRequested.emit(request)

    def request_render(self) -> None:
        request = self._build_render_request(initial=False)
        logger.debug(
            "Render started: request_id=%s viewport_id=%s window=%r",
            request.request_id,
            request.viewport_id,
            request.window
        )
        self.renderRequested.emit(request)

    @Slot(float, float)
    def setViewportSize(
            self,
            width: float,
            height: float,
    ) -> None:
        if width <= 0 or height <= 0:
            return

        if (
                width == self._state.width
                and height == self._state.height
        ):
            return

        self._state = replace(
            self._state,
            width=width,
            height=height,
        )

    @Slot(object)
    def handleRenderResult(self, result: RenderResult) -> None:
        if (
                result.viewport_id
                != self.viewport_config.viewport_id
        ):
            return
        self._validate_render_result(result)
        self._frame_meta = result.frame_meta
        self._state = replace(
            self._state,
            slice_index=result.frame_meta.slice_index,
            slice_count=result.frame_meta.slice_count,
            window=result.frame_meta.window,
            inverted=result.frame_meta.inverted,
        )
        self._modality_pixel = result.modality_pixel
        self._apply_specific_render_result(result)

        self.overlayChanged.emit()
        self.imageDimensionChanged.emit()
        if result.image is None:
            return

        self._has_image = True
        self._image_revision += 1
        self.imageSourceChanged.emit()
        logger.debug(
            "Viewport image updated: "
            "viewport_id=%s revision=%d",
            result.viewport_id,
            self._image_revision,
        )

    @property
    def viewport_state(self) -> ViewportState:
        return self._state

    @Property(str, notify=imageSourceChanged)
    def imageSource(self) -> str:
        if not self._has_image:
            return ""

        return (
            f"image://dicom/"
            f"{self.viewport_config.viewport_id}/"
            f"{self._image_revision}"
        )

    @Property("QVariantMap", notify=overlayChanged)
    def overlayInfo(self) -> dict:
        series = self.viewport_config.series_meta
        frame = self._frame_meta

        return self._overlay_presenter.build(
            viewport_config = self.viewport_config,
            series=series,
            frame=frame,
            state=self._state,
        )

    @Slot(float, float, int, bool, float, float, float, float)
    def beginInteraction(
            self,
            x: float,
            y: float,
            buttons: int,
            image_valid: bool,
            column: float,
            row: float,
            endpoint_tolerance: float,
            line_tolerance: float,
    ) -> None:
        logger.debug(f'beginInteraction,x:{x},y:{y},btn:{buttons}, col:{column}, row:{row}')
        position = _make_pointer_position(
            viewport_x=x,
            viewport_y=y,
            image_valid=image_valid,
            column=column,
            row=row,
        )
        self._active_drag_operation = None
        self._active_drag_start_position = None
        context: OperationStartContext | None = None
        specific_interaction = self._begin_specific_interaction(
            position,
            endpoint_tolerance,
        )
        if specific_interaction is not None:
            self._active_drag_operation, context = specific_interaction
        else:
            match self._tool_controller.active_interaction:
                case InteractionType.WINDOW:
                    self._active_drag_operation = self._window_level_operation
                    context = WindowLevelContext(
                        viewport_size=self.viewport_size,
                        inverted=self.inverted,
                        current_window=self.current_window,
                    )
                case InteractionType.SCROLL:
                    if self._state.slice_index is not None and self._state.slice_count is not None:
                        self._active_drag_operation = self._scroll_operation
                        context = ScrollContext(
                            slice_index=self._state.slice_index,
                            slice_count=self._state.slice_count,
                        )
                case InteractionType.PAN:
                    self._active_drag_operation = self._pan_operation
                    context = PanContext(
                        current_pan_x=self._state.pan_x,
                        current_pan_y=self._state.pan_y,
                    )
                case InteractionType.ZOOM:
                    self._active_drag_operation = self._zoom_operation
                    context = ZoomContext(
                        viewport_size=self.viewport_size,
                        current_zoom=self._state.zoom,
                    )
                case InteractionType.MEASURE_LENGTH | InteractionType.MEASURE_ANGLE:
                    if self._frame_meta is None:
                        logger.error(
                            "Cannot measure before an image is loaded"
                        )
                        return

                    measurement_kind = (
                        MeasurementKind.LENGTH
                        if self._tool_controller.active_interaction
                        == InteractionType.MEASURE_LENGTH
                        else MeasurementKind.ANGLE
                    )
                    if self._state.slice_index is not None:
                        self._active_drag_operation = self._measure_controller
                        context = MeasureContext(
                            measurement_kind=measurement_kind,
                            series_uid=self.viewport_config.series_uid,
                            sop_instance_uid=self._frame_meta.instance_meta.sop_instance_uid or '',
                            slice_index=self._state.slice_index,
                            geometry=self._frame_meta.geometry,
                            endpoint_tolerance=endpoint_tolerance,
                            line_tolerance=line_tolerance,
                        )
                case _:
                    context = None
        if self._active_drag_operation is None or context is None:
            return None
        self._active_drag_start_position = position
        result = self._active_drag_operation.begin(
            position,
            context,
        )
        if result is not None:
            self._apply_interaction_result(result)
        return None

    @Slot(
        QPointF,
        QPointF,
        QPointF,
        QPointF,
        bool,
        float,
        float,
    )
    def updateInteraction(
            self,
            start_point: QPointF,
            current_point: QPointF,
            step_offset: QPointF,
            total_offset: QPointF,
            image_valid: bool,
            column: float,
            row: float,
    ) -> None:
        operation = self._active_drag_operation
        start_position = self._active_drag_start_position

        if operation is None or start_position is None:
            return

        current_position = _make_pointer_position(
            viewport_x=current_point.x(),
            viewport_y=current_point.y(),
            image_valid=image_valid,
            column=column,
            row=row,
        )

        event = DragUpdateEvent(
            start_position=start_position,
            current_position=current_position,
            step_offset=Offset(
                x=step_offset.x(),
                y=step_offset.y(),
            ),
            total_offset=Offset(
                x=total_offset.x(),
                y=total_offset.y(),
            ),
        )

        result = operation.update(event)
        self._apply_interaction_result(result)

    @Slot(float, float, bool, float, float)
    def endInteraction(
            self,
            x: float,
            y: float,
            image_valid: bool,
            column: float,
            row: float,
    ) -> None:
        operation = self._active_drag_operation

        self._active_drag_operation = None
        self._active_drag_start_position = None

        if operation is None:
            return

        position = _make_pointer_position(
            viewport_x=x,
            viewport_y=y,
            image_valid=image_valid,
            column=column,
            row=row,
        )

        result = operation.end(position)
        self._apply_interaction_result(result)

    @Slot(QPointF)
    def handlePointerMoved(self, point: QPointF) -> None:
        current_point = Point(
            x=point.x(),
            y=point.y()),
        ...

    @Slot(float, float, float, float, bool, int, int)
    def updateCursorPosition(
            self,
            column: float,
            row: float,
            clipColumn: float,
            clipRow: float,
            image_valid: bool,
            column_index: int,
            row_index: int,
    ) -> None:
        if self._modality_pixel is None or not image_valid:
            self._cursor_controller.clearPosition()
            return

        ct_value = self._modality_pixel[
            int(clipRow)
        ][int(clipColumn)]
        if not np.isfinite(ct_value):
            self._cursor_controller.clearPosition()
            return

        self._cursor_controller.updatePosition(clipColumn, clipRow, ct_value)

    @Slot(float, float, float, float, int)
    def handleWheel(
            self,
            angle_delta_y: float,
            pixel_delta_y: float,
            x: float,
            y: float,
            modifiers: int,
    ) -> None:
        if self._state.slice_index is not None and self._state.slice_count is not None:
            slice_change = self._scroll_operation.handle_wheel(
                angle_delta_y=angle_delta_y,
                current_index=self._state.slice_index,
                slice_count=self._state.slice_count,
            )
            self._apply_interaction_result(slice_change)

    def _apply_interaction_result(
            self,
            result: InteractionResult | None,
    ) -> None:
        match result:
            case SliceIndexChange(slice_index=index):
                self.apply_slice_index(index)

            case WindowLevelChange(window=window, inverted=inverted):
                self.apply_window_level(
                    WindowLevelChange(
                        window=window,
                        inverted=inverted,
                    )
                )

            case PanChange(offset_x=x, offset_y=y):
                self.apply_pan(x, y)

            case ZoomChange(zoom=zoom):
                self.apply_zoom(zoom)

            case None:
                return

            case _ if self._apply_specific_interaction_result(result):
                return

    @property
    def current_window(self) -> WindowLevel | None:
        return self._state.window

    @property
    def viewport_size(self) -> tuple[float, float]:
        return self._state.width, self._state.height

    @property
    def inverted(self) -> bool:
        return self._state.inverted

    def apply_window_level(self, result: WindowLevelChange) -> None:
        if result.window == self._state.window and result.inverted == self.inverted:
            return
        logger.debug(f'apply_window_level,{result}')
        self._state = replace(
            self._state,
            window=result.window,
            inverted=result.inverted,
        )
        self.overlayChanged.emit()
        self.request_render()

    def apply_slice_index(self, index: int) -> None:
        if index == self._state.slice_index:
            return
        logger.debug(f'apply_slice_index,{index}')

        self._measure_controller.cancel_transaction()
        self._measure_controller.clear_selection()

        self._state = replace(
            self._state,
            slice_index=index,
        )
        self.request_render()

    @Property(QObject, constant=True)
    def measurementController(self) -> QObject:
        return self._measure_controller

    @Property(int, notify=imageDimensionChanged)
    def imageColumns(self) -> int:
        if self._frame_meta is None:
            return 0

        columns = self._frame_meta.instance_meta.columns
        return columns or 0

    @Property(int, notify=imageDimensionChanged)
    def imageRows(self) -> int:
        if self._frame_meta is None:
            return 0

        rows = self._frame_meta.instance_meta.rows
        return rows or 0

    @Property(float, notify=imageDimensionChanged)
    def imageRowSpacing(self) -> float:
        """返回图像行方向的物理间距，单位为 mm。"""
        if self._frame_meta is None:
            return 1.0

        spacing = self._frame_meta.geometry.pixel_spacing.row
        if not isfinite(spacing) or spacing <= 0:
            return 1.0
        return spacing

    @Property(float, notify=imageDimensionChanged)
    def imageColumnSpacing(self) -> float:
        """返回图像列方向的物理间距，单位为 mm。"""
        if self._frame_meta is None:
            return 1.0

        spacing = self._frame_meta.geometry.pixel_spacing.column
        if not isfinite(spacing) or spacing <= 0:
            return 1.0
        return spacing

    @Property(float, notify=transformChanged)
    def zoom(self) -> float:
        return self._state.zoom

    @Property(float, notify=transformChanged)
    def panX(self) -> float:
        return self._state.pan_x

    @Property(float, notify=transformChanged)
    def panY(self) -> float:
        return self._state.pan_y

    @Property(float, notify=transformChanged)
    def rotationDegrees(self) -> float:
        return self._state.rotation_degrees

    @Property(bool, notify=transformChanged)
    def horizontalFlip(self) -> bool:
        return self._state.horizontal_flip

    @Property(bool, notify=transformChanged)
    def verticalFlip(self) -> bool:
        return self._state.vertical_flip

    def apply_pan(self, x, y):
        self._state = replace(self._state,
                              pan_x=x,
                              pan_y=y
                              )
        self.transformChanged.emit()

    def apply_zoom(self, zoom: float) -> None:
        if not isfinite(zoom):
            return

        zoom = max(0.1, min(zoom, 20.0))

        if abs(zoom - self._state.zoom) < 0.0001:
            return

        self._state = replace(
            self._state,
            zoom=zoom,
        )

        self.transformChanged.emit()

        # overlayInfo 中显示了 zoom，因此也要更新
        self.overlayChanged.emit()

    @Slot(str)
    def applyTransformAction(self, action: str) -> None:
        try:
            transform_action = ViewportTransformAction(action)
        except ValueError:
            logger.warning(
                "Unsupported viewport transform action: %s",
                action,
            )
            return

        state = self._state

        match transform_action:
            case ViewportTransformAction.ROTATE_CLOCKWISE_90:
                next_state = replace(
                    state,
                    rotation_degrees=(
                                             state.rotation_degrees + 90.0
                                     ) % 360.0,
                )

            case ViewportTransformAction.ROTATE_COUNTERCLOCKWISE_90:
                next_state = replace(
                    state,
                    rotation_degrees=(
                                             state.rotation_degrees - 90.0
                                     ) % 360.0,
                )

            case ViewportTransformAction.MIRROR_HORIZONTAL:
                next_state = replace(
                    state,
                    horizontal_flip=not state.horizontal_flip,
                )

            case ViewportTransformAction.MIRROR_VERTICAL:
                next_state = replace(
                    state,
                    vertical_flip=not state.vertical_flip,
                )

        if next_state == state:
            return

        self._state = next_state
        self.transformChanged.emit()

    @Property(str, notify=displayStyleChanged)
    def canvasBackgroundColor(self) -> str:
        return self._state.display_style.no_data_color

    @Slot(float, float)
    def applyWindowPreset(
            self,
            center: float,
            width: float,
    ) -> None:
        window = WindowLevel(
            center=center,
            width=width,
        )

        self._state = replace(
            self._state,
            window=window,
        )

        self.request_render()

    @Slot(bool, float, float, float, float)
    def selectMeasurementAt(
            self,
            image_valid: bool,
            column: float,
            row: float,
            endpoint_tolerance: float,
            line_tolerance: float,
    ) -> None:
        if self._tool_controller.active_interaction not in (
            InteractionType.MEASURE_LENGTH,
            InteractionType.MEASURE_ANGLE,
        ):
            return

        point = None
        if image_valid and isfinite(column) and isfinite(row):
            point = ImagePoint(column=column, row=row)
        if self._state.slice_index is not None:
            self._measure_controller.tap_at(
                point,
                slice_index=self._state.slice_index,
                endpoint_tolerance=endpoint_tolerance,
                line_tolerance=line_tolerance,
            )

    @Property("QVariantMap", constant=True)
    def crosshairStyle(self) -> dict:
        return {
            "centerGap": 0,
            "lineWidth": 0,
            "horizontalColor": "transparent",
            "verticalColor": "transparent",
        }


    @Property(QPointF, notify=crosshairImagePositionChanged)
    def crosshairImagePosition(self) -> QPointF:
        return QPointF(-1.0, -1.0)
