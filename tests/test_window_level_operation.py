from qt_dicom_viewer.model import (
    DragUpdateEvent,
    Offset,
    Point,
    PointerPosition,
    WindowLevel,
)
from qt_dicom_viewer.model.interaction import WindowLevelContext
from qt_dicom_viewer.ui.controller.viewport.operation.window_level_operation import (
    WindowLevelOperation,
)


def _pointer(x: float, y: float) -> PointerPosition:
    return PointerPosition(
        viewport=Point(x=x, y=y),
        image=None,
    )


def test_default_window_level_drag_direction_matches_viewer_convention() -> None:
    """向右增大窗宽，向下减小窗位（即向上增大窗位）。"""
    operation = WindowLevelOperation()
    start = _pointer(50.0, 50.0)
    operation.begin(
        start,
        WindowLevelContext(
            viewport_size=(100.0, 100.0),
            inverted=False,
            current_window=WindowLevel(center=40.0, width=400.0),
        ),
    )

    result = operation.update(
        DragUpdateEvent(
            start_position=start,
            current_position=_pointer(60.0, 60.0),
            step_offset=Offset(x=10.0, y=10.0),
            total_offset=Offset(x=10.0, y=10.0),
        )
    )

    assert result is not None
    assert result.window.width > 400.0
    assert result.window.center < 40.0
