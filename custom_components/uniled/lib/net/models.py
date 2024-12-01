"""UniLED Supported NET(work) Models."""

from typing import Final
from .sp53x_54xe import SP5XXE
from .sp801e import SP801E

##
## Supported NET Models
##
UNILED_NET_MODELS: Final = [
    SP5XXE(),
    SP801E(),
]
