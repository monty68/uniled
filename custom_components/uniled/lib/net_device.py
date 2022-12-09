"""UniLED NETwork Device Handler."""
from __future__ import annotations

import asyncio
import async_timeout


from .classes import UNILEDDevice
from .net_model import UNILEDNETModel
from .models_db import UNILED_TRANSPORT_NET, UNILED_NET_MODELS

import logging

_LOGGER = logging.getLogger(__name__)

##
## UniLed NETwork Device Handler
##
class UNILEDNET(UNILEDDevice):
    """UniLED NETwork Device Class"""
