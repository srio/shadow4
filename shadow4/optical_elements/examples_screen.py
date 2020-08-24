
import numpy
from shadow4.beam.beam import Beam
from shadow4.sources.source_geometrical.gaussian import SourceGaussian
from shadow4.optical_elements.screen import Screen


from shadow4.compatibility.beam3 import Beam3
from Shadow.ShadowTools import plotxy

from syned.beamline.optical_elements.ideal_elements.lens import IdealLens as SyIdelLens
from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.beamline_element import BeamlineElement

from syned.beamline.optical_elements.ideal_elements.screen import Screen as SyScreen

from shadow4.syned.absorbers.beam_stopper import BeamStopper as SyBeamStopper   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.filter import Filter as SyFilter                   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.holed_filter import HoledFilter as SyHoledFilter   # TODO: syned.beamline.optical_elements.
from shadow4.syned.absorbers.slit import Slit as SySlit                         # TODO: syned.beamline.optical_elements.


from shadow4.syned.shape import Rectangle, Ellipse, TwoEllipses # TODO from syned.beamline.shape


def get_sigmas_radiation(photon_energy,undulator_length):
    import scipy.constants as codata
    lambdan = 1e-10 * codata.h*codata.c/codata.e*1e10 / photon_energy # in m
    print("wavelength in m",lambdan)
    return 1e6*2.740/4/numpy.pi*numpy.sqrt(lambdan*undulator_length),1e6*0.69*numpy.sqrt(lambdan/undulator_length)


def test_screen(do_plot=True):

    #
    # collimated source
    #
    src = SourceGaussian.initialize_collimated_source(number_of_rays=10000,sigmaX=1e-6,sigmaZ=1e-6)

    interface = 'old' # 'new'

    if interface == 'new':
        beam = src.get_beam()
    elif interface == "old":
        beam = Beam()
        beam.genSource(src)
    print(beam.info())
    SX, SZ = (1e6*beam.get_standard_deviation(1),1e6*beam.get_standard_deviation(3))

    # if do_plot:
    #     beam3 = Beam3.initialize_from_shadow4_beam(beam)
    #     plotxy(beam3,1,3,nbins=100,title="SOURCE")

    #
    # screen definition
    #

    syscreen1 = SyScreen(name="Undefined")

    coordinates_syned = ElementCoordinates(p=100.0, q=0.0)

    beamline_element_syned = BeamlineElement(optical_element=syscreen1, coordinates=coordinates_syned)

    screen1 = Screen(beamline_element_syned=beamline_element_syned)

    print(screen1.info())

    #
    # trace
    #
    interface = 'new'
    if interface == 'new':
        beam2 = screen1.trace_beam(beam)
    elif interface == 'old':
        beam2 = beam.traceOE(screen1, 1, overwrite=False)

    #
    if do_plot:
        beam3 = Beam3.initialize_from_shadow4_beam(beam2)
        plotxy(beam3,1,3,nbins=100,title="SCREEN")


def test_slit(do_plot=True):

    src = SourceGaussian.initialize_collimated_source(number_of_rays=10000,sigmaX=1e-6,sigmaZ=1e-6)
    beam = src.get_beam()

    # if do_plot:
    #     beam3 = Beam3.initialize_from_shadow4_beam(beam)
    #     plotxy(beam3,1,3,nbins=100,title="SOURCE")

    #
    # slit definition
    #
    boundary_shape = Rectangle(x_left=-0.5e-6, x_right=0.5e-6, y_bottom=-0.5e-6, y_top=0.5e-6)

    syslit1 = SySlit(name="Undefined",boundary_shape=boundary_shape)

    coordinates_syned = ElementCoordinates(p=100.0, q=0.0)

    beamline_element_syned = BeamlineElement(optical_element=syslit1, coordinates=coordinates_syned)

    slit1 = Screen(beamline_element_syned=beamline_element_syned)

    print(slit1.info())

    #
    # trace
    #

    beam2 = slit1.trace_beam(beam)


    #
    if do_plot:
        beam3 = Beam3.initialize_from_shadow4_beam(beam2)
        plotxy(beam3,1,3,nbins=100,title="SLIT", nolost=True)



