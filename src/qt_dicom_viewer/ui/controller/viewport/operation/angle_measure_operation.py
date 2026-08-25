from qt_dicom_viewer.model import PointerPosition, InteractionResult, DragUpdateEvent, OperationStartContext
from qt_dicom_viewer.ui.controller.viewport.operation.drag_operation import DragOperation


class AngleMeasureOperation(DragOperation):
    def begin(self, position: PointerPosition, context: OperationStartContext | None) -> InteractionResult | None:
        pass

    def update(self, drag_event: DragUpdateEvent) -> InteractionResult | None:
        pass

    def end(self, position: PointerPosition) -> InteractionResult | None:
        pass

    def __init__(
            self,
    ) -> None:
        super().__init__()
