"""CPU mask computation; neither QWidget nor OpenGL objects enter the worker."""
from PySide6.QtCore import QObject, QRunnable, Signal


class EditSignals(QObject):
    finished = Signal(int, str, object, str)


class VolumeEditTask(QRunnable):
    def __init__(self, token, kind, function, *args):
        super().__init__()
        self.token, self.kind = token, kind
        self.function, self.args = function, args
        self.signals = EditSignals()

    def run(self):
        try:
            result = self.function(*self.args)
        except Exception as error:
            self.signals.finished.emit(self.token, self.kind, None, str(error))
        else:
            self.signals.finished.emit(self.token, self.kind, result, "")
