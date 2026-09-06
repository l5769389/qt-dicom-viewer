from dataclasses import replace
import math

import numpy as np
import pytest

from qt_dicom_viewer.core.water_qa import analyze_water_phantom, detect_water_phantom, measure_water_phantom
from qt_dicom_viewer.model.water_qa import WaterPhantom, WaterQaSettings


def water_image(shape=(320, 400), spacing=(1.0, 1.0), center=(204.2, 149.4),
                radius=100, mean=2, noise=5, seed=17):
    rows, cols = np.indices(shape)
    distance = ((cols-center[0])*spacing[1])**2 + ((rows-center[1])*spacing[0])**2
    pixels = np.full(shape, -1000.0, dtype=np.float32)
    body = distance <= radius**2
    pixels[body] = np.random.default_rng(seed).normal(mean, noise, np.count_nonzero(body))
    return pixels


@pytest.mark.parametrize("spacing,shape,center", [
    ((1, 1), (320, 400), (204.2, 149.4)),
    ((.7, .5), (400, 512), (260.5, 190.7)),
    ((1.3, .8), (240, 320), (151.3, 122.8)),
])
def test_detects_off_center_water_and_places_five_physically_circular_rois(spacing, shape, center):
    pixels = water_image(shape, spacing, center)
    before = pixels.copy()
    result = analyze_water_phantom(pixels, spacing)
    assert abs((result.phantom.column-center[0])*spacing[1]) < 1.5
    assert abs((result.phantom.row-center[1])*spacing[0]) < 1.5
    assert result.phantom.radius_mm == pytest.approx(100, abs=1.5)
    assert len(result.rois) == 5
    c, left, right, top, bottom = result.rois
    assert {r.key for r in result.rois} == {"center", "left", "right", "top", "bottom"}
    assert c.row == left.row == right.row and c.column == top.column == bottom.column
    assert left.column < c.column < right.column and top.row < c.row < bottom.row
    for roi in result.rois:
        assert roi.radius_mm == 10
        assert roi.mean_hu == pytest.approx(2, abs=1.3)
        assert roi.std_hu == pytest.approx(5, abs=1)
        assert roi.area_mm2 == roi.pixel_count*spacing[0]*spacing[1]
    assert abs((right.column-c.column)*spacing[1]-(bottom.row-c.row)*spacing[0]) < 1e-10
    np.testing.assert_array_equal(before, pixels)


def test_holder_and_shell_do_not_displace_detected_phantom():
    p = water_image()
    y, x = np.indices(p.shape)
    radial = np.hypot(x-204.2, y-149.4)
    p[(radial > 100) & (radial < 104)] = 900  # Acrylic shell excluded by detection only.
    p[248:287, 202:206] = 100  # Narrow connector.
    p[280:288, 20:380] = 100  # Long support with water-like HU.
    phantom = detect_water_phantom(p, (1, 1))
    assert phantom.column == pytest.approx(204.2, abs=1)
    assert phantom.row == pytest.approx(149.4, abs=1)
    assert phantom.radius_mm == pytest.approx(100, abs=1)


def test_metrics_use_all_original_samples_and_explicit_spatial_consistency_definition():
    shape, spacing = (280, 280), (.9, 1.1)
    center = (130.0, 140.0)
    phantom = WaterPhantom(*center, 100, 1)
    settings = WaterQaSettings(22, 18)
    pixels = np.zeros(shape, dtype=np.float32)
    initial = measure_water_phantom(pixels, spacing, phantom, settings)
    y, x = np.indices(shape)
    for i, roi in enumerate(initial.rois):
        mask = ((x-roi.column)*spacing[1])**2+((y-roi.row)*spacing[0])**2 <= roi.radius_mm**2
        pixels[mask] = np.arange(np.count_nonzero(mask)) % 7 * (i+1) + (2-i*4)
    # A bright artefact must increase the measured noise rather than be filtered out.
    pixels[140, 130] = 1200
    result = measure_water_phantom(pixels, spacing, phantom, settings)
    means, stds = [], []
    for roi in result.rois:
        mask = ((x-roi.column)*spacing[1])**2+((y-roi.row)*spacing[0])**2 <= roi.radius_mm**2
        values = pixels[mask].astype(float)
        means.append(values.mean()); stds.append(values.std(ddof=0))
        assert roi.pixel_count == len(values)
        assert roi.mean_hu == pytest.approx(values.mean())
        assert roi.std_hu == pytest.approx(values.std(ddof=0))
        assert roi.minimum_hu == values.min() and roi.maximum_hu == values.max()
    assert result.water_ct_hu == pytest.approx(means[0])
    assert result.noise_hu == pytest.approx(stds[0])
    assert result.uniformity_hu == pytest.approx(max(abs(v-means[0]) for v in means[1:]))
    assert result.consistency_range_hu == pytest.approx(max(means)-min(means))
    assert result.horizontal_difference_hu == pytest.approx(abs(means[1]-means[2]))
    assert result.vertical_difference_hu == pytest.approx(abs(means[3]-means[4]))
    assert result.noise_range_hu == pytest.approx(max(stds)-min(stds))


def test_zero_water_mean_is_valid_and_constant_phantom_has_zero_noise():
    result = analyze_water_phantom(water_image(mean=0, noise=0), (1, 1))
    assert result.water_ct_hu == result.noise_hu == result.uniformity_hu == 0
    assert result.consistency_range_hu == result.noise_range_hu == 0


@pytest.mark.parametrize("kind", ["empty", "all-water", "rectangle", "clipped", "ellipse", "multiple"])
def test_ambiguous_nonround_or_incomplete_images_do_not_fabricate_rois(kind):
    pixels = np.full((320, 400), -1000, dtype=float)
    y, x = np.indices(pixels.shape)
    if kind == "all-water":
        pixels[:] = 0
    elif kind == "rectangle":
        pixels[80:240, 80:320] = 0
    elif kind == "clipped":
        pixels[(x-20)**2+(y-150)**2 < 100**2] = 0
    elif kind == "ellipse":
        pixels[((x-200)/120)**2+((y-160)/65)**2 < 1] = 0
    elif kind == "multiple":
        pixels[((x-95)**2+(y-160)**2 < 65**2) | ((x-290)**2+(y-160)**2 < 65**2)] = 0
    with pytest.raises(ValueError, match="未识别|多个"):
        analyze_water_phantom(pixels, (1, 1))


@pytest.mark.parametrize("spacing", [None, (0, 1), (float("nan"), 1), (-1, 1)])
def test_invalid_original_spacing_is_rejected(spacing):
    with pytest.raises(ValueError, match="PixelSpacing"):
        analyze_water_phantom(water_image(), spacing)


@pytest.mark.parametrize("settings", [WaterQaSettings(100, 20), WaterQaSettings(20, 90),
                                      WaterQaSettings(0, 20), WaterQaSettings(20, -1)])
def test_invalid_or_overlapping_voi_configuration_is_rejected(settings):
    with pytest.raises(ValueError, match="VOI|距边缘"):
        analyze_water_phantom(water_image(), (1, 1), settings)


def test_nonfinite_pixels_and_under_sampled_rois_are_rejected():
    pixels = water_image()
    pixels[0, 0] = math.nan
    with pytest.raises(ValueError, match="非有限"):
        analyze_water_phantom(pixels, (1, 1))
    with pytest.raises(ValueError, match="16 个像素"):
        analyze_water_phantom(water_image(), (1, 1), WaterQaSettings(2, 20))
