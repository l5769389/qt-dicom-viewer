from qt_dicom_viewer.model import InteractionType
from qt_dicom_viewer.ui.controller.tab.tool_controller import ToolController


def test_initial_tool_state_opens_window_panel() -> None:
    controller = ToolController()

    assert controller.activeTool == "window"
    assert controller.activePanel == "window"
    assert controller.activeInteraction == "window"


def test_interaction_tool_closes_panel_and_selects_interaction() -> None:
    controller = ToolController()

    controller.activateTool("pan")

    assert controller.activeTool == "pan"
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
