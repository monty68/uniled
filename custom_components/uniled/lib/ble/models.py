"""UniLED Supported BLE Models."""
from typing import Final
from .led_chord import SP107E
from .led_hue import SP110E
# from .banlanx2 import
from .banlanx3 import SP613E, SP614E
from .banlanx_60x import SP601E, SP602E, SP608E
from .banlanx_6xx import SP6XXE


##
## Supported BLE Models
##
UNILED_BLE_MODELS: Final = [
    SP107E,
    SP110E,
    ######
    SP601E,
    # SP602E,
    # SP608E,
    ######
    #SP611E,
    #SP617E,
    SP613E,
    SP614E,
    SP6XXE,
]
