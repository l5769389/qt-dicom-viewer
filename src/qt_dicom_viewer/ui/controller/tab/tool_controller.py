import logging

from PySide6.QtCore import Slot, Property, Signal, QObject

from qt_dicom_viewer.model import (
    InteractionType,
    TabType,
    ToolBehavior,
    ToolType,
)
from qt_dicom_viewer.model.tool_catalog import (
    ROTATE_ACTIONS,
    TOOL_CATALOG,
    TOOL_DEFINITIONS, MEASURE_ACTIONS,
)
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS

logger = logging.getLogger(__name__)


class ToolController(QObject):
    activeToolChanged = Signal()
    activePanelChanged = Signal()
    activeInteractionChanged = Signal()
    commandRequested = Signal(str)
    resetRequested = Signal(str)

    def __init__(
            self,
            parent=None,
            *,
            tab_type: TabType | None = None,
    ):
        super().__init__(parent)

        self._tab_type = tab_type
        self._active_tool = ToolType.WINDOW
        self._active_panel: ToolType | None = ToolType.WINDOW
        self._active_interaction = InteractionType.WINDOW

    @Property(str, notify=activeToolChanged)
    def activeTool(self) -> str:
        return self._active_tool

    @Property(str, notify=activeToolChanged)
    def activeToolLabel(self) -> str:
        definition = TOOL_DEFINITIONS.get(self._active_tool)
        return "" if definition is None else definition.label

    @Property(str, notify=activeToolChanged)
    def activeToolIcon(self) -> str:
        definition = TOOL_DEFINITIONS.get(self._active_tool)
        return "" if definition is None else definition.icon_name

    @Property(str, notify=activePanelChanged)
    def activePanel(self) -> str:
        return self._active_panel.value if self._active_panel is not None else ""

    @Property(str, notify=activeInteractionChanged)
    def activeInteraction(self) -> str:
        return self._active_interaction.value

    @property
    def active_interaction(self) -> InteractionType:
        return self._active_interaction

    @Property(str, notify=activeToolChanged)
    def resetLabel(self) -> str:
        definition = TOOL_DEFINITIONS.get(self._active_tool)
        if definition is None or definition.reset_label is None:
            return "暂无可重置内容"
        return definition.reset_label

    @Property(bool, notify=activeToolChanged)
    def canResetActiveTool(self) -> bool:
        definition = TOOL_DEFINITIONS.get(self._active_tool)
        return (
            definition is not None
            and definition.reset_label is not None
        )

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
        if (
            self._tab_type is not None
            and definition.supported_tab_types is not None
            and self._tab_type not in definition.supported_tab_types
        ):
            logger.warning(
                "Tool %s is not available for tab type %s",
                tool_type.value,
                self._tab_type.value,
            )
            return

        match definition.behavior:
            case ToolBehavior.INTERACTION:
                self._set_active_tool(definition.tool_type)
                self._set_active_interaction(definition.default_interaction)
                self._set_active_panel(None)

            case ToolBehavior.INTERACTION_PANEL:
                self._set_active_tool(definition.tool_type)
                self._set_active_interaction(definition.default_interaction)
                self._set_active_panel(definition.tool_type)

            case ToolBehavior.PANEL:
                self._set_active_tool(definition.tool_type)
                self._set_active_interaction(definition.default_interaction)
                self._set_active_panel(definition.tool_type)

            case ToolBehavior.COMMAND:
                if definition.command is not None:
                    self.commandRequested.emit(definition.command)

    @Slot(str)
    def selectInteraction(self, interaction_value: str) -> None:
        try:
            interaction = InteractionType(interaction_value)
        except ValueError:
            logger.warning("Unknown interaction type: %s", interaction_value)
            return

        self._set_active_interaction(interaction)

    @Slot()
    def resetActiveTool(self) -> None:
        if not self.canResetActiveTool:
            return
        self.resetRequested.emit(self._active_tool.value)

    def _set_active_tool(self, tool: ToolType | None) -> None:
        if tool is None or tool == self._active_tool:
            return

        self._active_tool = tool
        self.activeToolChanged.emit()

    def _set_active_panel(self, panel: ToolType | None) -> None:
        if panel == self._active_panel:
            return

        self._active_panel = panel
        self.activePanelChanged.emit()

    def _set_active_interaction(self, interaction: InteractionType) -> None:
        if interaction == self._active_interaction:
            return

        self._active_interaction = interaction
        self.activeInteractionChanged.emit()

    @Property(list, constant=True)
    def windowPresets(self) -> list[dict]:
        return build_window_presets()

    @Property(list, constant=True)
    def tools(self) -> list[dict]:
        return build_tool_items(self._tab_type)

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

    @Property(list, constant=True)
    def measureActions(self) -> list[dict]:
        return [
            {
                "action": item.action,
                "label": item.label,
                "iconName": item.icon_name,
            }
            for item in MEASURE_ACTIONS
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


def build_tool_items(
        tab_type: TabType | None = None,
) -> list[dict]:
    return [
        {
            "toolType": definition.tool_type.value,
            "label": definition.label,
            "iconName": definition.icon_name,
            "behavior": definition.behavior.value,
        }
        for definition in TOOL_CATALOG
        if (
            definition.supported_tab_types is None
            or tab_type is None
            or tab_type in definition.supported_tab_types
        )
    ]
