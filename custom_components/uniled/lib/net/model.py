"""UniLED Network Device Handler."""

from __future__ import annotations
from dataclasses import dataclass
from abc import abstractmethod
from typing import NewType
from ..model import UniledModel
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict  # pylint: disable=no-name-in-module
else:
    from typing_extensions import TypedDict
import logging

_LOGGER = logging.getLogger(__name__)
UniledNetDevice = NewType("UniledNetDevice", None)


##
## UniLed Network Model Class
##
@dataclass(frozen=True)
class UniledNetModel(UniledModel):
    """UniLED Network Model."""

    net_port: int
    net_close: bool

    @property
    def port(self) -> int:
        """Get the network port number."""
        return self.net_port

    @property
    def close_after_send(self) -> int:
        """Close after transaction flag."""
        return self.net_close

    def length_response_header(
        self, device: UniledNetDevice, command: bytearray
    ) -> int:
        """Expected length of a command response"""
        return 0

    def decode_response_header(
        self, device: UniledNetDevice, data: bytearray
    ) -> int | None:
        """Decode a response header"""
        return None

    @abstractmethod
    def decode_response_payload(self, device: UniledNetDevice, data: bytearray) -> bool:
        """Decode a response payload"""
        return False
