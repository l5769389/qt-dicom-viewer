"""解析高斯作为独立基准，不用另一遍 FFT 生成测试期望。"""

import math

import numpy as np
import pytest

from qt_dicom_viewer.core.bead_mtf import (
    compute_point_source_mtf, extract_rect_pixels, lsf_fwhm,
    threshold_frequency,
)
from qt_dicom_viewer.model import ImagePoint


def gaussian(rows=128, columns=128, row_spacing=.15, column_spacing=.1,
             sigma_x=.8, sigma_y=1.2):
    x = (np.arange(columns) - (columns - 1) / 2) * column_spacing
    y = (np.arange(rows) - (rows - 1) / 2) * row_spacing
    return 80 + 1000 * np.exp(-.5 * ((x[None, :] / sigma_x) ** 2
                                    + (y[:, None] / sigma_y) ** 2))


@pytest.mark.parametrize("spacing,sigmas", [((.15, .1), (.8, 1.2)), ((.12, .2), (1.2, .8))])
def test_anisotropic_gaussian_matches_analytic_curves_and_metrics(spacing, sigmas):
    pixels = gaussian(row_spacing=spacing[0], column_spacing=spacing[1],
                      sigma_x=sigmas[0], sigma_y=sigmas[1])
    original = pixels.copy()
    result = compute_point_source_mtf(pixels, *spacing)
    for axis, sigma, delta in [(result.x, sigmas[0], spacing[1]), (result.y, sigmas[1], spacing[0])]:
        expected_curve = np.exp(-2 * math.pi ** 2 * sigma ** 2 * np.array(axis.frequency) ** 2)
        np.testing.assert_allclose(axis.mtf, expected_curve, atol=2e-6)
        assert axis.frequency[-1] == pytest.approx(.5 / delta)
        assert axis.mtf50 == pytest.approx(math.sqrt(-math.log(.5) / (2 * math.pi ** 2 * sigma ** 2)), rel=.002)
        assert axis.mtf10 == pytest.approx(math.sqrt(-math.log(.1) / (2 * math.pi ** 2 * sigma ** 2)), rel=.004)
        assert axis.fwhm == pytest.approx(2 * math.sqrt(2 * math.log(2)) * sigma, rel=.006)
    assert not result.warnings
    np.testing.assert_array_equal(pixels, original)


def test_gaussian_analysis_fits_lsf_and_reports_analytic_equivalent_metrics():
    sigma_x, sigma_y = .8, 1.2
    result = compute_point_source_mtf(
        gaussian(sigma_x=sigma_x, sigma_y=sigma_y),
        .15,
        .1,
        measurement_method="bead",
        analysis_method="gaussian",
    )
    for axis, sigma in ((result.x, sigma_x), (result.y, sigma_y)):
        assert axis.fwhm == pytest.approx(2 * math.sqrt(2 * math.log(2)) * sigma, rel=.003)
        assert axis.mtf50 == pytest.approx(
            math.sqrt(math.log(2)) / (math.sqrt(2) * math.pi * sigma), rel=.003
        )
        assert axis.mtf10 == pytest.approx(
            math.sqrt(math.log(10)) / (math.sqrt(2) * math.pi * sigma), rel=.003
        )
        assert max(axis.mtf) == pytest.approx(1)
    assert not result.warnings


def test_wire_cross_section_uses_same_point_source_pipeline_without_size_correction():
    pixels = gaussian()
    bead = compute_point_source_mtf(pixels, .15, .1, measurement_method="bead")
    wire = compute_point_source_mtf(pixels, .15, .1, measurement_method="wire")
    np.testing.assert_allclose(wire.x.mtf, bead.x.mtf)
    np.testing.assert_allclose(wire.y.mtf, bead.y.mtf)


@pytest.mark.parametrize("keywords", [
    {"measurement_method": "edge"},
    {"analysis_method": "unknown"},
])
def test_unknown_method_or_analysis_is_rejected(keywords):
    with pytest.raises(ValueError, match="不支持"):
        compute_point_source_mtf(gaussian(), .15, .1, **keywords)


def test_background_offset_and_positive_scaling_do_not_change_mtf():
    pixels = gaussian()
    first = compute_point_source_mtf(pixels, .15, .1)
    second = compute_point_source_mtf(pixels * 2.3 - 1200, .15, .1)
    for a, b in [(first.x, second.x), (first.y, second.y)]:
        np.testing.assert_allclose(a.mtf, b.mtf, atol=1e-13)
        assert a.fwhm == pytest.approx(b.fwhm)


