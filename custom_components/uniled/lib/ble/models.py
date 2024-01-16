"""UniLED Supported BLE Models."""
from typing import Final
from .device import UNILED_TRANSPORT_BLE
from .led_chord import SP107E
from .led_hue import SP110E
from .banlanx_601 import SP601E
from .banlanx_60x import SP602E, SP608E
from .banlanx_6xx import SP6XXE
from .banlanx2 import SP611E, SP617E, SP620E, SP621E
from .banlanx3 import SP613E, SP614E, SP623E, SP624E


##
## Supported BLE Models
##
UNILED_BLE_MODELS: Final = [
    SP107E,
    SP110E,
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
    SP6XXE,
]
