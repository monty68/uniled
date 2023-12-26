"""UniLED Attributes."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from enum import IntEnum
from .const import *

dataclass(frozen=True)
class UniledGroup(IntEnum):
    """UniLED Attribute Group"""

    STANDARD = 0
    NEEDS_ON = 1
    CONFIGURATION = 2
    DIAGNOSTIC = 3


class UniledAttribute:
    """UniLED Base Attribute Class"""

    def __init__(
        self,
        platform: str,
        attr: str,
        name: str | None,
        icon: str | None,
        key: str | None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        self._platform = platform
        self._attr = attr
        self._name = name
        self._icon = icon
        self._key = key
        self._enabled = enabled
        self._group = group
        self._extra = extra
        self._reload: bool = False

    @property
    def platform(self) -> str:
        return self._platform

    @property
    def reload(self) -> bool:
        return self._reload

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def group(self) -> UniledGroup:
        return self._group

    @property
    def attr(self) -> str:
        return self._attr

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def key(self) -> str:
        return self._key or self._attr

    @property
    def extra(self) -> list:
        return self._extra


class SensorAttribute(UniledAttribute):
    """UniLED Sensor Attribute Class"""

    def __init__(
        self,
        attr: str,
        name: str,
        icon: str,
        key: str | None = None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        super().__init__(
           "sensor",
           attr,
           name,
           icon,
           key,
           enabled,
           group,
           extra 
        )


class SelectAttribute(UniledAttribute):
    """UniLED Select Attribute Class"""

    def __init__(
        self,
        attr: str,
        name: str,
        icon: str,
        key: str | None = None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        super().__init__(
           "select",
           attr,
           name,
           icon,
           key,
           enabled,
           group,
           extra 
        )


class SwitchAttribute(UniledAttribute):
    """UniLED Switch Attribute Class"""

    def __init__(
        self,
        attr: str,
        name: str,
        icon_on: str,
        icon_off: str | None = None,
        key: str | None = None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        super().__init__(
           "switch",
           attr,
           name,
           icon_on,
           key,
           enabled,
           group,
           extra 
        )
        self._icon2 = icon_off

    def state_icon(self, state: bool = True) -> str:
        """Return icon depending on state"""
        return self._icon if state or not self._icon2 else self._icon2


class ButtonAttribute(UniledAttribute):
    """UniLED Sensor Attribute Class"""

    def __init__(
        self,
        attr: str,
        name: str,
        icon: str,
        value: Any = True,
        key: str | None = None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        super().__init__(
           "button",
           attr,
           name,
           icon,
           key,
           enabled,
           group,
           extra 
        )
        self._value = value

    @property
    def value(self) -> int:
        return self._value


class NumberAttribute(UniledAttribute):
    """UniLED Number Attribute Class"""

    _min: int
    _max: int
    _inc: int

    def __init__(
        self,
        attr: str,
        name: str,
        icon: str,
        max: int,
        min: int = 1,
        inc: int = 1,
        key: str | None = None,
        enabled: bool = True,
        group: UniledGroup = UniledGroup.STANDARD,
        extra: list | None = None,
    ) -> None:
        super().__init__(
           "number",
           attr,
           name,
           icon,
           key,
           enabled,
           group,
           extra 
        )
        self._max = max
        self._min = min
        self._inc = inc

    @property
    def min_value(self) -> int:
        return self._min

    @property
    def max_value(self) -> int:
        return self._max

    @property
    def step(self) -> int:
        return self._inc
