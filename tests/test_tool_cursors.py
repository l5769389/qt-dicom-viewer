"""Native tool cursors keep their logical size on standard desktop DPI scales."""
import pytest
from PySide6.QtCore import QPoint, QSizeF, Qt
from qt_dicom_viewer.ui.cursors import tool_cursor, CURSOR_KINDS
from test_dicom_tags import qt_app


@pytest.mark.parametrize("kind", sorted(CURSOR_KINDS))
@pytest.mark.parametrize("ratio", [1.0, 1.25, 1.5, 2.0])
def test_native_tool_cursor_density_and_hotspot(qt_app, kind, ratio):
    cursor = tool_cursor(kind, ratio)
    assert cursor.shape() == Qt.BitmapCursor
    assert cursor.hotSpot() == QPoint(2, 2)
    pixmap = cursor.pixmap()
    assert pixmap.deviceIndependentSize() == QSizeF(40, 32)
    assert pixmap.devicePixelRatio() == ratio
    image = pixmap.toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    assert any(image.pixelColor(x, y).alpha() > 0
               for y in range(image.height()) for x in range(image.width()))
