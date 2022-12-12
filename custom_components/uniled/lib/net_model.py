"""UniLED NETwork Base Model"""
from __future__ import annotations
from dataclasses import dataclass
from abc import abstractmethod

from .classes import UNILEDModel

import logging

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UNILEDNETModel(UNILEDModel):
    """UniLED NETwork Model Class"""
