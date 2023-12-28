"""UniLED Base Model."""
from __future__ import annotations
from dataclasses import dataclass, replace
from abc import abstractmethod
from typing import Any, Final

from .channel import UniledChannel
from .chips import UniledChips

import logging

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class UniledModel(UniledChips):
    """UniLED Base Model Class"""

    model_num: int  # The model number
    model_name: str  # The model name
    description: str  # Description of the model ({type} {color_mode})
    manufacturer: str  # The manufacturers name
    channels: int  # The number of supported channels

    @abstractmethod
    def parse_notifications(self, device: Any, sender: int, data: bytearray) -> bool:
        """Parse notification message(s)"""
        from .device import ParseNotificationError

        raise ParseNotificationError("No parser available!")

    @abstractmethod
    def build_state_query(self, device: Any) -> bytearray | None:
        """Build a state query message"""

    def build_on_connect(self, device: Any) -> list[bytearray] | None:
        """Build state query message"""

    def build_command(
        self, device: Any, channel: UniledChannel, attr: str, value: any
    ) -> list[bytearray]:
        """Build supported command"""
        _LOGGER.info(
            "%s: %s, command: %s = %s (%s)",
            self.model_name,
            channel.identity or channel.name or f"{channel.number}",
            attr,
            value,
            channel.status.get(attr),
        )
        command_method = f"build_{attr}_command"
        command_builder = getattr(self, command_method, None)
        if callable(command_builder):
            if commands := command_builder(device, channel, value):
                channel.set(attr, value)
            return commands
        _LOGGER.warning("%s: Method '%s' not found.", self.model_name, command_method)
        return []

    def build_multi_commands(
        self, device: Any, channel: UniledChannel, **kwargs
    ) -> list[bytearray]:
        """Build multiple supported command(s)"""
        multi = []
        for attr, value in kwargs.items():
            commands = self.build_command(device, channel, attr, value)
            if isinstance(commands, list):
                multi.extend(commands)
                pass
            else:
                multi.append(commands)
        return multi

    def fetch_attribute_list(
        self, device: Any, channel: UniledChannel, attr: str
    ) -> list:
        """Return a list of attribute options"""
        list_method = f"fetch_{attr}_list"
        list_fetcher = getattr(self, list_method, None)
        if callable(list_fetcher):
            return list_fetcher(device, channel)
        _LOGGER.warning("%s: Method '%s' not found.", self.model_name, list_method)
        return []
