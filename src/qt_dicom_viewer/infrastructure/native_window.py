"""Platform chrome adjustments that have no public QWindow equivalent."""
import ctypes
import logging
import sys

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QGuiApplication, QWindow
from shiboken6 import isValid

logger = logging.getLogger(__name__)


class NativeWindowChrome(QObject):
    """Match Cocoa chrome to the dark client area and retain native window controls.

    ExpandedClientAreaHint/NoTitleBarBackgroundHint do not hide NSWindow's
    title on macOS. Qt's native handle is an NSView only with the Cocoa plugin.
    Reapply after Qt updates the platform window, including full-screen changes.
    """

    def __init__(self, window: QWindow, parent: QObject):
        super().__init__(parent)
        self._window = window
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._apply)
        self._enabled = sys.platform == "darwin" and QGuiApplication.platformName() == "cocoa"
        if self._enabled:
            self._objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
            self._objc.sel_registerName.restype = ctypes.c_void_p
            self._objc.sel_registerName.argtypes = [ctypes.c_char_p]
            self._view_window = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
                ("objc_msgSend", self._objc))
            self._set_visibility = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long)(
                ("objc_msgSend", self._objc))
            self._objc.objc_getClass.restype = ctypes.c_void_p
            self._objc.objc_getClass.argtypes = [ctypes.c_char_p]
            self._get_object = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
                ("objc_msgSend", self._objc))
            self._set_object = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(
                ("objc_msgSend", self._objc))
            self._set_bool = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool)(
                ("objc_msgSend", self._objc))
            self._string = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)(
                ("objc_msgSend", self._objc))
            self._color = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double)(("objc_msgSend", self._objc))
            self._window_selector = self._objc.sel_registerName(b"window")
            self._visibility_selector = self._objc.sel_registerName(b"setTitleVisibility:")
            window.installEventFilter(self)
            window.windowTitleChanged.connect(self._schedule)
            window.visibilityChanged.connect(self._schedule)
            window.activeChanged.connect(self._schedule)
            if hasattr(window, "colorChanged"):
                window.colorChanged.connect(self._schedule)
            self._schedule()

    def _schedule(self, *_args):
        if self._enabled:
            self._timer.start(0)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Show, QEvent.WinIdChange, QEvent.WindowStateChange):
            self._schedule()
        return False

    def _apply(self):
        if not self._enabled or not isValid(self._window):
            return
        try:
            ns_view = int(self._window.winId())
            if ns_view:
                ns_window = self._view_window(ns_view, self._window_selector)
                if ns_window:
                    self._set_visibility(ns_window, self._visibility_selector, 1)  # NSWindowTitleHidden
                    sel = self._objc.sel_registerName
                    # Qt's transparent-title hint alone can leave Cocoa's light
                    # frame/background exposed during resize or activation.
                    name = self._string(self._objc.objc_getClass(b"NSString"),
                        sel(b"stringWithUTF8String:"), b"NSAppearanceNameDarkAqua")
                    appearance = self._get_object(self._objc.objc_getClass(b"NSAppearance"),
                        sel(b"appearanceNamed:"), name)
                    if appearance:
                        self._set_object(ns_window, sel(b"setAppearance:"), appearance)
                    self._set_bool(ns_window, sel(b"setTitlebarAppearsTransparent:"), True)
                    color = self._window.color()
                    background = self._color(self._objc.objc_getClass(b"NSColor"),
                        sel(b"colorWithSRGBRed:green:blue:alpha:"),
                        color.redF(), color.greenF(), color.blueF(), 1.0)
                    self._set_object(ns_window, sel(b"setBackgroundColor:"), background)
        except (OSError, TypeError, ValueError):
            logger.exception("Unable to apply native window appearance")
