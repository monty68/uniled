"""UniLED NETwork Device Handler."""
from __future__ import annotations
from typing import Final
from ..device import UniledDevice, ParseNotificationError
from ..model import UniledModel

import logging

_LOGGER = logging.getLogger(__name__)

UNILED_TRANSPORT_NET: Final = "net"

##
## UniLed NETwork Model Handler
##
class UniledNetModel(UniledModel):
    """UniLED NETwork Model Class"""

##
## UniLed NETwork Device Handler
##
class UniledNetDevice(UniledDevice):
    """UniLED NETwork Device Class"""

    @property
    def transport(self) -> str:
        """Return the device transport."""
        return UNILED_TRANSPORT_NET
