"""UniLED Device Discovery."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Final, Literal, cast

from .const import (
    ATTR_UL_IP_ADDRESS,
    ATTR_UL_LOCAL_NAME,
    ATTR_UL_MAC_ADDRESS,
    ATTR_UL_MODEL_CODE,
    ATTR_UL_MODEL_NAME,
    ATTR_UL_SOURCE,
    ATTR_UL_TRANSPORT,
    CONF_HA_ADDRESS as CONF_ADDRESS,
    CONF_HA_CODE as CONF_CODE,
    CONF_HA_HOST as CONF_HOST,
    CONF_HA_MODEL as CONF_MODEL,
    CONF_HA_NAME as CONF_NAME,
    CONF_UL_SOURCE as CONF_SOURCE,
    CONF_UL_TRANSPORT as CONF_TRANSPORT,
)
from .model import UniledModel
from .typing import TypedDict

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
        """Match a devices model name."""

    @abstractmethod
    def match_model_code(self, code: int) -> UniledModel | None:
        """Match a devices model code(s)."""


##
## UniLED Device Discovery Class
##
class UniledDiscovery(TypedDict):
    """UniLED Discovered Device."""

    transport: Literal["net", "ble"]
    source: Any = None
    mac_address: str | None = None
    ip_address: str | None = None
    local_name: str | None = None
    model_code: int | None = None
    model_name: str | None = None

    @staticmethod
    def match_model_name(transport: str, name: str) -> UniledModel | None:
        """Lookup model from name."""
        if not name or not transport:
            return None

        from .models_db import UNILED_MODELS  # pylint: disable=import-outside-toplevel

        if not (models_db := (UNILED_MODELS.get(transport, None))):
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
        """Match a device model code."""
        if not transport:
            return None

        from .models_db import UNILED_MODELS  # pylint: disable=import-outside-toplevel

        if not (models_db := (UNILED_MODELS.get(transport, None))):
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


def discovery_model(discovery: UniledDiscovery) -> UniledModel | None:
    """Find discovered devices model."""
    model = None
    if discovery[ATTR_UL_MODEL_NAME]:
        model = UniledDiscovery.match_model_name(
            discovery[ATTR_UL_TRANSPORT], discovery[ATTR_UL_MODEL_NAME]
        )
    # if discovery[ATTR_UL_MODEL_CODE] is not None:
    if model is None and discovery[ATTR_UL_MODEL_CODE] is not None:
        if model := UniledDiscovery.match_model_code(
            discovery[ATTR_UL_TRANSPORT], discovery[ATTR_UL_MODEL_CODE]
        ):
            discovery[ATTR_UL_MODEL_NAME] = model.model_name
    return model
