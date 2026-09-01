import numpy as np
import pytest

from qt_dicom_viewer.model import (
    CrosshairCenterChange,
    FrameDisplayMeta,
    ImageGeometryMeta,
    ImagePoint,
    InstanceDisplayMeta,
    MprFrame,
    MprImageGeometry,
    MprPlane,
    MprRenderRequest,
    MprRenderResult,
    PixelSpacing,
    SeriesDisplayMeta,
    StackRenderRequest,
    StackRenderResult,
    RenderFailure,
    TabConfig,
    TabType,
    TwoDViewType,
    ViewportConfig,
    WindowLevel,
)
from qt_dicom_viewer.ui.controller.tab.tab_controller import TabController
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController
from qt_dicom_viewer.ui.controller.viewport.image_2d.mpr_viewport_controller import (
    MprViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.image_2d.stack_viewport_controller import (
    StackViewportController,
)
from qt_dicom_viewer.ui.controller.viewport.viewport_controller import (
    ViewportController,
)


def _series_meta() -> SeriesDisplayMeta:
    return SeriesDisplayMeta(
        patient_name="Example Patient",
        patient_id="P001",
        study_description="Study",
        series_description="Series",
        modality="CT",
        series_uid="series-1",
    )


def _viewport_config(viewport_type) -> ViewportConfig:
    series_meta = _series_meta()
    return ViewportConfig(
        viewport_id=f"viewport-{viewport_type.value}",
        tab_id="tab-1",
        viewport_type=viewport_type,
        series_uid=series_meta.series_uid,
        series_meta=series_meta,
    )


def _frame_meta() -> FrameDisplayMeta:
    return FrameDisplayMeta(
        slice_index=2,
        slice_count=5,
        window=WindowLevel(center=40.0, width=400.0),
        inverted=False,
        instance_meta=InstanceDisplayMeta(
            instance_number=None,
            sop_instance_uid=None,
            manufacturer=None,
            kvp=None,
            tube_current_ma=None,
            slice_thickness=None,
            rows=3,
            columns=4,
            pixel_spacing=(2.0, 3.0),
            image_position=None,
            slice_location=None,
        ),
        geometry=ImageGeometryMeta(
            rows=3,
            columns=4,
            pixel_spacing=PixelSpacing(row=2.0, column=3.0),
            image_position_patient=(10.0, 20.0, 30.0),
            image_orientation_patient=None,
        ),
    )


def _mpr_geometry(frame: MprFrame) -> MprImageGeometry:
    return MprImageGeometry(
        rows=3,
        columns=4,
        row_spacing=2.0,
        column_spacing=3.0,
        navigation_spacing=1.0,
        frame=frame,
        image_origin_mpr=(0.0, 0.0, 0.0),
        row_direction_mpr=(0.0, 1.0, 0.0),
        column_direction_mpr=(1.0, 0.0, 0.0),
        navigation_direction_mpr=(0.0, 0.0, 1.0),
    )


def _mpr_result(
    controller: MprViewportController,
    frame: MprFrame,
    response_id: str = "request-1",
) -> MprRenderResult:
    geometry = _mpr_geometry(frame)
    return MprRenderResult(
        response_id=response_id,
        viewport_id=controller.viewport_config.viewport_id,
        series_uid=controller.viewport_config.series_uid,
        view_type=controller.viewport_config.viewport_type,
        image=np.zeros((3, 4), dtype=np.uint8),
        modality_pixel=np.zeros((3, 4), dtype=np.float32),
        frame_meta=_frame_meta(),
        mpr_frame=frame,
        plane_geometry=geometry,
    )


def test_concrete_controllers_share_the_root_type() -> None:
    stack = StackViewportController(
        _viewport_config(TwoDViewType.STACK),
        ToolController(),
    )
    mpr = MprViewportController(
        _viewport_config(MprPlane.AXIAL),
        ToolController(),
    )

    assert isinstance(stack, ViewportController)
    assert isinstance(mpr, ViewportController)


def test_concrete_controllers_reject_mismatched_configs() -> None:
    with pytest.raises(ValueError):
        StackViewportController(
            _viewport_config(MprPlane.AXIAL),
            ToolController(),
        )
    with pytest.raises(ValueError):
        MprViewportController(
            _viewport_config(TwoDViewType.STACK),
            ToolController(),
        )


def test_concrete_controllers_build_typed_requests() -> None:
    stack = StackViewportController(
        _viewport_config(TwoDViewType.STACK),
        ToolController(),
    )
    mpr = MprViewportController(
        _viewport_config(MprPlane.CORONAL),
        ToolController(),
    )
    stack_requests = []
    mpr_requests = []
    stack.renderRequested.connect(stack_requests.append)
    mpr.renderRequested.connect(mpr_requests.append)

    stack.request_first_loader()
    mpr.request_first_loader()

    assert isinstance(stack_requests[0], StackRenderRequest)
    assert stack_requests[0].slice_index == 0
    assert isinstance(mpr_requests[0], MprRenderRequest)
    assert mpr_requests[0].plane == MprPlane.CORONAL
    assert mpr_requests[0].mpr_frame is None


def test_concrete_controllers_reject_wrong_result_types() -> None:
    stack = StackViewportController(
        _viewport_config(TwoDViewType.STACK),
        ToolController(),
    )
    mpr = MprViewportController(
        _viewport_config(MprPlane.AXIAL),
        ToolController(),
    )
    frame = MprFrame.standard_lps((10.0, 20.0, 30.0))
    mpr_result = _mpr_result(mpr, frame)
    stack_result = StackRenderResult(
        response_id="request-2",
        viewport_id=mpr.viewport_config.viewport_id,
        series_uid=mpr.viewport_config.series_uid,
        view_type=TwoDViewType.STACK,
        image=None,
        modality_pixel=None,
        frame_meta=_frame_meta(),
    )
    stack_state = stack.viewport_state
    mpr_state = mpr.viewport_state

    with pytest.raises(TypeError):
        stack.handleRenderResult(
            MprRenderResult(
                response_id=mpr_result.response_id,
                viewport_id=stack.viewport_config.viewport_id,
                series_uid=mpr_result.series_uid,
                view_type=mpr_result.view_type,
                image=mpr_result.image,
                modality_pixel=mpr_result.modality_pixel,
                frame_meta=mpr_result.frame_meta,
                mpr_frame=mpr_result.mpr_frame,
                plane_geometry=mpr_result.plane_geometry,
            )
        )
    with pytest.raises(TypeError):
        mpr.handleRenderResult(stack_result)

    assert stack.viewport_state == stack_state
    assert mpr.viewport_state == mpr_state


def test_stack_exposes_safe_empty_crosshair_properties() -> None:
    stack = StackViewportController(
        _viewport_config(TwoDViewType.STACK),
        ToolController(),
    )

    assert stack.crosshairImagePosition.x() == -1.0
    assert stack.crosshairImagePosition.y() == -1.0
    assert stack.crosshairStyle["lineWidth"] == 0


def test_mpr_crosshair_uses_the_viewports_geometry() -> None:
    mpr = MprViewportController(
        _viewport_config(MprPlane.AXIAL),
        ToolController(),
    )
    frame = MprFrame.standard_lps((10.0, 20.0, 30.0))
    centers = []
    mpr.crosshairCenterChangeRequested.connect(centers.append)
    mpr.handleRenderResult(_mpr_result(mpr, frame))

    assert mpr.crosshairImagePosition.x() == 0.0
    assert mpr.crosshairImagePosition.y() == 0.0

    handled = mpr._apply_specific_interaction_result(
        CrosshairCenterChange(ImagePoint(column=2.0, row=1.0))
    )

    assert handled is True
    assert centers == [(16.0, 22.0, 30.0)]


def test_tab_creates_specific_controller_types() -> None:
    stack_tab = TabController(
        TabConfig("stack-tab", "Stack", TabType.TWO_D, (_series_meta(),))
    )
    mpr_tab = TabController(
        TabConfig("mpr-tab", "MPR", TabType.MPR, (_series_meta(),))
    )

    assert all(
        isinstance(viewport, StackViewportController)
        for viewport in stack_tab.viewports_by_id.values()
    )
    assert all(
        isinstance(viewport, MprViewportController)
        for viewport in mpr_tab.viewports_by_id.values()
    )


def test_tab_updates_shared_frame_and_rerenders_all_mpr_views() -> None:
    tab = TabController(
        TabConfig("mpr-tab", "MPR", TabType.MPR, (_series_meta(),))
    )
    axial = next(
        viewport
        for viewport in tab.viewports_by_id.values()
        if viewport.viewport_config.viewport_type == MprPlane.AXIAL
    )
    assert isinstance(axial, MprViewportController)
    requests = []
    tab.renderRequested.connect(requests.append)

    initial_frame = MprFrame.standard_lps((10.0, 20.0, 30.0))
    tab.init_render()
    assert len(requests) == 1
    initial_request = requests.pop()
    tab.handleRenderResult(
        _mpr_result(
            axial,
            initial_frame,
            initial_request.request_id,
        )
    )

    assert len(requests) == 2
    for request in list(requests):
        viewport = tab.viewports_by_id[request.viewport_id]
        assert isinstance(viewport, MprViewportController)
        tab.handleRenderResult(
            _mpr_result(
                viewport,
                initial_frame,
                request.request_id,
            )
        )
    requests.clear()

    axial.crosshairCenterChangeRequested.emit((11.0, 22.0, 33.0))

    assert tab._target_mpr_frame is not None
    assert tab._target_mpr_frame.center_patient == (11.0, 22.0, 33.0)
    assert len(requests) == 3
    assert all(isinstance(request, MprRenderRequest) for request in requests)
    assert all(
        request.mpr_frame is not None
        and request.mpr_frame.center_patient == (11.0, 22.0, 33.0)
        for request in requests
    )


def test_mpr_render_coalesces_drag_updates_to_the_latest_frame() -> None:
    tab = TabController(
        TabConfig("mpr-tab", "MPR", TabType.MPR, (_series_meta(),))
    )
    requests = []
    tab.renderRequested.connect(requests.append)
    initial_frame = MprFrame.standard_lps((10.0, 20.0, 30.0))

    tab.init_render()
    initial_request = requests.pop()
    axial = tab.viewports_by_id[initial_request.viewport_id]
    assert isinstance(axial, MprViewportController)
    tab.handleRenderResult(
        _mpr_result(axial, initial_frame, initial_request.request_id)
    )
    for request in list(requests):
        viewport = tab.viewports_by_id[request.viewport_id]
        assert isinstance(viewport, MprViewportController)
        tab.handleRenderResult(
            _mpr_result(viewport, initial_frame, request.request_id)
        )
    requests.clear()

    axial.crosshairCenterChangeRequested.emit((11.0, 21.0, 31.0))
    active_requests = list(requests)
    axial.crosshairCenterChangeRequested.emit((12.0, 22.0, 32.0))
    axial.crosshairCenterChangeRequested.emit((13.0, 23.0, 33.0))

    assert requests == active_requests
    for request in active_requests:
        viewport = tab.viewports_by_id[request.viewport_id]
        assert isinstance(viewport, MprViewportController)
        tab.handleRenderResult(
            _mpr_result(
                viewport,
                request.mpr_frame,
                request.request_id,
            )
        )

    next_requests = requests[len(active_requests):]
    assert len(next_requests) == 3
    assert all(
        request.mpr_frame is not None
        and request.mpr_frame.center_patient == (13.0, 23.0, 33.0)
        for request in next_requests
    )


def test_mpr_single_view_invalidation_starts_one_request() -> None:
    tab = TabController(
        TabConfig("mpr-tab", "MPR", TabType.MPR, (_series_meta(),))
    )
    requests = []
    tab.renderRequested.connect(requests.append)
    initial_frame = MprFrame.standard_lps((10.0, 20.0, 30.0))

    tab.init_render()
    initial_request = requests.pop()
    axial = tab.viewports_by_id[initial_request.viewport_id]
    assert isinstance(axial, MprViewportController)
    tab.handleRenderResult(
        _mpr_result(axial, initial_frame, initial_request.request_id)
    )
    for request in list(requests):
        viewport = tab.viewports_by_id[request.viewport_id]
        assert isinstance(viewport, MprViewportController)
        tab.handleRenderResult(
            _mpr_result(viewport, initial_frame, request.request_id)
        )
    requests.clear()

    axial.request_render()

    assert len(requests) == 1
    assert requests[0].viewport_id == axial.viewport_config.viewport_id


def test_mpr_failure_finishes_the_active_round() -> None:
    tab = TabController(
        TabConfig("mpr-tab", "MPR", TabType.MPR, (_series_meta(),))
    )
    requests = []
    tab.renderRequested.connect(requests.append)

    tab.init_render()
    request = requests[0]
    tab.handleRenderFailure(
        RenderFailure(
            request_id=request.request_id,
            viewport_id=request.viewport_id,
            error=RuntimeError("failed"),
        )
    )

    assert tab._active_mpr_requests == {}
