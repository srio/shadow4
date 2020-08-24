#
# the screen optical element:
#       deals with screens, slits, beam-stoppers and absorbers (as in shadow3)
#       it is a stand-alone optical element (contrary to shadow4)
#
#
#
import numpy

from syned.beamline.optical_elements.ideal_elements.screen import Screen as SyScreen


from shadow4.syned.absorbers.beam_stopper import BeamStopper as SyBeamStopper   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.filter import Filter as SyFilter                   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.holed_filter import HoledFilter as SyHoledFilter   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.slit import Slit as SySlit                         # TODO: syned.beamline.optical_elements.


from syned.beamline.beamline_element import BeamlineElement
from syned.beamline.element_coordinates import ElementCoordinates
from shadow4.syned.shape import Rectangle, Ellipse, TwoEllipses # TODO from syned.beamline.shape

from shadow4.physical_models.prerefl.prerefl import PreRefl

class Screen(object):
    def __init__(self, beamline_element_syned = None):
        if beamline_element_syned is None:
            self._beamline_element_syned = BeamlineElement(
                SyScreen(name="Undefined"),
                ElementCoordinates(p=0.0, q=0.0, angle_radial=0.0, angle_azimuthal=0.0))
        else:
            ok = False
            for obj in [SyScreen, SySlit, SyBeamStopper, SyFilter, SyHoledFilter]:
                if isinstance(beamline_element_syned._optical_element, obj): ok = True
            if ok:
                self._beamline_element_syned = beamline_element_syned
            else:
                raise Exception("Please initialize shadow4 Screen with syned Screen, Slit, BeamStopper, Filter or HoledFilter")


    def set_positions(self, p, q):
        self._beamline_element_syned.get_coordinates()._p = p
        self._beamline_element_syned.get_coordinates()._q = q
        self._beamline_element_syned.get_coordinates()._angle_radial = 0.0
        self._beamline_element_syned.get_coordinates()._angle_azimuthal = 0.0

    def get_positions(self):
        return self._beamline_element_syned.get_coordinates()._p, \
            self._beamline_element_syned.get_coordinates()._q


    def info(self):
        if self._beamline_element_syned is not None:
            return (self._beamline_element_syned.info())

    def trace_beam(self,beam1,flag_lost_value=-1):
        beam = beam1.duplicate()

        p,q = self.get_positions()

        if p != 0.0:
            beam.retrace(p + q, resetY=True)

        if isinstance(self._beamline_element_syned._optical_element, SyScreen):
            apply_crop = False
            apply_attenuation = False
        elif isinstance(self._beamline_element_syned._optical_element, SySlit):
            apply_crop = True
            negative = False
            apply_attenuation = False
        elif isinstance(self._beamline_element_syned._optical_element, SyBeamStopper):
            apply_crop = True
            negative = True
            apply_attenuation = False
        elif isinstance(self._beamline_element_syned._optical_element, SyFilter):
            apply_crop = True
            negative = False
            apply_attenuation = True
        elif isinstance(self._beamline_element_syned._optical_element, SyHoledFilter):
            apply_crop = True
            negative = True
            apply_attenuation = True

        if apply_crop:
            shape = self._beamline_element_syned._optical_element.get_boundary_shape()
            if isinstance(shape, type(None)):
                pass
            elif isinstance(shape, Rectangle):
                x_left, x_right, y_bottom, y_top = shape.get_boundaries()
                beam.crop_rectangle(1, x_left, x_right, 3, y_bottom, y_top,
                                    negative=negative, flag_lost_value=flag_lost_value)
            elif isinstance(shape, Ellipse):
                a_axis_min, a_axis_max, b_axis_min, b_axis_max = shape.get_boundaries()
                beam.crop_ellipse(1, a_axis_min, a_axis_max, 3, b_axis_min, b_axis_max,
                                  negative=negative, flag_lost_value=flag_lost_value)
            else:
                raise Exception("Undefined slit shape")


        if apply_attenuation:
            material = self._beamline_element_syned._optical_element.get_material()
            thickness = self._beamline_element_syned._optical_element.get_thickness()

            if material is not None:
                try:
                    prerefl_file = material
                    pr = PreRefl()
                    pr.read_preprocessor_file(prerefl_file)
                    print(pr.info())
                except:
                    raise Exception("the syned material in filter definition must contain the prerefl preprocessor file")

                energy = beam.get_column(26)
                # tmp = pr.get_attenuation_coefficient(energy[0],verbose=1)
                coeff = pr.get_attenuation_coefficient(energy)
                I_over_I0 = numpy.exp(- coeff * thickness * 1e2)
                sqrt_I_over_I0 = numpy.sqrt(I_over_I0)
                print(energy, coeff, I_over_I0)
                beam.apply_reflectivities(sqrt_I_over_I0, sqrt_I_over_I0)


        if q != 0.0:
            beam.retrace(q, resetY=True)

        return beam


