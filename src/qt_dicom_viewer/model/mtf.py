"""点源法 MTF 的纯数据模型；方向固定为原始图像列 X、行 Y。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MtfAxisResult:
    lsf: tuple[float, ...]
    frequency: tuple[float, ...]
    mtf: tuple[float, ...]
    mtf50: float | None
    mtf10: float | None
    fwhm: float | None


@dataclass(frozen=True)
class BeadMtfResult:
    x: MtfAxisResult
    y: MtfAxisResult
    background: float
    noise: float
    warnings: tuple[str, ...]
