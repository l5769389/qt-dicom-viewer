import numpy as np

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class DicomImageProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)
        self._images: dict[str, QImage] = {}

    def set_array(
        self,
        viewport_id: str,
        pixels: np.ndarray,
    ) -> None:
        pixels = np.ascontiguousarray(
            pixels,
            dtype=np.uint8,
        )

        height, width = pixels.shape[:2]
        formats = {3: QImage.Format_RGB888, 4: QImage.Format_RGBA8888}
        if pixels.ndim == 2:
            image_format = QImage.Format_Grayscale8
        elif pixels.ndim == 3 and pixels.shape[2] in formats:
            image_format = formats[pixels.shape[2]]
        else:
            raise ValueError("Expected grayscale, RGB or RGBA pixels")

        image = QImage(
            pixels.data,
            width,
            height,
            pixels.strides[0],
            image_format,
        )

        # 必须 copy，让 QImage 脱离 NumPy 内存生命周期
        self._images[viewport_id] = image.copy()

    def set_image(self, image_id: str, image: QImage) -> None:
        self._images[image_id] = image.copy()

    def remove_image(self, viewport_id: str) -> None:
        self._images.pop(viewport_id, None)

    def requestImage(
        self,
        image_id: str,
        size: QSize,
        requested_size: QSize,
    ) -> QImage:
        # image_id 形式：viewport-id/version
        viewport_id = image_id.split("/", 1)[0]

        image = self._images.get(
            viewport_id,
            QImage(),
        )

        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())

        if requested_size.isValid():
            return image.scaled(
                requested_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

        return image
