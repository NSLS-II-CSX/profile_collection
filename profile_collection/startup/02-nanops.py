from ophyd.epics_motor import EpicsMotor
from ophyd.device import Component as Cpt
from ophyd.signal import EpicsSignal
from ophyd.status import (MoveStatus, DeviceStatus, wait as status_wait, StatusBase)
from ophyd import MotorBundle
from epics import caget,caput


class NanoMotor(EpicsMotor):
    _default_configuration_attrs = (
        EpicsMotor._default_configuration_attrs +
        ('dly', 'rdbd', 'rmod', 'cnen', 'pcof', 'icof'))
    user_setpoint = Cpt(EpicsSignal, 'PA_sm')
    dly = Cpt(EpicsSignal, '.DLY')
    rdbd = Cpt(EpicsSignal, '.RDBD')
    rmod = Cpt(EpicsSignal, '.RMOD')
    cnen = Cpt(EpicsSignal, '.CNEN')
    pcof = Cpt(EpicsSignal, '.PCOF')
    icof = Cpt(EpicsSignal, '.ICOF')

class NanoMotorOpenLoop(EpicsMotor):
    #_default_configuration_attrs = (
    #    EpicsMotor._default_configuration_attrs +
    #    ('dly', 'rdbd', 'rmod', 'cnen', 'pcof', 'icof'))
    _default_read_attrs = ('user_setpoint', 'user_readback','done_signal')
    _default_configuration_attrs = ('velocity',)
    user_setpoint = Cpt(EpicsSignal, 'Abs')
    velocity = Cpt(EpicsSignal,'FQUnits')
    done_signal=Cpt(EpicsSignal,'DMOV')
    #acceleration=Cpt(EpicsSignal,'DMOV')
    user_readback = Cpt(EpicsSignal, 'AbsLast')
    dly = Cpt(EpicsSignal, '.DLY')
    rdbd = Cpt(EpicsSignal, '.RDBD')
    rmod = Cpt(EpicsSignal, '.RMOD')
    cnen = Cpt(EpicsSignal, '.CNEN')
    pcof = Cpt(EpicsSignal, '.PCOF')
    icof = Cpt(EpicsSignal, '.ICOF')
    t_settle = Cpt(EpicsSignal, 'SETL')
    '''
    @property
    def connected(self):
         return True
    '''
    def remove_bad_signals(self):
        good_signals = list(self._default_read_attrs) + list(self._default_configuration_attrs)
        all_keys = list(self._signals.keys())
        for k in all_keys:
            if k not in good_signals:
                self._signals.pop(k, None)
        print(f'Signals: {list(self._signals.keys())}')

    def set(self, value):
        #self.done_signal.value=1
        st = DeviceStatus(self)
        # these arg sames matter
        #def am_done(old_value, value, **kwargs):
        def am_done(old_value,value, **kwargs):
            #if old_value == 1 and value == 0:
            #print("running",old_value,value,self.done_signal.value)
            #print("done_signal: ",smtr.done_signal.value)
            """
            if self.done_signal.value==1:
                if self.last_value==0:
                    st._finished()
                self.last_value=1
            else:
                self.last_value=0
            """
            if old_value==0 and value==1:
                st._finished()

        self.done_signal.subscribe(am_done, run=False)
        self.user_setpoint.set(value)
        return st


class NanoBundle(MotorBundle):
    tx = Cpt(NanoMotor, 'TopX}Mtr')
    ty = Cpt(NanoMotor, 'TopY}Mtr')
    tz = Cpt(NanoMotor, 'TopZ}Mtr')
    bx = Cpt(NanoMotor, 'BtmX}Mtr')
    by = Cpt(NanoMotor, 'BtmY}Mtr')
    #swap between the two following line if BtmZ close/open loop is desired, respectively
    #bz = Cpt(NanoMotor, 'BtmZ}Mtr')
    bz = Cpt(NanoMotorOpenLoop, 'BtmZ}OL')

nanop = NanoBundle('XF:23ID1-ES{Dif:Nano-Ax:', name='nanop')
nanop.bz.remove_bad_signals()  # solve the issue with disconnection errors


# Velocity (tested 0.5, 0.1, 0.05, 0.01)

# this was 0.30 but AB tried scanning with larger step
# size and had difficulty in that bluesky will never trigger the
# cube_beam because bsui is waiting on this to move??

# Settling time (tested 0.1 - 0.3)
temp_settle_time = 0.2

_base_nano_setting = {'velocity': 0.10,
                      #'acceleration': 0.20,
                      #'dly': temp_settle_time,
                      #'rdbd': 1e-5,
                      #'rmod': 1,
                      #'cnen': 1,
                      #'pcof': 0.1,
                      #'icof': 0.010
                      }

for nn in nanop.component_names:
    getattr(nanop, nn).configure(_base_nano_setting)

BlueskyMagics.positioners += [getattr(nanop, nn) for nn in nanop.component_names]

#sd.baseline += [getattr(nanop, nn) for nn in nanop.component_names]
sd.baseline += [nanop]
