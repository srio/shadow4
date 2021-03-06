from shadow4.syned.shape import Toroid
from shadow4.beamline.optical_elements.mirrors.s4_mirror import S4MirrorElement, S4Mirror, ElementCoordinates
from shadow4.optical_surfaces.s4_toroid import S4Toroid

from shadow4.beamline.s4_optical_element import SurfaceCalculation, S4ToroidalOpticalElement

class S4ToroidalMirror(S4Mirror, S4ToroidalOpticalElement):
    def __init__(self,
                 name="Toroidal Mirror",
                 boundary_shape=None,
                 surface_calculation=SurfaceCalculation.INTERNAL,
                 min_radius=0.0,
                 maj_radius=0.0,
                 p_focus=0.0,
                 q_focus=0.0,
                 grazing_angle=0.0,
                 # inputs related to mirror reflectivity
                 f_reflec=0,  # reflectivity of surface: 0=no reflectivity, 1=full polarization
                 f_refl=0,  # 0=prerefl file
                 # 1=electric susceptibility
                 # 2=user defined file (1D reflectivity vs angle)
                 # 3=user defined file (1D reflectivity vs energy)
                 # 4=user defined file (2D reflectivity vs energy and angle)
                 file_refl="",  # preprocessor file fir f_refl=0,2,3,4
                 refraction_index=1.0  # refraction index (complex) for f_refl=1
                 ):
        S4ToroidalOpticalElement.__init__(self, surface_calculation,
                                          min_radius, maj_radius, p_focus, q_focus, grazing_angle)
        S4Mirror.__init__(self, name, boundary_shape, self._curved_surface_shape,
                          f_reflec, f_refl, file_refl, refraction_index)

class S4ToroidalMirrorElement(S4MirrorElement):
    def __init__(self, optical_element=None, coordinates=None):
        super().__init__(optical_element if optical_element is not None else S4ToroidalMirror(),
                         coordinates if coordinates is not None else ElementCoordinates())
        if not isinstance(self.get_optical_element().get_surface_shape(), Toroid):
            raise ValueError("Wrong Optical Element: only Toroid shape is accepted")

    def apply_local_reflection(self, beam):
        surface_shape = self.get_optical_element().get_surface_shape()

        print(">>>>> Toroidal mirror", surface_shape._min_radius, surface_shape._maj_radius)

        toroid = S4Toroid()
        toroid.set_toroid_radii(surface_shape._maj_radius, surface_shape._min_radius)

        mirr, normal = toroid.apply_specular_reflection_on_beam(beam)

        return mirr, normal
