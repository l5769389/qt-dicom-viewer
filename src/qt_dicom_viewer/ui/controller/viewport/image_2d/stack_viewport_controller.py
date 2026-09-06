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
from qt_dicom_viewer.ui.controller.viewport.controller.mtf_controller import MtfController
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
        self._mtf_controller = MtfController(self)
        self.transformChanged.connect(self._mtf_controller.roiController.clearHover)

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
            window=(None if initial else self._pet_display.target.window
                    if self.isPetViewport and self._pet_display.target else state.window),
            inverted=False if initial else state.inverted,
            value_unit=self.pet_active_unit_id or None,
        )

    def _validate_render_result(self, result: RenderResult) -> None:
        if not isinstance(result, StackRenderResult):
            raise TypeError(
                "StackViewportController requires StackRenderResult"
            )
        if result.view_type != TwoDViewType.STACK:
            raise ValueError("Stack render result has an invalid view type")

    def _apply_specific_render_result(self, result: RenderResult) -> None:
        self._mtf_controller.set_frame(result.series_uid, result.frame_meta, result.modality_pixel)
