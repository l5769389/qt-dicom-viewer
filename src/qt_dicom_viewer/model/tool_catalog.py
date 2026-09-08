from dataclasses import dataclass

from .dicom_models import TabType, ToolType
from .ui_models import InteractionType, ToolBehavior


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    tool_type: ToolType  # 一级工具类型
    label: str           # 一级工具名称
    icon_name: str       #  icon样子
    behavior: ToolBehavior   #是打开面板不触发功能， 还是触发长期功能。 还是及触发面板又触发功能。 还是一次性指令。

    default_interaction: InteractionType = InteractionType.NONE
    command: str | None = None
    supported_tab_types: frozenset[TabType] | None = None
    reset_label: str | None = None
    enabled: bool = True


TOOL_CATALOG: tuple[ToolDefinition, ...] = (
    ToolDefinition(ToolType.SEGMENTATION, "阈值分割", "segmentation", ToolBehavior.INTERACTION_PANEL,
                   InteractionType.SEGMENTATION, supported_tab_types=frozenset((TabType.MPR,))),
    ToolDefinition(ToolType.VOI, "VOI", "voi", ToolBehavior.INTERACTION_PANEL,
                   InteractionType.VOI, supported_tab_types=frozenset((TabType.MPR,))),
    ToolDefinition(
        tool_type=ToolType.WINDOW,
        label="调窗",
        icon_name="window",
        behavior=ToolBehavior.INTERACTION_PANEL,
        default_interaction=InteractionType.WINDOW,
        reset_label="重置调窗",
    ),
    ToolDefinition(
        tool_type=ToolType.SCROLL,
        label="翻页",
        icon_name="scroll",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.SCROLL,
        reset_label="重置翻页",
    ),
    ToolDefinition(
        tool_type=ToolType.PAN,
        label="平移",
        icon_name="pan",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.PAN,
        reset_label="重置平移",
    ),
    ToolDefinition(
        tool_type=ToolType.ZOOM,
        label="缩放",
        icon_name="zoom",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.ZOOM,
        reset_label="重置缩放",
    ),
    ToolDefinition(
        tool_type=ToolType.MEASURE,
        label="测量",
        icon_name="measure",
        behavior=ToolBehavior.PANEL,
        default_interaction=InteractionType.MEASURE_LENGTH,
        reset_label="重置测量",
    ),
    ToolDefinition(
        tool_type=ToolType.ROTATE,
        label="旋转",
        icon_name="rotate",
        behavior=ToolBehavior.PANEL,
        reset_label="重置旋转",
    ),
    ToolDefinition(
        tool_type=ToolType.MIP,
        label="MIP",
        icon_name="mip",
        behavior=ToolBehavior.PANEL,
        supported_tab_types=frozenset((TabType.MPR, TabType.FOUR_D)),
        reset_label="重置 MIP",
    ),
    ToolDefinition(
        tool_type=ToolType.INVERT,
        label="反色（暂未实现）",
        icon_name="invert",
        behavior=ToolBehavior.COMMAND,
        supported_tab_types=frozenset((TabType.MONTAGE,)),
        enabled=False,
    ),
    ToolDefinition(
        tool_type=ToolType.MPR_ROTATE_3D,
        label="3D 旋转",
        icon_name="rotate-3d",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.MPR_ROTATE_3D,
        supported_tab_types=frozenset((TabType.MPR, TabType.FOUR_D)),
        reset_label="重置 3D 旋转",
    ),
    ToolDefinition(
        tool_type=ToolType.VOLUME_ROTATE,
        label="旋转",
        icon_name="rotate-3d",
        behavior=ToolBehavior.INTERACTION,
        default_interaction=InteractionType.VOLUME_ROTATE,
        supported_tab_types=frozenset((TabType.THREE_D,)),
        reset_label="重置旋转",
    ),
    ToolDefinition(
        tool_type=ToolType.VOLUME_DIRECTION,
        label="方向",
        icon_name="volume-direction",
        behavior=ToolBehavior.PANEL,
        default_interaction=InteractionType.VOLUME_ROTATE,
        supported_tab_types=frozenset((TabType.THREE_D,)),
        reset_label="重置方向",
    ),
    ToolDefinition(
        tool_type=ToolType.VOLUME_PRESET,
        label="模板",
        icon_name="palette",
        behavior=ToolBehavior.PANEL,
        default_interaction=InteractionType.VOLUME_ROTATE,
        supported_tab_types=frozenset((TabType.THREE_D,)),
        reset_label="重置模板",
    ),
    ToolDefinition(
        tool_type=ToolType.VOLUME_BED,
        label="去床板",
        icon_name="remove-bed",
        behavior=ToolBehavior.TOGGLE,
        command="volume:toggle-bed",
        supported_tab_types=frozenset((TabType.THREE_D,)),
    ),
    ToolDefinition(
        tool_type=ToolType.VOLUME_CROP,
        label="分割",
        icon_name="segmentation",
        behavior=ToolBehavior.INTERACTION_PANEL,
        default_interaction=InteractionType.VOLUME_CROP,
        supported_tab_types=frozenset((TabType.THREE_D,)),
        reset_label="重置裁剪",
    ),
    ToolDefinition(
        tool_type=ToolType.ANNOTATE,
        label="标注",
        icon_name="annotate",
        behavior=ToolBehavior.INTERACTION_PANEL,
        default_interaction=InteractionType.ANNOTATE_ARROW,
        supported_tab_types=frozenset((TabType.TWO_D, TabType.MPR, TabType.FOUR_D)),
        reset_label="重置标注",
    ),
    ToolDefinition(
        tool_type=ToolType.PSEUDOCOLOR,
        label="伪彩",
        icon_name="pseudocolor",
        behavior=ToolBehavior.PANEL,
        supported_tab_types=frozenset((TabType.TWO_D, TabType.MPR, TabType.FOUR_D)),
        reset_label="重置伪彩",
    ),
    ToolDefinition(
        tool_type=ToolType.VIEWPORT_SETTINGS,
        label="视口",
        icon_name="viewport-settings",
        behavior=ToolBehavior.PANEL,
        supported_tab_types=frozenset((TabType.TWO_D, TabType.MPR, TabType.FOUR_D)),
        reset_label="重置视口设置",
    ),
    ToolDefinition(
        tool_type=ToolType.PLAY,
        label="播放",
        icon_name="cine-play",
        behavior=ToolBehavior.PANEL,
        supported_tab_types=frozenset((TabType.FOUR_D,)),
    ),
    ToolDefinition(
        tool_type=ToolType.SERVICE,
        label="服务",
        icon_name="service",
        behavior=ToolBehavior.PANEL,
        supported_tab_types=frozenset((TabType.TWO_D,)),
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
class PlaceholderToolDefinition:
    """仅用于展示的规划入口，不注册为可执行工具。"""

    key: str
    label: str
    supported_tab_types: frozenset[TabType]


PLACEHOLDER_TOOLS: tuple[PlaceholderToolDefinition, ...] = ()

@dataclass(frozen=True, slots=True)
class ToolActionDefinition:
    action: str
    label: str
    icon_name: str


# 服务入口分别启动手动 MTF ROI 和自动水模 QA。
SERVICE_ACTIONS = (
    ToolActionDefinition(action="service:mtf", label="MTF", icon_name="mtf"),
    ToolActionDefinition(action="service:qa", label="QA", icon_name="qa"),
)


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

MEASURE_ACTIONS = (
    ToolActionDefinition(
        action= InteractionType.MEASURE_LENGTH,
        label="长度",
        icon_name="measure-line",
    ),
    ToolActionDefinition(
        action=InteractionType.MEASURE_ANGLE,
        label="角度",
        icon_name="measure-angle",
    ),
    ToolActionDefinition(
        action=InteractionType.MEASURE_RECT,
        label="矩形",
        icon_name="measure-rect",
    ),
    ToolActionDefinition(
        action=InteractionType.MEASURE_ELLIPSE,
        label="椭圆",
        icon_name="measure-ellipse",
    ),
)
