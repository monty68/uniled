"""UniLED Light Device."""
from __future__ import annotations
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

from .model import (
    UniledModel,
    UniledChannel,
)

from .const import (
    UNILED_MASTER as MASTER,
    ATTR_UL_INFO_FIRMWARE,
    ATTR_UL_DEVICE_FORCE_REFRESH,
)

import weakref
import logging

_LOGGER = logging.getLogger(__name__)


class ParseNotificationError(Exception):
    """Raised on notifcation parse errors."""

##
## Master Channel
##
class UniledMaster(UniledChannel):
    """UniLED Master Channel Class"""
    _device: UniledDevice

    def __init__(self, device: UniledDevice) -> None:
        self._device = device
        super().__init__(0)

    @property
    def name(self) -> str:
        """Returns the channel name."""
        return MASTER if self.device.channels > 1 else ""

    @property
    def device(self) -> UniledDevice:
        """Returns the device."""
        assert self._device is not None  # nosec
        return self._device

##
## Uniled Base Device Class
##
class UniledDevice:
    """UniLED Base Device Class"""
    _channels: list[UniledChannel] = []
    _model: weakref.ProxyType(UniledModel) | None = None
    _callbacks: list[Callable[[UniledChannel], None]] = []
    _last_notification_data: bytearray = ()
    _last_notification_time = None

    def __init__(self) -> None:
        """Init the UniLED Base Driver"""
        self._create_channels()
    
    def __del__(self):
        """Delete the device"""
        #self.stop()
        self._model = None
        self._channels.clear()
        _LOGGER.debug("%s: Deleted Device", self.name)

    def _create_channels(self) -> None:
        """Create device channels."""
        assert self._model is not None  # nosec
        total = self._model.channels or 1
        count = len(self._channels)
        if count < total:
            for index in range(total):
                if not index and not count:
                    self._channels.append(UniledMaster(self))
                else:
                    self._channels.append(UniledChannel(count + index + 1))
        elif count > total:
            for index in range(count - total):
                self._channels.pop()

    @property
    def model(self) -> UniledModel:
        """Return the device model."""
        return self._model

    @property
    def model_name(self) -> int:
        """Return the device model name."""
        assert self._model is not None  # nosec
        return self._model.model_name

    @property
    def model_number(self) -> int:
        """Return the device model number."""
        assert self._model is not None  # nosec
        return self._model.model_num

    @property
    def manufacturer(self) -> str:
        """Return the device manufacturer."""
        assert self._model is not None  # nosec
        return self._model.manufacturer

    @property
    def description(self) -> str:
        """Return the device description."""
        assert self._model is not None  # nosec
        return self._model.description

    #@property
    #def firmware(self) -> str | None:
    #    return self.master.get(ATTR_UL_INFO_FIRMWARE)

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the device."""
        return self.address

    @property
    def master(self) -> UniledMaster | None:
        """Return the master channel"""
        return None if not len(self._channels) else self._channels[0]

    @property
    def channel_list(self) -> list[UniledChannel]:
        """Return the number of channels"""
        return self._channels

    @property
    def channels(self) -> int:
        """Return the number of channels"""
        return len(self.channel_list)

    def channel(self, channel_id: int) -> UniledChannel | None:
        """Return a specified channel"""
        try:
            return self.channel_list[channel_id]
        except IndexError:
            pass
        return self.master

    @property
    def last_notification_data(self) -> bytearray:
        """Last notification data"""
        return self._last_notification_data

    def save_notification_data(self, save: bytearray) -> bytearray:
        """Save some notification data"""
        self._last_notification_data = save
        return save

    def register_callback(
        self, callback: Callable[[UniledChannel], None]
    ) -> Callable[[], None]:
        """Register a callback to be called when the state changes."""

        def unregister_callback() -> None:
            self._callbacks.remove(callback)

        self._callbacks.append(callback)
        return unregister_callback

    def _fire_callbacks(self) -> None:
        """Fire the callbacks."""
        for callback in self._callbacks:
            callback(self)

    def get_list(self, channel_id: int, name: str) -> list:
        """Get a channel (id) attribute list"""
        if channel := self.channel(channel_id) is not None:
            return self.get_list(channel, name)
        return []

    def get_list(self, channel: UniledChannel, name: str) -> list:
        """Get a channel attribute list"""
        return self._model.fetch_attribute_list(self, channel, name)

    def get_state(self, channel_id: int, name: str, default: Any = None) -> Any:
        """Get a channel (id) attribute state"""
        if channel := self.channel(channel_id) is not None:
            return self.get_state(channel, name, default)
        return default

    def get_state(self, channel: UniledChannel, name: str, default: Any = None) -> Any:
        """Get a channel attribute state"""
        return channel.get(name, default)

    async def async_set_state(self, channel_id: int, attr: str, state: Any) -> bool:
        """Set a channel (id) attribute state"""
        if not (channel := self.channel(channel_id)):
            return False
        return await self.async_set_state(self, channel, attr, state)

    async def async_set_state(self, channel: UniledChannel, attr: str, state: Any) -> bool:
        """Set a channel attribute state"""
        command = self._model.build_command(self, channel, attr, state)
        success = await self.send(command) if command else False
        #refresh = not channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH, False)
        if success:
            channel.set(attr, state, True)
        else:
            channel.refresh()
        return success
    
    async def async_set_multi_state(self, channel_id: int, **kwargs) -> None:
        """Set a channel (id) multi attribute states"""
        if not (channel := self.channel(channel_id)):
            return False
        return await self.async_set_multi_state(self, channel, **kwargs)

    async def async_set_multi_state(self, channel: UniledChannel, **kwargs) -> bool:
        """Set a channel multi attribute states"""
        success = await self.send(self._model.build_multi_commands(self, channel, **kwargs))
        #if not channel.status.get(ATTR_UL_DEVICE_FORCE_REFRESH, False):
        channel.refresh()
        return success

    @property
    @abstractmethod
    def transport(self) -> str:
        """Return the device transport."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the device."""

    @property
    @abstractmethod
    def address(self) -> str:
        """Return the address of the device."""

    @property
    @abstractmethod
    def available(self) -> bool:
        """Return if the device is available."""
        return False

    @abstractmethod
    async def update(self) -> None:
        """Update the device."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop the device"""

    @abstractmethod
    async def send(
        self, commands: list[bytes] | bytes
    ) -> bool:
        """Send command(s) to a device."""
        return False
    