from PySide6.QtCore import QObject, Property, Signal

from qt_dicom_viewer.model import RenderResult, ViewportConfig


class ViewportController(QObject):
    """所有 viewport controller 的最小 Qt 接口。"""

    renderRequested = Signal(object)
    viewportTypeChanged = Signal()

    def __init__(
        self,
        viewport_config: ViewportConfig,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.viewport_config = viewport_config

    @Property(str, constant=True)
    def viewportId(self) -> str:
        return self.viewport_config.viewport_id

    @Property(str, notify=viewportTypeChanged)
    def viewportType(self) -> str:
        return self.viewport_config.viewport_type.value

    @Property(str, constant=True)
    def viewportRole(self):
        return self.viewport_config.role

    @Property(QObject, constant=True)
    def reconstructionController(self):
        return getattr(self, "owner", None)

    def request_first_loader(self) -> None:
        raise NotImplementedError

    def request_render(self) -> None:
        raise NotImplementedError

    def handleRenderResult(self, result: RenderResult) -> None:
        raise NotImplementedError

    def shutdown(self) -> None:
        """关闭视口时释放后台任务；没有后台资源的视口无需处理。"""
