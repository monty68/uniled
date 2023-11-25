"""UniLED Models Database."""
from typing import Final
from .const import UNILED_TRANSPORT_BLE, UNILED_TRANSPORT_NET
from .ble.models import UNILED_BLE_MODELS
from .net.models import UNILED_NET_MODELS

##
## All Supported Models
##
UNILED_MODELS: Final = {
    UNILED_TRANSPORT_BLE: UNILED_BLE_MODELS,
    UNILED_TRANSPORT_NET: UNILED_NET_MODELS,
}
