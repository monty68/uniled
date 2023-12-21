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
    """UniLED Base Feature Class"""

    _reload: bool = False
    _enabled: bool = True
    _group: UniledGroup = UniledGroup.STANDARD
    _type: str
    _attr: str
    _name: str | None = None
    _icon: str | None = None
    _key: str | None = None
    _extra: list | None = None

    def __init__(
        self,
        attr: str,
        name: str | None = None,
        key: str | None = None,
    ) -> None:
        self._attr = attr
        self._name = name
        self._key = key

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
    def type(self) -> str:
        return self._type

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


class UniledSensor(UniledAttribute):
    """UniLED Sensor Feature Class"""

    def __init__(
        self,
        group: UniledGroup,
        enabled: bool,
        attr: str,
        name: str,
        icon: str,
        key: str | None,
        extra: list | None = None,
    ) -> None:
        self._type = "sensor"
        self._enabled = enabled
        self._group = group
        self._attr = attr
        self._name = name
        self._icon = icon
        self._key = key
        self._extra = extra


class UniledSelect(UniledAttribute):
    """UniLED Select Feature Class"""

    def __init__(
        self,
        group: UniledGroup,
        enabled: bool,
        attr: str,
        name: str,
        icon: str,
        key: str | None,
        extra: list | None = None,
    ) -> None:
        self._type = "select"
        self._enabled = enabled
        self._group = group
        self._attr = attr
        self._name = name
        self._icon = icon
        self._key = key
        self._extra = extra


class UniledSwitch(UniledAttribute):
    """UniLED Switch Feature Class"""

    def __init__(
        self,
        group: UniledGroup,
        enabled: bool,
        attr: str,
        name: str,
        icon_on: str,
        icon_off: str | None = None,
        key: str | None = None,
        extra: list | None = None,
    ) -> None:
        self._type = "switch"
        self._enabled = enabled
        self._group = group
        self._attr = attr
        self._name = name
        self._icon = icon_on
        self._icon2 = icon_off
        self._key = key
        self._extra = extra

    def state_icon(self, state: bool = True) -> str:
        """Return icon depending on state"""
        return self._icon if state or not self._icon2 else self._icon2


class UniledButton(UniledAttribute):
    """UniLED Sensor Feature Class"""

    def __init__(
        self,
        group: UniledGroup,
        enabled: bool,
        attr: str,
        name: str,
        icon: str | None = None,
        key: str | None = None,
        value: Any = True,
        extra: list | None = None,
    ) -> None:
        self._type = "button"
        self._enabled = enabled
        self._group = group
        self._attr = attr
        self._name = name
        self._icon = icon
        self._key = key
        self._value = value
        self._extra = extra

    @property
    def value(self) -> int:
        return self._value


class UniledNumber(UniledAttribute):
    """UniLED Number Feature Class"""

    _min: int
    _max: int
    _inc: int

    def __init__(
        self,
        group: UniledGroup,
        enabled: bool,
        attr: str,
        name: str,
        icon: str,
        key: str | None,
        max: int,
        min: int = 1,
        inc: int = 1,
        extra: list | None = None,
    ) -> None:
        self._type = "number"
        self._enabled = enabled
        self._group = group
        self._attr = attr
        self._name = name
        self._icon = icon
        self._key = key
        self._max = max
        self._min = min
        self._inc = inc
        self._extra = extra

    @property
    def min_value(self) -> int:
        return self._min

    @property
    def max_value(self) -> int:
        return self._max

    @property
    def step(self) -> int:
        return self._inc
