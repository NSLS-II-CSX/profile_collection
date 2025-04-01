from ophyd.signal import EpicsSignalBase

EpicsSignalBase.set_defaults(timeout=10, connection_timeout=10)  # new style
# EpicsSignalBase.set_default_timeout(timeout=10, connection_timeout=10)  # old style


import appdirs
import nslsii
from IPython import get_ipython
from bluesky.utils import PersistentDict
from pathlib import Path
from csx1.analysis.callbacks import BECwithTicks

ip = get_ipython()
nslsii.configure_base(
    ip.user_ns,
    broker_name="csx",
    redis_url="info.csx.nsls2.bnl.gov",
    redis_prefix="",
    publish_documents_with_kafka=True,
    bec=False,
)
nslsii.configure_olog(ip.user_ns)

bec = BECwithTicks()
peaks = bec.peaks  # just as alias for less typing
RE.subscribe(bec)


from csx1.startup import *
