"""Water phantom detection and five circular ROIs in original CT HU pixels.

All distances are physical millimetres. Image display transforms and windowing
never participate. The metrics are measurements, without acceptance thresholds.
"""
from dataclasses import replace
import math

import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkImagingMorphological import vtkImageConnectivityFilter

from qt_dicom_viewer.model.water_qa import WaterPhantom, WaterQaSettings, WaterQaRoi, WaterQaResult


def _validate_input(pixels, spacing):
    array = np.asarray(pixels)
    if array.ndim != 2 or min(array.shape) < 16:
        raise ValueError("水模 QA 需要有效的单层 CT 像素数据")
    if spacing is None or len(spacing) != 2:
        raise ValueError("缺少原始 DICOM PixelSpacing，无法放置毫米单位的 VOI")
    spacing = tuple(float(s) for s in spacing)
    if not all(math.isfinite(s) and s > 0 for s in spacing):
        raise ValueError("DICOM PixelSpacing 必须是有限正数")
    if not np.all(np.isfinite(array)):
        raise ValueError("像素包含非有限值，无法计算水模 QA")
    return array, spacing


def _components(mask):
    data = np.ascontiguousarray(mask, dtype=np.uint8)
    image = vtkImageData()
    image.SetDimensions(data.shape[1], data.shape[0], 1)
    image.GetPointData().SetScalars(numpy_to_vtk(data.ravel(), deep=False))
    connectivity = vtkImageConnectivityFilter()
    connectivity.SetInputData(image)
    connectivity.SetScalarRange(1, 1)
    connectivity.SetLabelScalarTypeToInt()
    connectivity.SetExtractionModeToAllRegions()
    connectivity.Update()
    return vtk_to_numpy(connectivity.GetOutput().GetPointData().GetScalars()).reshape(data.shape).copy()


def _circle_fit(points):
    origin = np.mean(points, axis=0)
    local = points-origin
    matrix = np.column_stack((2*local, np.ones(len(local))))
    values, _, rank, _ = np.linalg.lstsq(matrix, np.sum(local*local, axis=1), rcond=None)
    radius2 = values[2]+values[:2]@values[:2]
    if rank < 3 or radius2 <= 0:
        return None
    return values[:2]+origin, math.sqrt(radius2)


def _round_boundary(mask, spacing):
    """Robust circle fit can ignore a narrow holder attached to the phantom."""
    interior = np.zeros_like(mask)
    interior[1:-1, 1:-1] = (mask[:-2, 1:-1] & mask[2:, 1:-1]
                             & mask[1:-1, :-2] & mask[1:-1, 2:])
    rows, columns = np.nonzero(mask & ~interior)
    if len(rows) < 40:
        return None
    points = np.column_stack((columns*spacing[1], rows*spacing[0]))
    if len(points) > 1600:
        points = points[np.linspace(0, len(points)-1, 1600, dtype=int)]
    tolerance = max(1.5, max(spacing)*1.5)
    minimum_radius = 20.0
    maximum_radius = min((mask.shape[1]-1)*spacing[1], (mask.shape[0]-1)*spacing[0])/2
    candidates = [_circle_fit(points)]
    rng = np.random.default_rng(731)
    candidates.extend(_circle_fit(points[rng.choice(len(points), 3, replace=False)]) for _ in range(160))
    best, best_score = None, -1
    for candidate in candidates:
        if candidate is None:
            continue
        center, radius = candidate
        if not minimum_radius <= radius <= maximum_radius:
            continue
        distances = np.linalg.norm(points-center, axis=1)
        inliers = np.abs(distances-radius) <= tolerance
        if np.count_nonzero(inliers) < 35:
            continue
        angles = np.arctan2(*(points[inliers]-center)[:, ::-1].T)
        coverage = len(np.unique(np.floor((angles+np.pi)*36/(2*np.pi)).astype(int) % 36))/36
        if coverage < 0.86:
            continue
        score = np.count_nonzero(inliers)*coverage
        if score > best_score:
            best, best_score = (center, radius, coverage, inliers), score
    if best is None:
        return None
    center, radius, coverage, inliers = best
    for _ in range(3):
        fit = _circle_fit(points[inliers])
        if fit is None:
            return None
        center, radius = fit
        inliers = np.abs(np.linalg.norm(points-center, axis=1)-radius) <= tolerance
    # Refuse clipped phantoms; inventing their missing edge biases peripheral ROIs.
    margin = max(spacing)
    if (center[0]-radius < margin or center[1]-radius < margin
            or center[0]+radius > (mask.shape[1]-1)*spacing[1]-margin
            or center[1]+radius > (mask.shape[0]-1)*spacing[0]-margin):
        return None
    return WaterPhantom(float(center[0]/spacing[1]), float(center[1]/spacing[0]), float(radius), float(coverage))


