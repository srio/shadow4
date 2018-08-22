__authors__ = ["M Sanchez del Rio - ESRF ISDD Advanced Analysis and Modelling"]
__license__ = "MIT"
__date__ = "12/01/2017"


import numpy
import scipy.constants as codata

# import Shadow
from SourceUndulatorFactory import undul_cdf, undul_phot
from SourceUndulatorFactorySrw import undul_phot_srw
from SourceUndulatorFactoryPysru import undul_phot_pysru

from SourceUndulatorInputOutput import write_file_undul_cdf, load_file_undul_cdf
# from SourceUndulatorInputOutput import write_file_undul_phot_h5, write_file_undul_cdf_h5
# from SourceUndulatorInputOutput import load_file_undul_phot,write_file_undul_phot
# from SourceUndulatorInputOutput import load_file_undul_cdf,write_file_undul_sha

from syned.storage_ring.magnetic_structures.undulator import Undulator
from syned.storage_ring.electron_beam import ElectronBeam

import Shadow
from inverse_method_sampler import Sampler2D, Sampler3D

class SampleUndulator(object):
    def __init__(self,name="",
                 syned_electron_beam=ElectronBeam(),
                 syned_undulator=Undulator(),
                 FLAG_EMITTANCE=0,FLAG_SIZE=0,
                 EMIN=10000.0,EMAX=11000.0,NG_E=11,MAXANGLE=0.5,NG_T=31,NG_P=21,NG_J=20,SEED=36255655452,NRAYS=5000,
                 code_undul_phot="srw", # internal, pysru, srw
                 ):

        # # Machine
        self.syned_electron_beam = syned_electron_beam

        # # Undulator
        self.syned_undulator = syned_undulator

        self.FLAG_EMITTANCE  =  FLAG_EMITTANCE # Yes  # Use emittance (0=No, 1=Yes)
        self.FLAG_SIZE  =  FLAG_SIZE # 0=point,1=Gaussian,2=FT(Divergences)

        # Photon energy scan
        self.EMIN            = EMIN   # Photon energy scan from energy (in eV)
        self.EMAX            = EMAX   # Photon energy scan to energy (in eV)
        self.NG_E            = NG_E        # Photon energy scan number of points
        # Geometry
        self.MAXANGLE        = MAXANGLE      # Maximum radiation semiaperture in mrad # TODO: define it in rad, for consistency
        self.NG_T            = NG_T       # Number of points in angle theta
        self.NG_P            = NG_P       # Number of points in angle phi
        self.NG_J            = NG_J       # Number of points in electron trajectory (per period)
        # ray tracing
        self.SEED            = SEED  # Random seed
        self.NRAYS           = NRAYS         # Number of rays

        self.code_undul_phot = code_undul_phot

        self.result_radiation = None


    def info(self,debug=False):
        """
        gets text info

        :param debug: if True, list the undulator variables (Default: debug=True)
        :return:
        """
        # list all non-empty keywords
        txt = ""


        txt += "-----------------------------------------------------\n"

        txt += "Input Electron parameters: \n"
        txt += "        Electron energy: %f geV\n"%self.syned_electron_beam._energy_in_GeV
        txt += "        Electron current: %f A\n"%self.syned_electron_beam._current
        if self.FLAG_EMITTANCE:
            sigmas = self.syned_electron_beam.get_sigmas_all()
            txt += "        Electron sigmaX: %g [um]\n"%(1e6*sigmas[0])
            txt += "        Electron sigmaZ: %g [um]\n"%(1e6*sigmas[2])
            txt += "        Electron sigmaX': %f urad\n"%(1e6*sigmas[1])
            txt += "        Electron sigmaZ': %f urad\n"%(1e6*sigmas[3])
        txt += "Input Undulator parameters: \n"
        txt += "        period: %f m\n"%self.syned_undulator.period_length()
        txt += "        number of periods: %d\n"%self.syned_undulator.number_of_periods()
        txt += "        K-value: %f\n"%self.syned_undulator.K_vertical()

        txt += "-----------------------------------------------------\n"

        txt += "Lorentz factor (gamma): %f\n"%self.syned_electron_beam.gamma()
        txt += "Electron velocity: %.12f c units\n"%(numpy.sqrt(1.0 - 1.0 / self.syned_electron_beam.gamma() ** 2))
        txt += "Undulator length: %f m\n"%(self.syned_undulator.period_length()*self.syned_undulator.number_of_periods())
        K_to_B = (2.0 * numpy.pi / self.syned_undulator.period_length()) * codata.m_e * codata.c / codata.e

        txt += "Undulator peak magnetic field: %f T\n"%(K_to_B*self.syned_undulator.K_vertical())
        txt += "Resonances: \n"
        txt += "        harmonic number [n]                   %10d %10d %10d \n"%(1,3,5)
        txt += "        wavelength [A]:                       %10.6f %10.6f %10.6f   \n"%(\
                                                                1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=1),
                                                                1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=3),
                                                                1e10*self.syned_undulator.resonance_wavelength(self.syned_electron_beam.gamma(),harmonic=5))
        txt += "        energy [eV]   :                       %10.3f %10.3f %10.3f   \n"%(\
                                                                self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=1),
                                                                self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=3),
                                                                self.syned_undulator.resonance_energy(self.syned_electron_beam.gamma(),harmonic=5))
        txt += "        frequency [Hz]:                       %10.3g %10.3g %10.3g   \n"%(\
                                                                1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=1),
                                                                1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=3),
                                                                1e10*self.syned_undulator.resonance_frequency(self.syned_electron_beam.gamma(),harmonic=5))
        txt += "        central cone 'half' width [mrad]:     %10.6f %10.6f %10.6f   \n"%(\
                                                                1e3*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),1),
                                                                1e3*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),3),
                                                                1e3*self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),5))
        txt += "        first ring at [mrad]:                 %10.6f %10.6f %10.6f   \n"%(\
                                                                1e3*self.get_resonance_ring(1,1),
                                                                1e3*self.get_resonance_ring(3,1),
                                                                1e3*self.get_resonance_ring(5,1))

        txt += "-----------------------------------------------------\n"
        txt += "Sampling: \n"
        if self.NG_E == 1:
            txt += "        photon energy %f eV\n"%(self.EMIN)
        else:
            txt += "        photon energy from %10.3f eV to %10.3f eV\n"%(self.EMIN,self.EMAX)
        txt += "        number of points for the trajectory %d\n"%(self.NG_J)
        txt += "        number of energy points %d\n"%(self.NG_E)
        txt += "        maximum elevation angle %f mrad\n"%(self.MAXANGLE)
        txt += "        number of angular elevation points %d\n"%(self.NG_T)
        txt += "        number of angular azimuthal points %d\n"%(self.NG_P)
        txt += "        number of rays %d\n"%(self.NRAYS)
        txt += "        random seed %d\n"%(self.SEED)
        txt += "-----------------------------------------------------\n"

        if self.result_radiation is None:
            txt += "        radiation: NOT YET CALCULATED\n"
        else:
            txt += "        radiation: CALCULATED\n"

        txt += "-----------------------------------------------------\n"
        return txt

    def get_resonance_ring(self,harmonic_number=1, ring_order=1):
        return 1.0/self.syned_electron_beam.gamma()*numpy.sqrt( ring_order / harmonic_number * (1+0.5*self.syned_undulator.K_vertical()**2) )

    # def set_harmonic(self,harmonic):

    def set_energy_monochromatic_at_resonance(self,harmonic_number):

        self.set_energy_monochromatic(self.syned_undulator.resonance_energy(
            self.syned_electron_beam.gamma(),harmonic=harmonic_number))
        # take 3*sigma - MAXANGLE is in mrad!!

        # self.MAXANGLE = 3 * 0.69 * 1e3 * self.get_resonance_central_cone(harmonic_number)
        self.MAXANGLE = 3 * 0.69 * 1e3 * self.syned_undulator.gaussian_central_cone_aperture(self.syned_electron_beam.gamma(),harmonic_number)

    def set_energy_monochromatic(self,emin):
        """
        Sets a single energy line for the source (monochromatic)
        :param emin: the energy in eV
        :return:
        """
        self.EMIN = emin
        self.EMAX = emin
        self.NG_E = 1


    def set_energy_box(self,emin,emax,npoints=None):
        """
        Sets a box energy distribution for the source (monochromatic)
        :param emin:  Photon energy scan from energy (in eV)
        :param emax:  Photon energy scan to energy (in eV)
        :param npoints:  Photon energy scan number of points (optinal, if not set no changes)
        :return:
        """

        self.EMIN = emin
        self.EMAX = emax
        if npoints != None:
            self.NG_E = npoints

    def calculate_radiation(self):

        """
        Calculates the radiation (emission) as a function pf theta (elevation angle) and phi (azimuthal angle)
        This radiation will be sampled to create the source

        It calls undul_phot* in SourceUndulatorFactory

        :param code_undul_phot: 'internal' (calls undul_phot), 'pysru' (calls undul_phot_pysru) or
                'srw' (calls undul_phot_srw)
        :return: a dictionary (the output from undul_phot*)
        """

        # h = self.to_dictionary()
        # print(self.info())
        # os.system("rm -f xshundul.plt xshundul.par xshundul.traj xshundul.info xshundul.sha")

        # if code_undul_phot != "internal" or code_undul_phot != "srw":
        #     dump_uphot_dot_dat = True


        self.result_radiation = None

        # undul_phot
        if self.code_undul_phot == 'internal':
            undul_phot_dict = undul_phot(E_ENERGY  = self.syned_electron_beam.energy(),
                                         INTENSITY = self.syned_electron_beam.current(),
                                         LAMBDAU   = self.syned_undulator.period_length(),
                                         NPERIODS  = self.syned_undulator.number_of_periods(),
                                         K         = self.syned_undulator.K(),
                                         EMIN      = self.EMIN,
                                         EMAX      = self.EMAX,
                                         NG_E      = self.NG_E,
                                         MAXANGLE  = self.MAXANGLE,
                                         NG_T      = self.NG_T,
                                         NG_P      = self.NG_P,
                                         number_of_trajectory_points = self.NG_J)

        elif self.code_undul_phot == 'pysru':
            undul_phot_dict = undul_phot_pysru(E_ENERGY  = self.syned_electron_beam.energy(),
                                         INTENSITY = self.syned_electron_beam.current(),
                                         LAMBDAU   = self.syned_undulator.period_length(),
                                         NPERIODS  = self.syned_undulator.number_of_periods(),
                                         K         = self.syned_undulator.K(),
                                         EMIN      = self.EMIN,
                                         EMAX      = self.EMAX,
                                         NG_E      = self.NG_E,
                                         MAXANGLE  = self.MAXANGLE,
                                         NG_T      = self.NG_T,
                                         NG_P      = self.NG_P,)
        elif self.code_undul_phot == 'srw':
            undul_phot_dict = undul_phot_srw(E_ENERGY  = self.syned_electron_beam.energy(),
                                         INTENSITY = self.syned_electron_beam.current(),
                                         LAMBDAU   = self.syned_undulator.period_length(),
                                         NPERIODS  = self.syned_undulator.number_of_periods(),
                                         K         = self.syned_undulator.K(),
                                         EMIN      = self.EMIN,
                                         EMAX      = self.EMAX,
                                         NG_E      = self.NG_E,
                                         MAXANGLE  = self.MAXANGLE,
                                         NG_T      = self.NG_T,
                                         NG_P      = self.NG_P,)
        else:
            raise Exception("Not implemented undul_phot code: "+code_undul_phot)

        # add some info
        undul_phot_dict["code_undul_phot"] = self.code_undul_phot
        undul_phot_dict["info"] = self.info()

        self.result_radiation = undul_phot_dict
        return undul_phot_dict


    def calculate_shadow3_beam(self,user_unit_to_m=1.0):

        self.calculate_radiation()

        sampled_photon_energy,sampled_theta,sampled_phi = self._sample_photon_beam()

        beam = self._sample_shadow3_beam(sampled_photon_energy,sampled_theta,sampled_phi)

        if user_unit_to_m != 1.0:
            beam.rays[:,0] /= user_unit_to_m
            beam.rays[:,1] /= user_unit_to_m
            beam.rays[:,2] /= user_unit_to_m

        return beam


    def _sample_shadow3_beam(self,sampled_photon_energy,sampled_theta,sampled_phi):

        beam = Shadow.Beam(N=self.NRAYS)






        sigmas = self.syned_electron_beam.get_sigmas_all()

        #
        # sample sizes
        #
        if self.FLAG_EMITTANCE:
            x_electron = numpy.random.normal(loc=0.0,scale=sigmas[0],size=self.NRAYS)
            y_electron = 0.0
            z_electron = numpy.random.normal(loc=0.0,scale=sigmas[2],size=self.NRAYS)
        else:
            x_electron = 0.0
            y_electron = 0.0
            z_electron = 0.0

        if self.FLAG_SIZE == 0:
            x_photon = 0.0
            y_photon = 0.0
            z_photon = 0.0
        elif self.FLAG_SIZE == 1:
            undulator_length = self.syned_undulator.length()
            lambda1 = codata.h*codata.c/codata.e / sampled_photon_energy.mean()

            # calculate sizes of the photon undulator beam
            # see formulas 25 & 30 in Elleaume (Onaki & Elleaume)
            # sp_phot = 0.69*numpy.sqrt(lambda1/undulator_length)
            s_phot = 2.740/(4e0*numpy.pi)*numpy.sqrt(undulator_length*lambda1)

            cov = [[s_phot**2, 0], [0, s_phot**2]]
            mean = [0.0,0.0]

            tmp = numpy.random.multivariate_normal(mean, cov, self.NRAYS)
            x_photon = tmp[:,0]
            y_photon = 0.0
            z_photon = tmp[:,1]
        elif self.FLAG_SIZE == 2:
            raise Exception("To be implemented")


        beam.rays[:,0] = x_photon + x_electron
        beam.rays[:,1] = y_photon + y_electron
        beam.rays[:,2] = z_photon + z_electron


        # flag
        beam.rays[:,9] = 1.0

        #
        # divergences: the Shadow way
        #
        THETABM = sampled_theta
        PHI = sampled_phi
        A_Z = numpy.arcsin(numpy.sin(THETABM)*numpy.sin(PHI))
        A_X = numpy.arccos(numpy.cos(THETABM)/numpy.cos(A_Z))
        THETABM = A_Z
        PHI  = A_X
        # ! C Decide in which quadrant THETA and PHI are.
        myrand = numpy.random.random(self.NRAYS)
        THETABM[numpy.where(myrand < 0.5)] *= -1.0
        myrand = numpy.random.random(self.NRAYS)
        PHI[numpy.where(myrand < 0.5)] *= -1.0

        if self.FLAG_EMITTANCE:
            EBEAM1 = numpy.random.normal(loc=0.0,scale=sigmas[1],size=self.NRAYS)
            EBEAM3 = numpy.random.normal(loc=0.0,scale=sigmas[3],size=self.NRAYS)
            ANGLEX = EBEAM1 + PHI
            ANGLEV = EBEAM3 + THETABM
        else:
            ANGLEX = PHI # E_BEAM(1) + PHI
            ANGLEV =THETABM #  E_BEAM(3) + THETABM

        VX = numpy.tan(ANGLEX)
        VY = 1.0
        VZ = numpy.tan(ANGLEV)/numpy.cos(ANGLEX)
        VN = numpy.sqrt( VX*VX + VY*VY + VZ*VZ)
        VX /= VN
        VY /= VN
        VZ /= VN

        beam.rays[:,3] = VX
        beam.rays[:,4] = VY
        beam.rays[:,5] = VZ


        #
        # photon energy
        #

        A2EV = 2.0*numpy.pi/(codata.h*codata.c/codata.e*1e2)
        beam.rays[:,10] =  sampled_photon_energy * A2EV


        #
        # electric vectors
        #

        beam.rays[:,6] =  1.0

        return beam


    def _sample_photon_beam(self):

        #
        # sample divergences
        #

        theta = self.result_radiation["theta"]
        phi = self.result_radiation["phi"]
        photon_energy = self.result_radiation["photon_energy"]

        photon_energy_spectrum = 'polychromatic' # 'monochromatic' #
        if self.EMIN == self.EMAX:
            photon_energy_spectrum = 'monochromatic'
        if self.NG_E == 1:
            photon_energy_spectrum = 'monochromatic'


        if photon_energy_spectrum == 'monochromatic':

            #2D case
            tmp = self.result_radiation["radiation"][0,:,:].copy()
            tmp /= tmp.max()

            # correct radiation for DxDz / DthetaDphi
            tmp_theta = numpy.outer(theta,numpy.ones_like(phi))
            tmp_theta /= tmp_theta.max()
            tmp_theta += 1e-6 # to avoid zeros
            tmp *= tmp_theta
            # plot_image(tmp_theta,theta,phi,aspect='auto')

            s2d = Sampler2D(tmp,theta,phi)
            sampled_theta,sampled_phi = s2d.get_n_sampled_points(self.NRAYS)

            sampled_photon_energy = self.EMIN

        elif photon_energy_spectrum == "polychromatic":
            #3D case
            tmp = self.result_radiation["radiation"].copy()
            tmp /= tmp.max()
            # correct radiation for DxDz / DthetaDphi
            tmp_theta = numpy.outer(theta,numpy.ones_like(phi))
            tmp_theta /= tmp_theta.max()
            tmp_theta += 1e-6 # to avoid zeros
            for i in range(tmp.shape[0]):
                tmp[i,:,:] *= tmp_theta

            s3d = Sampler3D(tmp,photon_energy,theta,phi)

            sampled_photon_energy,sampled_theta,sampled_phi = s3d.get_n_sampled_points(self.NRAYS)


        return sampled_photon_energy,sampled_theta,sampled_phi

