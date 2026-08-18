from PySide6.QtCore import Signal, QObject, Property, Slot

from qt_dicom_viewer.model import ToolType


class ToolController(QObject):
    activeToolChanged = Signal()


    def __init__(self,default_tool_type:ToolType = ToolType.WINDOW ,parent=None):
        super().__init__(parent)
        self._active_tool = default_tool_type

    @Property(str, notify=activeToolChanged)
    def activeTool(self) -> str:
        return self._active_tool

    @Slot(str)
    def selectTool(self, tool: str) -> None:
        if tool == self._active_tool:
            return

        self._active_tool = tool
        self.activeToolChanged.emit()