from dataclasses import dataclass

from qt_dicom_viewer.model import ToolType, ToolBehavior, InteractionType, ToolPanelType


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    tool_type: ToolType
    label: str
    icon_name: str
    behavior: ToolBehavior

    interaction_tool: InteractionType | None = None
    panel: ToolPanelType = ToolPanelType.NONE
    command: str | None = None


TOOL_CATALOG: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        tool_type=ToolType.WINDOW,
        label="调窗",
        icon_name="window",
        behavior=ToolBehavior.INTERACTION_PANEL,
        interaction_tool=InteractionType.WINDOW,
        panel=ToolPanelType.WINDOW,
    ),
    ToolDefinition(
        tool_type=ToolType.SCROLL,
        label="翻页",
        icon_name="scroll",
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.SCROLL,
    ),
    ToolDefinition(
        tool_type=ToolType.PAN,
        label="平移",
        icon_name="pan",
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.PAN,
    ),
    ToolDefinition(
        tool_type=ToolType.ZOOM,
        label="缩放",
        icon_name="zoom",
        behavior=ToolBehavior.INTERACTION,
        interaction_tool=InteractionType.ZOOM,
    ),
    ToolDefinition(
        tool_type=ToolType.ROTATE,
        label="旋转",
        icon_name="rotate",
        behavior=ToolBehavior.PANEL,
        panel=ToolPanelType.ROTATE,
    ),
    ToolDefinition(
        tool_type=ToolType.ANNOTATE,
        label="标注",
        icon_name="annotate",
        behavior=ToolBehavior.INTERACTION_PANEL,
        panel=ToolPanelType.ANNOTATE,
    ),
    ToolDefinition(
        tool_type=ToolType.RESET,
        label="重置",
        icon_name="reset",
        behavior=ToolBehavior.COMMAND,
        command="viewport:reset",
    ),
)

TOOL_DEFINITIONS: dict[ToolType, ToolDefinition] = {
    definition.tool_type: definition
    for definition in TOOL_CATALOG
}

@dataclass(frozen=True, slots=True)
class ToolActionDefinition:
    action: str
    label: str
    icon_name: str


ROTATE_ACTIONS = (
    ToolActionDefinition(
        action="rotate:mirror-h",
        label="水平镜像",
        icon_name="mirror-h",
    ),
    ToolActionDefinition(
        action="rotate:mirror-v",
        label="垂直镜像",
        icon_name="mirror-v",
    ),
    ToolActionDefinition(
        action="rotate:cw90",
        label="顺时针旋转 90°",
        icon_name="rotate-cw90",
    ),
    ToolActionDefinition(
        action="rotate:ccw90",
        label="逆时针旋转 90°",
        icon_name="rotate-ccw90",
    ),
)