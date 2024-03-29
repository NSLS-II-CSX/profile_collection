import time as ttime
import datetime

from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd.device import Component as Cpt
from ophyd.device import FormattedComponent as FmtCpt
from ophyd.device import DeviceStatus
## 20210305 debug with Maksim, ct_dark_all and related "set while another set is in progress" problems
from nslsii.devices import _time_fmtstr


# TODO: sync this class with the one in nslsii.devices.TwoButtonShutter.
class EPSTwoStateDevice(Device):
    # @tcaswell, the names don't need to be fixed. These commands run
    # when the record is processed, you could as easily poke .PROC
    state1_cmd = FmtCpt(EpicsSignal, '{self.prefix}Cmd:{self._state1_nm}-Cmd',
                        string=True)
    state2_cmd = FmtCpt(EpicsSignal, '{self.prefix}Cmd:{self._state2_nm}-Cmd',
                        string=True)

    status = Cpt(EpicsSignalRO, 'Pos-Sts', string=True)
    fail_to_state2 = FmtCpt(EpicsSignalRO,
                            '{self.prefix}Sts:Fail{self._state2_nm}-Sts',
                            string=True)
    fail_to_state1 = FmtCpt(EpicsSignalRO,
                            '{self.prefix}Sts:Fail{self._state1_nm}-Sts',
                            string=True)

    def set(self, val):
        if self._set_st is not None:
            raise RuntimeError('trying to set while a set is in progress')

        cmd_map = {self.state1_str: self.state1_cmd,
                   self.state2_str: self.state2_cmd}
        target_map = {self.state1_str: self.state1_val,
                      self.state2_str: self.state2_val}

        cmd_sig = cmd_map[val]
        target_val = target_map[val]

        st = self._set_st = DeviceStatus(self)
        enums = self.status.enum_strs

        def shutter_cb(value, timestamp, **kwargs):
            try:
                value = enums[int(value)]
            except (ValueError, TypeError):
                # we are here because value is a str not int
                # just move on
                ...
            if value == target_val:
                self.status.clear_sub(shutter_cb)
                cmd_sig.clear_sub(cmd_retry_cb)
                # This was a race condition, fixed.
                # First clear self._set_st to allow future moves to start,
                # and _then_ mark the current move as done.
                self._set_st = None
                st.set_finished()

        cmd_enums = cmd_sig.enum_strs
        count = 0
        MAX_RETRIES = 5
        WAIT_FOR_RETRY = 0.5  # seconds
        def cmd_retry_cb(value, timestamp, **kwargs):
            nonlocal count
            try:
                value = cmd_enums[int(value)]
            except (ValueError, TypeError):
                # we are here because value is a str not int
                # just move on
                ...
            count += 1
            if count > MAX_RETRIES:
                cmd_sig.clear_sub(cmd_retry_cb)
                err = Exception(f"Retried {MAX_RETRIES} times and did not finish.")
                st.set_exception(err)
            if value == 'None':
                ttime.sleep(WAIT_FOR_RETRY)
                if not st.done:
                    # Retry setting the command to 1.
                    cmd_sig.set(1)
                    ts = datetime.datetime.fromtimestamp(timestamp).strftime(_time_fmtstr)
                    print('** ({}) Had to reactuate shutter while {}ing v2'.format(ts, val))

        cmd_sig.subscribe(cmd_retry_cb, run=False)
        self.status.subscribe(shutter_cb)
        cmd_sig.set(1)

        return st

    def __init__(self, *args, state1='Open', state2='Closed',
                 cmd_str1='Open', cmd_str2='Close',
                 nm_str1='Opn', nm_str2='Cls', **kwargs):

        self._state1_nm = nm_str1
        self._state2_nm = nm_str2

        super().__init__(*args, **kwargs)

        self._set_st = None
        self.read_attrs = ['status']

        self.state1_str = cmd_str1
        self.state2_str = cmd_str2
        self.state1_val = state1
        self.state2_val = state2
