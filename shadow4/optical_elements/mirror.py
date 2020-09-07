import numpy

from shadow4.syned.shape import Rectangle, Ellipse, TwoEllipses # TODO from syned.beamline.shape
from shadow4.syned.shape import Toroidal, Conic, SurfaceData, Plane, Sphere, Ellipsoid, Paraboloid, Hyperboloid # TODO from syned.beamline.shape
from shadow4.syned.shape import SphericalCylinder, EllipticalCylinder, HyperbolicCylinder # TODO from syned.beamline.shape


from syned.beamline.element_coordinates import ElementCoordinates
from syned.beamline.beamline import BeamlineElement

from syned.beamline.optical_element_with_surface_shape import OpticalElementsWithSurfaceShape
from syned.beamline.optical_elements.mirrors.mirror import Mirror as SyMirror

from shadow4.optical_surfaces.conic import Conic as S4Conic
from shadow4.optical_surfaces.toroid import Toroid as S4Toroid
from shadow4.optical_surfaces.mesh import Mesh as S4Mesh
from shadow4.physical_models.prerefl.prerefl import PreRefl


class Mirror(object):

    def __init__(self, beamline_element_syned=None,
                 f_reflec=0, # reflectivity of surface: 0=no reflectivity, 1=full polarization
                 f_refl=0,   # 0=prerefl file, 1=electric susceptibility
                             # 2=user defined file (1D reflectivity vs angle)
                             # 3=user defined file (1D reflectivity vs energy)
                             # 4=user defined file (2D reflectivity vs energy and angle)
                file_refl="", # preprocessor file
                 ):

        self._f_reflec = f_reflec
        self._f_refl = f_refl
        self._file_refl = file_refl



        if f_reflec not in [0,1]: raise NotImplementedError
        if f_refl not in [0]: raise NotImplementedError



        if beamline_element_syned is None:

            self._beamline_element_syned = BeamlineElement(
                SyMirror(name="Undefined",
                 surface_shape=Conic(conic_coefficients=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,-1.0, 0.0]), #plane
                 boundary_shape=None,
                 coating=None,
                 coating_thickness=None),
                ElementCoordinates())

        else:

            if isinstance(beamline_element_syned._optical_element, SyMirror):
                pass
            else:
                raise Exception("Please initialize shadow4 Mirror with syned Mirror")

            ok = False
            for obj in [Conic, Toroidal, SurfaceData, Plane, Sphere, Ellipsoid, Paraboloid, Hyperboloid, SphericalCylinder]:
                if isinstance(beamline_element_syned._optical_element._surface_shape, obj): ok = True
            if ok:
                self._beamline_element_syned = beamline_element_syned
            else:
                raise Exception(
                    "Please initialize shadow4 Mirror with syned Mirror surface shape as Conic, Toroidal, SurfaceData, Plane, Sphere, Ellipsoid, Paraboloid, Hyperboloid, SphericalCylinder")



    def info(self):
        if self._beamline_element_syned is not None:
            return (self._beamline_element_syned.info())

    def trace_beam(self,beam_in,flag_lost_value=-1):

        p = self._beamline_element_syned.get_coordinates().p()
        q = self._beamline_element_syned.get_coordinates().q()
        theta_grazing1 = numpy.pi / 2 - self._beamline_element_syned.get_coordinates().angle_radial()
        alpha1 = self._beamline_element_syned.get_coordinates().angle_azimuthal()

        #
        beam = beam_in.duplicate()

        #
        # put beam in mirror reference system
        #
        beam.rotate(alpha1, axis=2)
        beam.rotate(theta_grazing1, axis=1)
        beam.translation([0.0, -p * numpy.cos(theta_grazing1), p * numpy.sin(theta_grazing1)])

        #
        # reflect beam in the mirror surface
        #
        soe = self._beamline_element_syned.get_optical_element()

        v_in = beam.get_columns([4,5,6])
        if not isinstance(soe, OpticalElementsWithSurfaceShape): # undefined
            raise Exception("Undefined mirror")
        else:
            surshape = self._beamline_element_syned.get_optical_element().get_surface_shape()
            if isinstance(surshape,Conic):
                print(">>>>> Conic mirror")
                conic = self._beamline_element_syned.get_optical_element().get_surface_shape()
                ccc = S4Conic.initialize_from_coefficients(conic._conic_coefficients)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)
            elif isinstance(surshape, Toroidal):
                print(">>>>> Toroidal mirror",self._beamline_element_syned.get_optical_element().get_surface_shape()._min_radius,
                      self._beamline_element_syned.get_optical_element().get_surface_shape()._maj_radius)
                toroid = S4Toroid()
                toroid.set_toroid_radii( \
                    self._beamline_element_syned.get_optical_element().get_surface_shape()._maj_radius,
                    self._beamline_element_syned.get_optical_element().get_surface_shape()._min_radius,)
                mirr, normal = toroid.apply_specular_reflection_on_beam(beam)
            elif isinstance(surshape, SurfaceData):
                print(">>>>> SurfaceData mirror")
                num_mesh = S4Mesh()
                # num_mesh.load_h5file(self._beamline_element_syned.get_optical_element().get_surface_shape().surface_data_file)
                num_mesh.load_surface_data(self._beamline_element_syned.get_optical_element().get_surface_shape())
                mirr,normal,t,x1,v1,x2,v2 = num_mesh.apply_specular_reflection_on_beam(beam)
            elif isinstance(surshape, Plane):
                print(">>>>> Plane mirror")
                ccc = S4Conic.initialize_as_plane()
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)
            elif isinstance(surshape, SphericalCylinder):  # Note this check must come before Sphere as SphericalCylinder is Sphere
                print(">>>>> SphericalCylinder mirror")
                if surshape.get_direction() == 0:
                    cylangle = 0.0
                elif surshape.get_direction() == 1:
                    cylangle = numpy.pi / 2
                else:
                    raise Exception("Undefined cylinder direction")

                ccc = S4Conic.initialize_as_sphere_from_curvature_radius(surshape.get_radius(),cylindrical=True,cylangle=cylangle)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            elif isinstance(surshape, Sphere):
                print(">>>>> Sphere mirror")
                ccc = S4Conic.initialize_as_sphere_from_curvature_radius(surshape.get_radius(),cylindrical=False,cylangle=0.0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            elif isinstance(surshape, EllipticalCylinder):
                print(">>>>> EllipticalCylinder mirror",surshape)
                ccc = S4Conic.initialize_as_ellipsoid_from_focal_distances(surshape.get_p(),surshape.get_q(),
                            surshape.get_grazing_angle(), cylindrical=0, cylangle=0.0, switch_convexity=0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            elif isinstance(surshape, Ellipsoid):
                print(">>>>> Ellipsoid mirror",surshape)
                ccc = S4Conic.initialize_as_ellipsoid_from_focal_distances(surshape.get_p(),surshape.get_q(),
                            surshape.get_grazing_angle(), cylindrical=0, cylangle=0.0, switch_convexity=0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            elif isinstance(surshape, HyperbolicCylinder):
                print(">>>>> HyperbolicCylinder mirror",surshape)
                ccc = S4Conic.initialize_as_hyperboloid_from_focal_distances(surshape.get_p(),surshape.get_q(),
                            surshape.get_grazing_angle(), cylindrical=1, cylangle=0.0, switch_convexity=0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            elif isinstance(surshape, Hyperboloid):
                print(">>>>> Hyperboloid mirror",surshape)
                ccc = S4Conic.initialize_as_hyperboloid_from_focal_distances(surshape.get_p(),surshape.get_q(),
                            surshape.get_grazing_angle(), cylindrical=0, cylangle=0.0, switch_convexity=0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)


            elif isinstance(surshape, Paraboloid):
                print(">>>>> Paraboloid mirror",surshape)
                if surshape.get_at_infinity == 0:
                    p = 1e10
                    q = surshape.get_pole_to_focus()
                else:
                    q = 1e10
                    p = surshape.get_pole_to_focus()

                ccc = S4Conic.initialize_as_paraboloid_from_focal_distances(p,q,
                            surshape.get_grazing_angle(), cylindrical=0, cylangle=0.0, switch_convexity=0)
                mirr, normal = ccc.apply_specular_reflection_on_beam(beam)

            else:
                raise Exception("cannot trace this surface shape")

        #
        # apply mirror boundaries
        #
        mirr.apply_boundaries_syned(self._beamline_element_syned.get_optical_element().get_boundary_shape(),
                                    flag_lost_value=flag_lost_value)

        #
        # apply mirror reflectivity
        # TODO: add phase
        #

        coating = self._beamline_element_syned.get_optical_element()._coating
        print(">>>>>>>>>>>>>>>>>> COATING: ", coating)
        if self._f_reflec == 0:
            pass
        elif self._f_reflec == 1: # full polarization
            v_out = beam.get_columns([4, 5, 6])
            angle_in = numpy.arccos( v_in[0,:] * normal[0,:] +
                                     v_in[1,:] * normal[1,:] +
                                     v_in[2,:] * normal[2,:])

            angle_out = numpy.arccos( v_out[0,:] * normal[0,:] +
                                     v_out[1,:] * normal[1,:] +
                                     v_out[2,:] * normal[2,:])

            grazing_angle_mrad = 1e3 * (numpy.pi / 2 - angle_in)

            if self._f_refl == 0: # prerefl
                prerefl_file = self._file_refl
                print(">>>>>>>>>>> PREREFL FILE", prerefl_file)
                pr = PreRefl()
                pr.read_preprocessor_file(prerefl_file)
                print(pr.info())

                Rs, Rp, Ru = pr.reflectivity_fresnel(grazing_angle_mrad=grazing_angle_mrad,
                                                     photon_energy_ev=beam.get_column(-11),
                                                     roughness_rms_A=0.0)

            elif self._f_refl == 1:  # alpha, gamma, electric susceptibilities
                raise Exception("Not implemented f_refl == 1")
                # ! C
                # ! C Computes the optical coefficients.
                # ! C
                # COS_REF =  SQRT(1.0D0 - SIN_REF**2)
                # RHO  =   SIN_REF**2 - ALFA
                # RHO  =   RHO + SQRT ((SIN_REF**2 - ALFA)**2 + gamma1**2)
                # RHO  =   SQRT(RHO/2)
                # ! C
                # ! C Computes now the reflectivities
                # ! C
                # RS1  =   4*(RHO**2)*(ABS(SIN_REF)-RHO)**2 + gamma1**2
                # RS2  =   4*(RHO**2)*(ABS(SIN_REF)+RHO)**2 + gamma1**2
                # R_S  =   RS1/RS2
                # ! C
                # ! C Computes now the polarization ratio
                # ! C
                # RATIO1  =   4*RHO**2*(RHO*ABS(SIN_REF)-COS_REF**2)**2 + &
                # gamma1**2*SIN_REF**2
                # RATIO2  =   4*RHO**2*(RHO*ABS(SIN_REF)+COS_REF**2)**2 + &
                # gamma1**2*SIN_REF**2
                # RATIO  =   RATIO1/RATIO2
                # ! C
                # ! C The reflectivity for p light will be
                # ! C
                # R_P  =   R_S*RATIO
                # R_S  =   SQRT(R_S)
                # R_P  =   SQRT(R_P)

            elif self._f_refl == 2:  # user angle
                raise Exception("Not implemented f_refl == 2")

               # if self.user_defined_file_type == 0: # angle vs refl.
               #      values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/angle." +
               #                                             ("0" + str(input_beam._oe_number) if (input_beam._oe_number < 10) else
               #                                              str(input_beam._oe_number))))
               #
               #      beam_incident_angles = 90.0 - values[:, 1]
               #
               #      values = numpy.loadtxt(os.path.abspath(self.file_reflectivity) if self.file_reflectivity.startswith('/') else
               #                             os.path.abspath(os.path.curdir + "/" + self.file_reflectivity))
               #
               #      mirror_grazing_angles = values[:, 0]
               #      mirror_reflectivities = values[:, 1]
               #
               #      if mirror_grazing_angles[-1] < mirror_grazing_angles[0]: # XOPPY MLayer gives angles in descendent order
               #          mirror_grazing_angles = values[:, 0][::-1]
               #          mirror_reflectivities = values[:, 1][::-1]
               #
               #      if self.user_defined_angle_units == 0: mirror_grazing_angles = numpy.degrees(1e-3*mirror_grazing_angles) # mrad to deg
               #
               #      interpolated_weight_s = numpy.sqrt(numpy.interp(beam_incident_angles,
               #                                                      mirror_grazing_angles,
               #                                                      mirror_reflectivities,
               #                                                      left=mirror_reflectivities[0],
               #                                                      right=mirror_reflectivities[-1]))
               #      interpolated_weight_p = interpolated_weight_s

            elif self._f_refl == 3:  # user energy
                raise Exception("Not implemented f_refl == 3")

                # elif self.user_defined_file_type == 1: # Energy vs Refl.
                #     beam_energies = ShadowPhysics.getEnergyFromShadowK(input_beam._beam.rays[:, 10])
                #
                #     values = numpy.loadtxt(os.path.abspath(os.path.abspath(self.file_reflectivity)  if self.file_reflectivity.startswith('/') else
                #                                            os.path.abspath(os.path.curdir + "/" + self.file_reflectivity)))
                #
                #     mirror_energies = values[:, 0]
                #     mirror_reflectivities = values[:, 1]
                #
                #     if self.user_defined_energy_units == 1: mirror_energies *= 1e3 # KeV to eV
                #
                #     interpolated_weight_s = numpy.sqrt(numpy.interp(beam_energies,
                #                                                     mirror_energies,
                #                                                     mirror_reflectivities,
                #                                                     left=mirror_reflectivities[0],
                #                                                     right=mirror_reflectivities[-1]))
                #     interpolated_weight_p = interpolated_weight_s

            elif self._f_refl == 4:  # user 2D
                raise Exception("Not implemented f_refl == 4")

                # elif self.user_defined_file_type == 2: # 2D Energy vs Angle vs Reflectivity
                #     values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/angle." +
                #                                            ("0" + str(input_beam._oe_number) if (input_beam._oe_number < 10) else
                #                                             str(input_beam._oe_number))))
                #
                #     beam_incident_angles = 90.0 - values[:, 1]
                #
                #     beam_energies = ShadowPhysics.getEnergyFromShadowK(input_beam._beam.rays[:, 10])
                #
                #     values = numpy.loadtxt(os.path.abspath(os.path.abspath(self.file_reflectivity)  if self.file_reflectivity.startswith('/') else
                #                                            os.path.abspath(os.path.curdir + "/" + self.file_reflectivity)))
                #
                #     mirror_energies       = values[:, 0]
                #     mirror_grazing_angles = values[:, 1]
                #     mirror_energies         = numpy.unique(mirror_energies)
                #     mirror_grazing_angles   = numpy.unique(mirror_grazing_angles)
                #     if self.user_defined_angle_units  == 0: mirror_grazing_angles = numpy.degrees(1e-3*mirror_grazing_angles)
                #     if self.user_defined_energy_units == 1: mirror_energies *= 1e3 # KeV to eV
                #
                #     def get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities):
                #         mirror_reflectivities = numpy.reshape(mirror_reflectivities, (mirror_energies.shape[0], mirror_grazing_angles.shape[0]))
                #
                #         interpolator = RectBivariateSpline(mirror_energies, mirror_grazing_angles, mirror_reflectivities, kx=2, ky=2)
                #
                #         interpolated_weight = numpy.zeros(beam_energies.shape[0])
                #         for energy, angle, i in zip(beam_energies, beam_incident_angles, range(interpolated_weight.shape[0])):
                #             interpolated_weight[i] = numpy.sqrt(interpolator(energy, angle))
                #         interpolated_weight[numpy.where(numpy.isnan(interpolated_weight))] = 0.0
                #
                #         return interpolated_weight
                #
                #     if values.shape[1] == 3:
                #         mirror_reflectivities = values[:, 2]
                #
                #         interpolated_weight_s = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities)
                #         interpolated_weight_p = interpolated_weight_s
                #     elif values.shape[1] == 4:
                #         mirror_reflectivities_s = values[:, 2]
                #         mirror_reflectivities_p = values[:, 3]
                #
                #         interpolated_weight_s = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities_s)
                #         interpolated_weight_p = get_interpolator_weight_2D(mirror_energies, mirror_grazing_angles, mirror_reflectivities_p)

            else:
                raise Exception("Not implemented source of mirror reflectivity")

            beam.apply_reflectivities(numpy.sqrt(Rs), numpy.sqrt(Rp))


        #
        # TODO: write angle.xx for comparison
        #


        #
        # from mirror reference system to image plane
        #

        beam_out = mirr.duplicate()
        beam_out.change_to_image_reference_system(theta_grazing1, q)

        return beam_out, mirr

    #
    # i/o utilities
    #
    def set_positions(self, p, q, theta_grazing, theta_azimuthal=None):
        self._beamline_element_syned.get_coordinates()._p = p
        self._beamline_element_syned.get_coordinates()._q = q
        self._beamline_element_syned.get_coordinates()._angle_radial = numpy.pi / 2 - theta_grazing
        if theta_azimuthal is not None:
            self._beamline_element_syned.get_coordinates()._angle_azimuthal = theta_azimuthal

    def set_surface_plane(self):
        self._beamline_element_syned._optical_element._surface_shape = \
            Conic(conic_coefficients=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,-1.0,0.0])

    def set_surface_conic(self, conic_coefficients=[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,-1.0,0.0]):
        self._beamline_element_syned._optical_element._surface_shape = Conic(conic_coefficients=conic_coefficients)

    def set_surface_toroid(self, min_radius=0.0, maj_radius=0.0):
        self._beamline_element_syned._optical_element = Toroidal(min_radius=min_radius, maj_radius=maj_radius)

    def set_boundaries_rectangle(self, x_left=-1e3, x_right=1e3, y_bottom=-1e3, y_top=1e3):
        self._beamline_element_syned._optical_element._boundary_shape = \
            Rectangle(x_left=x_left, x_right=x_right, y_bottom=y_bottom, y_top=y_top)



if __name__ == "__main__":
    pass