def test_beam_stopper(do_plot=True):

    src = SourceGaussian.initialize_collimated_source(number_of_rays=10000,sigmaX=1e-6,sigmaZ=1e-6)
    beam = src.get_beam()

    # if do_plot:
    #     beam3 = Beam3.initialize_from_shadow4_beam(beam)
    #     plotxy(beam3,1,3,nbins=100,title="SOURCE")

    #
    # slit definition
    #
    boundary_shape = Ellipse(-1e-6, 1e-6, -0.5e-6, 0.5e-6)

    sy1 = SyBeamStopper(name="Undefined",boundary_shape=boundary_shape)

    coordinates_syned = ElementCoordinates(p=100.0, q=0.0)

    beamline_element_syned = BeamlineElement(optical_element=sy1, coordinates=coordinates_syned)

    screen1 = Screen(beamline_element_syned=beamline_element_syned)

    print(screen1.info())

    #
    # trace
    #

    beam2 = screen1.trace_beam(beam)


    #
    if do_plot:
        beam3 = Beam3.initialize_from_shadow4_beam(beam2)
        plotxy(beam3,1,3,nbins=100,title="BEAM STOPPER", nolost=True)


def test_filter(do_plot=True):

    src = SourceGaussian.initialize_collimated_source(number_of_rays=10000,sigmaX=1e-6,sigmaZ=1e-6)
    beam = src.get_beam()

    # if do_plot:
    #     beam3 = Beam3.initialize_from_shadow4_beam(beam)
    #     plotxy(beam3,1,3,nbins=100,title="SOURCE")

    #
    # slit definition
    #
    boundary_shape = None # Rectangle(x_left=-0.5e-6, x_right=0.5e-6, y_bottom=-0.5e-6, y_top=0.5e-6)

    syfilter1 = SyFilter(name="Undefined",boundary_shape=boundary_shape,
                         material="/Users/srio/Oasys/Be.dat",
                         thickness=10e-6
                         )

    coordinates_syned = ElementCoordinates(p=100.0, q=0.0)

    beamline_element_syned = BeamlineElement(optical_element=syfilter1, coordinates=coordinates_syned)

    filter1 = Screen(beamline_element_syned=beamline_element_syned)

    print(filter1.info())

    #
    # trace
    #

    beam2 = filter1.trace_beam(beam)


    #
    if do_plot:
        beam3 = Beam3.initialize_from_shadow4_beam(beam2)
        plotxy(beam3,1,3,nbins=100,title="FILTER", nolost=True)



def test_holed_filter(do_plot=True):

    src = SourceGaussian.initialize_collimated_source(number_of_rays=10000,sigmaX=1e-6,sigmaZ=1e-6)
    beam = src.get_beam()

    # if do_plot:
    #     beam3 = Beam3.initialize_from_shadow4_beam(beam)
    #     plotxy(beam3,1,3,nbins=100,title="SOURCE")

    #
    # slit definition
    #
    boundary_shape = Rectangle(x_left=-0.5e-6, x_right=0.5e-6, y_bottom=-0.5e-6, y_top=0.5e-6)

    syfilter1 = SyHoledFilter(name="Undefined",boundary_shape=boundary_shape,
                         material="/Users/srio/Oasys/Be.dat",
                         thickness=10e-6
                         )

    coordinates_syned = ElementCoordinates(p=100.0, q=0.0)

    beamline_element_syned = BeamlineElement(optical_element=syfilter1, coordinates=coordinates_syned)

    filter1 = Screen(beamline_element_syned=beamline_element_syned)

    print(filter1.info())

    #
    # trace
    #

    beam2 = filter1.trace_beam(beam)


    #
    if do_plot:
        beam3 = Beam3.initialize_from_shadow4_beam(beam2)
        plotxy(beam3,1,3,nbins=100,title="HOLED FILTER", nolost=True)


if __name__ == "__main__":
    from srxraylib.plot.gol import set_qt
    set_qt()

    test_screen(do_plot=True)
    test_slit(do_plot=True)
    test_beam_stopper(do_plot=True)
    test_filter(do_plot=True)
    test_holed_filter(do_plot=True)
