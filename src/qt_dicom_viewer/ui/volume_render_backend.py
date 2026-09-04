"""VTK objects live exclusively on the GUI thread of the native 3D widget."""
from dataclasses import replace
import numpy as np
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkUnsignedCharArray
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkFiltersSources import vtkCubeSource
from vtkmodules.vtkRenderingCore import (
    vtkRenderer, vtkVolume, vtkVolumeProperty, vtkColorTransferFunction,
    vtkActor, vtkPolyDataMapper, vtkPropAssembly,
)
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor
from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
# Object-factory registration and font rendering; also visible to PyInstaller.
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
import vtkmodules.vtkRenderingFreeType  # noqa: F401
import vtkmodules.vtkInteractionStyle  # noqa: F401

from qt_dicom_viewer.core.volume_view import camera_parameters
from qt_dicom_viewer.model.volume_models import VOLUME_DIRECTIONS, VolumeBlendMode, VolumeDisplayState
from qt_dicom_viewer.volume_presets import VOLUME_PRESET_BY_ID


def create_orientation_marker():
    """Color cube cells, not just vtkAnnotatedCubeActor's face text properties."""
    source = vtkCubeSource()
    source.Update()
    polydata = source.GetOutput()
    colors = vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("FaceColors")
    for index in range(polydata.GetNumberOfCells()):
        points = polydata.GetCell(index).GetPoints()
        normal = np.mean([points.GetPoint(i) for i in range(points.GetNumberOfPoints())], axis=0)
        direction = max(VOLUME_DIRECTIONS, key=lambda d: np.dot(d.normal, normal))
        colors.InsertNextTuple3(*(int(direction.color[i:i+2], 16) for i in (1, 3, 5)))
    polydata.GetCellData().SetScalars(colors)
    mapper = vtkPolyDataMapper()
    mapper.SetInputData(polydata)
    mapper.SetScalarModeToUseCellData()
    mapper.SetColorModeToDirectScalars()
    surface = vtkActor()
    surface.SetMapper(mapper)
    surface.GetProperty().LightingOff()
    labels = vtkAnnotatedCubeActor()
    labels.GetCubeProperty().SetOpacity(0)
    for axis, positive, negative in (("X", "L", "R"), ("Y", "P", "A"), ("Z", "S", "I")):
        for side, face in (("Plus", positive), ("Minus", negative)):
            getattr(labels, f"Set{axis}{side}FaceText")(face)
            prop = getattr(labels, f"Get{axis}{side}FaceProperty")()
            prop.SetColor(1, 1, 1)
            prop.LightingOff()
    labels.GetTextEdgesProperty().SetColor(1, 1, 1)
    labels.GetTextEdgesProperty().LightingOff()
    assembly = vtkPropAssembly()
    assembly.AddPart(surface)
    assembly.AddPart(labels)
    return assembly, labels, surface


def create_transfer_functions(preset, window, opacity_scale=1.0):
    if not np.isfinite(window.width) or not np.isfinite(window.center) or window.width < 1:
        raise ValueError("窗宽必须至少为 1，窗宽窗位必须为有限数值")
    low = float(window.center)-window.width/2
    colors = vtkColorTransferFunction()
    for position, red, green, blue in preset.colors:
        colors.AddRGBPoint(low+window.width*position, red, green, blue)
    opacity = vtkPiecewiseFunction()
    for position, alpha in preset.opacity:
        opacity.AddPoint(low+window.width*position, alpha*opacity_scale)
    return colors, opacity


def volume_to_vtk(volume):
    geometry = volume.geometry
    pixels = np.ascontiguousarray(volume.modality_pixels, dtype=np.float32)
    if pixels.shape != (geometry.slice_count, geometry.rows, geometry.columns):
        raise ValueError("体数据尺寸与空间信息不一致")
    spacing = (geometry.column_spacing, geometry.row_spacing, geometry.slice_spacing)
    if not all(np.isfinite(v) and v > 0 for v in spacing):
        raise ValueError("体素间距必须为有限正数")
    if not np.all(np.isfinite(pixels)):
        raise ValueError("体数据包含非有限像素值")
    image = vtkImageData()
    image.SetDimensions(geometry.columns, geometry.rows, geometry.slice_count)
    image.SetSpacing(*spacing)
    image.SetOrigin(*geometry.origin_patient)
    directions = np.column_stack((geometry.column_index_direction_patient,
                                  geometry.row_index_direction_patient,
                                  geometry.slice_index_direction_patient))
    image.SetDirectionMatrix(directions.ravel().tolist())
    # C-order data already has x (column) varying fastest. No transpose/quantization.
    image.GetPointData().SetScalars(numpy_to_vtk(pixels.reshape(-1), deep=False))
    return image, pixels


