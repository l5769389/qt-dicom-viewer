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
    PLACEHOLDER_TOOLS,
    ROTATE_ACTIONS,
    SERVICE_ACTIONS,
    TOOL_CATALOG,
    TOOL_DEFINITIONS,
)
from qt_dicom_viewer.preset import CT_WINDOW_PRESETS
from qt_dicom_viewer.ui.controller.settings_controller import resolve_settings

logger = logging.getLogger(__name__)

MONTAGE_TOOL_TYPES = frozenset((
    ToolType.WINDOW,
    ToolType.PAN,
    ToolType.ZOOM,
    ToolType.ROTATE,
    ToolType.INVERT,
    ToolType.RESET,
))


class ToolController(QObject):
    activeToolChanged = Signal()
    activePanelChanged = Signal()
    activeInteractionChanged = Signal()
    activeServiceChanged = Signal()
    serviceSelected = Signal(str)
    commandRequested = Signal(str)
    resetRequested = Signal(str)
    resetStateChanged = Signal()
    mprProjectionChanged = Signal()
    windowPresetsChanged = Signal()

    def __init__(
            self,
            parent=None,
            *,
            tab_type: TabType | None = None,
            modality: str = "",
    ):
        super().__init__(parent)

        self._settings_controller = resolve_settings(parent)
        self._settings_controller.changed.connect(self.windowPresetsChanged.emit)
        self._tab_type = tab_type
        self._modality = modality.strip().upper()
        self._active_tool = ToolType.WINDOW
        self._active_panel: ToolType | None = ToolType.WINDOW
        self._active_interaction = InteractionType.WINDOW
        if tab_type == TabType.PETCT_FUSION:
            self._active_tool = self._active_panel = ToolType.CT_WINDOW
        self._active_service = ""
        self._mpr_projection_settings = MprProjectionSettings()
        self._locked_tool: ToolType | None = None
        if tab_type == TabType.THREE_D:
            self._active_tool = ToolType.VOLUME_ROTATE
            self._active_panel = None
            self._active_interaction = InteractionType.VOLUME_ROTATE
        self.activeToolChanged.connect(self.resetStateChanged.emit)
        self.activeServiceChanged.connect(self.resetStateChanged.emit)

    @Property(str, notify=activeToolChanged)
    def activeTool(self) -> str:
        return self._active_tool

    @Property(str, notify=activeToolChanged)
    def activeToolLabel(self) -> str:
        if self._modality == "PT" and self._active_tool == ToolType.WINDOW:
            return "PET 强度"
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

    @Property(str, notify=resetStateChanged)
    def resetLabel(self) -> str:
        if self._modality == "PETCT3D" and self._active_tool == ToolType.VOLUME_PRESET:
            return "重置三维显示"
        if self._modality == "PT" and self._active_tool == ToolType.WINDOW:
            return "重置 PET 强度"
        if self._active_tool == ToolType.SERVICE and self._active_service == "service:mtf":
            return "重置 MTF"
        if self._active_tool == ToolType.SERVICE and self._active_service == "service:qa":
            return "重置水模 QA"
        definition = TOOL_DEFINITIONS.get(self._active_tool)
        if definition is None or definition.reset_label is None:
            return "暂无可重置内容"
        return definition.reset_label

    @Property(bool, notify=resetStateChanged)
    def canResetActiveTool(self) -> bool:
        if self._active_tool == ToolType.SERVICE:
            return self._active_service in ("service:mtf", "service:qa")
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

        if (
            self._locked_tool is not None
            and tool_type != self._locked_tool
        ):
            return

        definition = TOOL_DEFINITIONS.get(tool_type)
        if definition is None:
            logger.warning("Missing tool definition: %s", tool_type.value)
            return
        if not definition.enabled:
            return
        if not tool_available(tool_type, self._tab_type, self._modality):
            logger.warning(
                "Tool %s is not available for tab type %s",
                tool_type.value,
                self._tab_type.value if self._tab_type is not None else "any",
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
                # 3D windowing is drag-only; do not open the 2D preset panel.
                self._set_active_panel(None if self._tab_type == TabType.THREE_D
                                       and tool_type == ToolType.WINDOW else definition.tool_type)

            case ToolBehavior.PANEL:
                self._set_active_tool(definition.tool_type)
                self._set_active_interaction(
                    InteractionType(self._active_service)
                    if tool_type == ToolType.SERVICE and self._active_service in ("service:mtf", "service:qa")
                    else definition.default_interaction)
                self._set_active_panel(definition.tool_type)

            case ToolBehavior.COMMAND | ToolBehavior.TOGGLE:
                if definition.command is not None:
                    self.commandRequested.emit(definition.command)

    @Slot(str)
    def selectInteraction(self, interaction_value: str) -> None:
        if self._locked_tool is not None:
            return
        try:
            interaction = InteractionType(interaction_value)
        except ValueError:
            logger.warning("Unknown interaction type: %s", interaction_value)
            return

        if self._modality == "PETCT3D" and interaction not in (
            InteractionType.PAN, InteractionType.ZOOM, InteractionType.VOLUME_ROTATE,
        ):
            return
        if self._tab_type == TabType.THREE_D and interaction not in (
            InteractionType.PAN, InteractionType.ZOOM, InteractionType.VOLUME_ROTATE, InteractionType.WINDOW,
            InteractionType.VOLUME_CROP,
        ):
            return
        if interaction in (InteractionType.SERVICE_MTF, InteractionType.SERVICE_QA):
            self.selectService(interaction.value)
            return
        if (
            self._tab_type == TabType.MONTAGE
            and interaction not in {
                InteractionType.WINDOW,
                InteractionType.PAN,
                InteractionType.ZOOM,
            }
        ):
            logger.warning(
                "Interaction %s is not available for montage tabs",
                interaction.value,
            )
            return

        self._set_active_interaction(interaction)

    def lock_to_tool(self, tool: ToolType | None) -> None:
        self._locked_tool = tool

    @Slot(str)
    def selectService(self, action: str) -> None:
        """MTF 绘制矩形，QA 自动识别并支持拖动已有 ROI。"""
        if action not in {item.action for item in SERVICE_ACTIONS}:
            logger.warning("Unknown service entry: %s", action)
            return

        self.activateTool(ToolType.SERVICE.value)
        # 不能通过二级入口绕过一级工具的视图类型限制。
        if self._active_tool != ToolType.SERVICE:
            return
        if action != self._active_service:
            self._active_service = action
            self.activeServiceChanged.emit()
        self._set_active_interaction(InteractionType(action) if action in ("service:mtf", "service:qa")
                                     else InteractionType.NONE)
        self.serviceSelected.emit(action)

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
        return self._tab_type in (None, TabType.MPR, TabType.FOUR_D)

    def _set_mpr_projection_settings(
        self,
        settings: MprProjectionSettings,
    ) -> None:
        if settings == self._mpr_projection_settings:
            return
        self._mpr_projection_settings = settings
        self.mprProjectionChanged.emit()

    @Property(QObject, constant=True)
    def settingsController(self):
        return self._settings_controller

    @Property(list, notify=windowPresetsChanged)
    def windowPresets(self) -> list[dict]:
        return [] if self._modality == "PT" else self._settings_controller.window_presets

    @Property(list, constant=True)
    def tools(self) -> list[dict]:
        return build_tool_items(self._tab_type, self._modality)

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


def build_window_presets(modality: str = "") -> list[dict]:
    presets = () if modality.upper() == "PT" else CT_WINDOW_PRESETS
    return [
        {
            "presetId": preset.preset_id,
            "label": preset.label,
            "center": preset.center,
            "width": preset.width,
        }
        for preset in presets
    ]


def build_tool_items(
        tab_type: TabType | None = None,
        modality: str = "",
) -> list[dict]:
    items = [
        {
            "toolType": definition.tool_type.value,
            "label": (
                "PET 强度"
                if modality.upper() == "PT"
                and definition.tool_type == ToolType.WINDOW
                else "三维显示" if modality == "PETCT3D" and definition.tool_type == ToolType.VOLUME_PRESET
                else definition.label
            ),
            "iconName": definition.icon_name,
            "behavior": definition.behavior.value,
            "available": definition.enabled,
            "enabled": definition.enabled,
        }
        for definition in TOOL_CATALOG
        if tool_available(definition.tool_type, tab_type, modality)
    ]
    if tab_type == TabType.PETCT_FUSION:
        priority = {"ct-window": 0, "pet-window": 1, "pseudocolor": 2, "fusion-blend": 3, "registration": 4}
        items.sort(key=lambda item: priority.get(item["toolType"], 5))
    placeholders = [
        {"toolType": item.key, "label": item.label, "iconName": item.key,
         "behavior": "placeholder", "available": False}
        for item in PLACEHOLDER_TOOLS if tab_type in item.supported_tab_types and modality != "PETCT3D"
    ]
    # 重置始终位于最后；未实现入口不会改变工具控制器的状态或触发命令。
    reset_index = next((i for i, item in enumerate(items)
                        if item["toolType"] == "reset"), len(items))
    return items[:reset_index] + placeholders + items[reset_index:]


def tool_available(
    tool: ToolType,
    tab_type: TabType | None,
    modality: str = "",
) -> bool:
    if modality == "PETCT3D":
        return tool in (ToolType.PAN, ToolType.ZOOM, ToolType.VOLUME_ROTATE,
                        ToolType.VOLUME_DIRECTION, ToolType.VOLUME_PRESET, ToolType.RESET)
    if tab_type == TabType.PETCT_FUSION:
        return tool in (ToolType.REGISTRATION, ToolType.FUSION_BLEND, ToolType.CT_WINDOW, ToolType.PET_WINDOW, ToolType.SCROLL,
                        ToolType.PAN, ToolType.ZOOM, ToolType.MEASURE, ToolType.ROTATE,
                        ToolType.ANNOTATE, ToolType.PSEUDOCOLOR, ToolType.VIEWPORT_SETTINGS,
                        ToolType.RESET)
    if modality.upper() == "PT" and tool in (ToolType.SERVICE, ToolType.MIP):
        return False
    if tab_type == TabType.MONTAGE:
        return tool in MONTAGE_TOOL_TYPES
    if tab_type == TabType.THREE_D:
        return tool in (ToolType.WINDOW, ToolType.PAN, ToolType.ZOOM, ToolType.VOLUME_ROTATE,
                        ToolType.VOLUME_DIRECTION, ToolType.VOLUME_PRESET, ToolType.VOLUME_BED,
                        ToolType.VOLUME_CROP, ToolType.RESET)
    supported = TOOL_DEFINITIONS[tool].supported_tab_types
    return tab_type is None or supported is None or tab_type in supported
