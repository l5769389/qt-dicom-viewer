import logging
import uuid
from dataclasses import replace
from types import MappingProxyType

from PySide6.QtCore import QObject, Signal, Slot, Property

from qt_dicom_viewer.model import (
    MprPlane,
    MprRenderRequest,
    RenderFailure,
    RenderRequest,
    RenderResult,
    SeriesDisplayMeta,
    TabConfig,
    TabType,
    TwoDViewType,
    ViewportConfig,
)
from qt_dicom_viewer.model.dicom_core import MprFrame, Vector3
from qt_dicom_viewer.model.render_models import MprRenderResult
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.image_2d.mpr_viewport_controller import (
    MprViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.image_2d.stack_viewport_controller import (
    StackViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController

logger = logging.getLogger(__name__)
class TabController(QObject):
    renderRequested = Signal(object)
    activeToolChanged = Signal(object)
    activeViewportChanged = Signal()

    def __init__(self, tab_config: TabConfig,parent = None):
        super().__init__(parent)
        self._tab_config = tab_config
        self._viewport_dict: dict[str, ViewportController] = {}
        self._create_tool_controller()
        self._series_by_uid: dict[str, SeriesDisplayMeta] = {
            meta.series_uid: meta
            for meta in tab_config.series_metas
        }
        self._active_viewport_id: str = ''
        self._target_mpr_frame: MprFrame | None = None
        self._dirty_mpr_viewport_ids: set[str] = set()
        # request_id: viewport_id
        self._active_mpr_requests: dict[str, str] = {}
        self._create_viewport_dict()

    @Property(str, notify=activeToolChanged)
    def activeTool(self):
        return self._tool_controller.activeTool


    @Property(QObject, notify=activeViewportChanged)
    def activeViewport(self):
        if self._active_viewport_id == '':
            return None
        return self._viewport_dict.get(self._active_viewport_id)

    @Property(QObject,constant= True)
    def toolController(self) -> QObject:
        return self._tool_controller


    def _create_tool_controller(self) -> None:
        self._tool_controller = ToolController(
            parent=self
        )


    def _request_initial_mpr(self) -> None:
        for viewport in self._viewport_dict.values():
            if (
                isinstance(viewport, MprViewportController)
                and viewport.viewport_config.viewport_type == MprPlane.AXIAL
            ):
                request = viewport.build_mpr_render_request(
                    mpr_frame=None,
                    initial=True,
                )
                self._start_mpr_requests([request])
                return


    def init_render(self):
        if (
            self.tab_config.tab_type == TabType.MPR
            and self._target_mpr_frame is None
            and not self._active_mpr_requests
        ):
            self._request_initial_mpr()
        if self.tab_config.tab_type == TabType.TWO_D:
            for viewport in self._viewport_dict.values():
                viewport.request_first_loader()


    # MappingProxyType 可以防止 Workspace 意外修改 Tab 内部字典：
    @property
    def viewports_by_id(self) -> MappingProxyType[str,ViewportController]:
        return MappingProxyType(
            self._viewport_dict
        )

    def _create_viewport_dict(self) -> None:
        match self._tab_config.tab_type:
            case TabType.TWO_D:
                for series_meta in self._tab_config.series_metas:
                    viewport_id = str(uuid.uuid4())
                    self._active_viewport_id = viewport_id
                    viewport = StackViewportController(
                        viewport_config=ViewportConfig(
                            viewport_id,
                            tab_id=self._tab_config.tab_id,
                            viewport_type=TwoDViewType.STACK,
                            series_uid=series_meta.series_uid,
                            series_meta=series_meta,
                        ),
                        tool_controller=self._tool_controller,
                        parent=self
                    )
                    self.connect_signal(viewport)
                    self._viewport_dict[viewport_id] = viewport
            case TabType.MPR:
                    for series_meta in self._tab_config.series_metas:
                        for view_type in [MprPlane.AXIAL, MprPlane.SAGITTAL, MprPlane.CORONAL]:
                            viewport_id = str(uuid.uuid4())
                            if view_type == MprPlane.AXIAL:
                                self._active_viewport_id = viewport_id
                            viewport = MprViewportController(
                                viewport_config=ViewportConfig(
                                    viewport_id,
                                    tab_id=self._tab_config.tab_id,
                                    viewport_type=view_type,
                                    series_uid=series_meta.series_uid,
                                    series_meta=series_meta,
                                ),
                                tool_controller=self._tool_controller,
                                parent=self
                            )
                            self.connect_signal(viewport)
                            self._viewport_dict[viewport_id] = viewport


    def connect_signal(self, viewport: ViewportController):
        if isinstance(viewport, MprViewportController):
            viewport.crosshairCenterChangeRequested.connect(
                self._handle_crosshair_center_change_requested
            )
            viewport.renderInvalidated.connect(
                self._handle_mpr_viewport_invalidated
            )
            return

        viewport.renderRequested.connect(
            self._handle_render_requested
        )

    @Slot(str)
    def _handle_mpr_viewport_invalidated(
            self,
            viewport_id: str,
    ) -> None:
        viewport = self._viewport_dict.get(viewport_id)
        if not isinstance(viewport, MprViewportController):
            return

        self._dirty_mpr_viewport_ids.add(viewport_id)
        self._try_start_next_mpr_render()

    @Slot(object)
    def _handle_crosshair_center_change_requested(
            self,
            center_patient: Vector3,
    ) -> None:
        frame = self._target_mpr_frame
        if frame is None:
            return

        next_frame = replace(
            frame,
            center_patient=center_patient,
        )

        if next_frame == frame:
            return

        self._target_mpr_frame = next_frame

        self._dirty_mpr_viewport_ids.update(
            self._mpr_viewport_ids()
        )

        self._try_start_next_mpr_render()

    @Slot(object)
    def _handle_render_requested(
            self,
            request: RenderRequest,
    ) -> None:
        if request.viewport_id not in self._viewport_dict:
            logger.warning(
                "Reject request from unknown viewport: %s",
                request.viewport_id,
            )
            return

        self.renderRequested.emit(request)

    def accepts_render_result(self, result: RenderResult) -> bool:
        if not isinstance(result, MprRenderResult):
            return result.viewport_id in self._viewport_dict

        return (
            self._active_mpr_requests.get(result.response_id)
            == result.viewport_id
        )

    @Slot(object)
    def handleRenderResult(self, result: RenderResult) -> None:
        viewport = self._viewport_dict.get(result.viewport_id)
        if viewport is None:
            logger.warning(
                "Cannot route render result to unknown viewport: "
                "tab_id=%s viewport_id=%s",
                self._tab_config.tab_id,
                result.viewport_id,
            )
            return

        if isinstance(result, MprRenderResult):
            expected_viewport_id = self._active_mpr_requests.get(
                result.response_id
            )
            if expected_viewport_id != result.viewport_id:
                logger.debug(
                    "Discard stale MPR result: request_id=%s "
                    "viewport_id=%s",
                    result.response_id,
                    result.viewport_id,
                )
                return

            self._active_mpr_requests.pop(result.response_id)
            needs_initial_mpr_frame = self._target_mpr_frame is None

            viewport.handleRenderResult(result)
            # Bootstrap MPR with the axial view, then render the other views
            # after the first result establishes the shared frame.
            if needs_initial_mpr_frame and result.mpr_frame is not None:
                self._target_mpr_frame = result.mpr_frame
                self._mark_other_mpr_viewports_dirty(result.viewport_id)

            if not self._active_mpr_requests:
                self._try_start_next_mpr_render()
            return

        viewport.handleRenderResult(result)

    def _mark_other_mpr_viewports_dirty(
            self,
            excluded_viewport_id: str,
    ) -> None:
        self._dirty_mpr_viewport_ids.update(
            viewport_id
            for viewport_id in self._mpr_viewport_ids()
            if viewport_id != excluded_viewport_id
        )

    @Slot(object)
    def handleRenderFailure(self, failure: RenderFailure) -> None:
        expected_viewport_id = self._active_mpr_requests.get(
            failure.request_id
        )
        if expected_viewport_id != failure.viewport_id:
            return

        self._active_mpr_requests.pop(failure.request_id)
        logger.error(
            "MPR render failed: request_id=%s viewport_id=%s: %s",
            failure.request_id,
            failure.viewport_id,
            failure.error,
        )
        if not self._active_mpr_requests:
            self._try_start_next_mpr_render()


    def contains_viewport(self, viewport_id: str) -> bool:
        return viewport_id in self._viewport_dict

    @property
    def tab_config(self) -> TabConfig:
        return self._tab_config


    @Slot(str)
    def activateViewport(self, activeViewportId: str) -> None:
        if activeViewportId not in self._viewport_dict:
            logger.warning(
                "Cannot activate unknown viewport: viewport_id=%s",
                activeViewportId,
            )
            return

        if self._active_viewport_id == activeViewportId:
            return

        self._active_viewport_id = activeViewportId
        self.activeViewportChanged.emit()

    def _mpr_viewport_ids(self) -> list[str]:
        return [
            viewport_id
            for viewport_id, viewport in self._viewport_dict.items()
            if isinstance(viewport, MprViewportController)
        ]

    def _start_mpr_requests(
        self,
        requests: list[MprRenderRequest],
    ) -> None:
        if not requests:
            return
        if self._active_mpr_requests:
            raise RuntimeError(
                "Cannot start an MPR render while another round is active"
            )

        self._active_mpr_requests = {
            request.request_id: request.viewport_id
            for request in requests
        }
        for request in requests:
            self.renderRequested.emit(request)



    def _try_start_next_mpr_render(self) -> None:
        # Start a new round only when the previous round is complete,
        # at least one viewport is dirty, and a shared frame is available.
        if self._active_mpr_requests:
            return
        if not self._dirty_mpr_viewport_ids:
            return
        if self._target_mpr_frame is None:
            return

        viewport_ids = set(self._dirty_mpr_viewport_ids)
        self._dirty_mpr_viewport_ids.clear()

        requests: list[MprRenderRequest] = []

        for viewport_id, viewport in self._viewport_dict.items():
            if viewport_id not in viewport_ids:
                continue
            if not isinstance(viewport, MprViewportController):
                continue

            requests.append(
                viewport.build_mpr_render_request(
                    mpr_frame=self._target_mpr_frame,
                    initial=False,
                )
            )

        self._start_mpr_requests(requests)
