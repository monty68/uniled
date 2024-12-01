"""UniLED Master Channel."""

from __future__ import annotations
from typing import NewType
from .channel import UniledChannel
from .const import UNILED_MASTER
import logging

_LOGGER = logging.getLogger(__name__)

UniledDevice = NewType("UniledDevice", None)


##
## Master Channel Class
##
class UniledMaster(UniledChannel):
    """UniLED Master Channel."""

    _device: UniledDevice
    _name: str | None

    def __init__(self, device: UniledDevice, name: str | None = UNILED_MASTER) -> None:
        self._device = device
        self._name = UNILED_MASTER if name is True else name
        super().__init__(0)

    @property
    def name(self) -> str | None:
        """Returns the channel name."""
        if self.device.channels == 1:
            return ""
        if self.device.channels > 1 and self._name is not None:
            return self._name
        return super().name

    @property
    def identity(self) -> str | None:
        """Returns the channel identity."""
        if self.device.channels == 1:
            return None
        if self.device.channels > 1 and self._name is not None:
            return self._name.replace(" ", "_").lower()
        return super().identity

    @property
    def device(self) -> UniledDevice:
        """Returns the device."""
        assert self._device is not None  # nosec
        return self._device
