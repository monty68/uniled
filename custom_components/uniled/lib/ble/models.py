"""UniLED Supported BLE Models."""
from typing import Final
from .led_chord import SP107E
from .led_hue import SP110E
from .banlanx1 import SP601E, SP602E, SP608E
# from .banlanx2 import
# from .banlanx3 import
from .banlanx4 import SP630E, SP636E, SP637E, SP642E, SP648E

##
## Supported BLE Models
##
UNILED_BLE_MODELS: Final = [
    #SP107E,
    SP110E,
    #SP601E,
    #SP602E,
    #SP608E,
    SP630E,
    SP636E,
    SP637E,
    SP642E,
    SP648E,
]
