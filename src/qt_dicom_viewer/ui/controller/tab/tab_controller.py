import logging
import uuid
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
    ToolType,
    TwoDViewType,
    ViewportConfig,
)
from qt_dicom_viewer.core.mpr_rotation import (
    move_mpr_state_center,
    rotate_crosshair_state,
    rotate_mpr_state_3d,
)
from qt_dicom_viewer.model.dicom_core import (
    MprFrame,
    MprState,
    MprViewAnchors,
    Vector3,
)
from qt_dicom_viewer.model.render_models import MprRenderResult
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.tab.tag_controller import TagController
from qt_dicom_viewer.ui.controller.viewport.image_2d.mpr_viewport_controller import (
    MprViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.image_2d.stack_viewport_controller import (
    StackViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import ViewportController
from qt_dicom_viewer.ui.controller.viewport.volume_viewport_controller import VolumeViewportController
from qt_dicom_viewer.model.dicom_models import VolumeViewType
from qt_dicom_viewer.model.render_models import VolumeLoadResult

logger = logging.getLogger(__name__)
class TabController(QObject):
    renderRequested = Signal(object)
    activeToolChanged = Signal(object)
    activeViewportChanged = Signal()

    def __init__(self, tab_config: TabConfig, parent=None, *, tag_controller: TagController | None = None):
        super().__init__(parent)
        self._tab_config = tab_config
        self._tag_controller = tag_controller
        if tag_controller is not None:
            tag_controller.setParent(self)
        self._viewport_dict: dict[str, ViewportController] = {}
        self._create_tool_controller()
        self._series_by_uid: dict[str, SeriesDisplayMeta] = {
            meta.series_uid: meta
            for meta in tab_config.series_metas
        }
        self._active_viewport_id: str = ''
        self._target_mpr_state: MprState | None = None
        self._initial_mpr_state: MprState | None = None
        # 不包含 3D 旋转增量的并行状态，用于只撤销 3D 旋转，
        # 同时保留之后发生的十字线移动和十字线旋转。
        self._mpr_3d_reset_state: MprState | None = None
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


    @Property(QObject, constant=True)
    def tagController(self) -> QObject | None:
        return self._tag_controller

    def _create_tool_controller(self) -> None:
        modality = (
            self._tab_config.series_metas[0].modality
            if self._tab_config.series_metas
            else ""
        )
        self._tool_controller = ToolController(
            tab_type=self._tab_config.tab_type,
            modality=modality,
            parent=self
        )
        self._tool_controller.commandRequested.connect(
            self._handle_tool_command
        )
        self._tool_controller.resetRequested.connect(
            self._handle_tool_reset_requested
        )
        self._last_mpr_projection_settings = (
            self._tool_controller.mpr_projection_settings
        )
        self._tool_controller.mprProjectionChanged.connect(
            self._handle_mpr_projection_changed
        )

    @Slot(str)
    def _handle_tool_command(self, command: str) -> None:
        if command != "viewport:reset":
            logger.warning("Unknown tool command: %s", command)
            return

        viewport = self.activeViewport
        if not isinstance(viewport, ViewportController):
            return

        if (
            isinstance(viewport, MprViewportController)
            and self._initial_mpr_state is not None
        ):
            self._set_target_mpr_state(self._initial_mpr_state)
            self._mpr_3d_reset_state = self._initial_mpr_state
            self._dirty_mpr_viewport_ids.update(
                self._mpr_viewport_ids()
            )
            # 先恢复几何状态并标脏，再重置投影；投影变更信号只会
            # 启动一次使用最终状态的渲染轮次。
            self._tool_controller.resetMprProjection()
            viewport.reset_all_view_state(reset_slice=False)
            self._try_start_next_mpr_render()
            return

        if isinstance(viewport, (StackViewportController, VolumeViewportController)):
            viewport.reset_all_view_state()

    @Slot(str)
    def _handle_tool_reset_requested(self, tool_value: str) -> None:
        try:
            tool_type = ToolType(tool_value)
        except ValueError:
            logger.warning("Unknown reset tool: %s", tool_value)
            return

        if tool_type == ToolType.MPR_ROTATE_3D:
            self._reset_mpr_3d_rotation()
            return

        if tool_type == ToolType.MIP:
            self._tool_controller.resetMprProjection()
            return

        viewport = self.activeViewport
        if isinstance(viewport, (MprViewportController, StackViewportController, VolumeViewportController)):
            viewport.reset_tool_state(tool_type)

    def _reset_mpr_3d_rotation(self) -> None:
        state = self._target_mpr_state
        reset_state = self._mpr_3d_reset_state
        if state is None or reset_state is None:
            return
        if reset_state == state:
            return

        self._set_target_mpr_state(reset_state)
        self._dirty_mpr_viewport_ids.update(
            self._mpr_viewport_ids()
        )
        self._try_start_next_mpr_render()

    @Slot()
    def _handle_mpr_projection_changed(self) -> None:
        previous = self._last_mpr_projection_settings
        current = self._tool_controller.mpr_projection_settings
        self._last_mpr_projection_settings = current

        affected_planes = {
            plane
            for plane in MprPlane
            if (
                previous.effective_projection_for_plane(plane)
                != current.effective_projection_for_plane(plane)
            )
        }
        if not affected_planes:
            return

        self._dirty_mpr_viewport_ids.update(
            viewport_id
            for viewport_id, viewport in self._viewport_dict.items()
            if (
                isinstance(viewport, MprViewportController)
                and viewport.viewport_config.viewport_type in affected_planes
            )
        )
        self._try_start_next_mpr_render()


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
            and self._target_mpr_state is None
            and not self._active_mpr_requests
        ):
            self._request_initial_mpr()
        if self.tab_config.tab_type in (TabType.TWO_D, TabType.THREE_D):
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
            case TabType.THREE_D:
                for series_meta in self._tab_config.series_metas:
                    viewport_id = str(uuid.uuid4())
                    self._active_viewport_id = viewport_id
                    viewport = VolumeViewportController(
                        ViewportConfig(viewport_id, self._tab_config.tab_id,
                                       VolumeViewType.VOLUME, series_meta.series_uid, series_meta),
                        self._tool_controller, parent=self,
                    )
                    self.connect_signal(viewport)
                    self._viewport_dict[viewport_id] = viewport
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
            viewport.crosshairRotationRequested.connect(
                self._handle_crosshair_rotation_requested
            )
            viewport.mpr3DRotationRequested.connect(
                self._handle_mpr_3d_rotation_requested
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
        state = self._target_mpr_state
        if state is None:
            return

        next_state = move_mpr_state_center(
            state,
            center_patient,
        )
        if next_state.frame == state.frame:
            return

        self._set_target_mpr_state(next_state)
        if self._mpr_3d_reset_state is not None:
            self._mpr_3d_reset_state = move_mpr_state_center(
                self._mpr_3d_reset_state,
                center_patient,
            )

        self._dirty_mpr_viewport_ids.update(
            self._mpr_viewport_ids()
        )

        self._try_start_next_mpr_render()

    @Slot(object, float)
    def _handle_crosshair_rotation_requested(
        self,
        source_plane: MprPlane,
        angle_radians: float,
    ) -> None:
        state = self._target_mpr_state
        if state is None:
            return
        next_state = rotate_crosshair_state(
            state,
            source_plane,
            angle_radians,
        )
        self._set_target_mpr_state(next_state)
        if self._mpr_3d_reset_state is not None:
            self._mpr_3d_reset_state = rotate_crosshair_state(
                self._mpr_3d_reset_state,
                source_plane,
                angle_radians,
            )

        # 源视图的 Frame 旋转与 view roll 正好抵消，像素无需重采样。
        self._dirty_mpr_viewport_ids.update(
            viewport_id
            for viewport_id, viewport in self._viewport_dict.items()
            if (
                isinstance(viewport, MprViewportController)
                and viewport.viewport_config.viewport_type != source_plane
            )
        )
        self._try_start_next_mpr_render()

    @Slot(object, float)
    def _handle_mpr_3d_rotation_requested(
        self,
        axis_patient: Vector3,
        angle_radians: float,
    ) -> None:
        state = self._target_mpr_state
        if state is None:
            return
        self._set_target_mpr_state(
            rotate_mpr_state_3d(
                state,
                axis_patient,
                angle_radians,
            )
        )
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
        if isinstance(result, VolumeLoadResult):
            viewport = self._viewport_dict.get(result.viewport_id)
            return isinstance(viewport, VolumeViewportController) and viewport.accepts_result(result)
        if not isinstance(result, MprRenderResult):
            viewport = self._viewport_dict.get(result.viewport_id)
            return viewport is not None and (not isinstance(viewport, StackViewportController)
                                              or viewport.accepts_result(result))

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
            needs_initial_mpr_frame = self._target_mpr_state is None

            viewport.handleRenderResult(result)
            # Bootstrap MPR with the axial view, then render the other views
            # after the first result establishes the shared frame.
            if needs_initial_mpr_frame and result.mpr_frame is not None:
                initial_state = MprState(
                    frame=result.mpr_frame,
                    view_grids=result.mpr_view_grids,
                    view_anchors=(
                        MprViewAnchors.centered(
                            result.mpr_view_grids
                        )
                        if result.mpr_view_grids is not None
                        else None
                    ),
                )
                self._initial_mpr_state = initial_state
                self._mpr_3d_reset_state = initial_state
                self._set_target_mpr_state(initial_state)
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
        viewport = self._viewport_dict.get(failure.viewport_id)
        if isinstance(viewport, VolumeViewportController):
            viewport.handleRenderFailure(failure)
            return
        if isinstance(viewport, StackViewportController):
            viewport.handleRenderFailure(failure)
            return
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

    def dispose(self) -> None:
        if self._tag_controller is not None:
            self._tag_controller.dispose()
        for viewport in self._viewport_dict.values():
            viewport.shutdown()
            if isinstance(viewport, VolumeViewportController):
                viewport.dispose()

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
        if self._target_mpr_state is None:
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
                    mpr_state=self._target_mpr_state,
                    initial=False,
                )
            )

        self._start_mpr_requests(requests)

    def _set_target_mpr_state(self, state: MprState) -> None:
        self._target_mpr_state = state
        for viewport in self._viewport_dict.values():
            if isinstance(viewport, MprViewportController):
                viewport.apply_mpr_state(state)

    @property
    def _target_mpr_frame(self) -> MprFrame | None:
        """兼容旧测试和调试代码；新的单一真值来源是 MprState。"""
        if self._target_mpr_state is None:
            return None
        return self._target_mpr_state.frame
