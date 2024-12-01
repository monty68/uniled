"""Constants for the UniLED integration."""
from typing import Final
from .lib.const import *

DOMAIN: Final = "uniled"

UNILED_SIGNAL_STATE_UPDATED = "uniled_{}_state_updated"
UNILED_DISCOVERY_SIGNAL = "uniled_discovery_{entry_id}"