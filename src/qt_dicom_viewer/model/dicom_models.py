from enum import StrEnum
from typing import TypeAlias


class TabType(StrEnum):
    TWO_D = "2d"
    MPR = "mpr"
    THREE_D = "3d"
    FOUR_D = "4d"
    TAG = "tag"


class TwoDViewType(StrEnum):
    STACK = "stack"


class MprPlane(StrEnum):
    AXIAL = "axial"
    SAGITTAL = "sagittal"
    CORONAL = "coronal"


ViewportType: TypeAlias = MprPlane | TwoDViewType


class ToolType(StrEnum):
    WINDOW = "window"
    PAN = "pan"
    ZOOM = "zoom"
    SCROLL = "scroll"
    MEASURE = "measure"
    ANNOTATE = "annotate"
    ROTATE = "rotate"
    MPR_ROTATE_3D = "mpr-rotate-3d"
    SERVICE = "service"
    RESET = "reset"
