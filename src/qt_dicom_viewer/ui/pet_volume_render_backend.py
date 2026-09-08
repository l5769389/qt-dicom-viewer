"""Depth-correct CT/PET compositing with separate physical grids and transfer functions."""
from dataclasses import replace
from itertools import product
import numpy as np
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingCore import vtkVolume, vtkVolumeProperty, vtkColorTransferFunction
from vtkmodules.vtkRenderingVolume import vtkMultiVolume

from qt_dicom_viewer.core.pet_fusion import rigid_matrix
from qt_dicom_viewer.core.pseudocolor import COLOR_MAP_SPECS
from qt_dicom_viewer.model.dicom_core import VolumeGeometry
from qt_dicom_viewer.volume_presets import VOLUME_PRESET_BY_ID
from .volume_render_backend import VolumeRenderBackend, volume_to_vtk, create_transfer_functions


def fusion_camera_geometry(ct, pet, transform):
    """Fit the union in patient space, including rotated and translated PET."""
    corners = []
    for volume, matrix in ((ct, np.eye(4)), (pet, rigid_matrix(transform))):
        g = volume.geometry
        indices = np.array([(*p, 1) for p in product((0, g.slice_count-1),
                                                   (0, g.rows-1), (0, g.columns-1))])
        corners.extend((matrix @ g.voxel_to_patient @ indices.T).T[:, :3])
    low, high = np.min(corners, axis=0), np.max(corners, axis=0)
    size = np.maximum(high-low, .001)
    return VolumeGeometry(slice_count=2, rows=2, columns=2,
        column_spacing=size[0], row_spacing=size[1], slice_spacing=size[2],
        origin_patient=tuple(low), column_index_direction_patient=(1, 0, 0),
        row_index_direction_patient=(0, 1, 0), slice_index_direction_patient=(0, 0, 1))


def pet_transfer_functions(upper, threshold, palette, alpha):
    if not np.isfinite([upper, threshold, alpha]).all() or not 0 <= threshold < upper or not 0 <= alpha <= 1:
        raise ValueError("PET 三维阈值或透明度无效")
    colors = vtkColorTransferFunction()
    for position, rgb in COLOR_MAP_SPECS[palette][1]:
        colors.AddRGBPoint(position * upper, *(value/255 for value in rgb))
    opacity = vtkPiecewiseFunction()
    opacity.AddPoint(0, 0)
    opacity.AddPoint(threshold, 0)
    opacity.AddPoint(threshold + (upper-threshold)*.3, .25*alpha)
    opacity.AddPoint(upper, alpha)
    return colors, opacity


def padding_safe_vtk(volume, pet=False):
    data = volume.modality_pixels
    finite = np.isfinite(data)
    if not finite.any():
        raise ValueError("三维体数据没有有效像素")
    if not finite.all():
        # PET padding/zero are transparent; CT padding lies below all presets.
        fill = 0 if pet else min(-4096., float(data[finite].min())-1)
        data = np.where(finite, data, fill).astype(np.float32)
    image, pixels = volume_to_vtk(replace(volume, modality_pixels=data))
    image.GetPointData().GetScalars().SetName("Intensity")
    return image, pixels


class PetVolumeRenderBackend(VolumeRenderBackend):
    def __init__(self, widget, controller):
        super().__init__(widget)
        self.controller = controller
        self.renderer.RemoveVolume(self.actor)
        self.actor = vtkMultiVolume()
        self.actor.SetMapper(self.mapper)
        self.layers = (vtkVolume(), vtkVolume())
        for port, layer in enumerate(self.layers):
            prop = vtkVolumeProperty()
            prop.SetInterpolationTypeToLinear()
            prop.IndependentComponentsOn()
            layer.SetProperty(prop)
            self.actor.SetVolume(layer, port)
        self.renderer.AddVolume(self.actor)
        self._sources = [None, None]
        self._buffers = [None, None]

    def set_volume(self, volume):
        self.volume = volume

    def apply_mask(self, mask):
        pass  # The 3D tab has no destructive crop/edit tools.

    def apply_display(self, state):
        c, scene = self.controller, self.controller.scene
        if scene is None:
            return
        for port, volume in enumerate((scene.ct_volume, scene.pet_volume)):
            key = (id(volume.modality_pixels), volume.geometry)
            if key != self._sources[port]:
                image, pixels = padding_safe_vtk(volume, pet=bool(port))
                self.mapper.SetInputDataObject(port, image)
                self._sources[port], self._buffers[port] = key, (image, pixels)
        transform = rigid_matrix(scene.request.transform)
        matrix = vtkMatrix4x4()
        matrix.DeepCopy(transform.ravel())
        self.layers[1].SetUserMatrix(matrix)
        self.camera_geometry = fusion_camera_geometry(scene.ct_volume, scene.pet_volume, transform)
        preset = VOLUME_PRESET_BY_ID[c.ctPreset]
        colors, opacity = create_transfer_functions(preset,
            preset.default_window or scene.ct_window, c.ctOpacity if c.volumeMode != "pet" else 0)
        ct_prop = self.layers[0].GetProperty()
        ct_prop.SetColor(colors)
        ct_prop.SetScalarOpacity(opacity)
        ct_prop.SetShade(preset.shade)
        ct_prop.SetAmbient(preset.ambient)
        ct_prop.SetDiffuse(preset.diffuse)
        ct_prop.SetSpecular(preset.specular)
        ct_prop.SetScalarOpacityUnitDistance(preset.opacity_unit_distance)
        colors, opacity = pet_transfer_functions(c.petUpper, c.petThreshold, c.petPalette,
            c.petOpacity if c.volumeMode != "ct" else 0)
        pet_prop = self.layers[1].GetProperty()
        pet_prop.SetColor(colors)
        pet_prop.SetScalarOpacity(opacity)
        pet_prop.ShadeOff()
        g = scene.pet_volume.geometry
        pet_prop.SetScalarOpacityUnitDistance(min(g.column_spacing, g.row_spacing, g.slice_spacing))
        self.mapper.SetSampleDistance(min(scene.ct_volume.geometry.column_spacing,
            scene.ct_volume.geometry.row_spacing, scene.ct_volume.geometry.slice_spacing,
            g.column_spacing, g.row_spacing, g.slice_spacing))

    def dispose(self):
        super().dispose()
        self._sources, self._buffers = [None, None], [None, None]
        self.controller = None
