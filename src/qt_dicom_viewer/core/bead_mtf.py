"""原始像素上的点源 MTF，支持直接 FFT 与高斯等效分析。"""

import math

import numpy as np

from qt_dicom_viewer.model.mtf import BeadMtfResult, MtfAxisResult


MEASUREMENT_METHODS = ("bead", "wire")
ANALYSIS_METHODS = ("direct_fft", "gaussian")


def extract_rect_pixels(pixels: np.ndarray, points) -> np.ndarray:
    """按像素中心选取矩形，返回独立快照；越界不能静默截取。"""
    if pixels is None or np.ndim(pixels) != 2:
        raise ValueError("尚无可分析的原始二维像素")
    columns = [float(p.column) for p in points]
    rows = [float(p.row) for p in points]
    if len(columns) != 2 or not np.all(np.isfinite(columns + rows)):
        raise ValueError("ROI 坐标无效")
    height, width = pixels.shape
    # 图像边界位于最外层像素中心外半个像素处。
    if (min(columns) < -0.5 or max(columns) > width - 0.5
            or min(rows) < -0.5 or max(rows) > height - 0.5):
        raise ValueError("ROI 超出原始图像边界，请将整个矩形放在图像内")
    c0, c1 = math.ceil(min(columns)), math.floor(max(columns))
    r0, r1 = math.ceil(min(rows)), math.floor(max(rows))
    if r1 - r0 + 1 < 8 or c1 - c0 + 1 < 8:
        raise ValueError("ROI 至少需要包含 8 × 8 个像素")
    return np.array(pixels[r0:r1 + 1, c0:c1 + 1], dtype=np.float64, copy=True)


def threshold_frequency(frequency: np.ndarray, response: np.ndarray,
                        threshold: float) -> tuple[float | None, bool]:
    """第一次向下穿越阈值；额外穿越仅警告，不取平均或外推。"""
    above = response > threshold
    down = np.flatnonzero(above[:-1] & ~above[1:])
    crossings = np.count_nonzero(above[:-1] != above[1:])
    if len(down) == 0:
        return None, crossings > 1
    i = int(down[0])
    fraction = (response[i] - threshold) / (response[i] - response[i + 1])
    return float(frequency[i] + fraction * (frequency[i + 1] - frequency[i])), crossings > 1


def lsf_fwhm(lsf: np.ndarray, spacing: float) -> float | None:
    """从主峰向两侧找最近的半峰高交点，平台主峰也使用同一约定。"""
    peak_index = int(np.argmax(lsf))
    peak = float(lsf[peak_index])
    if peak <= 0:
        return None
    half = peak / 2
    left = next((i for i in range(peak_index - 1, -1, -1) if lsf[i] <= half), None)
    right = next((i for i in range(peak_index + 1, len(lsf)) if lsf[i] <= half), None)
    if left is None or right is None:
        return None
    left_crossing = left + (half - lsf[left]) / (lsf[left + 1] - lsf[left])
    right_crossing = right - 1 + (half - lsf[right - 1]) / (lsf[right] - lsf[right - 1])
    return float((right_crossing - left_crossing) * spacing)


