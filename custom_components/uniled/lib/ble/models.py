"""UniLED Supported BLE Models."""

from typing import Final
from .device import UNILED_TRANSPORT_BLE
from .sp107e import SP107E
from .sp110e import SP110E, SP110Ev1
from .sp601e import SP601E
from .sp60xe import SP602E, SP608E
from .banlanx2 import SP611E, SP617E, SP620E, SP621E
from .banlanx3 import SP613E, SP614E, SP623E, SP624E
from .sp63x_64xe import SP6XXE

##
## Supported BLE Models
##
UNILED_BLE_MODELS: Final = [
    SP107E,
    SP110E,
    SP110Ev1,
    ######
    SP601E,
    ######
    SP602E,
    SP608E,
    ######
    SP611E,
    SP617E,
    SP620E,
    SP621E,
    SP623E,
    SP624E,
    ######
    SP613E,
    SP614E,
    ######
    SP6XXE(),
]
