import logging
from dataclasses import replace
from math import isfinite

from PySide6.QtCore import Slot, Property, Signal, QObject

from qt_dicom_viewer.model import (
    InteractionType,
    MprPlane,
    MprProjectionMode,
    MprProjectionSettings,
    TabType,
    ToolBehavior,
    ToolType,
)
from qt_dicom_viewer.model.tool_catalog import (
    MEASURE_ACTIONS,
    ROTATE_ACTIONS,
    SERVICE_ACTIONS,
    TOOL_CATALOG,
    TOOL_DEFINITIONS,
)
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS

logger = logging.getLogger(__name__)


class ToolController(QObject):
    activeToolChanged = Signal()
    activePanelChanged = Signal()
    activeInteractionChanged = Signal()
    activeServiceChanged = Signal()
    commandRequested = Signal(str)
    resetRequested = Signal(str)
    mprProjectionChanged = Signal()

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
        self._active_service = ""
        self._mpr_projection_settings = MprProjectionSettings()

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

    @Property(str, notify=activeServiceChanged)
    def activeService(self) -> str:
        return self._active_service

    @Property(bool, notify=mprProjectionChanged)
    def mprProjectionEnabled(self) -> bool:
        return self._mpr_projection_settings.enabled

    @Property(str, notify=mprProjectionChanged)
    def mprProjectionMode(self) -> str:
        return self._mpr_projection_settings.mode.value

    @Property("QVariantMap", notify=mprProjectionChanged)
    def mprThicknesses(self) -> dict:
        settings = self._mpr_projection_settings
        return {
            MprPlane.AXIAL.value: settings.axial_thickness_mm,
            MprPlane.CORONAL.value: settings.coronal_thickness_mm,
            MprPlane.SAGITTAL.value: settings.sagittal_thickness_mm,
        }

    @property
    def mpr_projection_settings(self) -> MprProjectionSettings:
        return self._mpr_projection_settings

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

    @Slot(str)
    def selectService(self, action: str) -> None:
        """选择服务入口，但不启动绘制、计算或其他视口操作。"""
        if action not in {item.action for item in SERVICE_ACTIONS}:
            logger.warning("Unknown service entry: %s", action)
            return

        self.activateTool(ToolType.SERVICE.value)
        # 不能通过二级入口绕过一级工具的视图类型限制。
        if self._active_tool != ToolType.SERVICE:
            return
        if action == self._active_service:
            return
        self._active_service = action
        self.activeServiceChanged.emit()

    @Slot(bool)
    def setMprProjectionEnabled(self, enabled: bool) -> None:
        if not self._supports_mpr_projection():
            return
        self._set_mpr_projection_settings(
            replace(self._mpr_projection_settings, enabled=bool(enabled))
        )

    @Slot(str)
    def setMprProjectionMode(self, mode_value: str) -> None:
        if not self._supports_mpr_projection():
            return
        try:
            mode = MprProjectionMode(mode_value)
        except ValueError:
            logger.warning("Unknown MPR projection mode: %s", mode_value)
            return
        self._set_mpr_projection_settings(
            replace(self._mpr_projection_settings, mode=mode)
        )

    @Slot(str, float)
    def setMprThickness(self, plane_value: str, thickness: float) -> None:
        if not self._supports_mpr_projection() or not isfinite(thickness):
            return
        try:
            plane = MprPlane(plane_value)
        except ValueError:
            logger.warning("Unknown MPR projection plane: %s", plane_value)
            return

        value = min(100, max(0, int(round(thickness))))
        field_name = f"{plane.value}_thickness_mm"
        self._set_mpr_projection_settings(
            replace(
                self._mpr_projection_settings,
                **{field_name: value},
            )
        )

    @Slot()
    def resetMprProjection(self) -> None:
        if not self._supports_mpr_projection():
            return
        self._set_mpr_projection_settings(MprProjectionSettings())

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

    def _supports_mpr_projection(self) -> bool:
        return self._tab_type in (None, TabType.MPR)

    def _set_mpr_projection_settings(
        self,
        settings: MprProjectionSettings,
    ) -> None:
        if settings == self._mpr_projection_settings:
            return
        self._mpr_projection_settings = settings
        self.mprProjectionChanged.emit()

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

    @Property(list, constant=True)
    def serviceActions(self) -> list[dict]:
        return [
            {
                "action": item.action,
                "label": item.label,
                "iconName": item.icon_name,
            }
            for item in SERVICE_ACTIONS
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