def test_negative_lobes_are_retained_and_response_can_exceed_one():
    pixels = np.zeros((24, 24))
    pixels[12, 12] = 10
    pixels[12, 11] = pixels[12, 13] = -2
    result = compute_point_source_mtf(pixels, .5, .25)
    assert min(result.x.lsf) < 0
    assert max(result.x.mtf) > 2
    assert result.x.mtf50 is None and result.x.mtf10 is None
    assert result.x.lsf[12] == 5
    assert result.y.lsf[12] == 1.5


def test_threshold_uses_first_downward_crossing_and_warns_repeated_crossings():
    f = np.arange(7, dtype=float)
    response = np.array([1, .6, .4, .8, .5, .3, .1])
    crossing, multiple = threshold_frequency(f, response, .5)
    assert crossing == 1.5
    assert multiple
    assert threshold_frequency(f, response, .05) == (None, False)
    assert threshold_frequency(f, response, .1) == (6, False)


def test_peak_plateau_fwhm_is_not_gaussian_fitted():
    assert lsf_fwhm(np.array([0, 1, 4, 4, 1, 0]), .3) == pytest.approx(.7)
    assert lsf_fwhm(np.array([0, 1, 4, 4, 4]), .3) is None
    assert lsf_fwhm(np.zeros(8), 1) is None


def test_truncated_response_has_explicit_quality_warnings():
    pixels = np.zeros((24, 24))
    pixels[:, 0] = 10
    pixels[12, 0] = 100
    result = compute_point_source_mtf(pixels, 1, 1)
    assert any("主峰位于" in message for message in result.warnings)
    assert any("两端" in message for message in result.warnings)
    assert result.x.fwhm is None


def test_mad_low_signal_warning_is_not_a_pass_fail_decision():
    rng = np.random.default_rng(12)
    pixels = rng.normal(0, 10, (32, 32))
    pixels[8:24, 8:24] += 5
    result = compute_point_source_mtf(pixels, 1, 1)
    assert result.noise > 0
    assert any("低信号" in message for message in result.warnings)


@pytest.mark.parametrize("spacing", [(0, 1), (-1, 1), (1, float("nan")), (float("inf"), 1), (None, 1)])
def test_invalid_real_spacing_is_rejected(spacing):
    with pytest.raises(ValueError, match="间距"):
        compute_point_source_mtf(gaussian(), *spacing)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_invalid_pixels_are_not_filtered_out(value):
    pixels = gaussian()
    pixels[12, 14] = value
    with pytest.raises(ValueError, match="无效像素"):
        compute_point_source_mtf(pixels, 1, 1)


@pytest.mark.parametrize("pixels", [np.zeros((12, 12)), np.ones((12, 12)) * 1024,
                                     -np.pad(np.ones((4, 4)), 4)])
def test_flat_or_nonpositive_net_response_is_error(pixels):
    with pytest.raises(ValueError, match="有效正净响应"):
        compute_point_source_mtf(pixels, 1, 1)


def test_rect_pixel_centers_reverse_drag_and_snapshot():
    pixels = np.arange(400).reshape(20, 20)
    roi = extract_rect_pixels(pixels, [ImagePoint(12.2, 15.8), ImagePoint(2.3, 3.4)])
    np.testing.assert_array_equal(roi, pixels[4:16, 3:13])
    roi[0, 0] = -1
    assert pixels[4, 3] != -1


@pytest.mark.parametrize("points,pattern", [
    ([ImagePoint(-1, 0), ImagePoint(12, 12)], "超出"),
    ([ImagePoint(0, 0), ImagePoint(20, 12)], "超出"),
    ([ImagePoint(0, 0), ImagePoint(6.9, 12)], "8 × 8"),
    ([ImagePoint(float("nan"), 0), ImagePoint(10, 12)], "坐标"),
])
def test_crop_does_not_silently_clip_or_expand(points, pattern):
    with pytest.raises(ValueError, match=pattern):
        extract_rect_pixels(np.zeros((20, 20)), points)


def test_multiple_beads_cause_crossing_warning():
    pixels = np.zeros((64, 64))
    pixels[32, 20] = pixels[32, 40] = 10
    result = compute_point_source_mtf(pixels, 1, 1)
    assert any("多次穿越" in message for message in result.warnings)


