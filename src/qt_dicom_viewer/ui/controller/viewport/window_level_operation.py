from dataclasses import dataclass
from typing import TYPE_CHECKING

from qt_dicom_viewer.core.dicom_models import Point, WindowLevel, WindowLevelOperationResult, DragUpdateEvent
from qt_dicom_viewer.ui.controller.viewport.drag_operation import DragOperation

if TYPE_CHECKING:
    from qt_dicom_viewer.ui.controller.viewport.viewport_controller import (
        ViewportController,
    )


@dataclass(frozen=True, slots=True)
class WindowLevelInteractionConfig:
    swap_axes: bool = False    # 水平调窗宽，垂直调窗位
    width_direction: float = 1.0   # 向右增大窗宽
    center_direction: float = -1.0   # 屏幕 Y 向下，所以向上提高窗位
    width_sensitivity: float = 1.0
    center_sensitivity: float = 1.0
    minimum_width: float = 1
    minimum_width_control_range: float = 100.0
    max_width_control_range: float = 1000.0
    minimum_center_control_range: float = 100.0
    max_center_control_range: float = 1000.0


DEFAULT_WINDOW_LEVEL_CONFIG = WindowLevelInteractionConfig()


class WindowLevelOperation(DragOperation):
    def __init__(
        self,
        viewport: "ViewportController",
        config: WindowLevelInteractionConfig = DEFAULT_WINDOW_LEVEL_CONFIG,
    ) -> None:
        super().__init__(viewport)

        self._config = config
        self._start_window: WindowLevel | None = None
        self._viewport_width = 1.0
        self._viewport_height = 1.0
        self._start_inverted = False

    def begin(self, position: Point) -> None:
        self._start_window = self.viewport.current_window
        self._start_inverted = self.viewport.inverted

        width, height = self.viewport.viewport_size
        self._viewport_width = max(width, 1.0)
        self._viewport_height = max(height, 1.0)

    def update(
            self,
            drag_event: DragUpdateEvent,
    ) -> None:
        if self._start_window is None:
            return

        config = self._config
        start = self._start_window

        if config.swap_axes:
            width_delta = drag_event.total_offset.y
            center_delta = drag_event.total_offset.x
            width_axis_size = self._viewport_height
            center_axis_size = self._viewport_width
        else:
            width_delta = drag_event.total_offset.x
            center_delta = drag_event.total_offset.y
            width_axis_size = self._viewport_width
            center_axis_size = self._viewport_height


        width_control_range = max(
            start.width,
            config.minimum_width_control_range,
            config.max_width_control_range
        )

        center_control_range = max(
            start.width,
            config.minimum_center_control_range,
            config.max_center_control_range
        )
        # 100 / 视口的宽度 * 灵敏度
        width_step = (
                width_control_range
                / width_axis_size
                * config.width_sensitivity
                * config.width_direction
        )

        center_step = (
                center_control_range
                / center_axis_size
                * config.center_sensitivity
                * config.center_direction
        )

        # 把拖动开始时的 width 恢复为有符号值
        start_signed_width = (
            -start.width
            if self._start_inverted
            else start.width
        )

        signed_width = (
                start_signed_width
                + width_delta * width_step
        )

        window = WindowLevel(
            width=round(
                max(
                    config.minimum_width,
                    abs(signed_width),
                ),
                2,
            ),
            center=round(
                start.center
                + center_delta * center_step,
                2,
            ),
        )

        result = WindowLevelOperationResult(
            window=window,
            inverted=signed_width < 0,
        )

        self.viewport.apply_window_level(result)

    def end(self, position: Point) -> None:
        self._start_window = None

    def cancel(self) -> None:
        self._start_window = None