def _axis_result(lsf: np.ndarray, spacing: float, direction: str,
                 warnings: list[str]) -> MtfAxisResult:
    if not np.all(np.isfinite(lsf)):
        raise ValueError(f"{direction} 方向积分溢出，无法计算 MTF")
    nfft = 1 << (4 * len(lsf) - 1).bit_length()
    spectrum = np.abs(np.fft.rfft(lsf, n=nfft))
    if not np.all(np.isfinite(spectrum)) or spectrum[0] <= np.finfo(float).tiny:
        raise ValueError(f"{direction} 方向无有效零频幅值，无法归一化")
    frequency = np.fft.rfftfreq(nfft) / spacing
    response = spectrum / spectrum[0]
    if not np.all(np.isfinite(frequency)) or not np.all(np.isfinite(response)):
        raise ValueError(f"{direction} 方向频率或响应溢出")
    mtf50, multiple50 = threshold_frequency(frequency, response, 0.5)
    mtf10, multiple10 = threshold_frequency(frequency, response, 0.1)
    if multiple50 or multiple10:
        warnings.append(f"{direction} 方向 MTF 多次穿越阈值，报告第一次向下交点")
    peak = float(np.max(lsf))
    if peak <= 0 or max(abs(float(lsf[0])), abs(float(lsf[-1]))) > 0.05 * peak:
        warnings.append(f"{direction} 方向 LSF 两端未回落至主峰的 5% 内，可能存在截断或背景偏差")
    fwhm = lsf_fwhm(lsf, spacing)
    if fwhm is not None and not math.isfinite(fwhm):
        raise ValueError(f"{direction} 方向半高宽溢出")
    if fwhm is None:
        warnings.append(f"{direction} 方向 LSF 缺少完整的半高宽交点")
    return MtfAxisResult(tuple(map(float, lsf)), tuple(map(float, frequency)),
                         tuple(map(float, response)), mtf50, mtf10, fwhm)


def _fit_gaussian_lsf(lsf: np.ndarray, spacing: float) -> tuple[np.ndarray, float, float]:
    """最小二乘拟合 ``C + A exp(-(x-mu)^2/(2 sigma^2))``。

    背景常数 C 只用于吸收积分后的残余基线；返回的 LSF 不包含该常数，
    因而后续指标表示高斯中心响应本身。
    """
    values = np.asarray(lsf, dtype=np.float64)
    x = np.arange(len(values), dtype=np.float64) * spacing
    span = max(float(x[-1] - x[0]), spacing)
    peak_x = float(x[int(np.argmax(values))])
    mu_low, mu_high = max(float(x[0]), peak_x - span / 4), min(float(x[-1]), peak_x + span / 4)
    sigma_low, sigma_high = spacing * 0.2, span
    best = None
    centered_values = values - np.mean(values)
    total = float(np.sum(centered_values * centered_values))
    tiny = np.finfo(float).tiny

    # 振幅和常数基线使用带截距的一元最小二乘闭式解，避免为每个候选
    # 构造矩阵并调用 lstsq。保持为短向量运算，Qt 工作线程中不启动 BLAS。
    for _ in range(4):
        mus = np.linspace(mu_low, mu_high, 35)
        sigmas = np.geomspace(max(sigma_low, spacing * 0.05), sigma_high, 45)
        for mu in mus:
            distance2 = (x - mu) ** 2
            for sigma in sigmas:
                gaussian = np.exp(-distance2 / (2 * sigma ** 2))
                centered_gaussian = gaussian - np.mean(gaussian)
                variance = float(np.sum(centered_gaussian * centered_gaussian))
                if variance <= tiny:
                    continue
                covariance = float(np.sum(centered_values * centered_gaussian))
                amplitude = covariance / variance
                if amplitude <= 0:
                    continue
                error = max(0.0, total - covariance * amplitude)
                if math.isfinite(error) and (best is None or error < best[0]):
                    best = error, float(mu), float(sigma), amplitude
        if best is None:
            break
        _, mu, sigma, _ = best
        mu_radius = max((mu_high - mu_low) / 8, spacing / 100)
        sigma_radius = max((sigma_high - sigma_low) / 8, spacing / 100)
        mu_low, mu_high = max(float(x[0]), mu - mu_radius), min(float(x[-1]), mu + mu_radius)
        sigma_low, sigma_high = max(spacing * 0.05, sigma - sigma_radius), sigma + sigma_radius

    if best is None:
        raise ValueError("LSF 无法拟合有效的正峰高斯响应")
    error, mu, sigma, amplitude = best
    fitted = amplitude * np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))
    quality = 1.0 if total <= tiny else max(0.0, 1.0 - error / total)
    return fitted, sigma, quality


