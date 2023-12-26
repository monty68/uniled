"""UniLED Update Coordinator."""
from __future__ import annotations

import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, ConfigEntryError

from .const import UNILED_REFRESH_DELAY
from .lib.device import UniledDevice

import logging

_LOGGER = logging.getLogger(__name__)


class UniledUpdateCoordinator(DataUpdateCoordinator):
    """DataUpdateCoordinator to gather data for a specific UniLED device."""

    def __init__(
        self, hass: HomeAssistant, device: UniledDevice, entry: ConfigEntry
    ) -> None:
        """Initialize DataUpdateCoordinator to gather data for specific device."""
        self.device: UniledDevice = device
        self.lock = asyncio.Lock()
        self.title = entry.title
        self.entry = entry
        cooldown = 0.1 # UNILED_REFRESH_DELAY
        super().__init__(
            hass,
            _LOGGER,
            name=f"{self.device.name}",
            update_method=self._async_update,
            update_interval=timedelta(seconds = device.update_interval),
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=cooldown, immediate=True
            ),
        )

    def __del__(self):
        """Destroy the class"""
        _LOGGER.debug("%s: Coordinator destroyed", self.device.name)

    async def _async_update(self) -> None:
        """Fetch all device and sensor data from api."""

        if self.entry.state == ConfigEntryState.NOT_LOADED:
            if self._listeners:
                _LOGGER.warning("Still have listeners: %s", self._listeners)

        valid_states = (
            ConfigEntryState.LOADED,
            ConfigEntryState.SETUP_IN_PROGRESS,
            ConfigEntryState.SETUP_RETRY,
        )

        if self.entry.state not in valid_states:
            if self.device.available:
                await self.device.stop()
            raise UpdateFailed("Invalid entry state: %s", self.entry.state)

        if self.device.started:
            success = False
            async with self.lock:
                try:
                    retry = None if self.entry.state == ConfigEntryState.LOADED else 0
                    success = await self.device.update(retry)
                except Exception as ex:
                    raise ConfigEntryError(str(ex)) from ex
            if not success:
                raise UpdateFailed("Device update failed")
        else:
            pass
            # raise UpdateFailed("Device not started")
   