def detect_water_phantom(pixels, spacing):
    array, spacing = _validate_input(pixels, spacing)
    # This broad detection interval is NOT an acceptance criterion or a filter
    # on samples used for statistics. Every original voxel in each ROI is used.
    labels = _components((array > -300) & (array < 300))
    counts = np.bincount(labels.ravel())
    counts[0] = 0
    candidates = []
    y, x = np.ogrid[:array.shape[0], :array.shape[1]]
    for label in np.argsort(counts)[-5:][::-1]:
        if counts[label]*spacing[0]*spacing[1] < math.pi*20**2:
            continue
        phantom = _round_boundary(labels == label, spacing)
        if phantom is None:
            continue
        disk = ((x-phantom.column)*spacing[1])**2 + ((y-phantom.row)*spacing[0])**2
        values = array[disk <= (phantom.radius_mm*0.7)**2]
        if len(values) < 64 or abs(float(np.median(values))) > 80:
            continue
        if np.mean(np.abs(values) < 150) < 0.9:
            continue
        candidates.append(phantom)
    if not candidates:
        raise ValueError("未识别到完整的圆形水模，请选择包含均质水区的 CT 切片")
    candidates.sort(key=lambda p: p.radius_mm, reverse=True)
    if len(candidates) > 1 and candidates[1].radius_mm > candidates[0].radius_mm*0.85:
        raise ValueError("发现多个尺寸相近的水模，无法唯一定位，请选择单个水模的切片")
    return candidates[0]


def measure_water_phantom(pixels, spacing, phantom, settings=WaterQaSettings(), *, centers=None):
    """Sample five ROIs, optionally at manually adjusted (column, row) centers."""
    array, spacing = _validate_input(pixels, spacing)
    diameter, clearance = settings.roi_diameter_mm, settings.edge_clearance_mm
    if not (math.isfinite(diameter) and 2 <= diameter <= 100
            and math.isfinite(clearance) and 0 <= clearance <= 100):
        raise ValueError("VOI 直径应为 2–100 mm，距边缘距离应为 0–100 mm")
    radius = diameter/2
    offset = phantom.radius_mm-radius-clearance
    if centers is None and offset < diameter:
        raise ValueError("水模尺寸不足以放置 5 个互不重叠的 VOI，请减小直径或距边缘距离")
    placements = (("center", "中心", 0, 0), ("left", "左", -offset, 0),
                  ("right", "右", offset, 0), ("top", "上", 0, -offset),
                  ("bottom", "下", 0, offset))
    if centers is None:
        centers = [(phantom.column+dx/spacing[1], phantom.row+dy/spacing[0])
                   for _, _, dx, dy in placements]
    else:
        centers = np.asarray(centers, dtype=float)
        if centers.shape != (5, 2) or not np.all(np.isfinite(centers)):
            raise ValueError("需要 5 个有效的 ROI 中心")
        physical = (centers - (phantom.column, phantom.row)) * (spacing[1], spacing[0])
        if np.any(np.linalg.norm(physical, axis=1)+radius > phantom.radius_mm+1e-6):
            raise ValueError("ROI 应位于水模内部")
        for index, point in enumerate(physical):
            if np.any(np.linalg.norm(physical[index+1:]-point, axis=1) < diameter-1e-6):
                raise ValueError("ROI 不能重叠，请重新调整位置")
    rois = []
    for (key, label, _, _), (column, row) in zip(placements, centers):
        # QML QVariant maps need Python floats, not NumPy scalar wrappers.
        column, row = float(column), float(row)
        rx, ry = radius/spacing[1], radius/spacing[0]
        x0, x1 = math.ceil(column-rx), math.floor(column+rx)+1
        y0, y1 = math.ceil(row-ry), math.floor(row+ry)+1
        if x0 < 0 or y0 < 0 or x1 > array.shape[1] or y1 > array.shape[0]:
            raise ValueError("VOI 超出图像范围，无法进行完整采样")
        y, x = np.ogrid[y0:y1, x0:x1]
        inside = ((x-column)*spacing[1])**2 + ((y-row)*spacing[0])**2 <= radius**2
        values = array[y0:y1, x0:x1][inside].astype(np.float64)
        if len(values) < 16:
            raise ValueError("每个 VOI 至少需要 16 个像素，请增大 VOI 直径")
        # Do not reject outlier HU samples or drop non-water pixels here: doing
        # so would hide image artefacts and underestimate noise/nonuniformity.
        rois.append(WaterQaRoi(key, label, column, row, radius, len(values),
                              len(values)*spacing[0]*spacing[1], float(values.mean()),
                              float(values.std(ddof=0)), float(values.min()), float(values.max()), 0))
    center = rois[0]
    rois = tuple(replace(roi, delta_center_hu=roi.mean_hu-center.mean_hu) for roi in rois)
    means, noise = [roi.mean_hu for roi in rois], [roi.std_hu for roi in rois]
    return WaterQaResult(phantom, settings, rois, center.mean_hu, center.std_hu,
                         max(abs(roi.delta_center_hu) for roi in rois[1:]), max(means)-min(means),
                         abs(means[1]-means[2]), abs(means[3]-means[4]), max(noise)-min(noise))


def analyze_water_phantom(pixels, spacing, settings=WaterQaSettings()):
    phantom = detect_water_phantom(pixels, spacing)
    return measure_water_phantom(pixels, spacing, phantom, settings)
