import logging

from PySide6.QtCore import Slot, Property, Signal, QObject

from qt_dicom_viewer.model import (
    InteractionType,
    ToolBehavior,
    ToolPanelType,
    TOOL_DEFINITIONS,
    ToolType,
)
from qt_dicom_viewer.model.tool_catalog import TOOL_CATALOG, ROTATE_ACTIONS
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS

logger = logging.getLogger(__name__)


class ToolController(QObject):
    activeToolChanged = Signal()
    activePanelChanged = Signal()
    commandRequested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._active_tool = ToolType.WINDOW
        self._active_panel = ToolPanelType.WINDOW

    @Property(str, notify=activeToolChanged)
    def activeTool(self) -> str:
        return self._active_tool.value

    @Property(str, notify=activePanelChanged)
    def activePanel(self) -> str:
        return self._active_panel.value

    @Slot(str)
    def activateTool(self, tool_value: str) -> None:
        try:
            tool_type = ToolType(tool_value)
        except ValueError:
            logger.warning("Unknown tool type: %s", tool_value)
            return

        definition = TOOL_DEFINITIONS.get(tool_type)
        if definition is None:
            logger.warning("Missing tool definition: %s", tool_type.value)
            return

        match definition.behavior:
            case ToolBehavior.INTERACTION:
                self._set_active_tool(definition.interaction_tool)
                self._set_active_panel(ToolPanelType.NONE)

            case ToolBehavior.INTERACTION_PANEL:
                self._set_active_tool(definition.interaction_tool)
                self._set_active_panel(definition.panel)

            case ToolBehavior.PANEL:
                next_panel = (
                    ToolPanelType.NONE
                    if self._active_panel == definition.panel
                    else definition.panel
                )
                self._set_active_panel(next_panel)

            case ToolBehavior.COMMAND:
                self._set_active_panel(ToolPanelType.WINDOW)

                if definition.command is not None:
                    self.commandRequested.emit(definition.command)

    def _set_active_tool(self, tool: InteractionType | None) -> None:
        if tool is None or tool == self._active_tool:
            return

        self._active_tool = tool
        self.activeToolChanged.emit()

    def _set_active_panel(self, panel: ToolPanelType) -> None:
        if panel == self._active_panel:
            return

        self._active_panel = panel
        self.activePanelChanged.emit()

    @Property(list, constant=True)
    def windowPresets(self) -> list[dict]:
        return build_window_presets()

    @Property(list, constant=True)
    def tools(self) -> list[dict]:
        return build_tool_items()

    @Property(list, constant=True)
    def rotateActions(self) -> list[dict]:
        return [
            {
                "action": item.action,
                "label": item.label,
                "iconName": item.icon_name,
            }
            for item in ROTATE_ACTIONS
        ]


def build_window_presets() -> list[dict]:
    return [
        {
            "presetId": preset.preset_id,
            "label": preset.label,
            "center": preset.center,
            "width": preset.width,
        }
        for preset in CT_WINDOW_PRESETS
    ]


def build_tool_items() -> list[dict]:
    return [
        {
            "toolType": definition.tool_type.value,
            "label": definition.label,
            "iconName": definition.icon_name,
            "behavior": definition.behavior.value,
        }
        for definition in TOOL_CATALOG
    ]