class VolumeRenderBackend:
    def __init__(self, widget):
        self.widget = widget
        self.window = widget.GetRenderWindow()
        self.window.SetMultiSamples(0)
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(2/255, 7/255, 14/255)
        self.window.AddRenderer(self.renderer)
        self.mapper = vtkSmartVolumeMapper()
        self.mapper.SetBlendModeToComposite()
        # Keep the same ray step while dragging and after release. VTK's
        # interactive adjustment otherwise trades sampling quality for its
        # requested frame rate, which makes the volume visibly blur and then
        # snap back when interaction stops.
        self.mapper.SetInteractiveAdjustSampleDistances(False)
        self.mapper.SetAutoAdjustSampleDistances(False)
        self.actor = vtkVolume()
        self.actor.SetMapper(self.mapper)
        self.properties = vtkVolumeProperty()
        self.properties.SetInterpolationTypeToLinear()
        self.properties.ShadeOn()
        self.properties.SetAmbient(0.3)
        self.properties.SetDiffuse(0.7)
        self.properties.SetSpecular(0.15)
        self.actor.SetProperty(self.properties)
        self.renderer.AddVolume(self.actor)
        self.renderer.GetActiveCamera().ParallelProjectionOn()
        self.orientation_actor, self.cube, self.cube_surface = create_orientation_marker()
        self.marker = vtkOrientationMarkerWidget()
        self.marker.SetOrientationMarker(self.orientation_actor)
        self.marker.SetInteractor(self.window.GetInteractor())
        self.marker.SetCurrentRenderer(self.renderer)
        self._initialized = False
        self.volume = None
        self._image = None
        self._pixels = None
        self._sample_distance = None
        self._applied_display = None
        self._error = False
        self._observers = [(obj, obj.AddObserver("ErrorEvent", self._on_error))
                           for obj in (self.window, self.mapper)]

    def _on_error(self, *_):
        self._error = True

    def set_volume(self, volume):
        image, pixels = volume_to_vtk(volume)
        self.mapper.SetInputData(image)
        geometry = volume.geometry
        self._sample_distance = min(
            geometry.column_spacing, geometry.row_spacing, geometry.slice_spacing)
        self.mapper.SetSampleDistance(self._sample_distance)
        self._image, self._pixels, self.volume = image, pixels, volume
        self._applied_display = None

    def apply_display(self, state):
        if self.volume is None:
            return
        if state.window is None:
            state = replace(state, window=self.volume.default_window)
        if state == self._applied_display:
            return
        preset = VOLUME_PRESET_BY_ID[state.preset_id]
        additive = preset.blend_mode == VolumeBlendMode.ADDITIVE
        opacity_scale = 1.0
        if additive:
            # Additive integrates opacity-weighted normalized samples. Fix the
            # ray step and normalize by physical diagonal so interaction quality
            # and denser voxel sampling don't change exposure or saturate white.
            g = self.volume.geometry
            step = self._sample_distance
            diagonal = np.linalg.norm(((g.columns-1)*g.column_spacing,
                                       (g.rows-1)*g.row_spacing,
                                       (g.slice_count-1)*g.slice_spacing))
            opacity_scale = min(1.0, 3*step/max(step, diagonal))
            self.mapper.SetBlendModeToAdditive()
        else:
            if preset.blend_mode == VolumeBlendMode.MIP:
                self.mapper.SetBlendModeToMaximumIntensity()
            else:
                self.mapper.SetBlendModeToComposite()
        colors, opacity = create_transfer_functions(preset, state.window, opacity_scale)
        self.properties.SetColor(colors)
        self.properties.SetScalarOpacity(opacity)
        self.properties.SetScalarOpacityUnitDistance(preset.opacity_unit_distance)
        self.properties.SetShade(preset.shade)
        self.properties.SetAmbient(preset.ambient)
        self.properties.SetDiffuse(preset.diffuse)
        self.properties.SetSpecular(preset.specular)
        self.properties.SetSpecularPower(preset.specular_power)
        self._applied_display = state

    def apply_state(self, state):
        if self.volume is None:
            return
        width, height = max(1, self.widget.width()), max(1, self.widget.height())
        p = camera_parameters(self.volume.geometry, state, (width, height))
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(*p["position"])
        camera.SetFocalPoint(*p["focal"])
        camera.SetViewUp(*p["up"])
        camera.SetParallelScale(p["scale"])
        camera.SetClippingRange(*p["clipping"])
        edge = min(96, max(1, min(width, height)-24))
        margin = min(12, max(0, (min(width, height)-edge)/2))
        self.marker.SetViewport((width-margin-edge)/width, (height-margin-edge)/height,
                                (width-margin)/width, (height-margin)/height)

    def render(self, state, interactive=False, display_state=None):
        if self.volume is None:
            return
        self._error = False
        self.apply_display(display_state or VolumeDisplayState())
        if not self._initialized:
            self.widget.Initialize()
            # Input is handled by the Python controller, not the default VTK style.
            self.window.GetInteractor().SetInteractorStyle(None)
            self.marker.SetEnabled(True)
            self.marker.InteractiveOff()
            self._initialized = True
        self.apply_state(state)
        # DesiredUpdateRate also feeds VTK's interactive quality heuristics.
        # Keep it identical so an interactive render and its settled render
        # use the same quality path. The host already coalesces pointer events.
        self.window.SetDesiredUpdateRate(0.01)
        self.window.Render()
        if self._error:
            raise RuntimeError("VTK 无法绘制该体数据，请检查显卡驱动或尝试较小的序列")

    def dispose(self):
        if self._initialized:
            self.marker.SetEnabled(False)
        self.marker.SetInteractor(None)
        for obj, observer in self._observers:
            obj.RemoveObserver(observer)
        self._observers.clear()
        self.renderer.RemoveAllViewProps()
        self.mapper.RemoveAllInputs()
        self.window.RemoveRenderer(self.renderer)
        self.widget.Finalize()
        self.volume = self._image = self._pixels = self._sample_distance = None
        self._applied_display = None
