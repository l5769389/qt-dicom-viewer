from dataclasses import dataclass

from .dicom_models import ToolType
from .ui_models import InteractionType, ToolBehavior


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    tool_type: ToolType  # 一级工具类型
    label: str           # 一级工具名称
    icon_name: str       #  icon样子
    behavior: ToolBehavior   #是打开面板不触发功能， 还是触发长期功能。 还是及触发面板又触发功能。 还是一次性指令。

    default_interaction: InteractionType = InteractionType.NONE
    command: str | None = None


TOOL_CATALOG: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        tool_type=ToolType.WINDOW,
        label="调窗",
        icon_name="window",
        behavior=ToolBehavior.INTERACTION_PANEL,
        default_interaction=InteractionType.WINDOW,
    ),
    ToolDefinition(
        tool_type=ToolType.SCROLL,
        label="翻页",
        icon_name="scroll",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.SCROLL,
    ),
    ToolDefinition(
        tool_type=ToolType.PAN,
        label="平移",
        icon_name="pan",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.PAN,
    ),
    ToolDefinition(
        tool_type=ToolType.ZOOM,
        label="缩放",
        icon_name="zoom",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.ZOOM,
    ),
    ToolDefinition(
        tool_type=ToolType.MEASURE,
        label="测量",
        icon_name="measure",
        behavior=ToolBehavior.PANEL,
        default_interaction=InteractionType.MEASURE_LENGTH,
    ),
    ToolDefinition(
        tool_type=ToolType.ROTATE,
        label="旋转",
        icon_name="rotate",
        behavior=ToolBehavior.PANEL,
    ),
    ToolDefinition(
        tool_type=ToolType.ANNOTATE,
        label="标注",
        icon_name="annotate",
        behavior=ToolBehavior.INTERACTION_PANEL,
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
