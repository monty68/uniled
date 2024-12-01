"""UniLED Device Discovery."""

from __future__ import annotations
from typing import Any, Final, Optional, Union, Literal, cast
from collections import UserDict
from dataclasses import dataclass
from abc import abstractmethod
from .model import UniledModel
from .typing import TypedDict
from .const import (
    ATTR_UL_LOCAL_NAME,
    ATTR_UL_IP_ADDRESS,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_MODEL_CODE,
    ATTR_UL_MODEL_NAME,
    ATTR_UL_TRANSPORT,
    ATTR_UL_SOURCE,
    CONF_HA_ADDRESS as CONF_ADDRESS,
    CONF_HA_CODE as CONF_CODE,
    CONF_HA_HOST as CONF_HOST,
    CONF_HA_MODEL as CONF_MODEL,
    CONF_HA_NAME as CONF_NAME,
    CONF_UL_OPTIONS as CONF_OPTIONS,
    CONF_UL_SOURCE as CONF_SOURCE,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
    UNILED_TRANSPORT_BLE as TRANSPORT_BLE,
    UNILED_TRANSPORT_NET as TRANSPORT_NET,
    UNILED_TRANSPORT_ZNG as TRANSPORT_ZNG,
)
import importlib

CONF_TO_DISCOVERY: Final = {
    CONF_NAME: ATTR_UL_LOCAL_NAME,
    CONF_HOST: ATTR_UL_IP_ADDRESS,
    CONF_CODE: ATTR_UL_MODEL_CODE,
    CONF_MODEL: ATTR_UL_MODEL_NAME,
    CONF_ADDRESS: ATTR_UL_MAC_ADDRESS,
    CONF_TRANSPORT: ATTR_UL_TRANSPORT,
    CONF_SOURCE: ATTR_UL_SOURCE,
}

UNILED_DISCOVERY_SOURCE_UDP: Final = "UDP"
UNILED_DISCOVERY_SOURCE_DHCP: Final = "DHCP"


##
## UniLed Base Model Proxy Class
##
@dataclass(frozen=True)
class UniledProxy:
    """UniLED Base Model Proxy."""

    @abstractmethod
    def match_model_name(self, name: str) -> UniledModel | None:
        """Match a devices model name"""

    @abstractmethod
    def match_model_code(self, code: int) -> UniledModel | None:
        """Match a devices model code(s)"""


##
## UniLED Device Discovery Class
##
SourceTypes = Union[str, bytes, dict]

@dataclass
class UniledDiscovery(UserDict):
    """UniLED Discovered Device."""

    transport: Literal["net", "ble"]
    source: Optional[SourceTypes] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    local_name: Optional[str] = None
    model_name: Optional[str] = None
    model_code: Optional[int] = None
    options: Optional[dict[str, Any]] = None

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)
    
    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        setattr(self, item, value)

    @property
    def model(self) -> UniledModel | None:
        """Model Class"""
        model = None
        if self.model_name:
            model = UniledDiscovery.match_model_name(self.transport, self.model_name)
        if self.model_code is not None:
            if (model := UniledDiscovery.match_model_code(self.transport, self.model_code)):
                self.model_name = model.model_name
        return model

    @staticmethod
    def match_model_name(transport: str, name: str) -> UniledModel | None:
        """Lookup model from name"""
        if not name or not transport:
            return None

        from .models_db import (
            UNILED_MODELS,
        )  # pylint: disable=import-outside-toplevel

        if not (
            models_db := (
                UNILED_MODELS[transport] if transport in UNILED_MODELS else None
            )
        ):
            return None

        for model in models_db:
            if isinstance(model, UniledProxy):
                proxy = cast(UniledProxy, model)
                proxy_model = proxy.match_model_name(name)
                if isinstance(proxy_model, UniledModel):
                    return proxy_model
            elif not isinstance(model, UniledModel):
                continue
            elif model.model_name == name:
                return model
        return None

    @staticmethod
    def match_model_code(transport: str, code: int) -> UniledModel | None:
        """Match a device model code"""
        if not transport:
            return None

        from .models_db import (
            UNILED_MODELS,
        )  # pylint: disable=import-outside-toplevel

        if not (
            models_db := (
                UNILED_MODELS[transport] if transport in UNILED_MODELS else None
            )
        ):
            return None

        for model in models_db:
            if isinstance(model, UniledProxy):
                proxy = cast(UniledProxy, model)
                proxy_model = proxy.match_model_code(code)
                if isinstance(proxy_model, UniledModel):
                    return proxy_model
            elif not isinstance(model, UniledModel):
                continue
            elif isinstance(model.model_code, list):
                if code in model.model_code:
                    return model
            elif code == model.model_code:
                return model
        return None
