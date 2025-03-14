from ophyd import Component as Cpt
from ophyd import (PseudoSingle, EpicsMotor, SoftPositioner, Signal)
import gi
gi.require_version('Hkl', '5.0')
try:
    from hkl.diffract import E6C  #this works for mu=0
except ImportError:
    # The class was moved to hkl.geometries module in recent hklpy v0.3.16.
    from hkl.geometries import E6C
from ophyd.pseudopos import (pseudo_position_argument, real_position_argument)

# Add MuR and MuT to bluesky list of motors and detectors.
muR = EpicsMotor('XF:23ID1-ES{Dif-Ax:MuR}Mtr', name='muR')
# use the line below if very paranoid
# muR = EpicsSignal('XF:23ID1-ES{Dif-Ax:MuR}Mtr.RBV', name='muR')
muT = EpicsMotor('XF:23ID1-ES{Dif-Ax:MuT}Mtr', name='muT')


# TODO: fix upstream!!
class NullMotor(SoftPositioner):
    @property
    def connected(self):
        return True


class Tardis(E6C):  #this works for mu=0
    h = Cpt(PseudoSingle, '', labels=['tardis'])
    k = Cpt(PseudoSingle, '', labels=['tardis'])
    l = Cpt(PseudoSingle, '', labels=['tardis'])

    theta = Cpt(EpicsMotor, 'XF:23ID1-ES{Dif-Ax:Th}Mtr', labels=['tardis'])
    mu = Cpt(NullMotor, labels=['tardis'])

    chi =   Cpt(NullMotor, labels=['tardis'])
    phi =   Cpt(NullMotor, labels=['tardis'])
    delta = Cpt(EpicsMotor, 'XF:23ID1-ES{Dif-Ax:Del}Mtr', labels=['tardis'])
    gamma = Cpt(EpicsMotor, 'XF:23ID1-ES{Dif-Ax:Gam}Mtr', labels=['tardis'])


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # prime the 3 null-motors with initial values
        # otherwise, position == None --> describe, etc gets borked
        self.chi.move(0.0)
        self.phi.move(0.0)

        # we have to use a motor for omega to keep hkl happy,
        # but want to keep omega as read-only and to follow muR
        def muR_updater(value, **kwargs):
            self.mu.move(value)

        muR.subscribe(muR_updater)

    @pseudo_position_argument
    def set(self, position):
        return super().set([float(_) for _ in position])

# FIXME: hack to get around what should have been done at init of tardis_calc instance
# tardis_calc._lock_engine = True

# tardis = Tardis('', name='tardis', calc_inst=tardis_calc)
tardis = Tardis('', name='tardis')

tardis.theta.user_offset.kind = 'config' #hot fix https://github.com/bluesky/bluesky/issues/1665
tardis.delta.user_offset.kind = 'config'
tardis.gamma.user_offset.kind = 'config'

tardis.reflections.kind = "omitted"

# re-map Tardis' axis names onto what an E6C expects
name_map = {'mu': 'theta', 'omega': 'mu', 'chi': 'chi', 'phi': 'phi', 'gamma': 'delta', 'delta': 'gamma'}


tardis.calc.physical_axis_names = name_map

tardis.calc.engine.mode = 'lifting_detector_mu'  #THis is for E6C, it exists for petra3_09..., but not loaded

# from this point, we can configure the Tardis instance
from hkl.util import Lattice

## lengths are in Angstrom, angles are in degrees
##lattice = Lattice(a=9.069, b=9.069, c=10.390, alpha=90.0, beta=90.0, gamma=120.0)
#
## add the sample to the calculation engine
##tardis.calc.new_sample('esrf_sample', lattice=lattice)
#
## we can alternatively set the energy on the Tardis instance
##tardis.calc.wavelength = 1.61198 # angstroms

# apply some constraints

# Theta
tardis.calc['theta'].limits = (-181, 181)
tardis.calc['theta'].value = 0
tardis.calc['theta'].fit = True

# we don't have it. Fix to 0
tardis.calc['phi'].limits = (0, 0)
tardis.calc['phi'].value = 0
tardis.calc['phi'].fit = False

# we don't have it. Fix to 0
tardis.calc['chi'].limits = (0, 0)
tardis.calc['chi'].value = 0
tardis.calc['chi'].fit = False

# we don't have it!! Fix to 0
tardis.calc['mu'].limits = (0, 0)
tardis.calc['mu'].value = 0#tardis.omega.position.real
tardis.calc['mu'].fit = False

# Attention naming convention inverted at the detector stages!
# delta
tardis.calc['delta'].limits = (-5, 180)
tardis.calc['delta'].value = 0
tardis.calc['delta'].fit = True

# gamma
tardis.calc['gamma'].limits = (-5, 180)
tardis.calc['gamma'].value = 0
tardis.calc['gamma'].fit = True

## add two, known reflections and compute UB
#r1 = tardis.calc.sample.add_reflection(3, 3, 0,
#                           position=tardis.calc.Position(delta=64.449, theta=25.285, chi=0.0, phi=0.0, omega=0.0, gamma=-0.871))
#
#r2 = tardis.calc.sample.add_reflection(5, 2, 0,
#                           position=tardis.calc.Position(delta=79.712, theta=46.816, chi=0.0, phi=0.0, omega=0.0, gamma=-1.374))
#
#tardis.calc.sample.compute_UB(r1, r2)

# test computed real positions against the table below
# recall, lambda is 1.61198 A now
# ex:
# print(tardis.calc.forward((4,4,0)))
# print(tardis.calc.forward((4,1,0)))
#
# Experimentally found reflections @ Lambda = 1.61198 A
# (4, 4, 0) = [90.628, 38.373, 0, 0, 0, -1.156]
# (4, 1, 0) = [56.100, 40.220, 0, 0, 0, -1.091]
# @ Lambda = 1.60911
# (6, 0, 0) = [75.900, 61.000, 0, 0, 0, -1.637]
# @ Lambda = 1.60954
# (3, 2, 0) = [53.090, 26.144, 0, 0, 0, -.933]
# (5, 4, 0) = [106.415, 49.900, 0, 0, 0, -1.535]
# (4, 5, 0) = [106.403, 42.586, 0, 0, 0, -1.183]

## Useful basic commands
# tardis.position -> HKL related to the current physical position
# tardis.real_position -> current physical position
# tardis.calc.forward((1,0,1)) -> calculates physical motor positions
# given an HKL
# tardis.move(0,0,0) -> physical motion corresponding to a given HKL