def _gaussian_axis_result(lsf: np.ndarray, spacing: float, direction: str,
                          warnings: list[str]) -> MtfAxisResult:
    if not np.all(np.isfinite(lsf)):
        raise ValueError(f"{direction} 方向积分溢出，无法拟合高斯响应")
    fitted, sigma, quality = _fit_gaussian_lsf(lsf, spacing)
    if quality < 0.9:
        warnings.append(f"{direction} 方向高斯拟合度较低（R²={quality:.3f}），等效指标可能不适合该响应")
    nfft = 1 << (4 * len(lsf) - 1).bit_length()
    frequency = np.fft.rfftfreq(nfft) / spacing
    response = np.exp(-2 * math.pi ** 2 * sigma ** 2 * frequency ** 2)

    def crossing(threshold):
        value = math.sqrt(-math.log(threshold) / (2 * math.pi ** 2 * sigma ** 2))
        return value if value <= frequency[-1] else None

    return MtfAxisResult(
        tuple(map(float, fitted)), tuple(map(float, frequency)), tuple(map(float, response)),
        crossing(0.5), crossing(0.1), 2 * math.sqrt(2 * math.log(2)) * sigma,
    )


def compute_point_source_mtf(roi: np.ndarray, row_spacing: float,
                             column_spacing: float, *,
                             measurement_method: str = "bead",
                             analysis_method: str = "direct_fft") -> BeadMtfResult:
    """计算微珠或垂直扫描平面细丝截面的两方向 MTF。"""
    if measurement_method not in MEASUREMENT_METHODS:
        raise ValueError("不支持的 MTF 测量方法")
    if analysis_method not in ANALYSIS_METHODS:
        raise ValueError("不支持的 MTF 分析方式")
    source_name = "微珠" if measurement_method == "bead" else "细丝截面"
    try:
        valid_spacing = all(math.isfinite(v) and v > 0 for v in (row_spacing, column_spacing))
    except TypeError:
        valid_spacing = False
    if not valid_spacing:
        raise ValueError("缺少有效的原始像素间距，不能计算 lp/mm 或 mm")
    pixels = np.asarray(roi, dtype=np.float64)
    if pixels.ndim != 2 or min(pixels.shape) < 8:
        raise ValueError("ROI 至少需要包含 8 × 8 个像素")
    if not np.all(np.isfinite(pixels)):
        raise ValueError("ROI 包含 NaN 或 Inf 无效像素")
    band = max(1, math.ceil(min(pixels.shape) * 0.1))
    border = np.ones(pixels.shape, dtype=bool)
    border[band:-band, band:-band] = False
    background_pixels = pixels[border]
    background = float(np.median(background_pixels))
    noise = float(1.4826 * np.median(np.abs(background_pixels - background)))
    psf = pixels - background
    peak = float(np.max(psf))
    net = float(np.sum(psf))
    magnitude = float(np.sum(np.abs(psf)))
    if not math.isfinite(net) or not math.isfinite(magnitude):
        raise ValueError("ROI 响应溢出，无法归一化")
    if peak <= 0 or net <= max(np.finfo(float).tiny, magnitude * 1e-12):
        raise ValueError(f"ROI 平坦或无有效正净响应，请框选{source_name}及外围背景")
    warnings = []
    if noise > 0 and peak < 5 * noise:
        warnings.append(f"低信号：{source_name}峰值不足外围背景噪声的 5 倍")
    if border[np.unravel_index(np.argmax(psf), psf.shape)]:
        warnings.append("主峰位于外围背景带，背景估计可能受污染或微珠被截断")
    axis_builder = _axis_result if analysis_method == "direct_fft" else _gaussian_axis_result
    x = axis_builder(psf.sum(axis=0) * row_spacing, column_spacing, "X", warnings)
    y = axis_builder(psf.sum(axis=1) * column_spacing, row_spacing, "Y", warnings)
    return BeadMtfResult(x, y, background, noise, tuple(warnings))
