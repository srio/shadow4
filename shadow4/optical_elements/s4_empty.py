import numpy
from syned.beamline.optical_elements.ideal_elements.screen import Screen as SynedScreen
from syned.beamline.beamline_element import BeamlineElement
from shadow4.syned.element_coordinates import ElementCoordinates # TODO from syned.beamline.element_coordinates

from shadow4.optical_elements.s4_optical_element import S4OpticalElement

from shadow4.optical_elements.s4_beamline_element import S4BeamlineElement


class S4Empty(SynedScreen, S4OpticalElement):
    def __init__(self, name="Undefined"):
        super().__init__(name=name)


class S4EmptyElement(S4BeamlineElement):

    def __init__(self, optical_element=None, coordinates=None):
        super().__init__(optical_element if optical_element is not None else S4Empty(),
                         coordinates if coordinates is not None else ElementCoordinates())

    def set_positions(self, p=0.0, q=0.0, angle_radial=0.0, angle_radial_out=numpy.pi, angle_azimuthal=0.0):
        super().set_positions(p=p, q=q, angle_radial=angle_radial, angle_radial_out=angle_radial_out, angle_azimuthal=angle_azimuthal)


    def trace_beam(self,beam1):

        p, q, angle_radial, angle_radial_out, angle_azimuthal = self.get_positions()

        theta_grazing1 = numpy.pi / 2 - angle_radial
        theta_grazing2 = numpy.pi / 2 - angle_radial_out
        alpha1 = angle_azimuthal

        #
        beam = beam1.duplicate()

        #
        # put beam in mirror reference system
        #
        beam.rotate(alpha1, axis=2)
        beam.rotate(theta_grazing1, axis=1)
        beam.translation([0.0, -p * numpy.cos(theta_grazing1), p * numpy.sin(theta_grazing1)])

        #
        # oe does nothing
        #
        pass

        #
        # from oe reference system to image plane
        #
        beam_out = beam.duplicate()
        beam_out.change_to_image_reference_system(theta_grazing2, q)


        return beam_out, beam

