import pytest

from qt_dicom_viewer.model import InteractionType, TabType
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController


def test_initial_tool_state_opens_window_panel() -> None:
    controller = ToolController()

    assert controller.activeTool == "window"
    assert controller.activeToolLabel == "调窗"
    assert controller.activeToolIcon == "window"
    assert controller.activePanel == "window"
    assert controller.activeInteraction == "window"


def test_interaction_tool_closes_panel_and_selects_interaction() -> None:
    controller = ToolController()

    controller.activateTool("pan")

    assert controller.activeTool == "pan"
    assert controller.activeToolLabel == "平移"
    assert controller.activeToolIcon == "pan"
    assert controller.activePanel == ""
    assert controller.activeInteraction == "pan"


def test_panel_tool_disables_pointer_interaction() -> None:
    controller = ToolController()

    controller.activateTool("rotate")

    assert controller.activeTool == "rotate"
    assert controller.activePanel == "rotate"
    assert controller.activeInteraction == ""


def test_secondary_tool_can_select_concrete_interaction() -> None:
    controller = ToolController()
    controller.activateTool("measure")

    controller.selectInteraction("measure:length")

    assert controller.activeTool == "measure"
    assert controller.activePanel == "measure"
    assert controller.active_interaction is InteractionType.MEASURE_LENGTH


def test_command_preserves_current_tool_state() -> None:
    controller = ToolController()
    commands: list[str] = []
    controller.commandRequested.connect(commands.append)
    controller.activateTool("pan")

    controller.activateTool("reset")

    assert commands == ["viewport:reset"]
    assert controller.activeTool == "pan"
    assert controller.activePanel == ""
    assert controller.activeInteraction == "pan"


def test_active_tool_exposes_and_requests_its_scoped_reset() -> None:
    controller = ToolController()
    resets: list[str] = []
    controller.resetRequested.connect(resets.append)
    controller.activateTool("pan")

    assert controller.resetLabel == "重置平移"
    assert controller.canResetActiveTool is True

    controller.resetActiveTool()

    assert resets == ["pan"]


def test_tool_without_reset_content_disables_scoped_reset() -> None:
    controller = ToolController()
    resets: list[str] = []
    controller.resetRequested.connect(resets.append)
    controller.activateTool("annotate")

    assert controller.resetLabel == "暂无可重置内容"
    assert controller.canResetActiveTool is False

    controller.resetActiveTool()

    assert resets == []


def test_mpr_3d_rotation_is_a_primary_interaction_tool() -> None:
    controller = ToolController(tab_type=TabType.MPR)

    controller.activateTool("mpr-rotate-3d")

    assert controller.activeTool == "mpr-rotate-3d"
    assert controller.activePanel == ""
    assert controller.active_interaction is InteractionType.MPR_ROTATE_3D
    assert controller.activeInteraction == "mpr:rotate3d"
    assert any(
        tool["iconName"] == "rotate-3d"
        and tool["toolType"] == "mpr-rotate-3d"
        for tool in controller.tools
    )
    assert all(
        action["action"] != "mpr:rotate3d"
        for action in controller.rotateActions
    )


def test_mpr_3d_rotation_is_hidden_outside_mpr_tabs() -> None:
    controller = ToolController(tab_type=TabType.TWO_D)

    assert all(
        tool["toolType"] != "mpr-rotate-3d"
        for tool in controller.tools
    )

    controller.activateTool("mpr-rotate-3d")

    assert controller.activeTool == "window"
    assert controller.activeInteraction == "window"


def test_services_are_available_as_a_primary_panel_only_tool_in_2d() -> None:
    controller = ToolController(tab_type=TabType.TWO_D)
    assert any(tool["toolType"] == "service" and tool["iconName"] == "service"
               for tool in controller.tools)
    assert controller.serviceActions == [
        {"action": "service:mtf", "label": "MTF", "iconName": "mtf"},
        {"action": "service:qa", "label": "QA", "iconName": "qa"},
    ]

    controller.activateTool("service")

    assert controller.activeToolLabel == "服务"
    assert controller.activeToolIcon == "service"
    assert controller.activePanel == "service"
    assert controller.activeInteraction == ""
    assert controller.activeService == ""
    assert not controller.canResetActiveTool


@pytest.mark.parametrize("action", ["service:mtf", "service:qa"])
def test_service_selection_restores_corresponding_interaction_without_commands(action) -> None:
    controller = ToolController(tab_type=TabType.TWO_D)
    commands, resets, selections = [], [], []
    controller.commandRequested.connect(commands.append)
    controller.resetRequested.connect(resets.append)
    controller.activeServiceChanged.connect(lambda: selections.append(controller.activeService))
    controller.activateTool("measure")
    controller.selectInteraction("measure:rect")

    controller.selectService(action)
    controller.selectService(action)
    controller.resetActiveTool()

    assert controller.activeTool == controller.activePanel == "service"
    assert controller.activeService == action
    expected = InteractionType.SERVICE_MTF if action == "service:mtf" else InteractionType.NONE
    assert controller.active_interaction is expected
    assert selections == [action]
    assert commands == []
    assert resets == (["service"] if action == "service:mtf" else [])

    # 离开后重新打开面板保留入口选择，但不改变其他工具的行为。
    controller.activateTool("pan")
    assert controller.activeInteraction == "pan"
    controller.activateTool("service")
    assert controller.activeService == action
    assert controller.activeInteraction == expected.value


def test_unknown_service_entry_is_ignored() -> None:
    controller = ToolController()
    controller.selectService("measure:rect")
    assert controller.activeTool == "window"
    assert controller.activeInteraction == "window"
    assert controller.activeService == ""


def test_global_reset_remains_available_from_services() -> None:
    controller = ToolController(tab_type=TabType.TWO_D)
    commands = []
    controller.commandRequested.connect(commands.append)
    controller.selectService("service:mtf")
    controller.activateTool("reset")
    assert commands == ["viewport:reset"]
    assert controller.activePanel == "service"
    assert controller.activeService == "service:mtf"
    assert controller.activeInteraction == "service:mtf"


@pytest.mark.parametrize("tab_type", [TabType.MPR, TabType.THREE_D, TabType.FOUR_D, TabType.TAG])
def test_services_are_hidden_and_cannot_be_selected_outside_2d(tab_type) -> None:
    controller = ToolController(tab_type=tab_type)
    assert all(tool["toolType"] != "service" for tool in controller.tools)
    events = []
    controller.activeToolChanged.connect(lambda: events.append("tool"))
    controller.activePanelChanged.connect(lambda: events.append("panel"))
    controller.activeServiceChanged.connect(lambda: events.append("service"))
    controller.activeInteractionChanged.connect(lambda: events.append("interaction"))
    controller.commandRequested.connect(events.append)
    controller.resetRequested.connect(events.append)

    controller.activateTool("service")
    controller.selectService("service:mtf")
    controller.selectService("service:qa")

    assert controller.activeTool == controller.activePanel == "window"
    assert controller.activeInteraction == "window"
    assert controller.activeService == ""
    assert events == []
