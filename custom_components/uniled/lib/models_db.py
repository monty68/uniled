"""UniLED Models Database."""
from typing import Final
#from .zng.models import UNILED_TRANSPORT_ZNG, UNILED_ZNG_MODELS
from .ble.models import UNILED_TRANSPORT_BLE, UNILED_BLE_MODELS
from .net.models import UNILED_TRANSPORT_NET, UNILED_NET_MODELS

##
## All Supported Models
##
UNILED_MODELS: Final = {
    #UNILED_TRANSPORT_ZNG: UNILED_ZNG_MODELS,
    UNILED_TRANSPORT_BLE: UNILED_BLE_MODELS,
    UNILED_TRANSPORT_NET: UNILED_NET_MODELS,
}
