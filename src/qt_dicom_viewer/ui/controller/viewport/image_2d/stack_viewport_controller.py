import logging
import uuid
from dataclasses import replace

from qt_dicom_viewer.model import (
    RenderRequest,
    RenderResult,
    StackRenderRequest,
    StackRenderResult,
    TwoDViewType,
    ViewportConfig,
)
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from .image_2d_viewport_controller import (
    Image2DViewportController,
)

logger = logging.getLogger(__name__)
class StackViewportController(Image2DViewportController):
    def __init__(
        self,
        viewport_config: ViewportConfig,
        tool_controller: ToolController,
        parent=None,
    ) -> None:
        if viewport_config.viewport_type != TwoDViewType.STACK:
            raise ValueError(
                "StackViewportController requires a stack viewport config"
            )
        super().__init__(viewport_config, tool_controller, parent)

    def _initial_slice_index(self) -> int:
        return 0

    def apply_slice_index(self, index: int) -> None:
        if not self._prepare_slice_index_change(index):
            return
        self._state = replace(
            self._state,
            slice_index=index,
        )
        self.request_render()


    def _build_render_request(self, *, initial: bool) -> RenderRequest:
        state = self.viewport_state
        return StackRenderRequest(
            request_id=str(uuid.uuid4()),
            viewport_id=self.viewport_config.viewport_id,
            series_uid=self.viewport_config.series_uid,
            slice_index=(
                0
                if initial or state.slice_index is None
                else state.slice_index
            ),
            window=None if initial else state.window,
            inverted=False if initial else state.inverted,
        )

    def _validate_render_result(self, result: RenderResult) -> None:
        if not isinstance(result, StackRenderResult):
            raise TypeError(
                "StackViewportController requires StackRenderResult"
            )
        if result.view_type != TwoDViewType.STACK:
            raise ValueError("Stack render result has an invalid view type")

    def _apply_specific_render_result(self, result: RenderResult) -> None:
        return None
