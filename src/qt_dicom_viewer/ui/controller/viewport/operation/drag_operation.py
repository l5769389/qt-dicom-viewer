from typing import Protocol

from qt_dicom_viewer.model import DragUpdateEvent, PointerPosition
from qt_dicom_viewer.model.interaction import (
    InteractionResult,
    OperationStartContext,
)


class DragOperation(Protocol):
    def begin(
        self,
        position: PointerPosition,
        context: OperationStartContext | None,
    ) -> InteractionResult | None:
        ...

    def update(
        self,
        drag_event: DragUpdateEvent,
    ) -> InteractionResult | None:
        ...

    def end(
        self,
        position: PointerPosition,
    ) -> InteractionResult | None:
        ...
