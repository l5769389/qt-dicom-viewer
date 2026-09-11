"""Native QWidget content for the QML WindowContainer; never a second app window."""
import logging

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedLayout, QLabel, QPushButton
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from qt_dicom_viewer.ui.volume_render_backend import VolumeRenderBackend
from qt_dicom_viewer.ui.cursors import tool_cursor

logger = logging.getLogger(__name__)


class VolumeInteractor(QVTKRenderWindowInteractor):
    def __init__(self, host):
        self.host = host
        super().__init__(host)
        self.setAcceptDrops(True)

    def _getPixelRatio(self):
        # VTK's default follows the cursor's screen, which can differ from the
        # embedded window's screen on mixed-DPI desktops.
        return self.devicePixelRatioF()

    def event(self, event):
        handled = super().event(event)
        if event.type() == QEvent.DevicePixelRatioChange and "_RenderWindow" in self.__dict__:
            self.resizeEvent(None)
            if getattr(self.host, "vtk_widget", None) is self:
                self.host._update_cursor()
        return handled

    def paintEvent(self, event):
        # Rendering from the native paint callback can deadlock Cocoa when its
        # parent is a QQuickWindow. Render only from the host's coalescing timer.
        pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.host.controller.viewport_resized()
        self.host.request_render()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus(Qt.MouseFocusReason)
            p = event.position()
            self.host.controller.begin_drag((p.x(), p.y()), (self.width(), self.height()))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            p = event.position()
            self.host.controller.update_drag((p.x(), p.y()))
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            p = event.position()
            self.host.controller.update_drag((p.x(), p.y()))
            self.host.controller.end_drag()
            self.host._update_cursor()
            event.accept()

    def wheelEvent(self, event):
        self.host.controller.wheel_zoom(event.angleDelta().y(), event.pixelDelta().y())
        event.accept()

    def keyPressEvent(self, event):
        QWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        QWidget.keyReleaseEvent(self, event)

    def focusOutEvent(self, event):
        # Focus loss must never commit an unfinished stroke. A crop already
        # dispatched on mouse release continues independently of keyboard focus.
        self.host.controller.cancel_drag()
        self.host._update_cursor()
        super().focusOutEvent(event)


class VolumeViewportHost(QWidget):
    def __init__(self, controller, backend_factory=VolumeRenderBackend):
        super().__init__(None, Qt.FramelessWindowHint)
        self.controller = controller
        self._active = False
        self._disposed = False
        self._dirty = False
        self._interactive = False
        self.setAttribute(Qt.WA_NativeWindow)
        # Mark an explicit initial size so QWidget.show() cannot replace the
        # container's geometry with a sizeHint when first attached.
        self.resize(640, 480)
        self.setStyleSheet("QWidget { background: #02070e; color: #eaf3fb; }"
                           "QPushButton { padding: 8px 20px; background: #17354a; border-radius: 4px; }")
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._render)
        self._settle = QTimer(self)
        self._settle.setSingleShot(True)
        self._settle.setInterval(160)
        self._settle.timeout.connect(lambda: self.request_render(False))
        self.stack = QStackedLayout(self)
        self.stack.setContentsMargins(0, 0, 0, 0)
        self.status_page = QWidget(self)
        status_layout = QVBoxLayout(self.status_page)
        status_layout.addStretch()
        self.message = QLabel("正在准备 3D 影像…", self.status_page)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.message)
        self.retry_button = QPushButton("重试", self.status_page)
        self.retry_button.clicked.connect(controller.retry)
        status_layout.addWidget(self.retry_button, alignment=Qt.AlignCenter)
        status_layout.addStretch()
        self.stack.addWidget(self.status_page)
        self.vtk_widget = VolumeInteractor(self)
        self.stack.addWidget(self.vtk_widget)
        self.backend = backend_factory(self.vtk_widget)
        self.winId()
        self.windowHandle().installEventFilter(self)
        self.vtk_widget.windowHandle().installEventFilter(self)
        controller.stateChanged.connect(self._state_changed)
        controller.displayStateChanged.connect(self._state_changed)
        controller.maskChanged.connect(self._state_changed)
        controller.selectionChanged.connect(self._selection_changed)
        controller.loadStateChanged.connect(self.sync_status)
        controller.activeInteractionChanged.connect(self._update_cursor)
        self._update_cursor()

    def _update_cursor(self):
        kind = {"pan": "pan", "zoom": "zoom", "window": "window",
                "volume:crop": "volume-crop", "volume:rotate": "rotate-3d"}.get(
                    self.controller.activeInteraction)
        self.vtk_widget.setCursor(tool_cursor(kind, self.vtk_widget.devicePixelRatioF())
                                  if kind else Qt.ArrowCursor)

    def _selection_changed(self):
        if self._disposed:
            return
        self.backend.set_selection(self.controller.selection_points, self.controller._selection_size)
        self.request_render()

    def _state_changed(self):
        self.request_render(True)
        self._settle.start()

    def set_active(self, active):
        if self._disposed:
            return
        self._active = active
        if active:
            # WindowContainer must attach the native window before QWidget.show().
            if self.windowHandle().parent() is not None:
                self.show()
                self.request_render()
        else:
            self._timer.stop()
            self._settle.stop()
            self.hide()

    def sync_status(self):
        if self._disposed:
            return
        if self.controller.loadState == "ready":
            try:
                if self.backend.volume is not self.controller.volume:
                    self.backend.set_volume(self.controller.volume)
                self.stack.setCurrentWidget(self.vtk_widget)
                self.request_render()
            except Exception as error:
                logger.exception("Could not prepare VTK volume")
                self.controller.render_failed(str(error))
        else:
            self.stack.setCurrentWidget(self.status_page)
            failed = self.controller.loadState == "error"
            self.message.setText("无法显示 3D 影像\n"+self.controller.errorMessage
                                 if failed else "正在加载 3D 影像…")
            self.retry_button.setVisible(failed)

    def request_render(self, interactive=False):
        if self._disposed:
            return
        self._dirty = True
        self._interactive = interactive
        if self._active and not self._timer.isActive():
            self._timer.start()

    def _render(self):
        if (self._disposed or not self._active or not self._dirty
                or self.controller.loadState != "ready"
                or not self.windowHandle().isExposed()):
            return
        self._dirty = False
        try:
            self.backend.render(self.controller.state, self._interactive, self.controller.display_state,
                                self.controller.visible_mask)
        except Exception as error:
            logger.exception("VTK rendering failed")
            self.controller.render_failed(str(error))

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Expose and watched.isExposed():
            self.request_render()
        return super().eventFilter(watched, event)

    def dispose(self):
        if self._disposed:
            return
        self._disposed = True
        self._timer.stop()
        self._settle.stop()
        self.controller.stateChanged.disconnect(self._state_changed)
        self.controller.displayStateChanged.disconnect(self._state_changed)
        self.controller.maskChanged.disconnect(self._state_changed)
        self.controller.selectionChanged.disconnect(self._selection_changed)
        self.controller.loadStateChanged.disconnect(self.sync_status)
        self.controller.activeInteractionChanged.disconnect(self._update_cursor)
        self.vtk_widget.DestroyTimer(None, None)
        self.backend.dispose()
        self.hide()
        self.deleteLater()
