import logging
import uuid
from dataclasses import replace
from math import isfinite

from PySide6.QtCore import QObject, Signal, Slot, Property, QPointF

from qt_dicom_viewer.model import ViewportState, ViewportConfig, RenderRequest, RenderResult, \
    WindowLevel, FrameDisplayMeta, ToolType, Point, WindowLevelOperationResult, Offset, DragUpdateEvent, \
    PointerDisplayMeta
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.controller.cursor_controller import CursorController
from qt_dicom_viewer.ui.controller.viewport.controller.overlay_presenter import OverlayPresenter
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation
from qt_dicom_viewer.ui.controller.viewport.operation.scroll_operation import ScrollOperation
from qt_dicom_viewer.ui.controller.viewport.operation.window_level_operation import WindowLevelOperation
from qt_dicom_viewer.utils.utils import _display_text, _display_number

logger = logging.getLogger(__name__)

class ViewportController(QObject):
    renderRequested = Signal(object)
    imageSourceChanged = Signal()
    overlayChanged = Signal()
    imageDimensionChanged = Signal()
    transformChanged = Signal()


    def __init__(self, viewport_config: ViewportConfig, tool_controller: ToolController, parent=None):
        super().__init__(parent)
        self.viewport_config = viewport_config
        self._state = ViewportState()
        self._image_revision = 0
        self._has_image = False
        self._frame_meta: FrameDisplayMeta | None = None

        self._tool_controller = tool_controller
        self._scroll_operation = ScrollOperation(
            threshold=120.0,
        )
        self._cursor_controller = CursorController(viewport_config = self.viewport_config, parent= self)
        self._overlay_presenter = OverlayPresenter()
        self._active_drag_operation: DragOperation | None = None
        self._window_level_operation = WindowLevelOperation(self)

    @Property(QObject, constant=True)
    def cursorController(self):
        return self._cursor_controller


    def request_first_loader(self) -> None:
        request = RenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            slice_index=0,
            window=None,
            inverted=False,
        )
        logger.debug(
            "Render started: request_id=%s viewport_id=%s",
            request.request_id,
            request.viewport_id,
        )
        self.renderRequested.emit(request)

    def request_render(self) -> None:
        request = RenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            slice_index=self._state.slice_index,
            window=self._state.window,
            inverted=self._state.inverted,
        )
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
        self._frame_meta = result.frame_meta
        self._state = replace(
            self._state,
            slice_index=result.frame_meta.slice_index,
            slice_count=result.frame_meta.slice_count,
            window=result.frame_meta.window,
            inverted =result.frame_meta.inverted,
        )
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
            series=series,
            frame=frame,
            state=self._state,
        )

    @Slot(float, float, int)
    def beginInteraction(
            self,
            x: float,
            y: float,
            buttons: int,
    ) -> None:
        logger.debug(f'beginInteraction,{x},{y},{buttons}')
        operation = None

        if self._tool_controller.activeTool == ToolType.WINDOW:
            operation = self._window_level_operation

        self._active_drag_operation = operation

        if operation is not None:
            operation.begin(Point(x, y))

    @Slot(QPointF, QPointF, QPointF, QPointF)
    def updateInteraction(
            self,
            start_point: QPointF,
            current_point: QPointF,
            step_offset: QPointF,
            total_offest: QPointF,
    ) -> None:
        if self._active_drag_operation is None:
            return
        event = DragUpdateEvent(
            start_position=Point(
                x=start_point.x(),
                y=start_point.y()),
            current_position=Point(
                x=current_point.x(),
                y=current_point.y()
            ),
            step_offset=Offset(x=step_offset.x(), y=step_offset.y()),
            total_offset=Offset(x=total_offest.x(), y=total_offest.y())
        )
        self._active_drag_operation.update(event)

    @Slot(float, float)
    def endInteraction(
            self,
            x: float,
            y: float,
    ) -> None:
        ...


    @Slot(QPointF)
    def handlePointerMoved(self, point: QPointF) -> None:
        current_point = Point(
                x=point.x(),
                y=point.y()),
        ...

    @Slot(float, float,float,float, int, int)
    def updateCursorPosition(
            self,
            column: float,
            row: float,
            clipColumn: float,
            clipRow: float,
            column_index: int,
            row_index: int,
    ) -> None:
        self._cursor_controller.updatePosition(clipColumn, clipRow)

    @Slot(float, float, float, float, int)
    def handleWheel(
            self,
            angle_delta_y: float,
            pixel_delta_y: float,
            x: float,
            y: float,
            modifiers: int,
    ) -> None:
        next_index = self._scroll_operation.handle_wheel(
            angle_delta_y=angle_delta_y,
            current_index=self._state.slice_index,
            slice_count=self._state.slice_count,
        )
        if next_index is None:
            return
        logger.debug(f'scroll next_index,{next_index}')
        self._state = replace(
            self._state,
            slice_index=next_index,
        )
        self.request_render()

    @property
    def current_window(self) -> WindowLevel | None:
        return self._state.window

    @property
    def viewport_size(self) -> tuple[float, float]:
        return self._state.width, self._state.height

    @property
    def inverted(self) -> bool:
        return self._state.inverted

    def apply_window_level(self, result: WindowLevelOperationResult) -> None:
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