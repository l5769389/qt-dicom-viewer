from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from qt_dicom_viewer.model import Point, DragUpdateEvent

# TYPE_CHECKING 中的导入只供类型检查器使用，运行时不会导入，因此可以消除循环依赖。
if TYPE_CHECKING:
    from qt_dicom_viewer.ui.controller.viewport.viewport_controller import (
        ViewportController,
    )


class DragOperation(ABC):
    def __init__(self, viewport: "ViewportController") -> None:
        self.viewport = viewport

    @abstractmethod
    def begin(self, position: Point) -> None:
        ...

    @abstractmethod
    def update(self,
                drag_event: DragUpdateEvent
               ) -> None:
        ...

    @abstractmethod
    def end(self, position: Point) -> None:
        ...

    def cancel(self) -> None:
        pass