"""Linked PET MPR/fusion reconstruction on physical sampling grids."""
from collections import OrderedDict
from dataclasses import replace
from itertools import product

import numpy as np

from qt_dicom_viewer.core.dicom_loader import DicomLoader
from qt_dicom_viewer.core.mpr_reslicer import MprReslicer
from qt_dicom_viewer.core.pet_fusion import transformed_volume, pet_rgb, blend_pet_ct
from qt_dicom_viewer.model import (MprFrame, MprState, MprPlane, MprViewAnchors,
                                  FrameDisplayMeta, ImageGeometryMeta, PixelSpacing,
                                  WindowLevel, TwoDViewType)
from qt_dicom_viewer.model.render_models import (PetBatchRenderResult,
                                                PetMipRenderResult, MprRenderResult)


class PetReconstructor:
    def __init__(self, catalog, volumes):
        self.catalog = catalog
        self.volumes = volumes
        self.reslicer = MprReslicer()
        self._cache = OrderedDict()

    def _cached(self, key, build):
        if key not in self._cache:
            self._cache[key] = build()
            while len(self._cache) > 24:
                self._cache.popitem(last=False)
        self._cache.move_to_end(key)
        return self._cache[key]

    def render(self, request):
        pet_series = self.catalog.get_series(request.series_uid)
        ct_series = self.catalog.get_series(request.ct_series_uid) if request.ct_series_uid else None
        if pet_series is None or pet_series.modality.upper() != "PT":
            raise ValueError("找不到可用的 PET 序列")
        if request.ct_series_uid and (ct_series is None or ct_series.modality.upper() != "CT"):
            raise ValueError("融合需要一个 CT 和一个 PET 序列")
        pet_base = self.volumes.get_or_build(pet_series)
        ct = self.volumes.get_or_build(ct_series) if ct_series else None
        available = {o.unit_id for o in pet_base.pixel_value_meta.unit_options if o.available}
        unit = request.value_unit if request.value_unit in available else pet_base.pixel_value_meta.unit_id
        pet = self._cached(("unit", pet_base.fingerprint, pet_base.series_uid, unit),
                           lambda: pet_base.in_unit(unit))
        transformed_pet = transformed_volume(pet, request.transform) if ct else pet
        reference = ct or pet
        state = request.state
        if state is None:
            frame = MprFrame.standard_lps(reference.geometry.center_patient)
            grids = self.reslicer.create_view_grids(reference, frame)
            state = MprState(frame=frame, view_grids=grids,
                             view_anchors=MprViewAnchors.centered(grids))
        pet_window = request.pet_window
        if pet_window is None or (request.value_unit and request.value_unit != unit):
            ratio = pet.pixel_value_meta.scale_from_source / pet_base.pixel_value_meta.scale_from_source
            upper = (pet_base.default_window.center + pet_base.default_window.width / 2) * ratio
            pet_window = WindowLevel(upper / 2, upper)
        minimum = 0.01 if pet.pixel_value_meta.is_suv else 0.001
        upper = max(minimum, pet_window.center + pet_window.width / 2)
        pet_window = WindowLevel(upper / 2, upper)
        ct_window = request.ct_window or (ct.default_window if ct else None)
        frames = []
        ct_samples = None
        warning = ""
        for role, viewport_id in request.viewports:
            if role == "mip":
                key = ("mip", pet_base.fingerprint, pet_base.series_uid, unit, request.transform)
                mip, peaks = self._cached(key, lambda: self._full_mip(transformed_pet))
                pixels, geometry = mip.modality_pixels, mip.geometry
                display = DicomLoader.apply_window(pixels, pet_window, False, minimum)
                image = display if request.pet_color_map == "grayscale" else pet_rgb(display, request.pet_color_map)
                frames.append(PetMipRenderResult(
                    response_id=request.request_id, viewport_id=viewport_id, series_uid=pet.series_uid,
                    view_type=TwoDViewType.PET_MIP, image=image, modality_pixel=pixels,
                    frame_meta=self._meta(pet, mip, pet_window), mpr_frame=geometry.frame,
                    plane_geometry=geometry, peak_positions=peaks))
                continue
            plane = request.plane if ct else MprPlane(role)
            geometry_key = (state, plane)
            ref_slice = self._cached(("plane", reference.fingerprint, reference.series_uid,
                                      unit if not ct else "ct", geometry_key),
                lambda: self.reslicer.reslice(reference, plane, state.frame,
                    view_roll_radians=state.view_rolls.for_plane(plane),
                    grid_spec=state.view_grids.for_plane(plane) if state.view_grids else None,
                    grid_anchor=state.view_anchors.for_plane(plane) if state.view_anchors else None))
            pet_pixels = (self._cached(("pet-plane", pet_base.fingerprint, pet.series_uid, unit,
                                       request.transform, ref_slice.geometry),
                           lambda: self.reslicer._sample_plane(transformed_pet, ref_slice.geometry))
                          if ct else ref_slice.modality_pixels)
            pet_gray = DicomLoader.apply_window(pet_pixels, pet_window, False, minimum)
            if ct:
                ct_samples = ref_slice.modality_pixels
                ct_gray = DicomLoader.apply_window(ct_samples, ct_window, False)
                if not (np.isfinite(ct_samples) & np.isfinite(pet_pixels)).any():
                    warning = "当前切面没有 CT/PET 重叠区域，可调整切面或配准"
            if role == "ct":
                pixels, image, volume, window = ct_samples, ct_gray, ct, ct_window
            elif role == "fusion":
                pixels, volume, window = pet_pixels, pet, pet_window
                image = blend_pet_ct(ct_gray, pet_gray, pet_pixels, request.opacity, request.fusion_color_map)
            else:
                pixels, volume, window = pet_pixels, pet, pet_window
                image = pet_gray if request.pet_color_map == "grayscale" else pet_rgb(pet_gray, request.pet_color_map)
            frames.append(MprRenderResult(response_id=request.request_id, viewport_id=viewport_id,
                series_uid=volume.series_uid, view_type=plane, image=image, modality_pixel=pixels,
                frame_meta=self._meta(volume, ref_slice, window), mpr_frame=state.frame,
                plane_geometry=ref_slice.geometry, mpr_view_grids=state.view_grids))
        return PetBatchRenderResult(response_id=request.request_id, viewport_id=request.viewport_id,
            series_uid=pet.series_uid, frames=tuple(frames), state=state, pet_volume=pet,
            ct_volume=ct, pet_window=pet_window, ct_window=ct_window,
            ct_samples=ct_samples, warning=warning)

    @staticmethod
    def _meta(volume, sampled, window):
        g = sampled.geometry
        spacing = PixelSpacing(g.row_spacing, g.column_spacing)
        instance = replace(volume.representative_instance_meta, sop_instance_uid=None,
                           rows=g.rows, columns=g.columns, pixel_spacing=(g.row_spacing, g.column_spacing),
                           image_position=g.image_origin_patient)
        return FrameDisplayMeta(slice_index=sampled.slice_index, slice_count=sampled.slice_count,
            window=window, inverted=False, instance_meta=instance,
            geometry=ImageGeometryMeta(g.rows, g.columns, spacing, g.image_origin_patient,
                                       g.image_orientation_patient), pixel_value_meta=volume.pixel_value_meta)

    def _full_mip(self, volume):
        frame = MprFrame.standard_lps(volume.geometry.center_patient)
        sampled = self.reslicer.reslice(volume, MprPlane.CORONAL, frame)
        g = sampled.geometry
        corners = np.array([(*p, 1) for p in product(*[(0, n-1) for n in volume.modality_pixels.shape])])
        positions = (volume.geometry.voxel_to_patient @ corners.T).T[:, :3]
        normal = np.asarray(g.navigation_direction_patient)
        depths = (positions - g.image_origin_patient) @ normal
        count = max(2, int(np.ceil(np.ptp(depths) / g.navigation_spacing)) + 1)
        maximum = np.full((g.rows, g.columns), -np.inf, dtype=np.float32)
        peak_depth = np.full_like(maximum, np.nan)
        # Bounded memory: one sampled plane at a time, no full CT-grid PET copy.
        for offset in np.linspace(depths.min(), depths.max(), count):
            pixels = self.reslicer._sample_plane(volume, g, float(offset))
            better = np.isfinite(pixels) & (pixels > maximum)
            maximum[better] = pixels[better]
            peak_depth[better] = offset
        maximum[~np.isfinite(maximum)] = np.nan
        row, col = np.indices(maximum.shape)
        peaks = (np.asarray(g.image_origin_patient)[None, None, :]
                 + row[..., None] * g.row_spacing * np.asarray(g.row_direction_patient)
                 + col[..., None] * g.column_spacing * np.asarray(g.column_direction_patient)
                 + peak_depth[..., None] * normal).astype(np.float32)
        return replace(sampled, modality_pixels=maximum), peaks
