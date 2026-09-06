from enum import StrEnum
from typing import TypeAlias


class TabType(StrEnum):
    TWO_D = "2d"
    MPR = "mpr"
    THREE_D = "3d"
    FOUR_D = "4d"
    TAG = "tag"
    SETTINGS = "settings"
    PACS = "pacs"


class TwoDViewType(StrEnum):
    STACK = "stack"


class MprPlane(StrEnum):
    AXIAL = "axial"
    SAGITTAL = "sagittal"
    CORONAL = "coronal"


class MprProjectionMode(StrEnum):
    MIN_IP = "minip"
    MIP = "mip"
    MEAN = "mean"
    SUM = "sum"


class VolumeViewType(StrEnum):
    VOLUME = "volume"


ViewportType: TypeAlias = MprPlane | TwoDViewType | VolumeViewType


class ToolType(StrEnum):
    WINDOW = "window"
    PAN = "pan"
    ZOOM = "zoom"
    SCROLL = "scroll"
    MEASURE = "measure"
    ANNOTATE = "annotate"
    ROTATE = "rotate"
    MIP = "mip"
    MPR_ROTATE_3D = "mpr-rotate-3d"
    VOLUME_ROTATE = "volume-rotate"
    VOLUME_DIRECTION = "volume-direction"
    VOLUME_PRESET = "volume-preset"
    PLAY = "play"
    SERVICE = "service"
    RESET = "reset"
