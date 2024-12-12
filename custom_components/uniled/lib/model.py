"""UniLED Base Model."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, NewType

from .channel import UniledChannel
from .chips import UniledChips

_LOGGER = logging.getLogger(__name__)

UniledDevice = NewType("UniledDevice", None)


##
## UniLed Base Model Class
##
@dataclass(frozen=True)
class UniledModel(UniledChips):
    """UniLED Base Model."""

    model_code: list[int] | int  # The model code number
    model_name: str  # The model name
    model_info: str  # Description of the model ({type} {color_mode})
    manufacturer: str  # The manufacturers name
    channels: int  # The number of supported channels

    @abstractmethod
    def build_state_query(self, device: UniledDevice) -> bytearray | None:
        """Build a state query message."""

    def build_on_connect(self, device: UniledDevice) -> list[bytearray] | None:
        """Build state query message."""
        return None

    def build_command(
        self, device: Any, channel: UniledChannel, attr: str, value: any
    ) -> list[bytearray]:
        """Build supported command."""
        if channel.status.has(attr):
            if channel.get(attr, value) == value:
                _LOGGER.debug(
                    "%s: Channel %s, command: %s ignored, as no state changed",
                    device.name,
                    channel.number,
                    attr,
                )
                return []
            _LOGGER.debug(
                "%s: Channel %s, command: %s = %s (%s)",
                device.name,
                channel.number,
                attr,
                value,
                channel.status.get(attr),
            )
            command_method = f"build_{attr}_command"
            command_builder = getattr(self, command_method, None)
            if callable(command_builder):
                try:
                    if commands := command_builder(device, channel, value):
                        channel.set(attr, value)
                    return commands  # noqa: TRY300
                except Exception as ex:  # noqa: BLE001
                    _LOGGER.warning(
                        "%s: Channel %s, command %s generated an exception: %s",
                        self.model_name,
                        channel.number,
                        attr,
                        str(ex),
                    )
                    return []
            _LOGGER.warning(
                "%s: Channel %s, command method '%s' not found",
                device.name,
                channel.number,
                command_method,
            )
        else:
            _LOGGER.debug(
                "%s: Channel %s, command: %s ignored, no matching status attribute",
                device.name,
                channel.number,
                attr,
            )
        return []

    def build_multi_commands(
        self, device: Any, channel: UniledChannel, **kwargs
    ) -> list[bytearray]:
        """Build multiple supported command(s)."""
        multi = []
        for attr, value in kwargs.items():
            commands = self.build_command(device, channel, attr, value)
            if commands:
                if isinstance(commands, list):
                    multi.extend(commands)
                else:
                    multi.append(commands)
        return multi

    def fetch_attribute_list(
        self, device: Any, channel: UniledChannel, attr: str
    ) -> list:
        """Return a list of attribute options."""
        list_method = f"fetch_{attr}_list"
        list_fetcher = getattr(self, list_method, None)
        if callable(list_fetcher):
            return list_fetcher(device, channel)
        _LOGGER.warning(
            "%s: Fetch list method '%s' not found", device.name, list_method
        )
        return []
