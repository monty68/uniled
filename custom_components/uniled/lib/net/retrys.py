import logging
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast

from ..const import UNILED_DEVICE_RETRYS

_LOGGER = logging.getLogger(__name__)


WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])


if TYPE_CHECKING:
    from .device import UniledNetDevice


def _socket_retry(attempts: int = UNILED_DEVICE_RETRYS) -> WrapFuncType:  # type: ignore[type-var, misc]
    """Define a wrapper to retry on socket failures."""

    def decorator_retry(func: WrapFuncType) -> WrapFuncType:
        def _retry_wrap(
            self: "UniledNetDevice",
            *args: Any,
            retry: int = attempts,
            **kwargs: Any,
        ) -> Any:
            attempts_remaining = retry + 1
            while attempts_remaining:
                attempts_remaining -= 1
                try:
                    ret = func(self, *args, **kwargs)
                    self.set_available(f"{func.__name__} was successful")
                    return ret
                except OSError as ex:
                    _LOGGER.debug(
                        "%s: socket error while calling %s: %s", self.ip_address, func, ex
                    )
                    if attempts_remaining:
                        continue
                    self.set_unavailable(f"{func.__name__} failed: {ex}")
                    self._close()
                    # We need to raise or the device will
                    # always be seen as available in Home Assistant
                    # when it goes offline
                    raise

        return cast(WrapFuncType, _retry_wrap)

    return cast(WrapFuncType, decorator_retry)