def test_background_band_uses_ceil_of_ten_percent_short_side():
    pixels = np.full((19, 22), 7.0)
    pixels[:2] = pixels[-2:] = 10
    pixels[:, :2] = pixels[:, -2:] = 10
    pixels[9, 11] = 2000
    result = compute_point_source_mtf(pixels, 1, 1)
    assert result.background == 10
    assert result.noise == 0
    assert min(result.x.lsf) < 0


def test_minimum_eight_by_eight_is_allowed():
    pixels = np.zeros((8, 8))
    pixels[4, 4] = 10
    result = compute_point_source_mtf(pixels, 1, 1)
    assert len(result.x.frequency) == 17  # 8 × 4 点 FFT，含零频和 Nyquist。
    assert result.x.mtf10 is None


@pytest.mark.parametrize("target50", [.7, 1.13])
def test_reported_frequency_range_against_independent_gaussian_formula(target50):
    """直接覆盖本次比对量级，不能只用此前较低频率的高斯基准。"""
    sigma = math.sqrt(math.log(2)) / (math.sqrt(2) * math.pi * target50)
    pixels = gaussian(rows=64, columns=64, row_spacing=.06, column_spacing=.06,
                      sigma_x=sigma, sigma_y=sigma)
    result = compute_point_source_mtf(pixels, .06, .06)
    for axis in (result.x, result.y):
        assert axis.mtf50 == pytest.approx(target50, rel=.001)
        assert axis.mtf10 == pytest.approx(target50 * math.sqrt(math.log(10) / math.log(2)), rel=.002)


def test_discrete_binomial_response_has_analytic_thresholds_without_gaussian_assumption():
    """三点 LSF 的解析响应为 (1 + cos(2πfΔ)) / 2，验证补零、归一化及行列单位。"""
    pixels = np.zeros((16, 24))
    kernel = np.array([.25, .5, .25])
    pixels[7:10, 11:14] = kernel[:, None] * kernel[None, :]
    result = compute_point_source_mtf(pixels, .16, .11)
    for axis, spacing in [(result.x, .11), (result.y, .16)]:
        expected = .5 + .5 * np.cos(2 * math.pi * np.array(axis.frequency) * spacing)
        np.testing.assert_allclose(axis.mtf, expected, atol=1e-14)
        assert axis.mtf50 == pytest.approx(1 / (4 * spacing), abs=1e-12)
        assert axis.mtf10 == pytest.approx(math.acos(-.8) / (2 * math.pi * spacing), rel=.001)


def test_same_bead_tight_roi_contaminates_background_and_overestimates_mtf():
    """记录现有外围背景法的局限；这是合成对照，不是实际 1.13 的成因定论。"""
    sigma = math.sqrt(math.log(2)) / (math.sqrt(2) * math.pi * .7)
    pixels = gaussian(rows=64, columns=64, row_spacing=.06, column_spacing=.06,
                      sigma_x=sigma, sigma_y=sigma)
    full = compute_point_source_mtf(pixels, .06, .06)
    tight = compute_point_source_mtf(pixels[24:40, 24:40], .06, .06)
    assert full.x.mtf50 == pytest.approx(.7, rel=.001)
    assert full.x.mtf10 == pytest.approx(.7 * math.sqrt(math.log(10) / math.log(2)), rel=.002)
    assert tight.x.mtf50 > full.x.mtf50 * 1.5
    assert tight.x.mtf10 > full.x.mtf10 * 1.3
    assert full.background == pytest.approx(80, abs=.001)
    assert tight.background > 280  # 背景真值 80，但小框将微珠尾部计入外围背景。
    assert any("截断或背景偏差" in warning for warning in tight.warnings)


def test_wrong_pixel_spacing_rescales_both_thresholds_by_same_factor():
    pixels = gaussian()
    correct = compute_point_source_mtf(pixels, .15, .1)
    wrong = compute_point_source_mtf(pixels, .15 / 1.614, .1 / 1.614)
    for axis_correct, axis_wrong in [(correct.x, wrong.x), (correct.y, wrong.y)]:
        assert axis_wrong.mtf50 / axis_correct.mtf50 == pytest.approx(1.614)
        assert axis_wrong.mtf10 / axis_correct.mtf10 == pytest.approx(1.614)
        assert axis_wrong.fwhm / axis_correct.fwhm == pytest.approx(1 / 1.614)
